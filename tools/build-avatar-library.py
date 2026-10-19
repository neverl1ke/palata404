"""Package the exhaustive screenshots into a local, dependency-free gallery."""
import argparse
import json
from pathlib import Path

from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]


def build(report,metadata_only=False):
    result=json.loads((report/'captures/result.json').read_text())
    records=[json.loads(line) for line in (report/'captures/records.jsonl').read_text().splitlines()]
    assert len(records)==result['expected']==3375
    issues=json.loads((report/'issues.json').read_text())
    decisions=json.loads((report/'visual-assessment.json').read_text())
    restored=set()
    for journal in (report/'reload').glob('shard-*.jsonl'):
        for line in journal.read_text().splitlines():
            proof=json.loads(line)
            if proof['restored'] and proof['patient_trip_preserved']:restored.add(proof['key'])
    for record in records:
        decision=decisions.get('/'.join([record['gender'],record['face'] or 'base',record['hair']]))
        record['status']=decision['status'] if decision else 'REVIEW'
        record['issues']=list(decision.get('issues',[])) if decision else []
        record['reload_verified']=record['key'] in restored
    data={'catalog':result['catalog'],'records':records,'full_body':result['full_body'],'issues':issues,
          'summary':'Усі комбінації знято реальним рендерером. Зауваження не виправлялися без огляду власником.'}
    (report/'data.js').write_text('window.AVATAR_AUDIT='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n')
    (report/'combination-manifest.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    if metadata_only:
        print('Updated gallery metadata:',len(records),'screenshots,',len(restored),'reload proofs')
        return
    overviews=report/'overviews';overviews.mkdir(exist_ok=True)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
    for gender,info in result['genders'].items():
        for face in info['faces']:
            combos=[r for r in records if r['gender']==gender and r['face']==face]
            sheet=Image.new('RGB',(160*len(info['hairs']),180*len(info['colors'])),'#dedbd4');draw=ImageDraw.Draw(sheet)
            original=Image.new('RGB',(400*4,424*2),'#dedbd4');odraw=ImageDraw.Draw(original)
            for r in combos:
                row=info['colors'].index(r['color']);column=info['hairs'].index(r['hair']);im=Image.open(report/r['path']).convert('RGB')
                sheet.paste(im.resize((160,160),Image.Resampling.LANCZOS),(column*160,row*180+20));draw.text((column*160+3,row*180+1),r['color'],font=font,fill='black')
                if r['color']=='original':
                    x=column%4*400;y=column//4*424;original.paste(im,(x,y+24));odraw.text((x+3,y+2),r['hair'],font=font,fill='black')
            stem=gender+'-'+(face or 'base')
            sheet.save(overviews/(stem+'-all-colors.webp'),lossless=True,method=4)
            original.save(overviews/(stem+'-geometry.webp'),lossless=True,method=4)
    print('Built gallery:',len(records),'combinations')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--report',type=Path,default=ROOT/'review/male-heads-full-library');p.add_argument('--metadata-only',action='store_true');a=p.parse_args();build(a.report,a.metadata_only)
