/* Optional rendered acceptance: npm install --prefix /tmp/life-skills-browser playwright
 * NODE_PATH=/tmp/life-skills-browser/node_modules node apps/life-skills/scripts/browser-acceptance.cjs
 * Set LIFE_SKILLS_BROWSER_PATH to use an existing Chromium executable.
 * Starts its own loopback development server and deletes its temporary account data.
 */
'use strict';
const {chromium}=require('playwright');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),net=require('node:net');
const {spawn}=require('node:child_process');
const assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..');
const checks=[];
const check=(name)=>checks.push(name);
const delay=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 const temp=fs.mkdtempSync(path.join(os.tmpdir(),'life-skills-browser-'));
 let browser,server;
 try{
  const socket=net.createServer();await new Promise(r=>socket.listen(0,'127.0.0.1',r));const port=socket.address().port;await new Promise(r=>socket.close(r));
  const base='http://127.0.0.1:'+port;
  server=spawn(process.env.PYTHON||'python3',[path.join(root,'server.py'),'--port',String(port)],{env:{...process.env,LIFE_SKILLS_DEV:'1',LIFE_SKILLS_DB:path.join(temp,'test.sqlite3'),LIFE_SKILLS_BASE_URL:base},stdio:'ignore'});
  let healthy=false;for(let i=0;i<100;i++){try{if((await fetch(base+'/api/health')).ok){healthy=true;break}}catch{}await delay(50)}assert(healthy,'Server starts');
  browser=await chromium.launch({headless:true,executablePath:process.env.LIFE_SKILLS_BROWSER_PATH||undefined,args:['--no-sandbox','--disable-dev-shm-usage','--disable-gpu']});
  const context=await browser.newContext({viewport:{width:1440,height:1000}}),page=await context.newPage(),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base);
  await page.getByRole('button',{name:'Create an account',exact:true}).click();
  await page.getByLabel('Your name',{exact:true}).fill('Browser Learner');await page.getByLabel('Email address',{exact:true}).fill('browser@example.test');
  await page.getByLabel('Password',{exact:true}).fill('BrowserPass123!');await page.getByLabel('Confirm password',{exact:true}).fill('BrowserPass123!');await page.locator('[name=consent]').check();
  await page.getByRole('button',{name:'Create account',exact:true}).click();await page.getByText('Please check your email to verify your account',{exact:true}).waitFor();
  const mail=JSON.parse(fs.readFileSync(path.join(temp,'outbox.jsonl'),'utf8').trim().split('\n').at(-1));await page.goto(mail.link);await page.getByText('Email verified. You can sign in.',{exact:true}).waitFor();
  await page.getByLabel('Email address',{exact:true}).fill('browser@example.test');await page.getByLabel('Password',{exact:true}).fill('BrowserPass123!');await page.getByRole('button',{name:'Sign in',exact:true}).click();await page.getByRole('heading',{name:'Welcome back, Browser Learner.'}).waitFor();check('Browser registration, verification and sign-in');
  await page.getByRole('link',{name:'Learning goals',exact:true}).click();await page.getByRole('heading',{name:'Learning goals',exact:true}).waitFor();assert.equal(await page.locator('#goaltype option').count(),4);await page.getByLabel('Goal template').selectOption('daily');await page.getByLabel('Goal name',{exact:true}).fill('Daily browser practice');
  await page.locator('#goaltarget').fill('2');await page.getByLabel('Target date',{exact:true}).fill('2099-12-31');await page.getByRole('button',{name:'Create goal',exact:true}).click();await page.getByRole('heading',{name:'Daily browser practice',exact:true}).waitFor();check('Four goal templates and persisted daily goal creation');
  await page.getByRole('link',{name:'Money tools',exact:true}).click();await page.getByRole('heading',{name:'Savings goals',exact:true}).waitFor();await page.locator('#savings-name').fill('Browser savings');await page.locator('#savings-target').fill('100');await page.locator('#savings-deadline').fill('2099-12-31');await page.getByRole('button',{name:'Create savings goal',exact:true}).click();await page.getByRole('heading',{name:'Browser savings',exact:true}).waitFor();await page.locator('.contribution-form input[name=amount]').fill('25');await page.getByRole('button',{name:'Record contribution',exact:true}).click();await page.getByText('Remaining: £75.00',{exact:true}).waitFor();check('Savings goal and contribution update through rendered UI');
  await page.goto(base+'/#lesson/emotional-intelligence-1');await page.getByLabel('Your practice reflection',{exact:true}).waitFor();const reflection='I noticed frustration and paused before choosing a calm response.';await page.getByLabel('Your practice reflection',{exact:true}).fill(reflection);await page.locator('input[name=q0][value="0"]').check();await page.getByText('Saved to your account',{exact:true}).waitFor();
  await page.getByRole('link',{name:'Overview',exact:true}).click();await page.getByRole('button',{name:'Resume saved lesson →',exact:true}).click();await page.getByText('Saved practice restored',{exact:true}).waitFor();assert.equal(await page.getByLabel('Your practice reflection',{exact:true}).inputValue(),reflection);assert(await page.locator('input[name=q0][value="0"]').isChecked());check('Lesson autosave and dashboard resume restore reflection and quiz selection');
  await page.reload();await page.getByText('Saved practice restored',{exact:true}).waitFor();assert.equal(await page.getByLabel('Your practice reflection',{exact:true}).inputValue(),reflection);check('Draft restored after full browser reload');
  await page.route('**/api/drafts/emotional-intelligence-1',route=>route.request().method()==='POST'?route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:'Temporary save failure'})}):route.continue());
  await page.getByLabel('Your practice reflection',{exact:true}).fill(reflection+' Saved after recovery.');await page.getByRole('link',{name:'Overview',exact:true}).click();await page.waitForFunction(()=>location.hash==='#lesson/emotional-intelligence-1');assert.equal(await page.getByLabel('Your practice reflection',{exact:true}).inputValue(),reflection+' Saved after recovery.');
  await page.unroute('**/api/drafts/emotional-intelligence-1');await page.getByRole('button',{name:'Save practice now',exact:true}).click();await page.getByText('Practice saved',{exact:true}).waitFor();assert.equal(await page.evaluate(()=>localStorage.length),0);check('Save failure retains unsaved lesson and recovery saves without private browser storage');
  const content=JSON.parse(fs.readFileSync(path.join(root,'content.json'),'utf8'));const lesson=content.flatMap(t=>t.lessons).find(l=>l.id==='emotional-intelligence-1');for(let i=0;i<lesson.quiz.length;i++)await page.locator(`input[name=q${i}][value="${lesson.quiz[i].answer}"]`).check();await page.getByRole('button',{name:'Complete practice and check answers',exact:true}).click();await page.getByRole('heading',{name:/100%/}).waitFor();const me=await page.evaluate(async()=>await(await fetch('/api/me')).json());assert(!me.drafts.some(d=>d.lesson_id===lesson.id));check('Server-scored completion clears saved draft');
  await page.getByRole('link',{name:'My progress',exact:true}).click();await page.getByRole('heading',{name:'Your last 14 days',exact:true}).waitFor();await page.getByRole('heading',{name:'Time by topic',exact:true}).waitFor();if(process.env.LIFE_SKILLS_SCREENSHOT_DIR){fs.mkdirSync(process.env.LIFE_SKILLS_SCREENSHOT_DIR,{recursive:true});await page.screenshot({path:path.join(process.env.LIFE_SKILLS_SCREENSHOT_DIR,'progress-desktop.png'),fullPage:true})}check('Learning analytics render activity and topic duration tables');
  for(const hash of ['dashboard','goals','tools','progress']){
   await page.setViewportSize({width:390,height:844});await page.goto(base+'/#'+hash);await page.locator('main#main').waitFor();await page.waitForLoadState('networkidle');assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1),'Mobile overflow on '+hash);if(process.env.LIFE_SKILLS_SCREENSHOT_DIR)await page.screenshot({path:path.join(process.env.LIFE_SKILLS_SCREENSHOT_DIR,hash+'-mobile.png'),fullPage:true});const menu=page.getByRole('button',{name:'Menu',exact:true});await menu.click();assert.equal(await menu.getAttribute('aria-expanded'),'true');await menu.click();
  }check('390px mobile layouts fit viewport and navigation opens');
  assert.deepEqual(errors,[]);check('No uncaught browser JavaScript errors');
  console.log(JSON.stringify({ok:true,browser:browser.version(),checks,limitations:['Chromium only','No WCAG conformance certification','Time tracking is an activity estimate','No live SMTP or deployed HTTPS verification']},null,2));
 }finally{if(browser)await browser.close();if(server){server.kill();await new Promise(r=>server.once('exit',r))}fs.rmSync(temp,{recursive:true,force:true})}
})().catch(e=>{console.error(e.stack);process.exitCode=1});
