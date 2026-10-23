"""Capture actual Lab frames for male anatomy review. No reference substitution."""
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
import base64,functools,html,io,json,threading
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'review/avatar-core-2';OUT.mkdir(exist_ok=True)
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20)
panels=[];errors=[];missing=[];states={};records=[]
def panel(name,title):panels.append((name,title))
def pair(old,new,name,title,zoom=1):
    old=old.resize((old.width*zoom,old.height*zoom));new=new.resize((new.width*zoom,new.height*zoom))
    out=Image.new('RGB',(old.width*2,old.height+36),'#e0dcd3');d=ImageDraw.Draw(out)
    d.text((8,6),'ДО · 90904dd',fill='#172022',font=font);d.text((old.width+8,6),'ПІСЛЯ · чоловічі руки',fill='#172022',font=font)
    out.paste(old,(0,36));out.paste(new,(old.width,36));out.save(OUT/name,lossless=True);panel(name,title)
try:
    with sync_playwright() as pw:
        browser=pw.chromium.launch();p=browser.new_page(viewport={'width':1500,'height':1850},device_scale_factor=1)
        p.on('pageerror',lambda e:errors.append(str(e)));p.on('response',lambda r:missing.append([r.url,r.status]) if r.status>=400 else None)
        p.goto(f'http://127.0.0.1:{server.server_port}/avatar-lab/');p.wait_for_function('window.avatarLab?.ready')
        storage=p.evaluate('JSON.stringify({...localStorage})')
        p.evaluate('''()=>{const e=avatarLab.engine;e.pause();e.setOptions({breathing:false,transitionMs:0});Object.assign(e.canvas.style,{width:'941px',height:'1672px',maxWidth:'none',maxHeight:'none',position:'fixed',left:0,top:0,margin:0,padding:0,border:0});e.render()}''')
        def frame():return Image.open(io.BytesIO(base64.b64decode(p.evaluate('avatarLab.engine.canvas.toDataURL().split(",")[1]')))).convert('RGB')
        for pose in ['idle','melee','pistol','rifle']:
            p.evaluate('p=>{const e=avatarLab.engine;e.time=0;e.setOptions({breathing:false,background:"#d3cfc6"});e.setPose(p)}',pose)
            im=frame();im.save(OUT/f'male-{pose}.webp',lossless=True);states[pose]=p.evaluate('avatarLab.engine.snapshot()')
            old=Image.open(ROOT/'review/avatar-core-cleanup'/f'male-{pose}.png').convert('RGB')
            pair(old,im,f'{pose}-full-before-after.webp',pose+' · однакова камера941×1672')
            if pose!='idle':
                pair(old.crop((150,290,800,700)),im.crop((150,290,800,700)),f'{pose}-arms-before-after.webp',pose+' · руки та хват ×2',2)
                for side in ['right','left'] if pose=='rifle' else ['right']:
                    for joint in ['shoulder','elbow','wrist','grip']:
                        x,y=states[pose]['frame']['arms'][side][joint];x,y=round(x),round(y)
                        box=(x-75,y-75,x+75,y+75)
                        pair(old.crop(box),im.crop(box),f'{pose}-{side}-{joint}.webp',pose+' · '+side+' · '+joint+' ×4',4)
            if pose in ['rifle','pistol']:
                p.evaluate('avatarLab.engine.setOptions({debugPivots:true,debugGrips:true})');frame().save(OUT/f'{pose}-skeleton.webp',lossless=True);panel(f'{pose}-skeleton.webp',pose+' · скелет і точки хвату');p.evaluate('avatarLab.engine.setOptions({debugPivots:false,debugGrips:false})')
            if pose!='idle':
                sheet=Image.new('RGB',(1300,900),'#e0dcd3');d=ImageDraw.Draw(sheet)
                for i,(label,bg) in enumerate([('Білий','#fff'),('Сірий','#777'),('Чорний','#000'),('Зелений','#00ff00')]):
                    p.evaluate('bg=>avatarLab.engine.setOptions({background:bg})',bg);crop=frame().crop((150,270,800,684))
                    x=i%2*650;y=i//2*450;sheet.paste(crop,(x,y+36));d.text((x+8,y+6),label,font=font,fill='#172022');records.append({'pose':pose,'background':bg})
                name=f'{pose}-four-backgrounds.webp';sheet.save(OUT/name,lossless=True);panel(name,pose+' · чотири фони')
        p.evaluate('Object.assign(avatarLab.engine.canvas.style,{width:"470px",height:"835.133px"});avatarLab.engine.setOptions({background:"#d3cfc6",breathing:true})')
        for pose in ['idle','melee','pistol','rifle']:
            p.evaluate('p=>avatarLab.engine.setPose(p)',pose);frames=[]
            for t in range(0,4000,160):
                p.evaluate('t=>{avatarLab.engine.time=t;avatarLab.engine.render()}',t);frames.append(frame())
            name=f'{pose}-breathing.webp';frames[0].save(OUT/name,save_all=True,append_images=frames[1:],duration=160,loop=0,lossless=True);panel(name,pose+' · 4000мс,25 фактичних кадрів')
        frames=[]
        p.evaluate('avatarLab.engine.setOptions({breathing:false,transitionMs:320});avatarLab.engine.setPose("idle");avatarLab.engine.step(320)')
        montage=Image.new('RGB',(470*4,418*4),'#e0dcd3')
        for row,pose in enumerate(['rifle','pistol','melee','idle']):
            p.evaluate('p=>avatarLab.engine.setPose(p)',pose)
            for i in range(9):
                p.evaluate('avatarLab.engine.step(40)');im=frame();frames.append(im)
                if i in [0,2,4,7]:montage.paste(im.crop((0,220,470,638)),([0,2,4,7].index(i)*470,row*418))
        frames[0].save(OUT/'transitions.webp',save_all=True,append_images=frames[1:],duration=40,loop=0,lossless=True);panel('transitions.webp','Переходи · фактичні кадри');montage.save(OUT/'transition-contact-sheet.webp',lossless=True);panel('transition-contact-sheet.webp','Перехідні кадри · контроль матеріалів і силуету')
        p.goto(f'http://127.0.0.1:{server.server_port}/avatar-lab/');p.wait_for_function('window.avatarLab?.ready');p.evaluate('avatarLab.engine.pause();avatarLab.engine.setOptions({breathing:false,transitionMs:0});avatarLab.engine.setPose("rifle")')
        p.set_viewport_size({'width':1440,'height':1100});p.screenshot(path=str(OUT/'lab-desktop.png'),full_page=True);panel('lab-desktop.png','Avatar Lab · desktop')
        for width in [320,390,768]:
            p.set_viewport_size({'width':width,'height':844});assert p.evaluate('document.documentElement.scrollWidth<=innerWidth');p.screenshot(path=str(OUT/f'lab-mobile-{width}.png'),full_page=True);panel(f'lab-mobile-{width}.png',str(width)+'px · емуляція Chromium')
        assert storage==p.evaluate('JSON.stringify({...localStorage})');assert not errors and not missing,(errors,missing)
        (OUT/'browser-check.json').write_text(json.dumps({'browser':browser.version,'entry':'avatar-lab/index.html','states':states,'backgrounds':records,'js_errors':errors,'http_errors':missing,'storage_unchanged':True,'physical_device':False},indent=2)+'\n');browser.close()
finally:server.shutdown();server.server_close()
style='body{max-width:1440px;margin:auto;padding:20px;background:#172022;color:#ece4d4;font:17px/1.5 system-ui}a{color:#a6d7df}img{width:100%;height:auto}figure{margin:20px 0 40px}p{max-width:1000px}figcaption{padding:8px}.notice{border:1px solid #a78;padding:16px}'
intro='<h1>Чоловічі руки · Avatar Core2.0 · версія для перегляду</h1><p class="notice">Це художньо-технічний прототип для погодження. Оригінальні PNG та жіночий риг збережені. Три надані референси не включені в ресурси. Усі знімки нижче — фактичний Canvas Avatar Lab. До main не перенесено й не опубліковано.</p><p>Пістолет — однією рукою; ніж — збоку, лезом униз. Локально домальовані ділянки рук rifle/pistol прив’язані до чинних кісток. Проєкційне скорочення — 2D-наближення. Плечові стики й перехідні кадри потребують художнього погодження; тести не доводять ідеальну анатомію.</p><p><a href="Avatar-Lab.html">Відкрити автономний Lab</a> · <a href="README.md">Технічний звіт</a></p>'
body=''.join('<figure><img src="'+name+'" alt="'+html.escape(title)+'"><figcaption>'+html.escape(title)+'</figcaption></figure>' for name,title in panels)
doc='<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Чоловічий Avatar Core2 · перевірка</title><style>'+style+'</style>'+intro+body+'</html>'
(OUT/'index.html').write_text(doc.replace('href="Avatar-Lab.html"','href="../../avatar-lab/"'))
for name,_ in panels:
    p=OUT/name
    if p.suffix=='.webp':payload=p.read_bytes()
    else:
        im=Image.open(p);b=io.BytesIO();im.save(b,format='WEBP',lossless=True);payload=b.getvalue()
    doc=doc.replace('src="'+name+'"','src="data:image/webp;base64,'+base64.b64encode(payload).decode()+'"')
(OUT/'Report.html').write_text(doc);print('Captured',len(panels),'real Lab panels and animations')
