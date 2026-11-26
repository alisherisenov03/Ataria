const {chromium}=require('playwright');const fs=require('fs');const path=require('path');
const OUT='/home/user/Ataria/brand/product/sm23/kaspi_cards/v2/';fs.mkdirSync(OUT,{recursive:true});
(async()=>{const jobs=JSON.parse(fs.readFileSync('jobs2.json'));const b=await chromium.launch();
const p=await b.newPage({viewport:{width:900,height:900},deviceScaleFactor:2});
for(const j of jobs){await p.goto('file://'+path.resolve('q_'+j+'.html'));await p.waitForLoadState('networkidle');await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(300);await p.screenshot({path:'raw_'+j+'.png'});}
await b.close();console.log('ok')})();
