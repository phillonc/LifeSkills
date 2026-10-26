"""HTTP acceptance and privacy checks against a fresh, isolated SQLite database."""
import http.client
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import os

APP = Path(__file__).resolve().parents[1]


class Client:
    def __init__(self, port):
        self.port = port
        self.cookie = ''

    def request(self, method, path, data=None, headers=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.port, timeout=5)
        request_headers = {'X-Requested-With': 'LifeSkills'}
        if self.cookie:
            request_headers['Cookie'] = self.cookie
        body = None
        if data is not None:
            body = json.dumps(data)
            request_headers['Content-Type'] = 'application/json'
        if headers:
            request_headers.update(headers)
        connection.request(method, path, body, request_headers)
        response = connection.getresponse()
        status = response.status
        response_headers = dict(response.getheaders())
        if response.getheader('Set-Cookie'):
            self.cookie = response.getheader('Set-Cookie').split(';')[0]
        raw = response.read()
        connection.close()
        try:
            payload = json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            payload = raw.decode(errors='replace')
        return status, payload, response_headers

class ServerFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            cls.port = sock.getsockname()[1]
        cls.db = Path(cls.temp.name) / 'test.sqlite3'
        env = dict(os.environ, LIFE_SKILLS_DEV='1', LIFE_SKILLS_DB=str(cls.db),
                   LIFE_SKILLS_BASE_URL=f'http://127.0.0.1:{cls.port}')
        cls.process = subprocess.Popen([sys.executable, str(APP / 'server.py'), '--port', str(cls.port)],
                                       env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for _ in range(100):
            try:
                if Client(cls.port).request('GET', '/api/health')[0] == 200:
                    break
            except OSError:
                time.sleep(.05)
        else:
            raise RuntimeError('Server did not start')
        cls.private_catalog = json.loads((APP / 'content.json').read_text())
        cls.alice = cls.create_user('alice@example.test')
        cls.bob = cls.create_user('bob@example.test')

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()
        cls.process.communicate(timeout=5)
        cls.temp.cleanup()

    @classmethod
    def create_user(cls, email):
        client = Client(cls.port)
        payload = {'email': email, 'name': email.split('@')[0], 'password': 'SecurePass123!',
                   'confirm_password': 'SecurePass123!', 'consent': True}
        assert client.request('POST', '/api/register', payload)[0] == 200
        assert client.request('POST', '/api/login', payload)[0] == 403
        token = cls.token(email, 'verify')
        assert client.request('POST', '/api/verify', {'token': token})[0] == 200
        assert client.request('POST', '/api/verify', {'token': token})[0] == 400
        status, _, headers = client.request('POST', '/api/login', payload)
        assert status == 200
        assert 'HttpOnly' in headers['Set-Cookie'] and 'SameSite=Strict' in headers['Set-Cookie']
        return client

    @classmethod
    def token(cls, email, kind):
        mails = [json.loads(line) for line in (cls.db.parent / 'outbox.jsonl').read_text().splitlines()]
        return next(m['link'].split('=', 1)[1] for m in reversed(mails) if m['to'] == email and m['kind'] == kind)



class AcceptanceTests(ServerFixture):
    def test_01_registration_validation_and_private_routes(self):
        anonymous = Client(self.port)
        self.assertEqual(anonymous.request('GET', '/api/me')[0], 401)
        self.assertEqual(anonymous.request('GET', '/api/export')[0], 401)
        payload = {'email': 'invalid', 'name': 'New', 'password': 'short', 'confirm_password': 'short', 'consent': True}
        self.assertEqual(anonymous.request('POST', '/api/register', payload)[0], 400)
        payload.update(email='alice@example.test', password='SecurePass123!', confirm_password='SecurePass123!')
        self.assertEqual(anonymous.request('POST', '/api/register', payload)[0], 409)
        payload.update(email='new@example.test', consent=False)
        self.assertEqual(anonymous.request('POST', '/api/register', payload)[0], 400)

    def test_02_csrf_and_security_headers(self):
        self.assertEqual(self.alice.request('POST', '/api/logout', {}, {'X-Requested-With': ''})[0], 403)
        self.assertEqual(self.alice.request('POST', '/api/logout', {}, {'Origin': 'https://evil.example'})[0], 403)
        status, _, headers = self.alice.request('GET', '/')
        self.assertEqual(status, 200)
        self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
        self.assertIn("frame-ancestors 'none'", headers['Content-Security-Policy'])
        self.assertEqual(self.alice.request('GET', '/sources/03-Life-Skills-Product-Requirements-Document-PRD-.txt')[0], 404)
        self.assertEqual(self.alice.request('GET', '/data/outbox.jsonl')[0], 404)
        self.assertEqual(self.alice.request('GET', '/../server.py')[0], 404)

    def test_03_catalog_and_server_scored_progress(self):
        status, data, _ = self.alice.request('GET', '/api/catalog')
        self.assertEqual(status, 200)
        self.assertEqual(len(data['topics']), 15)
        self.assertEqual(len([t for t in data['topics'] if t['domain'] == 'Personal Development']), 9)
        for topic in data['topics']:
            for item in topic['lessons']:
                for question in item['quiz']:
                    self.assertNotIn('answer', question)
                    self.assertNotIn('explanation', question)
        lesson = self.private_catalog[0]['lessons'][0]
        wrong = [(q['answer'] + 1) % len(q['options']) for q in lesson['quiz']]
        payload = {'lesson_id': lesson['id'], 'reflection': 'I will name my emotions before choosing a response.', 'answers': wrong, 'score': 100, 'passed': True}
        status, data, _ = self.alice.request('POST', '/api/complete', payload)
        self.assertEqual(status, 200)
        self.assertFalse(data['passed'])
        payload['answers'] = [q['answer'] for q in lesson['quiz']]
        status, data, _ = self.alice.request('POST', '/api/complete', payload)
        self.assertEqual((status, data['passed'], data['score']), (200, True, 100))
        self.alice.request('POST', '/api/complete', payload)
        alice = self.alice.request('GET', '/api/me')[1]
        self.assertEqual(sum(p['lesson_id'] == lesson['id'] for p in alice['progress']), 1)
        self.assertIn('First step', alice['badges'])
        self.assertEqual(alice['streak'], 1)
        self.assertEqual(self.bob.request('GET', '/api/me')[1]['progress'], [])

    def test_04_journal_privacy_and_delete_ownership(self):
        status, data, _ = self.alice.request('POST', '/api/journal', {'text': '<script>alert(1)</script> private reflection', 'mood': 'Calm'})
        self.assertEqual(status, 200)
        entry_id = data['id']
        self.assertEqual(self.bob.request('GET', '/api/journal')[1]['entries'], [])
        self.bob.request('DELETE', f'/api/journal/{entry_id}', {})
        self.assertTrue(any(e['id'] == entry_id for e in self.alice.request('GET', '/api/journal')[1]['entries']))
        self.assertEqual(self.alice.request('POST', '/api/journal', {'text': 'Reflection', 'mood': 'Invalid'})[0], 400)
        self.alice.request('DELETE', f'/api/journal/{entry_id}', {})
        self.assertFalse(any(e['id'] == entry_id for e in self.alice.request('GET', '/api/journal')[1]['entries']))

    def test_05_budget_expenses_and_validation(self):
        payload = {'income': 4000, 'allocations': {'Housing': 1200, 'Transportation': 600, 'Food': 480}, 'month': '2026-10'}
        status, data, _ = self.alice.request('POST', '/api/budget', payload)
        self.assertEqual(status, 200)
        budget = data['budget']
        self.assertEqual(sum(budget['allocations'].values()), 2280)
        self.assertEqual(budget['income'] - sum(budget['allocations'].values()), 1720)
        self.assertEqual(self.bob.request('GET', '/api/budget')[1]['budget'], None)
        expense = {'category': 'Food', 'amount': 12.34, 'note': 'Lunch', 'day': '2026-10-25'}
        self.assertEqual(self.alice.request('POST', '/api/expenses', expense)[0], 200)
        saved = self.alice.request('GET', '/api/budget')[1]['expenses'][0]
        self.assertEqual(saved['amount'], 12.34)
        self.bob.request('DELETE', f"/api/expenses/{saved['id']}", {})
        self.assertEqual(len(self.alice.request('GET', '/api/budget')[1]['expenses']), 1)
        self.assertEqual(self.bob.request('GET', '/api/budget')[1]['expenses'], [])
        for amount in (-1, 'NaN', 'Infinity', True):
            with self.subTest(amount=amount):
                self.assertEqual(self.alice.request('POST', '/api/expenses', dict(expense, amount=amount))[0], 400)
        self.assertEqual(self.alice.request('POST', '/api/expenses', dict(expense, day='2026-02-30'))[0], 400)

    def test_06_calculators_match_prd_and_zero_rate(self):
        payload = {'kind': 'simple', 'amount': 1000, 'rate': 5, 'years': 2, 'frequency': 12}
        self.assertEqual(self.alice.request('POST', '/api/calculators', payload)[1]['total'], 1100)
        compound = self.alice.request('POST', '/api/calculators', dict(payload, kind='compound', years=5))[1]
        self.assertAlmostEqual(compound['total'], 1000 * (1 + .05 / 12) ** 60, places=2)
        loan = self.alice.request('POST', '/api/calculators', dict(payload, kind='loan', amount=1200, rate=0, years=1))[1]
        self.assertEqual(loan['monthly_payment'], 100)
        self.assertEqual(loan['interest'], 0)
        for rate in (-1, 'NaN', 'Infinity', 101):
            self.assertEqual(self.alice.request('POST', '/api/calculators', dict(payload, rate=rate))[0], 400)

    def test_07_goals_persist_and_are_owned(self):
        topic_id = self.private_catalog[0]['id']
        status, data, _ = self.alice.request('POST', '/api/goals', {'name': 'Master Emotional Intelligence', 'topic_id': topic_id, 'deadline': '2099-12-31'})
        self.assertEqual(status, 200)
        goal_id = data['id']
        self.bob.request('DELETE', f'/api/goals/{goal_id}', {})
        goal = next(g for g in self.alice.request('GET', '/api/me')[1]['goals'] if g['id'] == goal_id)
        self.assertEqual(goal['completed'], 1)
        self.assertEqual(goal['total'], 5)
        self.assertEqual(self.bob.request('GET', '/api/me')[1]['goals'], [])

    def test_08_reset_revokes_sessions_export_and_account_deletion(self):
        charlie = self.create_user('charlie@example.test')
        charlie.request('POST', '/api/journal', {'text': 'Delete this personal data', 'mood': 'Mixed'})
        charlie.request('POST', '/api/forgot-password', {'email': 'charlie@example.test'})
        token = self.token('charlie@example.test', 'reset')
        self.assertEqual(charlie.request('POST', '/api/reset-password', {'token': token, 'password': 'NewPassword456!'})[0], 200)
        self.assertEqual(charlie.request('GET', '/api/me')[0], 401)
        self.assertEqual(charlie.request('POST', '/api/reset-password', {'token': token, 'password': 'NewPassword456!'})[0], 400)
        self.assertEqual(charlie.request('POST', '/api/login', {'email': 'charlie@example.test', 'password': 'SecurePass123!'})[0], 401)
        self.assertEqual(charlie.request('POST', '/api/login', {'email': 'charlie@example.test', 'password': 'NewPassword456!'})[0], 200)
        exported = charlie.request('GET', '/api/export')[1]
        self.assertEqual(exported['profile']['email'], 'charlie@example.test')
        self.assertEqual(len(exported['journal']), 1)
        self.assertNotIn('password', exported['profile'])
        self.assertNotIn('sessions', exported)
        self.assertEqual(charlie.request('DELETE', '/api/account', {'password': 'wrong'})[0], 403)
        self.assertEqual(charlie.request('DELETE', '/api/account', {'password': 'NewPassword456!'})[0], 200)
        self.assertEqual(charlie.request('GET', '/api/export')[0], 401)
        outbox = (self.db.parent / 'outbox.jsonl').read_text()
        self.assertNotIn('charlie@example.test', outbox)
        self.assertIn('alice@example.test', outbox)
        import sqlite3
        with sqlite3.connect(self.db) as connection:
            self.assertEqual(connection.execute('SELECT count(*) FROM users WHERE email=?', ('charlie@example.test',)).fetchone()[0], 0)
            self.assertEqual(connection.execute("SELECT count(*) FROM journal WHERE text='Delete this personal data'").fetchone()[0], 0)

    def test_09_static_entry_assets_resolve(self):
        import re
        status, html, _ = Client(self.port).request('GET', '/')
        self.assertEqual(status, 200)
        paths = re.findall(r'(?:src|href)="(/[^"#]+)"', html)
        self.assertTrue(paths)
        for path in paths:
            with self.subTest(path=path):
                status, body, _ = Client(self.port).request('GET', path)
                self.assertEqual(status, 200)
                self.assertTrue(body)

    def test_10_logout_invalidates_session(self):
        other = Client(self.port)
        self.assertEqual(other.request('POST', '/api/login', {'email': 'bob@example.test', 'password': 'SecurePass123!'})[0], 200)
        old_cookie = other.cookie
        self.assertEqual(other.request('POST', '/api/logout', {})[0], 200)
        other.cookie = old_cookie
        self.assertEqual(other.request('GET', '/api/me')[0], 401)

    def test_11_invalid_nested_payloads_are_client_errors(self):
        self.assertEqual(self.alice.request('POST', '/api/profile', {'name': 'Alice', 'interests': [[]]})[0], 400)
        self.assertEqual(self.alice.request('POST', '/api/goals', {'name': 'Goal', 'topic_id': [], 'deadline': '2099-12-31'})[0], 400)


if __name__ == '__main__':
    unittest.main()
