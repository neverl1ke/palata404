from pathlib import Path
import subprocess,io,json,hashlib
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];D=R/'review/avatar-selective-merge';rows=[];imgs=[]
for line in subprocess.check_output(['git','rev-list','--objects','--all','--','avatar-core/assets/weapons'],cwd=R,text=True).splitlines():
 sha,_,name=line.partition(' ')
 if not name.endswith('.png'):continue
 data=subprocess.check_output(['git','cat-file','blob',sha],cwd=R);im=Image.open(io.BytesIO(data)).convert('RGBA');bbox=im.getbbox();thumb=im.crop(bbox) if bbox else im;thumb.thumbnail((370,200));rows.append({'path':name,'git_blob':sha,'sha256':hashlib.sha256(data).hexdigest(),'size':im.size,'bbox':bbox,'first_commit':subprocess.check_output(['git','log','--all','--reverse','--format=%h %s','--find-object='+sha],cwd=R,text=True).splitlines()[:1]});imgs.append(thumb)
sheet=Image.new('RGB',(1200,((len(imgs)+2)//3)*250),'#ddd');d=ImageDraw.Draw(sheet);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11)
for i,(row,im) in enumerate(zip(rows,imgs)):
 x=(i%3)*400;y=(i//3)*250;sheet.paste(im,(x,y),im);d.text((x+4,y+205),str(i)+' '+row['path'].split('weapons/')[-1]+'\n'+row['git_blob'][:12],font=font,fill='black')
sheet.save(D/'Gallery/weapon-history.webp',lossless=True);(D/'Evidence/weapon-history.json').write_text(json.dumps(rows,indent=2)+'\n');print(len(rows),'unique historical weapon PNGs')
