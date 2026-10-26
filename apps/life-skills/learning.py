"""Persistent pilot learning activity, goals, analytics, and savings plans.

Tracked time is a bounded browser activity estimate, not proof of attention.
"""
from datetime import datetime, timezone, timedelta, date
import json
import math
import time

class ValidationError(Exception): pass

def stamp(): return datetime.now(timezone.utc).isoformat()
def utcday(): return datetime.now(timezone.utc).date()

def migrate(c):
    columns={r[1] for r in c.execute('PRAGMA table_info(goals)')}
    for name,ddl in [('type',"TEXT NOT NULL DEFAULT 'topic'"),('target','INTEGER NOT NULL DEFAULT 0'),('created',"TEXT NOT NULL DEFAULT ''")]:
        if name not in columns: c.execute(f'ALTER TABLE goals ADD COLUMN {name} {ddl}')
    c.executescript('''
    CREATE TABLE IF NOT EXISTS drafts(user_id INTEGER NOT NULL REFERENCES users ON DELETE CASCADE,lesson_id TEXT NOT NULL,reflection TEXT NOT NULL DEFAULT '',answers TEXT NOT NULL DEFAULT '[]',updated TEXT NOT NULL,PRIMARY KEY(user_id,lesson_id));
    CREATE TABLE IF NOT EXISTS learning_timers(user_id INTEGER PRIMARY KEY REFERENCES users ON DELETE CASCADE,lesson_id TEXT NOT NULL,last_seen REAL NOT NULL);
    CREATE TABLE IF NOT EXISTS learning_events(id INTEGER PRIMARY KEY,user_id INTEGER NOT NULL REFERENCES users ON DELETE CASCADE,lesson_id TEXT NOT NULL,kind TEXT NOT NULL,seconds INTEGER NOT NULL DEFAULT 0,created TEXT NOT NULL);
    CREATE INDEX IF NOT EXISTS learning_events_user_created ON learning_events(user_id,created);
    CREATE TABLE IF NOT EXISTS financial_goals(id INTEGER PRIMARY KEY,user_id INTEGER NOT NULL REFERENCES users ON DELETE CASCADE,name TEXT NOT NULL,target_amount INTEGER NOT NULL,deadline TEXT NOT NULL,created TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS financial_contributions(id INTEGER PRIMARY KEY,goal_id INTEGER NOT NULL REFERENCES financial_goals ON DELETE CASCADE,user_id INTEGER NOT NULL REFERENCES users ON DELETE CASCADE,amount INTEGER NOT NULL,note TEXT NOT NULL,created TEXT NOT NULL);
    ''')

def _lesson(lessons,lid):
    if not isinstance(lid,str) or lid not in lessons: raise ValidationError('Lesson not found')
    return lessons[lid]

def drafts(c,uid):
    result=[]
    for r in c.execute('SELECT lesson_id,reflection,answers,updated FROM drafts WHERE user_id=? ORDER BY updated DESC',(uid,)):
        item=dict(r);item['answers']=json.loads(item['answers'])
        item['time_spent_seconds']=c.execute('SELECT COALESCE(SUM(seconds),0) FROM learning_events WHERE user_id=? AND lesson_id=?',(uid,item['lesson_id'])).fetchone()[0]
        result.append(item)
    return result

def draft(c,uid,lid,lessons,data=None):
    lesson=_lesson(lessons,lid)
    if data is not None:
        reflection=data.get('reflection','');answers=data.get('answers',[None]*len(lesson['quiz']))
        if not isinstance(reflection,str) or len(reflection)>4000: raise ValidationError('Reflection must be at most 4000 characters')
        if not isinstance(answers,list) or len(answers)!=len(lesson['quiz']): raise ValidationError('Invalid draft answers')
        if any(a is not None and (type(a)!=int or not 0<=a<len(q['options'])) for a,q in zip(answers,lesson['quiz'])): raise ValidationError('Invalid draft answers')
        elapsed=data.get('elapsed_seconds',data.get('time_spent_seconds',0))
        if isinstance(elapsed,bool) or not isinstance(elapsed,(int,float)) or not math.isfinite(elapsed) or not 0<=elapsed<=120: raise ValidationError('Elapsed time must be between 0 and 120 seconds')
        # Serialize timer read+update so concurrent requests cannot award the same interval.
        c.execute('BEGIN IMMEDIATE')
        timer=c.execute('SELECT lesson_id,last_seen FROM learning_timers WHERE user_id=?',(uid,)).fetchone()
        seconds=min(int(elapsed),max(0,int(time.time()-timer['last_seen'])),120) if timer and timer['lesson_id']==lid else 0
        if seconds:
            c.execute('INSERT INTO learning_events(user_id,lesson_id,kind,seconds,created) VALUES(?,?,?,?,?)',(uid,lid,'time',seconds,stamp()))
        c.execute('INSERT INTO drafts VALUES(?,?,?,?,?) ON CONFLICT(user_id,lesson_id) DO UPDATE SET reflection=excluded.reflection,answers=excluded.answers,updated=excluded.updated',(uid,lid,reflection,json.dumps(answers),stamp()))
    c.execute('INSERT INTO learning_timers VALUES(?,?,?) ON CONFLICT(user_id) DO UPDATE SET lesson_id=excluded.lesson_id,last_seen=excluded.last_seen',(uid,lid,time.time()))
    return next((d for d in drafts(c,uid) if d['lesson_id']==lid),None)

def record_completion(c,uid,lid):
    c.execute('DELETE FROM drafts WHERE user_id=? AND lesson_id=?',(uid,lid))
    c.execute('DELETE FROM learning_timers WHERE user_id=? AND lesson_id=?',(uid,lid))
    # Repeated submissions can establish practice on a new UTC day, never multiple
    # completions for one lesson on the same day.
    if not c.execute("SELECT 1 FROM learning_events WHERE user_id=? AND lesson_id=? AND kind='completion' AND substr(created,1,10)=?",(uid,lid,utcday().isoformat())).fetchone():
        c.execute('INSERT INTO learning_events(user_id,lesson_id,kind,seconds,created) VALUES(?,?,?,?,?)',(uid,lid,'completion',0,stamp()))

def create_goal(c,uid,d,topics):
    kind=d.get('type','topic');topic=d.get('topic_id','') or ''
    if not isinstance(kind,str) or kind not in ('topic','daily','skill','time'): raise ValidationError('Choose a valid goal template')
    if not isinstance(topic,str) or (topic and topic not in topics) or (kind=='topic' and not topic): raise ValidationError('Choose a valid topic')
    name=d.get('name','');deadline=d.get('deadline','')
    if not isinstance(name,str) or not 1<=len(name.strip())<=120: raise ValidationError('Enter a goal name of 1–120 characters')
    try:
        if not isinstance(deadline,str) or date.fromisoformat(deadline)<utcday(): raise ValueError()
    except (ValueError,TypeError): raise ValidationError('Choose today or a future deadline')
    target=len(topics[topic]['lessons']) if kind=='topic' else d.get('target')
    limits={'topic':1000,'daily':366,'skill':sum(len(t['lessons']) for t in topics.values()),'time':10080}
    if type(target)!=int or not 1<=target<=limits[kind]: raise ValidationError(f'Target must be an integer between 1 and {limits[kind]}')
    if kind=='skill' and topic and target>len(topics[topic]['lessons']): raise ValidationError('Target exceeds available topic lessons')
    if kind in ('daily','time'):topic=''
    return c.execute('INSERT INTO goals(user_id,name,topic_id,deadline,type,target,created) VALUES(?,?,?,?,?,?,?)',(uid,name.strip(),topic,deadline,kind,target,stamp())).lastrowid

def goals(c,uid,topics):
    result=[];nowday=utcday();monday=(nowday-timedelta(days=nowday.weekday())).isoformat()
    progress=[dict(r) for r in c.execute('SELECT lesson_id,completed FROM progress WHERE user_id=?',(uid,))]
    events=[dict(r) for r in c.execute('SELECT lesson_id,kind,seconds,created FROM learning_events WHERE user_id=?',(uid,))]
    for r in c.execute('SELECT * FROM goals WHERE user_id=? ORDER BY id DESC',(uid,)):
        g=dict(r);kind=g['type'];topic=g['topic_id'];created=g['created'] or ''; relevant=[e for e in events if e['created']>=created]
        ids={l['id'] for l in topics[topic]['lessons']} if topic in topics else None
        if kind=='topic':
            total=len(ids or []);value=sum(p['lesson_id'] in (ids or set()) for p in progress)
        elif kind=='skill':
            total=g['target'];value=len({e['lesson_id'] for e in relevant if e['kind']=='completion' and (ids is None or e['lesson_id'] in ids)})
        elif kind=='time':
            total=g['target'];value=round(sum(e['seconds'] for e in relevant if e['created'][:10]>=monday)/60,2)
        else:
            total=g['target'];days={e['created'][:10] for e in relevant if e['kind']=='completion'};seconds={}
            for e in relevant:seconds[e['created'][:10]]=seconds.get(e['created'][:10],0)+e['seconds']
            days.update(day for day,n in seconds.items() if n>=60)
            # A daily practice goal remains achieved after reaching its consecutive-day target.
            streak=best=0;previous=None
            for day in sorted(days):
                current=date.fromisoformat(day);streak=streak+1 if previous and current-previous==timedelta(days=1) else 1;previous=current;best=max(best,streak)
            latest=nowday if nowday.isoformat() in days else nowday-timedelta(days=1)
            current_streak=0
            while latest.isoformat() in days:current_streak+=1;latest-=timedelta(days=1)
            value=best if best>=total else current_streak
        g.update({'target':total,'completed':min(value,total),'progress':min(value,total),'total':total,'status':'completed' if value>=total else ('overdue' if g['deadline']<nowday.isoformat() else 'active'),'unit':{'topic':'lessons','skill':'lessons','daily':'days','time':'minutes'}[kind]})
        result.append(g)
    return result

def reminders(goals_list):
    result=[]
    for g in goals_list:
        remaining=(date.fromisoformat(g['deadline'])-utcday()).days
        if g['status']!='completed' and remaining<=3:
            result.append({'goal_id':g['id'],'name':g['name'],'deadline':g['deadline'],'days_remaining':remaining,'message':f"{g['name']} is overdue." if remaining<0 else f"{g['name']} is due in {remaining} day(s)."})
    return result

def analytics(c,uid,topics):
    events=[dict(r) for r in c.execute('SELECT lesson_id,kind,seconds,created FROM learning_events WHERE user_id=?',(uid,))]
    progress=[dict(r) for r in c.execute('SELECT lesson_id,completed FROM progress WHERE user_id=?',(uid,))]
    breakdown=[]
    for t in topics.values():
        ids={l['id'] for l in t['lessons']};completed=sum(p['lesson_id'] in ids for p in progress)
        breakdown.append({'topic_id':t['id'],'title':t['title'],'time_spent_seconds':sum(e['seconds'] for e in events if e['lesson_id'] in ids),'completed':completed,'total':len(ids),'percent':round(completed/len(ids)*100) if ids else 0})
    trend=[]
    for ago in range(13,-1,-1):
        day=(utcday()-timedelta(days=ago)).isoformat()
        trend.append({'day':day,'completed':sum(p['completed'][:10]==day for p in progress),'time_spent_seconds':sum(e['seconds'] for e in events if e['created'][:10]==day)})
    return {'total_seconds':sum(e['seconds'] for e in events),'topics':breakdown,'trend':trend,'time_measurement':'Bounded browser activity estimate, not verified attention. UTC calendar periods.'}

def financial_goals(c,uid):
    out=[]
    for row in c.execute('SELECT * FROM financial_goals WHERE user_id=? ORDER BY id DESC',(uid,)):
        g=dict(row);contributions=[dict(r) for r in c.execute('SELECT id,amount,note,created FROM financial_contributions WHERE goal_id=? AND user_id=? ORDER BY id DESC',(g['id'],uid))]
        saved=sum(x['amount'] for x in contributions)
        for item in contributions:item['amount']/=100
        g.update({'target_amount':g['target_amount']/100,'saved_amount':saved/100,'remaining':max(0,g['target_amount']-saved)/100,'percent':min(100,round(saved/g['target_amount']*100)),'status':'completed' if saved>=g['target_amount'] else ('overdue' if g['deadline']<utcday().isoformat() else 'active'),'contributions':contributions})
        out.append(g)
    return out
