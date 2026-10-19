"""GitHub-readable female review pages; no HTML download or local server."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'review/female-heads-new-library';OUT=D/'browser-gallery'
def run():
 OUT.mkdir(exist_ok=True)
 entries=json.loads((D/'integration-manifest.json').read_text())['files']
 records=[json.loads(s) for s in (D/'captures/records.jsonl').read_text().splitlines()]
 index=['# Палата 404 — перегляд нових жіночих облич','', 'Зображення відкриваються прямо на цій сторінці. Натисніть назву обличчя, щоб побачити ДО/ПІСЛЯ, всі зачіски, світле й темне волосся та перевірку на чотирьох фонах.','', '**Це контрольні знімки локальної інтеграції. Онлайн-гру ще не оновлено.**','', '![Вісім нових жіночих облич](../all-new-faces.webp)','', '[Повний звіт](../README.md) · [Відповідність джерел і назв](../SOURCE_MAPPING.md)','']
 for e in entries:
  k=e['kind'];name=e['name'];index += [f'## [{name}]({k}.md)','',f'![ДО / ПІСЛЯ — {name}](../review-captures/{k}-comparison.webp)','']
  lines=[f'# {name}','', '[← Усі обличчя](README.md)','',f"ID: `{e['id']}`. Джерело: `{e['original_name']}`.",'', 'ДО — той самий новий портрет після реєстрації, до узгодження тону та шийного стику. ПІСЛЯ — робоча інтеграція. Усі примірки отримані з фактичного рендеру index.html.','', f'![ДО / ПІСЛЯ](../review-captures/{k}-comparison.webp)','', '## Усі зачіски','',f'![Усі зачіски](../overviews/{k}-hairstyles.webp)','', '## Original / black / white','']
  for c in ['original','black','white']:
   lines += [f'### {c}','']
   for r in records:
    if r['face']==e['id'] and r['color']==c and r['path']:
     lines += [f"**{r['hair']}**",'',f"![{r['hair']} / {c}](../{r['path']})",'']
  lines += ['## Чотири фони, біле волосся','']
  for bg,label in [('white','Білий'),('gray','Сірий'),('black','Чорний'),('green','Зелений')]:
   lines += [f'### {label}','']
   for h in ['hair-none','hair-messy','hair-shoulder-length','hair-bob-bangs']:
    lines += [f'![{bg} / {h}](../review-captures/{k}/{bg}-{h}.webp)','']
  lines += ['## Туніка та повний зріст','',f'![Туніка, original](../review-captures/{k}/tunic-original.webp)','',f'![Туніка, black](../review-captures/{k}/tunic-black.webp)','',f'![Повний зріст](../review-captures/{k}/full.webp)','']
  (OUT/(k+'.md')).write_text('\n'.join(lines).rstrip()+'\n')
 index += ['## Вуха та шийні стики крупним планом','', '![Вуха ×4 та шия ×2](../ear-neck-details.webp)','', '## Гардероб на телефоні — емуляція Chromium','', '![390 px](../review-captures/mobile-390-faces.webp)','']
 (OUT/'README.md').write_text('\n'.join(index).rstrip()+'\n')
if __name__=='__main__':run()
