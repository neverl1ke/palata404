"""Real Lab evidence for the two cleanup areas. Historical polish stays intact."""
from pathlib import Path
import argparse,base64,functools,html,io,json,re,subprocess,threading
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from PIL import Image,ImageDraw,ImageFont
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'review/avatar-core-cleanup';OLD=OUT/'before'
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--capture',action='store_true');parser.add_argument('--gallery-only',action='store_true');args=parser.parse_args()
if args.capture:subprocess.run(['python',str(ROOT/'tools/review-avatar-core.py'),'--output',str(OUT)],cwd=ROOT,check=True)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',19)
states={(s['gender'],s['pose']):s for s in json.loads((OUT/'browser-check.json').read_text())['states']}
records=[];panels=[]
def pair(old,new,title,name):
    assert old.size==new.size
    im=Image.new('RGB',(old.width*2,old.height+40),'#e0dcd3');d=ImageDraw.Draw(im)
    d.text((8,8),'ДО · '+title,font=font,fill='#172426');d.text((old.width+8,8),'ПІСЛЯ · '+title,font=font,fill='#172426')
    im.paste(old,(0,40));im.paste(new,(old.width,40));im.save(OUT/name,lossless=True)
for g in ['male','female']:
    for pose,side in [('melee','right'),('pistol','right'),('pistol','left'),('rifle','right'),('rifle','left')]:
        x,y=states[g,pose]['frame']['arms'][side]['wrist'];box=(round(x-75),round(y-75),round(x+75),round(y+75))
        a=Image.open(OLD/f'{g}-{pose}.png').convert('RGB');b=Image.open(OUT/f'{g}-{pose}.png').convert('RGB')
        name=f'{g}-{pose}-{side}-wrist-before-after.webp';pair(a.crop(box).resize((600,600)),b.crop(box).resize((600,600)),f'{g} · {pose} · {side} ×4',name)
        records.append({'file':name,'source_box':box,'zoom':4,'same_camera_and_joint':True});panels.append((name,f'{g} · {pose} · {side}'))
for label,box,zoom in [('shoulder',(590,290,800,510),3),('upper-arm',(540,280,900,580),2)]:
    a=Image.open(OLD/'female-rifle.png').convert('RGB').crop(box);b=Image.open(OUT/'female-rifle.png').convert('RGB').crop(box)
    size=(a.width*zoom,a.height*zoom);name=f'female-rifle-{label}-before-after.webp';pair(a.resize(size),b.resize(size),'female · rifle · '+label+' ×'+str(zoom),name)
    records.append({'file':name,'source_box':box,'zoom':zoom,'same_camera_and_joint':True});panels.append((name,'Жіноче плече / верх руки · rifle'))
(OUT/'comparison-registration.json').write_text(json.dumps({'baseline_commit':'4f46b15','capture_frame':[941,1672],'pairs':records},indent=2)+'\n')
if not args.gallery_only:
    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
    errors=[];missing=[];cases=[]
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch();p=browser.new_page(viewport={'width':1440,'height':1100});p.on('pageerror',lambda e:errors.append(str(e)));p.on('response',lambda r:missing.append([r.url,r.status]) if r.status>=400 else None)
            p.goto(f'http://127.0.0.1:{server.server_port}/avatar-lab/');p.wait_for_function('window.avatarLab?.ready')
            p.evaluate('avatarLab.engine.pause();avatarLab.engine.setOptions({transitionMs:0,breathing:false,pistolSupport:true});Object.assign(avatarLab.engine.canvas.style,{width:"941px",height:"1672px",maxWidth:"none",maxHeight:"none",position:"fixed",left:"0",top:"0",margin:"0",padding:"0",border:"0",transform:"none"})')
            for g in ['male','female']:
                p.evaluate('async g=>{await avatarLab.engine.setGender(g);await avatarLab.engine.setAppearance({layers:[]})}',g)
                slots=[('melee','right'),('pistol','right'),('pistol','left'),('rifle','right'),('rifle','left')]
                if g=='female':slots.append(('rifle','shoulder'))
                sheet=Image.new('RGB',(300*len(slots),1200),'#e0dcd3');draw=ImageDraw.Draw(sheet)
                for row,(label,bg) in enumerate([('Білий','#fff'),('Сірий','#777'),('Чорний','#000'),('Зелений','#00ff00')]):
                    images={}
                    for pose in ['idle','melee','pistol','rifle']:
                        p.evaluate('v=>{const e=avatarLab.engine;e.time=0;e.setOptions({background:v[1]});e.setPose(v[0])}',[pose,bg])
                        payload=p.evaluate('avatarLab.engine.canvas.toDataURL().split(",")[1]');images[pose]=Image.open(io.BytesIO(base64.b64decode(payload))).convert('RGB')
                        assert images[pose].size==(941,1672);cases.append({'gender':g,'pose':pose,'background':bg})
                    for col,(pose,side) in enumerate(slots):
                        if side=='shoulder':box=(590,290,800,500)
                        else:
                            x,y=states[g,pose]['frame']['arms'][side]['wrist'];box=(round(x-75),round(y-75),round(x+75),round(y+75))
                        draw.text((col*300+5,row*300+5),label+' · '+pose+' · '+side,font=font,fill='#172426');sheet.paste(images[pose].crop(box).resize((270,270)),(col*300,row*300+30))
                sheet.save(OUT/f'{g}-four-backgrounds.webp',lossless=True)
                p.evaluate('avatarLab.engine.setOptions({background:"#d3cfc6",transitionMs:0});avatarLab.engine.setPose("idle");Object.assign(avatarLab.engine.canvas.style,{width:"470px",height:"835.133px"});avatarLab.engine.render()')
                frames=[]
                for pose in ['rifle','pistol','melee','idle']:
                    p.evaluate('v=>{avatarLab.engine.setOptions({transitionMs:320});avatarLab.engine.setPose(v)}',pose)
                    for i in range(13):
                        if i<8:p.evaluate('avatarLab.engine.step(40)')
                        frames.append(Image.open(io.BytesIO(p.locator('#avatar').screenshot())).convert('RGB'))
                frames[0].save(OUT/f'{g}-transitions.webp',save_all=True,append_images=frames[1:],duration=40,loop=0,lossless=True)
                p.evaluate('Object.assign(avatarLab.engine.canvas.style,{width:"941px",height:"1672px"});avatarLab.engine.setOptions({transitionMs:0})')
            assert not errors and not missing,(errors,missing)
            (OUT/'visual-browser-check.json').write_text(json.dumps({'browser':'Chromium '+browser.version,'real_entry':'avatar-lab/index.html','background_cases':cases,'transition_frames_per_gender':52,'js_errors':errors,'http_errors':missing,'physical_device':False},indent=2)+'\n');browser.close()
    finally:server.shutdown();server.server_close()
sections=[]
def picture(name,caption):return '<figure><img loading="lazy" src="'+name+'" alt="'+html.escape(caption)+'"><figcaption>'+html.escape(caption)+'</figcaption></figure>'
sections.append('<h2>Жіноче плече · незмінна бойова стійка</h2>'+''.join(picture(n,c) for n,c in panels[-2:]))
sections.append('<h2>Усі10 хватів · зап’ястя ДО/ПІСЛЯ ×4</h2>'+''.join(picture(n,c) for n,c in panels[:-2]))
sections.append('<h2>Чотири фони</h2>'+''.join(picture(f'{g}-four-backgrounds.webp',g+' · білий, сірий, чорний, зелений') for g in ['male','female']))
sections.append('<h2>Перевірка руху</h2><div class="grid">'+''.join(picture(f'{g}-transitions.webp',g+' · реальні кадри переходів') for g in ['male','female'])+'</div>')
for pose in ['idle','melee','pistol','rifle']:sections.append('<h2>'+pose+'</h2><div class="grid">'+''.join(picture(f'{g}-{pose}.png',g+' · '+pose) for g in ['male','female'])+'</div>')
sections.append('<h2>Lab</h2>'+picture('lab-desktop.png','Інструменти Lab збережено')+picture('lab-mobile-390.png','390px · емуляція Chromium'))
validation=OUT/'validation-summary.json';summary=json.loads(validation.read_text())['statements'] if validation.exists() else ['Фінальні результати перевірок ще не внесено.']
doc='''<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Avatar Core · final cleanup</title><style>body{margin:auto;max-width:1440px;padding:20px;background:#172022;color:#e2dcd0;font:17px/1.5 system-ui}a{color:#a6d7df}img{width:100%;height:auto;background:#d3cfc6}figure{margin:15px 0 30px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}h2{margin-top:40px;border-top:1px solid #697;padding-top:20px}.notice{border:1px solid #9b8a68;padding:16px}@media(max-width:600px){body{padding:12px}.grid{grid-template-columns:1fr}}</style><h1>Avatar Core · два локальні виправлення</h1><p class="notice">ДО: прийнятий polish4f46b15. ПІСЛЯ: очищення контурів зап’ясть і жіночого плеча в rifle. Однакова камера941×1672, пози та точки хвату. Усі знімки — фактичний Chromium/Canvas Avatar Lab; нових персонажів не генерували.</p><p><a href="../../avatar-lab/">Інтерактивний Lab</a> · <a href="README.md">Технічний звіт</a></p><ul>'''+''.join('<li>'+html.escape(s)+'</li>' for s in summary)+'</ul>'+''.join(sections)+'</html>'
(OUT/'index.html').write_text(doc)
def embed(m):
    p=OUT/m[1];im=Image.open(p)
    if p.suffix=='.webp':payload=p.read_bytes()
    else:
        b=io.BytesIO();im.save(b,format='WEBP',lossless=True);payload=b.getvalue();assert Image.open(io.BytesIO(payload)).convert('RGBA').tobytes()==im.convert('RGBA').tobytes()
    return 'src="data:image/webp;base64,'+base64.b64encode(payload).decode()+'"'
offline=re.sub(r'src="([^"]+)"',embed,doc.replace('href="../../avatar-lab/"','href="Avatar-Lab.html"').replace('href="README.md"','href="Technical-report.html"').replace(' loading="lazy"',''))
(OUT/'Report.html').write_text(offline);print('Cleanup gallery:',doc.count('<img '),'actual-render images;',len(offline.encode()),'offline bytes')
