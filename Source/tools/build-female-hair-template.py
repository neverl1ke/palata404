"""Export the unchanged young-face reference, measured guides and hair contract."""
import json,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageChops
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'review/female-head-standard';OUT=D/'template'
def run():
 OUT.mkdir(exist_ok=True);m=json.loads((D/'manifest.json').read_text());ref=next(e for e in m['heads'] if e['reference']);head=Image.open(ROOT/ref['output']).convert('RGBA');base=Image.open(ROOT/'base_female.png').convert('RGBA');body=base.copy();body.putalpha(ImageChops.multiply(body.getchannel('A'),Image.open(ROOT/ref['mask']).getchannel('A')));body=Image.alpha_composite(body,head)
 shutil.copyfile(ROOT/ref['output'],OUT/'reference-head.png');body.save(OUT/'reference-body.png',optimize=True)
 a=np.array(head)[:,:,3]>=128;cap=[]
 for y in range(33,125):
  x=np.where(a[y])[0]
  if len(x):cap.append({'y':y,'left':int(x.min()),'right':int(x.max())})
 union=np.zeros((1672,941),bool)
 for e in m['heads']:union[:125]|=np.array(Image.open(ROOT/e['output']))[:125,:,3]>=128
 yy,xx=np.where(union);envelope={'left':int(xx.min()),'top':int(yy.min()),'right':int(xx.max()),'bottom':int(yy.max()),'width':int(np.ptp(xx)+1),'height':int(np.ptp(yy)+1)}
 params={'reference_id':'face-young','reference_png':'reference-head.png','units':'natural Paper Doll pixels, not screen CSS pixels','frame':{'width':941,'height':1672,'origin':'top-left','format':'RGBA PNG, transparent background'},'head_mount':{'left_x':385,'right_x':560,'width':176,'crown_y':33,'center_x':472.5,'threshold_alpha':128},'reference_scalp_above_ears':{'rows':cap,'bounds':{'left':min(r['left'] for r in cap),'right':max(r['right'] for r in cap),'top':33,'bottom':124}},'common_upper_scalp_envelope':envelope,'landmarks_reference_visual_approximate':{'left_eye':[438,141],'right_eye':[508,141],'chin':[474,240],'left_temple':[400,120],'right_temple':[546,120],'left_ear_box':[385,124,415,185],'right_ear_box':[530,124,561,185]},'rendering':{'fittedToGender':True,'x':0,'y':0,'width':941,'height':1672,'scale':1,'front_z':9,'optional_rear_z':-1},'high_resolution_crop':{'x':340,'y':0,'width':270,'height':420,'magnification':4,'export_width':1080,'export_height':1680,'return_scale':.25,'return_x':340,'return_y':0},'limits':['All female heads share the mounting width, crown height and horizontal centre; facial shape, ear anatomy and jaw length remain individual.','A single uniform scale preserves identity; ear maximum-width rows still differ between portraits.','For short hair, cover the common upper-scalp envelope with a small natural strand overlap; the reference silhouette alone does not prove compatibility.','AI generation must be followed by real overlay verification; pixel coordinates in a prompt alone cannot guarantee exact placement.']}
 (OUT/'hair-template.json').write_text(json.dumps(params,ensure_ascii=False,indent=2)+'\n')
 guide=body.copy();d=ImageDraw.Draw(guide);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
 d.line((472.5,5,472.5,320),fill=(20,170,255,220),width=1);d.rectangle((385,33,560,241),outline=(0,180,230,255),width=1)
 for y,label in [(33,'crown y=33'),(124,'ear zone y~124'),(141,'eyes y~141'),(240,'chin y~240')]:
  d.line((350,y,595,y),fill=(0,170,230,200),width=1);d.text((600,y-7),label,font=font,fill=(20,70,100,255))
 for box in [[385,124,415,185],[530,124,561,185]]:d.rectangle(box,outline=(235,150,0,255),width=1)
 d.text((350,12),'x=385..560 / width=176',font=font,fill=(20,70,100,255));guide.save(OUT/'geometry-guide.png',optimize=True)
 body.crop((340,0,610,420)).resize((1080,1680),Image.Resampling.NEAREST).save(OUT/'reference-head-4x.png',optimize=True)
 guide.crop((340,0,700,330)).resize((1440,1320),Image.Resampling.NEAREST).save(OUT/'geometry-guide-4x.png',optimize=True)
 overlay=Image.new('RGBA',(941,1672));ov=np.array(overlay);ov[union]=[30,180,245,90];Image.fromarray(ov).save(OUT/'common-scalp-envelope.png',optimize=True)
 prompt='''Створи тільки жіночу зачіску для прикріпленого еталона «Молоде обличчя» гри «Палата 404». Використовуй надане зображення як незмінну геометричну підкладку. Не перемальовуй голову, лице, вуха, шию або тіло. Збережи фронтальний ракурс без повороту, нахилу й зміни перспективи. Художній стиль: semi-realistic hand-painted 2D game art, muted colours, dark psychological horror.\n\nФінальний ігровий ресурс: прозорий RGBA PNG 941×1672, початок координат у верхньому лівому куті, без автоматичного обрізання прозорих полів. Голова займає x=385..560 разом із вухами, ширина 176 px; верх лисої маківки y=33, вісь x=472.5. Обличчя й вуха мають залишатися природно відкритими відповідно до дизайну зачіски; орієнтири на еталоні: скроні приблизно (400,120)/(546,120), очі приблизно y=141. Верхній об’єм волосся може виходити вище y=33 — це висота шкіри маківки, а не обов’язковий край волосся. Врахуй common-scalp-envelope.png, щоб коротка зачіска перекривала верхній контур усіх жіночих голів без лисих просвітів.\n\nВиводь лише волосся: без обличчя, шкіри, тіла, одягу, фону, розмітки й написів. Краї пасом мають бути чистими, з природним antialiasing і без кольорового ореолу. Для довгих зачісок за потреби віддай окремі задні пасма на тому самому полотні; передній шар над головою, задній — позаду тіла. Посадка готового вирівняного PNG: x=0, y=0, scale=1, width=941, height=1672.\n\nПісля генерації обов’язкова технічна реєстрація й перевірка накладання: текстовий промпт сам по собі не гарантує піксельно точного результату.\n'''
 (OUT/'HAIR_GENERATION_PROMPT_UK.txt').write_text(prompt)
 print('Reference scalp bounds:',params['reference_scalp_above_ears']['bounds'],'common cap:',envelope)
if __name__=='__main__':run()
