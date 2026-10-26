"""LifeSkills Quest: dependency-free, single-host pilot. See README for deployment limits."""
from __future__ import annotations
import hashlib, hmac, json, math, os, re, secrets, smtplib, sqlite3, time, threading, ssl
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import learning
from email.message import EmailMessage
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

ROOT = Path(__file__).resolve().parent
DB_PATH = os.environ.get('LIFE_SKILLS_DB', str(ROOT / 'data' / 'life-skills.sqlite3'))
DEV = os.environ.get('LIFE_SKILLS_DEV') == '1'
BASE_URL = os.environ.get('LIFE_SKILLS_BASE_URL', 'http://127.0.0.1:8080').rstrip('/')
CATALOG = json.loads((ROOT / 'content.json').read_text())
LESSONS = {l['id']: l for t in CATALOG for l in t['lessons']}
TOPICS = {t['id']: t for t in CATALOG}
OUTBOX_LOCK = threading.Lock()

class APIError(Exception):
    def __init__(self, message, status=400): self.message, self.status = message, status

def db():
    c = sqlite3.connect(DB_PATH, timeout=15)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    return c

def init_db():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with db() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, name TEXT NOT NULL, password TEXT NOT NULL, verified INTEGER NOT NULL DEFAULT 0, interests TEXT NOT NULL DEFAULT '[]', created TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS tokens(hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users ON DELETE CASCADE, kind TEXT NOT NULL, expires REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions(hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users ON DELETE CASCADE, expires REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS progress(user_id INTEGER NOT NULL REFERENCES users ON DELETE CASCADE, lesson_id TEXT NOT NULL, score INTEGER NOT NULL, reflection TEXT NOT NULL, completed TEXT NOT NULL, PRIMARY KEY(user_id,lesson_id));
        CREATE TABLE IF NOT EXISTS journal(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users ON DELETE CASCADE, text TEXT NOT NULL, mood TEXT NOT NULL, created TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS goals(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users ON DELETE CASCADE, name TEXT NOT NULL, topic_id TEXT NOT NULL, deadline TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS budgets(user_id INTEGER PRIMARY KEY REFERENCES users ON DELETE CASCADE, income INTEGER NOT NULL DEFAULT 0, allocations TEXT NOT NULL DEFAULT '{}', month TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS expenses(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users ON DELETE CASCADE, category TEXT NOT NULL, amount INTEGER NOT NULL, note TEXT NOT NULL, day TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS rate_limits(key TEXT PRIMARY KEY, count INTEGER NOT NULL, started REAL NOT NULL);
        ''')
        learning.migrate(c)
    os.chmod(DB_PATH, 0o600)

def now(): return datetime.now(timezone.utc).isoformat()
def digest(v): return hashlib.sha256(v.encode()).hexdigest()
def password_hash(password):
    salt = secrets.token_hex(16)
    return salt + ':' + hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 310000).hex()
def password_ok(password, stored):
    salt, expected = stored.split(':')
    return hmac.compare_digest(hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 310000).hex(), expected)
def strong_password(p):
    if not isinstance(p,str) or not 8 <= len(p) <= 128 or not all(re.search(x,p) for x in ('[a-z]','[A-Z]','[0-9]')):
        raise APIError('Password must be 8–128 characters with uppercase, lowercase, and number')
def string(data, key, maximum=200, minimum=1):
    value = data.get(key,'')
    if not isinstance(value,str) or not minimum <= len(value.strip()) <= maximum: raise APIError(f'Enter a valid {key} ({minimum}–{maximum} characters)')
    return value.strip()
def money(v):
    if isinstance(v,bool) or not isinstance(v,(str,int,float)): raise APIError('Enter a valid amount')
    try:
        n=Decimal(str(v))
        if not n.is_finite() or n<0 or n>Decimal('1000000000'): raise ValueError()
        return int((n*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
    except (InvalidOperation,ValueError,TypeError): raise APIError('Amount must be between 0 and 1,000,000,000')
def public_user(u): return {k:u[k] for k in ('id','email','name','verified','created')} | {'interests':json.loads(u['interests'])}
def issue_token(c, uid, kind):
    raw = secrets.token_urlsafe(32)
    c.execute('DELETE FROM tokens WHERE user_id=? AND kind=?',(uid,kind))
    c.execute('INSERT INTO tokens VALUES(?,?,?,?)',(digest(raw),uid,kind,time.time()+(86400 if kind=='verify' else 1800)))
    return raw

def send_mail(email, kind, token):
    link = BASE_URL + '/#' + kind + '=' + token
    msg = EmailMessage(); msg['From'] = os.environ.get('LIFE_SKILLS_MAIL_FROM','LifeSkills <noreply@example.invalid>'); msg['To']=email
    msg['Subject'] = 'Verify your LifeSkills account' if kind=='verify' else 'Reset your LifeSkills password'
    msg.set_content(f'Open this link to {kind} your account:\n{link}\n\nIf you did not request this, ignore this message.')
    if DEV:
        path = Path(DB_PATH).parent / 'outbox.jsonl'
        with OUTBOX_LOCK:
            fd = os.open(path, os.O_CREAT | os.O_WRONLY | os.O_APPEND, 0o600)
            with os.fdopen(fd,'a') as f: f.write(json.dumps({'to':email,'kind':kind,'link':link})+'\n')
    else:
        host = os.environ.get('LIFE_SKILLS_SMTP_HOST')
        if not host: raise APIError('Email service is not configured',503)
        with smtplib.SMTP(host, int(os.environ.get('LIFE_SKILLS_SMTP_PORT','587')),timeout=15) as s:
            s.starttls(context=ssl.create_default_context())
            if os.environ.get('LIFE_SKILLS_SMTP_USER'): s.login(os.environ['LIFE_SKILLS_SMTP_USER'],os.environ['LIFE_SKILLS_SMTP_PASSWORD'])
            s.send_message(msg)

class Handler(BaseHTTPRequestHandler):
    server_version = 'LifeSkills/1'
    def setup(self):
        super().setup()
        self.connection.settimeout(15)
    def log_message(self, fmt, *args): pass # No tokens, email addresses, or personal data in access logs.
    def reply(self, value, status=200, cookie=None, mime='application/json'):
        payload = json.dumps(value).encode() if mime=='application/json' else value
        self.send_response(status)
        self.send_header('Content-Type',mime + ('; charset=utf-8' if mime.startswith('text/') else ''))
        self.send_header('Content-Length',str(len(payload)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        if cookie: self.send_header('Set-Cookie',cookie)
        self.end_headers(); self.wfile.write(payload)
    def auth(self,c):
        try:
            jar=cookies.SimpleCookie(self.headers.get('Cookie','')); raw=jar['session'].value
        except (KeyError,cookies.CookieError): raise APIError('Please sign in',401)
        u=c.execute('SELECT users.* FROM sessions JOIN users ON users.id=sessions.user_id WHERE sessions.hash=? AND expires>?',(digest(raw),time.time())).fetchone()
        if not u: raise APIError('Please sign in',401)
        return u
    def throttle(self,c,bucket,limit=20):
        key = bucket + ':' + self.client_address[0]
        row=c.execute('SELECT * FROM rate_limits WHERE key=?',(key,)).fetchone()
        if row and time.time()-row['started']<600:
            if row['count']>=limit: raise APIError('Too many requests. Try again in 10 minutes.',429)
            c.execute('UPDATE rate_limits SET count=count+1 WHERE key=?',(key,))
        else: c.execute('INSERT OR REPLACE INTO rate_limits VALUES(?,?,?)',(key,1,time.time()))
        c.commit()
    def do_GET(self): self.handle_request('GET')
    def do_POST(self): self.handle_request('POST')
    def do_DELETE(self): self.handle_request('DELETE')
    def handle_request(self,method):
        try:
            path=urlsplit(self.path).path
            if not path.startswith('/api/'):
                if method!='GET': raise APIError('Not found',404)
                assets={'/':('index.html','text/html'),'/app.js':('app.js','text/javascript'),'/styles.css':('styles.css','text/css')}
                if path not in assets: raise APIError('Not found',404)
                name,mime=assets[path]; return self.reply((ROOT/'static'/name).read_bytes(),mime=mime)
            data={}
            if method!='GET':
                if self.headers.get('X-Requested-With')!='LifeSkills': raise APIError('Request header required',403)
                origin=self.headers.get('Origin')
                if origin and origin!=BASE_URL: raise APIError('Origin not allowed',403)
                if self.headers.get('Content-Type','').split(';')[0]!='application/json': raise APIError('JSON body required',415)
                try: length=int(self.headers.get('Content-Length','0'))
                except ValueError: raise APIError('Invalid body')
                if not 0 < length <= 65536: raise APIError('Request too large or empty',413)
                try: data=json.loads(self.rfile.read(length))
                except (ValueError,UnicodeError): raise APIError('Invalid JSON')
                if not isinstance(data,dict): raise APIError('JSON object required')
            with db() as c:
                result,cookie=self.route(c,method,path,data)
            self.reply(result,cookie=cookie)
        except APIError as e: self.reply({'error':e.message},e.status)
        except learning.ValidationError as e: self.reply({'error':str(e)},400)
        except (sqlite3.Error,OSError,smtplib.SMTPException): self.reply({'error':'Service unavailable. Please try again.'},503)
        except Exception: self.reply({'error':'Unexpected error'},500)
    def route(self,c,method,path,d):
        cookie=None
        if method=='GET' and path=='/api/health': return {'status':'ok'},None
        if method=='GET' and path=='/api/catalog':
            public=json.loads(json.dumps(CATALOG))
            for topic in public:
                for lesson in topic['lessons']:
                    for q in lesson['quiz']: q.pop('answer',None); q.pop('explanation',None)
            return {'topics':public},None
        if method=='POST' and path in ('/api/register','/api/login','/api/forgot-password','/api/resend-verification'):
            self.throttle(c,path)
            email=string(d,'email',254).lower()
            if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email): raise APIError('Enter a valid email address')
            u=c.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
            if path=='/api/register':
                strong_password(d.get('password')); name=string(d,'name',80)
                if d.get('consent') is not True: raise APIError('Accept the terms and privacy notice')
                if d.get('password')!=d.get('confirm_password'): raise APIError('Passwords do not match')
                if u: raise APIError('An account with this email already exists',409)
                uid=c.execute('INSERT INTO users(email,name,password,created) VALUES(?,?,?,?)',(email,name,password_hash(d['password']),now())).lastrowid
                token=issue_token(c,uid,'verify'); send_mail(email,'verify',token)
                return {'message':'Please check your email to verify your account'},None
            if path=='/api/login':
                p=d.get('password','')
                if not isinstance(p,str) or len(p)>128: raise APIError('Invalid email or password',401)
                if not u:
                    hashlib.pbkdf2_hmac('sha256',p.encode(),b'0'*16,310000)
                    raise APIError('Invalid email or password',401)
                if not password_ok(p,u['password']): raise APIError('Invalid email or password',401)
                if not u['verified']: raise APIError('Please verify your email before signing in',403)
                raw=secrets.token_urlsafe(32); duration=86400*30 if d.get('remember') is True else 43200
                c.execute('INSERT INTO sessions VALUES(?,?,?)',(digest(raw),u['id'],time.time()+duration))
                cookie=f'session={raw}; HttpOnly; SameSite=Strict; Path=/; Max-Age={duration}' + ('; Secure' if BASE_URL.startswith('https:') else '')
                return {'user':public_user(u)},cookie
            if u:
                kind='reset' if path=='/api/forgot-password' else 'verify'
                if kind=='reset' or not u['verified']: send_mail(email,kind,issue_token(c,u['id'],kind))
            return {'message':'If the account is eligible, an email has been sent.'},None
        if method=='POST' and path in ('/api/verify','/api/reset-password'):
            self.throttle(c,'tokens',30)
            token=string(d,'token',200); kind='verify' if path=='/api/verify' else 'reset'
            row=c.execute('SELECT * FROM tokens WHERE hash=? AND kind=? AND expires>?',(digest(token),kind,time.time())).fetchone()
            if not row: raise APIError('This link is invalid or expired')
            if kind=='verify': c.execute('UPDATE users SET verified=1 WHERE id=?',(row['user_id'],))
            else:
                strong_password(d.get('password'))
                c.execute('UPDATE users SET password=? WHERE id=?',(password_hash(d['password']),row['user_id']))
                c.execute('DELETE FROM sessions WHERE user_id=?',(row['user_id'],))
            c.execute('DELETE FROM tokens WHERE hash=?',(digest(token),))
            return {'message':'Email verified. You can sign in.' if kind=='verify' else 'Password reset. You can sign in.'},None
        u=self.auth(c); uid=u['id']
        if method=='POST' and path=='/api/logout':
            jar=cookies.SimpleCookie(self.headers.get('Cookie','')); c.execute('DELETE FROM sessions WHERE hash=?',(digest(jar['session'].value),))
            return {'message':'Signed out'},'session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0'
        if method=='GET' and path=='/api/me':
            progress=[dict(r) for r in c.execute('SELECT lesson_id,score,reflection,completed FROM progress WHERE user_id=? ORDER BY completed DESC',(uid,))]
            days={r['completed'][:10] for r in progress}
            for activity in c.execute("SELECT substr(created,1,10) AS day, SUM(seconds) AS seconds, MAX(kind='completion') AS practiced FROM learning_events WHERE user_id=? GROUP BY substr(created,1,10)",(uid,)):
                if activity['practiced'] or activity['seconds']>=60: days.add(activity['day'])
            streak=0; day=learning.utcday()
            if day.isoformat() not in days: day-=timedelta(days=1)
            while day.isoformat() in days: streak+=1; day-=timedelta(days=1)
            badges=[]
            if progress: badges.append('First step')
            if len(progress)>=10: badges.append('Dedicated Learner')
            if len(progress)>=25: badges.append('Consistent Learner')
            goals=learning.goals(c,uid,TOPICS)
            if any(g['status']=='completed' for g in goals): badges.append('Goal Achiever')
            drafts=learning.drafts(c,uid)
            return {'user':public_user(u),'progress':progress,'streak':streak,'badges':badges,'goals':goals,'drafts':drafts,'resume':drafts[0] if drafts else None,'analytics':learning.analytics(c,uid,TOPICS),'goal_reminders':learning.reminders(goals)},None
        if path.startswith('/api/drafts/') and method in ('GET','POST'):
            lid=path[len('/api/drafts/'):]
            if lid not in LESSONS: raise APIError('Lesson not found',404)
            return {'draft':learning.draft(c,uid,lid,LESSONS,d if method=='POST' else None)},None
        if method=='POST' and path=='/api/profile':
            name=string(d,'name',80); interests=d.get('interests',[])
            if not isinstance(interests,list) or any(not isinstance(i,str) or i not in TOPICS for i in interests) or len(interests)>15: raise APIError('Choose valid interests')
            c.execute('UPDATE users SET name=?,interests=? WHERE id=?',(name,json.dumps(interests),uid))
            return {'message':'Profile saved'},None
        if method=='POST' and path=='/api/complete':
            lid=d.get('lesson_id'); lesson=LESSONS.get(lid) if isinstance(lid,str) else None
            if not lesson: raise APIError('Lesson not found',404)
            reflection=string(d,'reflection',4000,10); answers=d.get('answers')
            if not isinstance(answers,list) or len(answers)!=len(lesson['quiz']) or any(type(a)!=int or a<0 or a>=len(q['options']) for a,q in zip(answers,lesson['quiz'])): raise APIError('Answer every quiz question')
            score=round(100*sum(a==q['answer'] for a,q in zip(answers,lesson['quiz']))/len(answers))
            passed=score>=70
            if passed:
                c.execute('INSERT INTO progress VALUES(?,?,?,?,?) ON CONFLICT(user_id,lesson_id) DO UPDATE SET score=excluded.score,reflection=excluded.reflection',(uid,lid,score,reflection,now()))
                learning.record_completion(c,uid,lid)
            return {'score':score,'passed':passed,'feedback':[q['explanation'] for q in lesson['quiz']],'message':'Exercise completed' if passed else 'Review the lesson and try again. You need 70%.'},None
        if path=='/api/journal':
            if method=='GET': return {'entries':[dict(r) for r in c.execute('SELECT id,text,mood,created FROM journal WHERE user_id=? ORDER BY id DESC',(uid,))]},None
            if method=='POST':
                text=string(d,'text',4000); mood=string(d,'mood',30)
                if mood not in ('Calm','Happy','Sad','Anxious','Angry','Hopeful','Mixed'): raise APIError('Choose a mood')
                id=c.execute('INSERT INTO journal(user_id,text,mood,created) VALUES(?,?,?,?)',(uid,text,mood,now())).lastrowid
                return {'id':id,'message':'Reflection saved'},None
        if path.startswith('/api/journal/') and method=='DELETE':
            c.execute('DELETE FROM journal WHERE id=? AND user_id=?',(path.rsplit('/',1)[-1],uid)); return {'message':'Reflection deleted'},None
        if path=='/api/goals':
            if method=='POST':
                id=learning.create_goal(c,uid,d,TOPICS)
                return {'id':id,'message':'Goal created successfully!'},None
            if method=='GET': return {'goals':learning.goals(c,uid,TOPICS)},None
        if path.startswith('/api/goals/') and method=='DELETE':
            c.execute('DELETE FROM goals WHERE id=? AND user_id=?',(path.rsplit('/',1)[-1],uid)); return {'message':'Goal removed'},None
        if path=='/api/financial-goals':
            if method=='GET': return {'goals':learning.financial_goals(c,uid)},None
            if method=='POST':
                name=string(d,'name',120); target=money(d.get('target_amount')); deadline=d.get('deadline',d.get('target_date'))
                if target<=0: raise APIError('Savings target must be greater than zero')
                try:
                    if not isinstance(deadline,str) or date.fromisoformat(deadline)<learning.utcday(): raise ValueError()
                except (ValueError,TypeError): raise APIError('Choose today or a future deadline')
                id=c.execute('INSERT INTO financial_goals(user_id,name,target_amount,deadline,created) VALUES(?,?,?,?,?)',(uid,name,target,deadline,now())).lastrowid
                return {'id':id,'message':'Savings goal created'},None
        if path.startswith('/api/financial-goals/'):
            parts=path.split('/')[3:]
            if not parts[0].isdigit(): raise APIError('Savings goal not found',404)
            gid=int(parts[0]); goal=c.execute('SELECT * FROM financial_goals WHERE id=? AND user_id=?',(gid,uid)).fetchone()
            if not goal: raise APIError('Savings goal not found',404)
            if len(parts)==1 and method=='DELETE':
                c.execute('DELETE FROM financial_goals WHERE id=? AND user_id=?',(gid,uid));return {'message':'Savings goal deleted'},None
            if len(parts)==2 and parts[1]=='contributions' and method=='POST':
                amount=money(d.get('amount'));note=string(d,'note',200,0)
                if amount<=0: raise APIError('Contribution must be greater than zero')
                # Contributions record self-reported saving, not a bank transfer.
                c.execute('BEGIN IMMEDIATE')
                saved=c.execute('SELECT COALESCE(SUM(amount),0) FROM financial_contributions WHERE goal_id=? AND user_id=?',(gid,uid)).fetchone()[0]
                if saved+amount>100000000000: raise APIError('Total contributions exceed the maximum supported amount')
                id=c.execute('INSERT INTO financial_contributions(goal_id,user_id,amount,note,created) VALUES(?,?,?,?,?)',(gid,uid,amount,note,now())).lastrowid
                return {'id':id,'message':'Savings contribution recorded'},None
            if len(parts)==3 and parts[1]=='contributions' and method=='DELETE':
                c.execute('DELETE FROM financial_contributions WHERE id=? AND goal_id=? AND user_id=?',(parts[2],gid,uid));return {'message':'Contribution removed'},None
        if path=='/api/budget':
            if method=='POST':
                income=money(d.get('income')); allocations=d.get('allocations')
                if not isinstance(allocations,dict) or len(allocations)>30 or any(not isinstance(k,str) or not 1<=len(k)<=50 for k in allocations): raise APIError('Invalid budget categories')
                alloc={k:money(v) for k,v in allocations.items()}; month=string(d,'month',7)
                if not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])',month): raise APIError('Enter a valid month')
                c.execute('INSERT INTO budgets VALUES(?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET income=excluded.income,allocations=excluded.allocations,month=excluded.month',(uid,income,json.dumps(alloc),month))
            if method in ('GET','POST'):
                row=c.execute('SELECT * FROM budgets WHERE user_id=?',(uid,)).fetchone()
                b={'income':row['income']/100,'allocations':{k:v/100 for k,v in json.loads(row['allocations']).items()},'month':row['month']} if row else None
                expenses=[dict(r) for r in c.execute('SELECT id,category,amount,note,day FROM expenses WHERE user_id=? ORDER BY day DESC,id DESC',(uid,))]
                for e in expenses: e['amount']/=100
                return {'budget':b,'expenses':expenses},None
        if path=='/api/expenses' and method=='POST':
            category=string(d,'category',50); amount=money(d.get('amount')); note=string(d,'note',200,0); day=string(d,'day',10)
            try: date.fromisoformat(day)
            except ValueError: raise APIError('Enter a valid date')
            if amount<=0: raise APIError('Expense must be greater than zero')
            c.execute('INSERT INTO expenses(user_id,category,amount,note,day) VALUES(?,?,?,?,?)',(uid,category,amount,note,day))
            return {'message':'Expense saved'},None
        if path.startswith('/api/expenses/') and method=='DELETE':
            c.execute('DELETE FROM expenses WHERE id=? AND user_id=?',(path.rsplit('/',1)[-1],uid)); return {'message':'Expense removed'},None
        if path=='/api/calculators' and method=='POST':
            principal=money(d.get('amount'))/100
            try: rate=float(d.get('rate')); years=float(d.get('years')); frequency=int(d.get('frequency',12))
            except (ValueError,TypeError): raise APIError('Enter valid calculation inputs')
            if not math.isfinite(rate) or not math.isfinite(years) or not 0<=rate<=100 or not 0<years<=100 or frequency not in (1,2,4,12,365): raise APIError('Rate 0–100%, term 0–100 years, valid frequency required')
            kind=d.get('kind','compound'); r=rate/100
            if kind not in ('simple','compound','loan'): raise APIError('Choose a calculator')
            if kind=='loan':
                n=round(years*12)
                if n<1: raise APIError('Loan term must be at least one month')
                monthly=principal/n if r==0 else principal*(r/12)/(1-(1+r/12)**(-n))
                return {'monthly_payment':round(monthly,2),'total':round(monthly*n,2),'interest':round(monthly*n-principal,2)},None
            def amount(t): return principal*(1+r*t) if kind=='simple' else principal*(1+r/frequency)**(frequency*t)
            final=amount(years)
            return {'total':round(final,2),'interest':round(final-principal,2),'years':[{'year':i,'amount':round(amount(i),2)} for i in range(math.floor(years)+1)]+([{'year':years,'amount':round(final,2)}] if years%1 else [])},None
        if path=='/api/export' and method=='GET':
            out={'profile':public_user(u)}
            for table in ('progress','journal','goals','budgets','expenses','drafts','learning_events','learning_timers','financial_goals','financial_contributions'): out[table]=[dict(r) for r in c.execute(f'SELECT * FROM {table} WHERE user_id=?',(uid,))]
            return out,None
        if path=='/api/account' and method=='DELETE':
            p=d.get('password','')
            if not isinstance(p,str) or len(p)>128 or not password_ok(p,u['password']): raise APIError('Enter your current password',403)
            if DEV:
                outbox = Path(DB_PATH).parent / 'outbox.jsonl'
                with OUTBOX_LOCK:
                    if outbox.exists():
                        records = [line for line in outbox.read_text().splitlines() if json.loads(line).get('to') != u['email']]
                        outbox.write_text(''.join(line+'\n' for line in records))
                        os.chmod(outbox,0o600)
            c.execute('DELETE FROM users WHERE id=?',(uid,))
            return {'message':'Account and personal data deleted'},'session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0'
        raise APIError('Not found',404)

def main():
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('--host',default='127.0.0.1'); p.add_argument('--port',type=int,default=8080); a=p.parse_args()
    if not DEV and not BASE_URL.startswith('https://'): p.error('Set an HTTPS LIFE_SKILLS_BASE_URL or LIFE_SKILLS_DEV=1 for local development')
    if DEV and a.host not in ('127.0.0.1','localhost','::1'): p.error('Development mode must bind to loopback')
    init_db(); print(f'LifeSkills listening on {a.host}:{a.port}. Development outbox: {DEV}',flush=True)
    ThreadingHTTPServer((a.host,a.port),Handler).serve_forever()
if __name__=='__main__': main()
