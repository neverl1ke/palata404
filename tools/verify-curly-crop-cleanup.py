"""Verify the curly-crop scalp repair in the real DOM and animated renderers."""
import functools
import http.server
import json
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'review/curly-crop-scalp-cleanup-20261104'
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
errors=[]
with sync_playwright() as playwright:
    browser=playwright.chromium.launch(headless=True)
    for baseline in [True,False]:
        page=browser.new_page(viewport={'width':1260,'height':650},reduced_motion='reduce')
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.route('https://**/*',lambda route:route.abort())
        if baseline:
            for file in ['hair-color.js','paper-doll.js']:
                page.route('**/'+file+'?*',lambda route,request,f=file:route.fulfill(path=str(REPORT/'before'/f),content_type='text/javascript'))
        page.goto(f'http://127.0.0.1:{server.server_port}/',wait_until='networkidle')
        page.evaluate('openCustomization();setGender("male");setPaperDollView("patient");equipPaperDollItem("hair","hair-m6-curly-crop")')
        page.evaluate('''()=>{let wrap=document.createElement('div');wrap.id='repair-proof';Object.assign(wrap.style,{position:'fixed',inset:0,zIndex:2147483647,display:'flex',background:'#ddd'});document.body.append(wrap);window.repairProbe=(color)=>{let box=document.createElement('div');Object.assign(box.style,{position:'relative',width:'420px',height:'650px',overflow:'hidden'});wrap.append(box);let host=document.createElement('div');Object.assign(host.style,{position:'absolute',width:'1882px',height:'3344px',left:'-730px',top:'-20px'});box.append(host);renderPaperDollAt(host,'repair-'+color+'-')}}''')
        for color in ['original','blue','white']:
            page.evaluate('c=>{setHairColor(c);repairProbe(c)}',color)
            page.wait_for_function('''async c=>{const i=document.getElementById('repair-'+c+'-layer-hair'),src=selectedPaperDollItem('hair').genderVariants.male;return i?.complete&&i.naturalWidth>0&&i.getAttribute('src')===await coloredHairSource(src,c)}''',arg=color)
        page.screenshot(path=str(REPORT/('before.png' if baseline else 'after.png')))
        if not baseline:
            evidence=page.evaluate('''async()=>{
                const src=selectedPaperDollItem('hair').genderVariants.male;
                async function pixels(s){let im=new Image();im.src=s;await im.decode();let c=document.createElement('canvas');c.width=im.width;c.height=im.height;let ctx=c.getContext('2d');ctx.drawImage(im,0,0);return ctx.getImageData(0,0,c.width,c.height).data}
                const raw=await pixels(src),clean=await pixels(await coloredHairSource(src,'original'));
                let removed=0,outsideChanges=0,rgbChanges=0;
                for(let i=0;i<raw.length;i+=4){let x=(i/4)%941,y=Math.floor(i/4/941);if(raw[i+3]!==clean[i+3]){removed++;if(x<415||x>535||y<88||y>102)outsideChanges++}else if(raw[i+3]===255&&raw.slice(i,i+3).some((v,c)=>v!==clean[i+c]))rgbChanges++}
                const palette=[];
                for(const color of HAIR_COLORS){let a=await pixels(await coloredHairSource(src,color.id)),alphaChanges=0;for(let i=3;i<a.length;i+=4)if(a[i]!==clean[i])alphaChanges++;palette.push({color:color.id,alphaChanges})}
                return {removed,outsideChanges,rgbChanges,palette,foreheadSampleAlpha:clean[(98*941+446)*4+3],curlSampleAlpha:clean[(80*941+450)*4+3]};
            }''')
            assert 100<evidence['removed']<1000,evidence
            assert evidence['outsideChanges']==0 and evidence['rgbChanges']==0,evidence
            assert evidence['foreheadSampleAlpha']==0,evidence
            assert evidence['curlSampleAlpha']>200,evidence
            assert all(x['alphaChanges']==0 for x in evidence['palette']),evidence
            page.locator('#repair-proof').evaluate('e=>e.remove()')
            source=page.evaluate('selectedPaperDollItem("hair").genderVariants.male')
            for face in page.evaluate('Object.keys(MALE_HAIR_REVIEW.heads)'):
                page.evaluate('f=>equipPaperDollItem("face",f==="@native"?null:f)',face)
                page.wait_for_function('''async()=>{const i=document.getElementById('wardrobe-layer-hair');return i?.complete&&i.getAttribute('src')===await coloredHairSource(selectedPaperDollItem('hair').genderVariants.male,'white')}''')
            evidence['maleHeadsChecked']=16
            for face in [None,'face-male-new-almond']:
                page.evaluate('f=>{equipPaperDollItem("face",f);setPaperDollView("combat");equipPaperDollItem("upperBody",null)}',face)
                page.wait_for_function('''async()=>{let s=avatarCoreGamePreview.instances.get(document.getElementById('wardrobe-paperdoll'));return s?.host.dataset.avatarCoreReady==='true'&&!s.running&&s.engine.appearance.layers.some(l=>l.slot==='hair'&&l.order===9&&l.source.startsWith('data:'))}''')
            evidence['animatedHeadsChecked']=2
            page.evaluate('setGender("female");equipPaperDollItem("hair","hair-bob");setHairColor("blue")')
            page.wait_for_function('''()=>{let s=avatarCoreGamePreview.instances.get(document.getElementById('wardrobe-paperdoll'));return s?.host.dataset.avatarCoreReady==='true'&&!s.running&&s.engine.gender==='female'}''')
            assert page.locator('#wardrobe-layer-hair-rear').count()==0
            page.evaluate('equipPaperDollItem("hair","hair-none")')
            assert page.locator('#wardrobe-layer-hair').evaluate('i=>i.classList.contains("hidden")')
            evidence['femaleSwitchAndUnequip']=True
        page.close()
    browser.close()
server.shutdown()
assert not errors,errors
evidence['pageErrors']=errors
(REPORT/'checks.json').write_text(json.dumps(evidence,indent=2)+'\n')
print(json.dumps(evidence))
