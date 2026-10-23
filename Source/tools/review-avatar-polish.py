"""Actual Lab captures and same-scale prototype/polish comparisons.

--capture refreshes the eight main frames first; --gallery-only uses existing
captures. Generated hand atlases are provenance, never substitute screenshots.
"""
import argparse,base64,functools,html,io,json,subprocess,threading,re
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from PIL import Image,ImageDraw,ImageFont
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'review/avatar-core-polish';OLD=OUT/'before'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--capture',action='store_true')
parser.add_argument('--gallery-only',action='store_true')
args=parser.parse_args();OUT.mkdir(parents=True,exist_ok=True)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',19)
if args.capture:
    subprocess.run(['python',str(ROOT/'tools/review-avatar-core.py'),'--output',str(OUT)],check=True,cwd=ROOT)

def compare(before,after,title,path):
    result=Image.new('RGB',(before.width+after.width,before.height+40),'#e0dcd3')
    draw=ImageDraw.Draw(result);draw.text((9,8),'ДО · '+title,font=font,fill='#172426')
    draw.text((before.width+9,8),'ПІСЛЯ · '+title,font=font,fill='#172426')
    result.paste(before,(0,40));result.paste(after,(before.width,40));result.save(path,lossless=True)

before={(s['gender'],s['pose']):s for s in json.loads((OLD/'browser-check.json').read_text())['states']}
after={(s['gender'],s['pose']):s for s in json.loads((OUT/'browser-check.json').read_text())['states']}
crops=[]
for g in ['male','female']:
    a=Image.open(OLD/f'{g}-rifle.png').convert('RGB');b=Image.open(OUT/f'{g}-rifle.png').convert('RGB')
    assert a.size==b.size==(941,1672)
    compare(a,b,g+' · rifle · 1:1',OUT/f'{g}-rifle-before-after.webp')
    for side in ['right','left']:
        for joint in ['shoulder','elbow','wrist','grip']:
            centres=[before[g,'rifle']['frame']['arms'][side][joint],after[g,'rifle']['frame']['arms'][side][joint]]
            images=[]
            for im,(x,y) in zip([a,b],centres):
                images.append(im.crop((round(x-85),round(y-85),round(x+85),round(y+85))).resize((510,510)))
            name=f'{g}-{side}-{joint}-before-after.webp';compare(*images,g+' · '+side+' · '+joint+' ×3',OUT/name)
            crops.append({'file':name,'source_pixels':170,'display_zoom':3,'before_center':centres[0],'after_center':centres[1]})
    for pose in ['melee','pistol','rifle']:
        im=Image.open(OUT/f'{g}-{pose}.png')
        for side in ['right','left']:
            if pose=='melee' and side=='left':continue
            x,y=after[g,pose]['frame']['arms'][side]['grip']
            im.crop((round(x-85),round(y-85),round(x+85),round(y+85))).resize((510,510)).save(OUT/f'{g}-{pose}-{side}-hand-300.webp',lossless=True)
(OUT/'comparison-registration.json').write_text(json.dumps({'baseline_commit':'1331a91','full_frame':[941,1672],
    'note':'Full stance uses unchanged camera. Detail panels centre each actual joint separately, at identical3x zoom. Pose calibration differs intentionally.','crops':crops},indent=2)+'\n')

if not args.gallery_only:
    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start();errors=[];http=[];records=[]
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch();p=browser.new_page(viewport={'width':1560,'height':2050})
            p.on('pageerror',lambda e:errors.append(str(e)))
            p.on('response',lambda r:http.append([r.url,r.status]) if r.status>=400 else None)
            p.goto(f'http://127.0.0.1:{server.server_port}/avatar-lab/');p.wait_for_function('window.avatarLab?.ready')
            p.evaluate('avatarLab.engine.pause();avatarLab.engine.setOptions({breathing:false,transitionMs:0,pistolSupport:true});Object.assign(avatarLab.engine.canvas.style,{width:"941px",height:"1672px",maxWidth:"none",minWidth:"0",position:"fixed",left:"0",top:"0",margin:"0",padding:"0",border:"0",transform:"none",maxHeight:"none"})')
            backgrounds=[('Білий','#fff'),('Сірий','#777'),('Чорний','#000'),('Зелений','#00ff00')]
            for g in ['male','female']:
                p.evaluate('g=>avatarLab.engine.setGender(g)',g)
                for pose in ['idle','melee','pistol','rifle']:
                    sheet=Image.new('RGB',(1600,1640),'#e0dcd3');draw=ImageDraw.Draw(sheet)
                    for index,(label,bg) in enumerate(backgrounds):
                        p.evaluate('v=>{avatarLab.engine.setOptions({background:v[1]});avatarLab.engine.setPose(v[0])}',[pose,bg])
                        im=Image.open(io.BytesIO(p.locator('#avatar').screenshot())).convert('RGB')
                        assert im.size==(941,1672)
                        x=(index%2)*800;y=(index//2)*820
                        draw.text((x+10,y+8),g+' · '+pose+' · '+label,font=font,fill='#172426')
                        sheet.paste(im.crop((120,280,920,1060)),(x,y+40));records.append({'gender':g,'pose':pose,'background':bg})
                    sheet.save(OUT/f'{g}-{pose}-four-backgrounds.webp',lossless=True)
                p.evaluate('avatarLab.engine.setOptions({background:"#d3cfc6",transitionMs:0});avatarLab.engine.setPose("idle");Object.assign(avatarLab.engine.canvas.style,{width:"470px",height:"835.133px"});avatarLab.engine.render()')
                frames=[]
                for pose in ['rifle','pistol','melee','idle']:
                    p.evaluate('v=>{avatarLab.engine.setOptions({transitionMs:320});avatarLab.engine.setPose(v)}',pose)
                    for index in range(13):
                        if index<8:p.evaluate('avatarLab.engine.step(40)')
                        frames.append(Image.open(io.BytesIO(p.locator('#avatar').screenshot())).convert('RGB'))
                frames[0].save(OUT/f'{g}-transitions.webp',save_all=True,append_images=frames[1:],duration=40,loop=0,lossless=True)
                p.evaluate('Object.assign(avatarLab.engine.canvas.style,{width:"941px",height:"1672px"});avatarLab.engine.setOptions({transitionMs:0})')
            assert not errors and not http,(errors,http)
            (OUT/'supplemental-browser-check.json').write_text(json.dumps({'browser':'Chromium '+browser.version,'background_cases':records,'transition_frames_per_gender':52,'transition_duration_ms':320,'errors':errors,'http_errors':http,'side_view':'Not available in original front-view2D assets; not generated.'},indent=2)+'\n');browser.close()
    finally:server.shutdown();server.server_close()

sections=[]
def image(name,caption):return '<figure><img loading="lazy" src="'+name+'" alt="'+html.escape(caption)+'"><figcaption>'+html.escape(caption)+'</figcaption></figure>'
for pose in ['idle','melee','pistol','rifle']:
    sections.append('<section><h2>'+pose+' · обидві моделі</h2><div class="grid">'+''.join(image(f'{g}-{pose}.png',g+' · '+pose) for g in ['male','female'])+'</div></section>')
sections.append('<section><h2>Рух між позами ·320мс</h2><div class="grid">'+''.join(image(f'{g}-transitions.webp',g+' · переходи') for g in ['male','female'])+'</div></section>')
sections.append('<section><h2>Дихання ·4000мс</h2><div class="grid">'+''.join(image(f'{g}-breathing.webp',g+' · дихання') for g in ['male','female'])+'</div></section>')
sections.append('<section><h2>Rifle · ДО/ПІСЛЯ</h2>'+''.join(image(f'{g}-rifle-before-after.webp',g+' · та сама камера й масштаб') for g in ['male','female'])+'</section>')
for joint in ['shoulder','elbow','wrist','grip']:
    sections.append('<section><h2>'+joint+' · ДО/ПІСЛЯ ×3</h2><p>Центрування кожного фактичного суглоба окреме; масштаб однаковий.</p>'+''.join(image(f'{g}-{s}-{joint}-before-after.webp',g+' · '+s) for g in ['male','female'] for s in ['right','left'])+'</section>')
sections.append('<section><h2>Нові хвати ×3</h2><div class="grid">'+''.join(image(f'{g}-{pose}-{side}-hand-300.webp',g+' · '+pose+' · '+side) for g in ['male','female'] for pose in ['melee','pistol','rifle'] for side in ['right','left'] if not(pose=='melee' and side=='left'))+'</div></section>')
sections.append('<section><h2>Контрастні фони · без зменшення вихідного фрагмента</h2>'+''.join(image(f'{g}-{pose}-four-backgrounds.webp',g+' · '+pose) for g in ['male','female'] for pose in ['idle','melee','pistol','rifle'])+'</section>')
sections.append('<section><h2>Avatar Lab</h2>'+image('lab-desktop.png','Десктоп')+'<div class="grid">'+''.join(image(f'lab-mobile-{w}.png',str(w)+'px · емуляція') for w in [320,390,768])+'</div></section>')
checks=OUT/'validation-summary.json'
statements=json.loads(checks.read_text())['statements'] if checks.exists() else ['Фінальний регресійний прогін триває; проміжний результат не оголошується остаточним.']
doc='''<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Палата404 · Avatar Core · polish</title><style>body{margin:auto;padding:20px;max-width:1440px;background:#172022;color:#e2dcd0;font:17px/1.5 system-ui}a{color:#a6d7df}.notice{padding:18px;border:1px solid #9b8a68;background:#303731}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}img{width:100%;height:auto;background:#d3cfc6}figure{margin:10px 0 22px}section{border-top:1px solid #586060;margin-top:30px}figcaption{color:#c5c5b9}h1{font:36px Georgia,serif}@media(max-width:600px){body{padding:12px}.grid{grid-template-columns:1fr}h1{font-size:28px}}</style><h1>Avatar Core · цільовий polish pass</h1><p class="notice">Нові кадри фактичного Avatar Lab. Вихідні тіла, обличчя й пропорції не замінені. Позові кисті — окремі локальні домальовки. Робота тільки в feature/avatar-core-1; main і публікація не змінені. Остаточне художнє приймання потребує перегляду крупних планів.</p><p><a href="../../avatar-lab/">Інтерактивний Avatar Lab (HTTP)</a> · <a href="README.md">Технічний звіт</a></p><h2>Перевірки та межі</h2><ul>'''+''.join('<li>'+html.escape(v)+'</li>' for v in statements)+'</ul><p>Справжнього бічного ракурсу у фронтальних2D джерелах немає. Схематична зброя не доводить точний контакт із деталями майбутньої фінальної зброї. Форма пальців позова; окремої анімації стискання пальців не додавали.</p>'+''.join(sections)+'</html>'
(OUT/'index.html').write_text(doc)
def embed(match):
    p=OUT/match[1];im=Image.open(p)
    if p.suffix=='.webp':payload=p.read_bytes()
    else:
        buf=io.BytesIO();im.save(buf,format='WEBP',lossless=True);payload=buf.getvalue()
        assert Image.open(io.BytesIO(payload)).convert('RGBA').tobytes()==im.convert('RGBA').tobytes()
    return 'src="data:image/webp;base64,'+base64.b64encode(payload).decode()+'"'
offline=re.sub(r'src="([^"]+)"',embed,doc.replace('href="../../avatar-lab/"','href="Avatar-Lab.html"').replace('href="README.md"','href="Technical-report.html"').replace(' loading="lazy"',''))
(OUT/'Report.html').write_text(offline)
print('Polish gallery:',doc.count('<img '),'actual-render images;',len(offline.encode()),'offline bytes')
