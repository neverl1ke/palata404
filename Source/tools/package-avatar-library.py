"""Create two self-contained offline review archives; never publish the game."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def package(report,output):
    output.mkdir(parents=True,exist_ok=True)
    data=json.loads((report/'combination-manifest.json').read_text())
    assert len(data['records'])==3375
    archives=[]
    for gender in ['male','female']:
        scoped={**data,'records':[r for r in data['records'] if r['gender']==gender],
                'full_body':[r for r in data['full_body'] if r['gender']==gender]}
        stem='palata404-'+gender+'-avatar-library'
        archive=output/(stem+'.zip');prefix=stem+'/'
        paths={r['path'] for r in scoped['records']}|{r['path'] for r in scoped['full_body']}
        paths.update(str(p.relative_to(report)) for p in (report/'overviews').glob(gender+'-*.webp'))
        # Keep the source mapping, original PNGs, historical resources, actual
        # test logs and reload evidence. Only redundant early contact sheets
        # are excluded; the full working report retains them.
        for p in report.rglob('*'):
            if not p.is_file():continue
            rel=p.relative_to(report)
            if rel.parts[0] in {'captures','overviews','quick','geometry'}:continue
            if str(rel) in {'data.js','combination-manifest.json'}:continue
            paths.add(str(rel))
        for name in ['inputs.json','result.json']:paths.add('captures/'+name)
        integrated=[ROOT/f'base_{gender}.png',*(ROOT/'assets/wardrobe/faces').glob(f'{gender}_*_head.png'),
                    *(ROOT/'assets/wardrobe/faces/masks').glob(f'{gender}_*_body.png')]
        assert len(integrated)==17
        with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for path in sorted(paths):z.write(report/path,prefix+path)
            for path in sorted(integrated):z.write(path,prefix+'integrated/'+str(path.relative_to(ROOT)))
            z.writestr(prefix+'data.js','window.AVATAR_AUDIT='+json.dumps(scoped,ensure_ascii=False,separators=(',',':'))+';\n')
            z.writestr(prefix+'combination-manifest.json',json.dumps(scoped,ensure_ascii=False,indent=2)+'\n')
            z.writestr(prefix+'captures/records.jsonl',''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in scoped['records']))
            z.writestr(prefix+'ПОЧАТИ-ТУТ.txt',f'Розпакуйте весь архів. Відкрийте avatar_visual_audit.html.\nЦей том: {gender}, {len(scoped["records"])} детальних кадрів і {len(scoped["full_body"])} повноростових еталонів.\nREADME.md і журнали містять спільний звіт обох томів: 3375 комбінацій.\nУ integrated/ — 17 активних PNG цієї статі зі збереженими шляхами. Це копії ресурсів для огляду, не окрема гра.\nГра та main не опубліковані; це матеріали для огляду.\n')
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            names=set(z.namelist())
            assert all(prefix+r['path'] in names for r in scoped['records']+scoped['full_body'])
            assert prefix+'avatar_visual_audit.html' in names
        archives.append({'file':archive.name,'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'gender':gender,'details':len(scoped['records']),'full_body':len(scoped['full_body']),'integrated_pngs':len(integrated),'crc_check':True})
    (output/'avatar-library-archives.json').write_text(json.dumps(archives,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(archives,ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--report',type=Path,default=ROOT/'review/male-heads-full-library');p.add_argument('--output',type=Path,default=Path('/workspace/outputs'));a=p.parse_args();package(a.report,a.output)
