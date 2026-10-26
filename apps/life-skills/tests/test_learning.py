"""Persistent learning, goal-template, analytics and savings acceptance checks."""
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
from datetime import date, timedelta, datetime, timezone

from test_http import APP, Client, ServerFixture


class LearningTests(ServerFixture):
    def login_again(self, client, email='alice@example.test'):
        self.assertEqual(client.request('POST', '/api/logout', {})[0], 200)
        self.assertEqual(client.request('POST', '/api/login', {'email': email, 'password': 'SecurePass123!'})[0], 200)

    def test_01_drafts_survive_relogin_and_stay_private(self):
        lesson = self.private_catalog[0]['lessons'][0]
        route = '/api/drafts/' + lesson['id']
        self.assertEqual(Client(self.port).request('GET', route)[0], 401)
        self.assertEqual(self.alice.request('GET', route)[1]['draft'], None)
        payload = {'reflection': 'A private unfinished reflection.', 'answers': [1, None], 'elapsed_seconds': 0}
        self.assertEqual(self.alice.request('POST', route, payload)[0], 200)
        self.assertEqual(self.bob.request('GET', route)[1]['draft'], None)
        self.login_again(self.alice)
        draft = self.alice.request('GET', route)[1]['draft']
        self.assertEqual(draft['reflection'], payload['reflection'])
        self.assertEqual(draft['answers'], payload['answers'])
        me = self.alice.request('GET', '/api/me')[1]
        self.assertTrue(me['resume'])
        self.assertTrue(any(d['lesson_id'] == lesson['id'] for d in me['drafts']))
        self.assertFalse(self.bob.request('GET', '/api/me')[1]['drafts'])
        for elapsed in (-1, 121, True, 'NaN', 'Infinity', []):
            with self.subTest(elapsed=elapsed):
                self.assertEqual(self.alice.request('POST', route, dict(payload, elapsed_seconds=elapsed))[0], 400)
        for answers in ([0], [True, None], [99, None], 'not-list'):
            with self.subTest(answers=answers):
                self.assertEqual(self.alice.request('POST', route, dict(payload, answers=answers))[0], 400)
        self.assertEqual(self.alice.request('GET', '/api/drafts/missing-lesson')[0], 404)

    def test_02_unearned_time_and_duplicate_save_do_not_inflate_progress(self):
        lesson = self.private_catalog[0]['lessons'][1]
        route = '/api/drafts/' + lesson['id']
        payload = {'reflection': 'Practise listening before responding.', 'answers': [None] * len(lesson['quiz']), 'elapsed_seconds': 120}
        self.assertEqual(self.bob.request('POST', route, payload)[0], 200)
        first = self.bob.request('GET', route)[1]['draft']['time_spent_seconds']
        self.assertEqual(first, 0)
        self.bob.request('POST', route, payload)
        second = self.bob.request('GET', route)[1]['draft']['time_spent_seconds']
        self.assertLessEqual(second - first, 1)
        self.bob.request('POST', route, payload)
        third = self.bob.request('GET', route)[1]['draft']['time_spent_seconds']
        self.assertLessEqual(third - second, 1)
        # Simulate one minute of wall-clock activity without a slow sleeping test.
        status, created, _ = self.bob.request('POST', '/api/goals', {'name': 'One minute of practice', 'type': 'time', 'target': 1, 'deadline': '2099-12-31'})
        self.assertEqual(status, 200)
        with sqlite3.connect(self.db) as connection:
            connection.execute("UPDATE learning_timers SET last_seen=? WHERE user_id=(SELECT id FROM users WHERE email='bob@example.test')", (time.time() - 61,))
        payload['elapsed_seconds'] = 60
        self.assertEqual(self.bob.request('POST', route, payload)[0], 200)
        credited = self.bob.request('GET', route)[1]['draft']['time_spent_seconds']
        self.assertEqual(credited - third, 60)
        self.bob.request('POST', route, payload)
        self.assertEqual(self.bob.request('GET', route)[1]['draft']['time_spent_seconds'], credited)
        goals = self.bob.request('GET', '/api/goals')[1]['goals']
        goal = next(g for g in goals if g['id'] == created['id'])
        self.assertEqual(goal['completed'], 1)
        self.assertEqual(goal['status'], 'completed')
        analytics = self.bob.request('GET', '/api/me')[1]['analytics']
        self.assertEqual(analytics['total_seconds'], credited)
        self.assertEqual(len(analytics['trend']), 14)
        # Switching lessons invalidates the previous active interval.
        self.bob.request('GET', '/api/drafts/' + self.private_catalog[0]['lessons'][2]['id'])
        self.bob.request('POST', route, payload)
        self.assertEqual(self.bob.request('GET', route)[1]['draft']['time_spent_seconds'], credited)
        self.bob.request('DELETE', '/api/goals/' + str(created['id']), {})

    def test_03_all_goal_templates_validate_and_compute(self):
        topic = self.private_catalog[0]['id']
        deadline = (date.today() + timedelta(days=30)).isoformat()
        base = {'name': 'A measurable learning goal', 'topic_id': topic, 'deadline': deadline}
        ids = {}
        for kind, target in [('topic', 5), ('daily', 2), ('skill', 1), ('time', 15)]:
            status, data, _ = self.alice.request('POST', '/api/goals', dict(base, type=kind, target=target))
            self.assertEqual(status, 200, data)
            ids[kind] = data['id']
        for extra in ({'type': 'unknown'}, {'type': []}, {'type': 'daily', 'target': 0}, {'type': 'time', 'target': -2}, {'type': 'skill', 'target': True}, {'type': 'skill', 'target': 1.5}):
            with self.subTest(extra=extra):
                self.assertEqual(self.alice.request('POST', '/api/goals', dict(base, **extra))[0], 400)
        lesson = self.private_catalog[0]['lessons'][0]
        status, data, _ = self.alice.request('POST', '/api/complete', {'lesson_id': lesson['id'], 'reflection': 'I pause, name the feeling and decide what to do.', 'answers': [q['answer'] for q in lesson['quiz']]})
        self.assertEqual(status, 200, data)
        self.assertTrue(data['passed'])
        goals = {g['id']: g for g in self.alice.request('GET', '/api/goals')[1]['goals']}
        self.assertEqual(goals[ids['topic']]['completed'], 1)
        self.assertEqual(goals[ids['daily']]['completed'], 1)
        self.assertEqual(goals[ids['skill']]['completed'], 1)
        self.assertEqual(goals[ids['time']]['completed'], 0)
        self.assertEqual(self.bob.request('GET', '/api/goals')[1]['goals'], [])
        self.assertIsNone(self.alice.request('GET', '/api/drafts/' + lesson['id'])[1]['draft'])
        self.login_again(self.alice)
        self.assertEqual(len(self.alice.request('GET', '/api/goals')[1]['goals']), 4)

    def test_04_analytics_reminders_are_private_and_server_derived(self):
        me = self.alice.request('GET', '/api/me')[1]
        self.assertIn('analytics', me)
        self.assertIn('total_seconds', me['analytics'])
        self.assertIn('topics', me['analytics'])
        self.assertIn('trend', me['analytics'])
        self.assertIsInstance(me['goal_reminders'], list)
        # A goal due today produces an in-app reminder, and cannot leak to another user.
        status, created, _ = self.alice.request('POST', '/api/goals', {'name': 'Due today private goal', 'type': 'daily', 'target': 30, 'deadline': date.today().isoformat()})
        self.assertEqual(status, 200)
        reminders = self.alice.request('GET', '/api/me')[1]['goal_reminders']
        self.assertTrue(any('Due today private goal' in json.dumps(r) for r in reminders))
        self.assertNotIn('Due today private goal', json.dumps(self.bob.request('GET', '/api/me')[1]))
        self.bob.request('DELETE', '/api/goals/' + str(created['id']), {})
        self.assertTrue(any(g['id'] == created['id'] for g in self.alice.request('GET', '/api/goals')[1]['goals']))

    def test_05_savings_money_precision_ownership_and_export(self):
        payload = {'name': 'Emergency reserve', 'target_amount': '1000.00', 'deadline': '2099-12-31'}
        status, created, _ = self.alice.request('POST', '/api/financial-goals', payload)
        self.assertEqual(status, 200, created)
        gid = created['id']
        route = f'/api/financial-goals/{gid}/contributions'
        self.assertEqual(self.bob.request('POST', route, {'amount': 1, 'note': 'Not mine'})[0], 404)
        for amount in ('0.10', '0.20'):
            self.assertEqual(self.alice.request('POST', route, {'amount': amount, 'note': 'Saved change'})[0], 200)
        for amount in (-1, 0, True, 'NaN', 'Infinity', '0.001'):
            with self.subTest(amount=amount):
                self.assertEqual(self.alice.request('POST', route, {'amount': amount, 'note': ''})[0], 400)
        goals = self.alice.request('GET', '/api/financial-goals')[1]['goals']
        goal = next(g for g in goals if g['id'] == gid)
        self.assertEqual(goal['saved_amount'], .3)
        self.assertEqual(goal['target_amount'], 1000)
        contributions = goal['contributions']
        self.assertEqual(len(contributions), 2)
        cid = contributions[0]['id']
        self.bob.request('DELETE', f'{route}/{cid}', {})
        self.assertEqual(len(self.alice.request('GET', '/api/financial-goals')[1]['goals'][0]['contributions']), 2)
        exported = self.alice.request('GET', '/api/export')[1]
        self.assertTrue(exported['financial_goals'])
        self.assertEqual(len(exported['financial_contributions']), 2)
        self.assertFalse(self.bob.request('GET', '/api/export')[1]['financial_contributions'])
        self.login_again(self.alice)
        self.assertEqual(self.alice.request('GET', '/api/financial-goals')[1]['goals'][0]['saved_amount'], .3)
        self.assertEqual(self.alice.request('DELETE', f'{route}/{cid}', {})[0], 200)
        self.bob.request('DELETE', f'/api/financial-goals/{gid}', {})
        self.assertTrue(self.alice.request('GET', '/api/financial-goals')[1]['goals'])
        self.assertEqual(self.alice.request('DELETE', f'/api/financial-goals/{gid}', {})[0], 200)
        self.assertFalse(self.alice.request('GET', '/api/export')[1]['financial_contributions'])

    def test_06_account_deletion_cascades_new_private_records(self):
        dana = self.create_user('dana@example.test')
        lesson = self.private_catalog[0]['lessons'][0]
        self.assertEqual(dana.request('POST', '/api/drafts/' + lesson['id'], {'reflection': 'Remove this unfinished private reflection', 'elapsed_seconds': 0})[0], 200)
        status, created, _ = dana.request('POST', '/api/financial-goals', {'name': 'Private reserve', 'target_amount': 100, 'deadline': '2099-12-31'})
        self.assertEqual(status, 200)
        self.assertEqual(dana.request('POST', '/api/financial-goals/' + str(created['id']) + '/contributions', {'amount': 12.34, 'note': 'Remove this note'})[0], 200)
        uid = dana.request('GET', '/api/me')[1]['user']['id']
        self.assertEqual(dana.request('DELETE', '/api/account', {'password': 'SecurePass123!'})[0], 200)
        with sqlite3.connect(self.db) as connection:
            for table in ('drafts', 'learning_timers', 'learning_events', 'financial_goals', 'financial_contributions'):
                with self.subTest(table=table):
                    self.assertEqual(connection.execute(f'SELECT count(*) FROM {table} WHERE user_id=?', (uid,)).fetchone()[0], 0)


    def test_07_goal_windows_exclude_old_activity_and_keep_earned_streak(self):
        eve = self.create_user('eve@example.test')
        lid = self.private_catalog[0]['lessons'][0]['id']
        uid = eve.request('GET', '/api/me')[1]['user']['id']
        time_goal = eve.request('POST', '/api/goals', {'name': 'This week only', 'type': 'time', 'target': 2, 'deadline': '2099-12-31'})[1]['id']
        daily_goal = eve.request('POST', '/api/goals', {'name': 'Two days earned', 'type': 'daily', 'target': 2, 'deadline': '2099-12-31'})[1]['id']
        now = datetime.now(timezone.utc)
        monday = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        event = lambda dt: dt.isoformat()
        with sqlite3.connect(self.db) as connection:
            connection.execute('UPDATE goals SET created=? WHERE id=?', (event(monday), time_goal))
            connection.execute('UPDATE goals SET created=? WHERE id=?', (event(now - timedelta(days=7)), daily_goal))
            connection.executemany('INSERT INTO learning_events(user_id,lesson_id,kind,seconds,created) VALUES(?,?,?,?,?)', [
                (uid, lid, 'time', 60, event(now)),
                (uid, lid, 'time', 600, event(monday - timedelta(seconds=1))),
                (uid, lid, 'completion', 0, event(now - timedelta(days=4))),
                (uid, lid, 'completion', 0, event(now - timedelta(days=3))),
            ])
        goals = {g['id']: g for g in eve.request('GET', '/api/goals')[1]['goals']}
        self.assertEqual(goals[time_goal]['completed'], 1)
        self.assertEqual(goals[daily_goal]['completed'], 2)
        self.assertEqual(goals[daily_goal]['status'], 'completed')
        # A newly created skills target cannot claim previous completions.
        skill_goal = eve.request('POST', '/api/goals', {'name': 'Only future new lessons', 'type': 'skill', 'target': 1, 'deadline': '2099-12-31'})[1]['id']
        goals = {g['id']: g for g in eve.request('GET', '/api/goals')[1]['goals']}
        self.assertEqual(goals[skill_goal]['completed'], 0)


class MigrationTests(ServerFixture):
    def test_existing_goal_schema_migrates_without_data_loss(self):
        with tempfile.TemporaryDirectory() as directory:
            old_db = Path(directory) / 'legacy.sqlite3'
            with sqlite3.connect(old_db) as connection:
                connection.executescript('''
                    CREATE TABLE users(id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, name TEXT NOT NULL, password TEXT NOT NULL, verified INTEGER NOT NULL DEFAULT 0, interests TEXT NOT NULL DEFAULT '[]', created TEXT NOT NULL);
                    CREATE TABLE goals(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users ON DELETE CASCADE, name TEXT NOT NULL, topic_id TEXT NOT NULL, deadline TEXT NOT NULL);
                    INSERT INTO users(id,email,name,password,verified,created) VALUES(1,'legacy@example.test','Legacy user','legacy-hash',1,'2026-01-01T00:00:00+00:00');
                    INSERT INTO goals(id,user_id,name,topic_id,deadline) VALUES(1,1,'Keep my existing goal','emotional-intelligence','2099-12-31');
                ''')
            env = dict(os.environ, LIFE_SKILLS_DB=str(old_db), LIFE_SKILLS_DEV='1')
            script = "import runpy; m=runpy.run_path('server.py'); m['init_db'](); m['init_db']()"
            result = subprocess.run([sys.executable, '-c', script], cwd=APP, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            with sqlite3.connect(old_db) as connection:
                connection.row_factory = sqlite3.Row
                row = connection.execute('SELECT * FROM goals WHERE id=1').fetchone()
                self.assertEqual(row['name'], 'Keep my existing goal')
                self.assertEqual(row['topic_id'], 'emotional-intelligence')
                self.assertEqual(row['user_id'], 1)
                self.assertEqual(row['type'], 'topic')
                self.assertEqual(connection.execute('SELECT count(*) FROM goals').fetchone()[0], 1)
                self.assertEqual(connection.execute('SELECT name FROM users WHERE id=1').fetchone()[0], 'Legacy user')
                tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                self.assertTrue({'drafts', 'learning_events', 'financial_goals', 'financial_contributions'} <= tables)
