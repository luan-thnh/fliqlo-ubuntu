// Optional: requires Playwright, system Chromium and the user's original ZIP/SCR.
const {chromium} = require('playwright');
const {spawnSync} = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const source = process.argv[2], scratch = path.resolve(process.argv[3] || 'work/visual-comparison');
if (!source) throw Error('Usage: node scripts/compare-reference.cjs /path/FliqloScr.zip /path/scratch');
const helper = path.resolve(__dirname, '../tests/reference-render.py');
function python(mode, ...args) {const r=spawnSync('/usr/bin/python3', [helper,mode,scratch,...args], {stdio:'inherit'}); if(r.status!==0)throw Error(`Python ${mode} failed`);}
const cases = [
 {width:1350,height:700,hour:13,minute:11,format:0,scale:100,brightness:100,background:true},
 {width:1350,height:700,hour:9,minute:41,format:0,scale:100,brightness:100,background:true},
 {width:700,height:1350,hour:23,minute:1,format:0,scale:100,brightness:100,background:true},
 {width:1920,height:1080,hour:0,minute:0,format:0,scale:100,brightness:100,background:true},
 {width:1920,height:1080,hour:12,minute:0,format:0,scale:75,brightness:75,background:true},
 {width:1080,height:1920,hour:1,minute:21,format:2,scale:100,brightness:50,background:true},
 {width:640,height:360,hour:1,minute:31,format:1,scale:50,brightness:100,background:true},
 {width:1440,height:900,hour:21,minute:51,format:2,scale:100,brightness:100,background:false},
 {width:900,height:1440,hour:13,minute:11,format:0,scale:75,brightness:75,background:false},
 {width:1920,height:1080,hour:23,minute:59,format:2,scale:100,brightness:100,background:true},
];
if (process.argv.includes('--animated')) for (const milliseconds of [45,120,210,290]) cases.push({width:1350,height:700,hour:12,minute:0,previous:{hour:11,minute:59},progress:milliseconds/330,format:0,scale:100,brightness:100,background:true});
(async()=>{
 python('extract',path.resolve(source)); fs.writeFileSync(path.join(scratch,'cases.json'),JSON.stringify(cases)); python('render');
 const server=http.createServer((req,res)=>{if(req.url!='/reference.html'){res.writeHead(404).end();return;}res.setHeader('Content-Type','text/html');res.end(fs.readFileSync(path.join(scratch,'reference.html')));});
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 let browser;
 try {
 browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH || '/usr/bin/chromium',args:['--no-sandbox']});
 for(let i=0;i<cases.length;i++){
  const c=cases[i], context=await browser.newContext({viewport:{width:c.width,height:c.height},deviceScaleFactor:1});
  const page=await context.newPage(); const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.addInitScript(c=>{
   Object.defineProperty(window,'chrome',{value:undefined}); const D=Date;
   window.__fliqloTime=[2026,0,1,c.previous?.hour ?? c.hour,c.previous?.minute ?? c.minute,20];
   window.Date=class extends D{constructor(...args){super(...(args.length?args:window.__fliqloTime));}};
   localStorage.setItem('tf',String(c.format===1?2:c.format===2?1:0));
   localStorage.setItem('sc',String(c.scale)); localStorage.setItem('br',String(c.brightness));localStorage.setItem('bg',String(c.background));
  },c);
  await page.goto(`http://127.0.0.1:${server.address().port}/reference.html`);
  await page.waitForSelector('#loader',{state:'detached'});await page.evaluate(()=>document.fonts.ready);
  if(c.previous) await page.evaluate(c=>{
   window.__fliqloTime=[2026,0,1,c.hour,c.minute,20];
   document.body.dispatchEvent(new CustomEvent('_updateTime'));
   document.body.getBoundingClientRect();
   const milliseconds=c.progress*330;
   for(const animation of document.getAnimations()){animation.pause();animation.currentTime=Math.min(milliseconds,164.999);}
   if(milliseconds>=165){
    document.querySelectorAll('#hur-top-clone,#min-top-clone').forEach(el=>el.dispatchEvent(new Event('animationend')));
    document.querySelectorAll('#hur-bottom-org,#min-bottom-org').forEach(el=>el.dispatchEvent(new Event('animationend')));
    document.body.getBoundingClientRect();
    for(const animation of document.getAnimations()){animation.pause();animation.currentTime=animation.animationName==='fadeIn'?165:milliseconds-165;}
   }
  },c);
  if(errors.length)throw Error(errors.join('\n'));
  await page.screenshot({path:path.join(scratch,`original-${i}.png`)});await context.close();
 }
 python('compare');
 } finally {if(browser)await browser.close();server.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
