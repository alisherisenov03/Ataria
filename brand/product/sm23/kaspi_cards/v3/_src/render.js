const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:900,height:900},deviceScaleFactor:2});
for(const n of process.argv.slice(2)){await p.goto('file://'+process.cwd()+'/s'+n+'.html',{waitUntil:'networkidle'});await p.evaluate(()=>document.fonts.ready);await p.screenshot({path:'o'+n+'.png'})}
await b.close()})();
