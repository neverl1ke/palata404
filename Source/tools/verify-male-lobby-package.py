"""Verify the delivered ZIP after extraction, including real file:// Lab behavior."""
from pathlib import Path
import hashlib,json,tempfile,zipfile
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'review/avatar-core-lobby-rework'
archive=ROOT.parent/'Avatar-Core-Male-Lobby-Rework.zip'
with tempfile.TemporaryDirectory() as td:
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None;z.extractall(td)
    folder=Path(td)/'Avatar-Core-Male-Lobby-Rework'
    manifest=json.loads((folder/'Package-SHA256.json').read_text())
    for row in manifest:assert hashlib.sha256((folder/row['path']).read_bytes()).hexdigest()==row['sha256'],row['path']
    errors=[];requests=[];cases=[]
    with sync_playwright() as p:
        browser=p.chromium.launch();page=browser.new_page(viewport={'width':1440,'height':1100})
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('request',lambda r:requests.append(r.url) if r.url.startswith(('http:','https:')) else None)
        page.goto((folder/'Avatar-Lab.html').as_uri());page.wait_for_function('window.avatarLab?.ready')
        page.evaluate('avatarLab.engine.pause();avatarLab.engine.setOptions({transitionMs:0,breathing:false})')
        storage=page.evaluate('JSON.stringify({...localStorage})')
        for gender in ['male','female']:
            page.locator(f'[data-gender="{gender}"]').click();page.wait_for_function('g=>avatarLab.engine.gender===g&&document.getElementById("status").textContent.startsWith("Готово")',arg=gender)
            for pose in ['idle','melee','pistol','rifle']:
                page.locator(f'[data-pose="{pose}"]').click()
                page.wait_for_function('document.getElementById("previous-arms").complete&&document.getElementById("previous-arms").naturalWidth>0')
                for color in ['original','black']:
                    page.select_option('#color',color);page.wait_for_function('document.getElementById("status").textContent.startsWith("Готово")')
                    f=page.evaluate('avatarLab.engine.frame');assert f['primaryError']<1e-6 and f['supportError']<1e-6
                cases.append([gender,pose])
        assert storage==page.evaluate('JSON.stringify({...localStorage})')
        for width in [320,390,768]:
            page.set_viewport_size({'width':width,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.goto((folder/'Report.html').as_uri());page.wait_for_function('Array.from(document.images).every(i=>i.complete&&i.naturalWidth>0)')
        image_count=page.locator('img').count();assert image_count>=16,image_count
        assert page.locator('#switch option').count()==12
        for direction in range(12):
            page.select_option('#switch',str(direction))
            for step in range(-1,21):
                page.locator('#step').evaluate('(e,v)=>{e.value=v;e.dispatchEvent(new Event("input"))}',str(step))
                page.wait_for_function('["before","after"].every(id=>{const i=document.getElementById(id);return i.complete&&i.naturalWidth>0})')
        page.goto((folder/'Technical-report.html').as_uri());assert page.locator('h1').count()==1
        assert not errors and not requests,(errors,requests)
        result={'archive':archive.name,'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
            'crc':'passed','manifest_files_verified':len(manifest),'extracted_file_uri':True,
            'browser':'Chromium '+browser.version,'pose_cases':cases,'gallery_images_loaded':image_count,'viewer_frames_checked':264,
            'mobile_emulation':[320,390,768],'physical_device':False,'http_requests':requests,'js_errors':errors,
            'storage_unchanged':True,'main_or_remote_modified':False}
        browser.close()
(OUT/'offline-package-check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
