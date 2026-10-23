"""Actual f49ae7b/current Lab A/B and all 12 directed switches at 16ms steps."""
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
import base64,functools,hashlib,html,io,json,subprocess,tempfile,threading
from PIL import Image,ImageDraw,ImageFont
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'review/avatar-core-grip-pass';FRAMES=OUT/'frames';FRAMES.mkdir(exist_ok=True)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20)
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
def serve(root):
    s=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root)));threading.Thread(target=s.serve_forever,daemon=True).start();return s
def save_frame(im):
    key=hashlib.sha256(im.tobytes()).hexdigest();path=FRAMES/(key+'.webp')
    if not path.exists():im.save(path,lossless=True)
    return key
panels=[];switches=[];errors=[];missing=[];states={};servers=[]
def pair(a,b,name,label):
    out=Image.new('RGB',(a.width+b.width,a.height+36),'#ded9cd');d=ImageDraw.Draw(out);d.text((8,6),'ДО · f49ae7b',font=font,fill='#172022');d.text((a.width+8,6),'ПОТОЧНИЙ · хвати без змін',font=font,fill='#172022');out.paste(a,(0,36));out.paste(b,(a.width,36));out.save(OUT/name,lossless=True);panels.append((name,label))
with tempfile.TemporaryDirectory() as td:
    before=Path(td)
    names=['avatar-core/'+n for n in ['engine.mjs','math.mjs','skin.mjs','pose-art.mjs','weapon-controller.mjs','weapons.json','manifest.json','male-preview.json']]
    names+=['avatar-lab/'+n for n in ['index.html','lab.mjs','lab.css','catalog-bridge.js']]
    for name in names:
        p=before/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(subprocess.check_output(['git','show','f49ae7b:'+name],cwd=ROOT))
    for path in ['base_male.png','base_female.png','paper-doll-data.js','paper-doll.js','hair-color.js','assets','review']:(before/path).symlink_to(ROOT/path,target_is_directory=(ROOT/path).is_dir())
    (before/'avatar-core/assets').symlink_to(ROOT/'avatar-core/assets',target_is_directory=True)
    (before/'avatar-core/rigs').mkdir()
    for path in (ROOT/'avatar-core/rigs').glob('*.json'):
        (before/'avatar-core/rigs'/path.name).write_bytes(subprocess.check_output(['git','show','f49ae7b:avatar-core/rigs/'+path.name],cwd=ROOT))
    servers=[serve(before),serve(ROOT)]
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch();pages=[]
            for server in servers:
                p=browser.new_page(viewport={'width':1440,'height':1800},device_scale_factor=1);p.on('pageerror',lambda e:errors.append(str(e)));p.on('response',lambda r:missing.append([r.url,r.status]) if r.status>=400 else None)
                p.goto(f'http://127.0.0.1:{server.server_port}/avatar-lab/');p.wait_for_function('window.avatarLab?.ready');p.evaluate('''()=>{const e=avatarLab.engine;e.pause();e.time=0;e.setOptions({breathing:false,transitionMs:0});Object.assign(e.canvas.style,{width:'941px',height:'1672px',maxWidth:'none',maxHeight:'none',position:'fixed',left:0,top:0,margin:0,padding:0,border:0});e.render()}''');pages.append(p)
            storage=[p.evaluate('JSON.stringify({...localStorage})') for p in pages]
            def frame(p):return Image.open(io.BytesIO(base64.b64decode(p.evaluate('avatarLab.engine.canvas.toDataURL().split(",")[1]')))).convert('RGB')
            for pose in ['idle','rifle','pistol','melee']:
                images=[]
                for index,p in enumerate(pages):
                    p.evaluate('p=>{avatarLab.engine.setOptions({transitionMs:0,breathing:false});avatarLab.engine.time=0;avatarLab.engine.setPose(p)}',pose)
                    images.append(frame(p));images[-1].save(OUT/f'{"before" if index==0 else "after"}-{pose}.webp',lossless=True)
                states[pose]=pages[1].evaluate('avatarLab.engine.snapshot()');pair(*images,f'{pose}-full.webp',pose+' · однаковий масштаб941×1672')
                if pose!='idle':
                    box=(150,300,850,900) if pose=='rifle' else (150,150,350,630) if pose=='pistol' else (160,800,270,970)
                    zoom=2 if pose!='melee' else 4
                    pair(*(im.crop(box).resize(((box[2]-box[0])*zoom,(box[3]-box[1])*zoom)) for im in images),f'{pose}-close.webp',pose+' · крупний план')
            for pose,sides in [('rifle',['right','left']),('pistol',['right']),('melee',['right'])]:
                for p in pages:p.evaluate('p=>avatarLab.engine.setPose(p)',pose)
                images=[frame(p) for p in pages]
                for side in sides:
                    for joint in ['shoulder','elbow','wrist','grip']:
                        x,y=states[pose]['frame']['arms'][side][joint];box=(round(x)-60,round(y)-60,round(x)+60,round(y)+60)
                        pair(*(im.crop(box).resize((360,360)) for im in images),f'{pose}-{side}-{joint}.webp',pose+' · '+side+' · '+joint+' ×3')
                if pose=='rifle':
                    box=(190,530,335,680);pair(*(im.crop(box).resize((435,450)) for im in images),'rifle-stock-contact.webp','rifle · опора приклада ×3')
            after=pages[1]
            for pose in ['rifle','pistol','melee']:
                after.evaluate('p=>avatarLab.engine.setPose(p)',pose);sheet=Image.new('RGB',(1400,1400),'#ded9cd');d=ImageDraw.Draw(sheet)
                for i,(label,bg) in enumerate([('Білий','#fff'),('Сірий','#777'),('Чорний','#000'),('Зелений','#00ff00')]):
                    after.evaluate('bg=>avatarLab.engine.setOptions({background:bg})',bg);im=frame(after).crop((150,280,850,944))
                    x=i%2*700;y=i//2*700;sheet.paste(im,(x,y+36));d.text((x+8,y+6),label,font=font,fill='#172022')
                name=pose+'-four-backgrounds.webp';sheet.save(OUT/name,lossless=True);panels.append((name,pose+' · 4 фони'))
            for p in pages:p.evaluate('Object.assign(avatarLab.engine.canvas.style,{width:"470px",height:"835.133px"});avatarLab.engine.setOptions({background:"#d3cfc6",breathing:false})')
            poses=['idle','melee','pistol','rifle']
            for first in poses:
                for second in poses:
                    if first==second:continue
                    rows=[]
                    for p in pages:p.evaluate('p=>{const e=avatarLab.engine;e.setOptions({transitionMs:0});e.time=0;e.setPose(p);e.setOptions({transitionMs:320})}',first)
                    pre=[save_frame(frame(p)) for p in pages]
                    for p in pages:p.evaluate('p=>avatarLab.engine.setPose(p)',second)
                    for time in range(0,321,16):
                        row={'time_ms':time}
                        for label,p in zip(['before','after'],pages):
                            p.evaluate('t=>{avatarLab.engine.time=t;avatarLab.engine.render()}',time);row[label]=save_frame(frame(p))
                        rows.append(row)
                    assert len({r['after'] for r in rows})==1,(first,second,'not an atomic cut')
                    switches.append({'from':first,'to':second,'pre_switch':pre,'frames':rows})
            for pose in ['idle','rifle','pistol','melee']:
                for p in pages:p.evaluate('p=>{avatarLab.engine.setOptions({breathing:true,transitionMs:320});avatarLab.engine.setPose(p)}',pose)
                full=[];close=[]
                for t in range(0,4000,125):
                    ims=[]
                    for p in pages:p.evaluate('t=>{avatarLab.engine.time=t;avatarLab.engine.render()}',t);ims.append(frame(p))
                    pairim=Image.new('RGB',(ims[0].width*2,ims[0].height+30),'#ded9cd');d=ImageDraw.Draw(pairim);d.text((8,3),'ДО',font=font,fill='#172022');d.text((ims[0].width+8,3),'ПОТОЧНИЙ · грудна клітка',font=font,fill='#172022')
                    for i,im in enumerate(ims):pairim.paste(im,(i*im.width,30))
                    full.append(pairim)
                    crops=[im.crop((145,155,335,315)).resize((570,480)) for im in ims];c=Image.new('RGB',(1140,510),'#ded9cd');dd=ImageDraw.Draw(c);dd.text((8,3),'ДО · цикл4000мс',font=font,fill='#172022');dd.text((578,3),'ПОТОЧНИЙ · додаткова локальна амплітуда',font=font,fill='#172022')
                    c.paste(crops[0],(0,30));c.paste(crops[1],(570,30));close.append(c)
                for suffix,frames in [('breathing',full),('chest-breathing',close)]:
                    name=pose+'-'+suffix+'.webp';frames[0].save(OUT/name,save_all=True,append_images=frames[1:],duration=125,loop=0,lossless=True);panels.append((name,pose+' · ДО/ПОТОЧНИЙ · 4000мс,32 реальні кадри'))
            for p,s in zip(pages,storage):assert s==p.evaluate('JSON.stringify({...localStorage})')
            after.goto(f'http://127.0.0.1:{servers[1].server_port}/avatar-lab/');after.wait_for_function('window.avatarLab?.ready');after.evaluate('avatarLab.engine.pause();avatarLab.engine.setOptions({breathing:false});avatarLab.engine.setPose("rifle")');after.set_viewport_size({'width':1440,'height':1100});after.screenshot(path=str(OUT/'lab-desktop.png'),full_page=True);panels.append(('lab-desktop.png','Lab · desktop'))
            for width in [320,390,768]:after.set_viewport_size({'width':width,'height':844});assert after.evaluate('document.documentElement.scrollWidth<=innerWidth');after.screenshot(path=str(OUT/f'lab-{width}.png'),full_page=True)
            assert not errors and not missing,(errors,missing)
            result={'baseline':'f49ae7b','real_entry':'avatar-lab/index.html','browser':browser.version,'states':states,'switches':switches,'directed_switches':len(switches),'frames_per_switch':21,'frames_per_version':252,'frame_size':[470,835],'switch_policy':'immediate opaque cut; no animation morph claimed','js_errors':errors,'http_errors':missing,'storage_unchanged':True,'physical_device':False}
            (OUT/'frame-report.json').write_text(json.dumps(result,indent=2)+'\n');browser.close()
    finally:
        for server in servers:server.shutdown();server.server_close()
style='body{max-width:1450px;margin:auto;padding:20px;background:#172022;color:#ece4d4;font:17px/1.5 system-ui}a{color:#a6d7df}img{max-width:100%;height:auto}figure{margin:25px 0}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}.pair img{width:100%}select,button,input{min-height:44px;font:inherit}input{width:100%}.notice{border:1px solid #9a8;padding:15px}pre{white-space:pre-wrap}@media(max-width:600px){body{padding:10px}}'
intro='<h1>Male Core2 · chest breathing / grips blocked</h1><p class="notice">Частковий прохід. ДО — f49ae7b, ПОТОЧНИЙ — додаткове локальне дихання грудної клітки. Хвати НЕ виправлено: обидві художні правки заблоковані інструментом генерації. Статичні кадри рук свідомо однакові. Жіночий риг, оригінальні PNG та всі пози збережені. Замість проблемного морфінгу чоловічі пози перемикаються одразу; плавної зміни анатомії не заявляємо. Цикл4000мс залишений. Pose-specific множники послаблюють рух рук і props; докази у breathing-metrics.json.</p><p><a href="Avatar-Lab.html">Автономний Lab</a> · <a href="Technical-report.html">Звіт</a></p>'
viewer='<h2>Повний покадровий A/B · 12 напрямків ×21 кадр</h2><p>Записано кожні16мс від0 до320мс для обох версій. У новій версії всі кадри після команди дорівнюють непрозорій цільовій позі. Кадр 0 показує позу ДО команди; далі цільова поза. Виберіть напрямок і кадр.</p><select id="switch"></select><input id="step" type="range" min="-1" max="20" value="-1"><button id="prev">← Кадр</button><button id="next">Кадр →</button><p id="label"></p><div class="pair"><figure><img id="before"><figcaption>ДО · f49ae7b</figcaption></figure><figure><img id="after"><figcaption>ПІСЛЯ · непрозорий cut</figcaption></figure></div><details><summary>Точні хеші кадру</summary><pre id="metadata"></pre></details>'
figures=''.join('<figure><img src="'+n+'"><figcaption>'+html.escape(t)+'</figcaption></figure>' for n,t in panels)
unique={key for s in switches for r in s['frames'] for key in [r['before'],r['after']]}
images={k:'frames/'+k+'.webp' for k in sorted(unique)}
script='const switches='+json.dumps(switches)+';const images='+json.dumps(images)+';'+'''const $=id=>document.getElementById(id);switches.forEach((s,i)=>{const o=document.createElement('option');o.value=i;o.textContent=s.from+' → '+s.to;$('switch').append(o)});function draw(){const s=switches[+$('switch').value],r=+$('step').value<0?{time_ms:-1,before:s.pre_switch[0],after:s.pre_switch[1]}:s.frames[+$('step').value];$('before').src=images[r.before];$('after').src=images[r.after];$('label').textContent=s.from+' → '+s.to+' · '+r.time_ms+'мс · кадр '+(+$('step').value+1)+'/21';$('metadata').textContent=JSON.stringify(r,null,2)}$('switch').onchange=draw;$('step').oninput=draw;$('prev').onclick=()=>{$('step').value=Math.max(-1,+$('step').value-1);draw()};$('next').onclick=()=>{$('step').value=Math.min(20,+$('step').value+1);draw()};draw();'''
doc='<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Male Core2 · chest breathing / grips blocked</title><style>'+style+'</style>'+intro+viewer+figures+'<script>'+script+'</script></html>'
(OUT/'index.html').write_text(doc.replace('href="Avatar-Lab.html"','href="../../avatar-lab/"'))
for name,_ in panels:
    p=OUT/name
    if p.suffix=='.webp':payload=p.read_bytes()
    else:
        b=io.BytesIO();Image.open(p).save(b,format='WEBP',lossless=True);payload=b.getvalue()
    doc=doc.replace('src="'+name+'"','src="data:image/webp;base64,'+base64.b64encode(payload).decode()+'"')
for key,path in images.items():doc=doc.replace('"'+path+'"','"data:image/webp;base64,'+base64.b64encode((OUT/path).read_bytes()).decode()+'"')
(OUT/'Report.html').write_text(doc)
print('A/B captured:',len(switches),'directions,252 frames per version;',len(unique),'unique frame images;',len(panels),'static/animated panels')
