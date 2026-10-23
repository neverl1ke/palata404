"""Re-render frozen1331a91 in a temporary read-only source tree, not main."""
from pathlib import Path
import functools,hashlib,io,json,subprocess,tarfile,tempfile,threading
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'review/avatar-core-polish/before'
OUT.mkdir(parents=True,exist_ok=True);COMMIT='1331a91'
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
paths=['avatar-core','avatar-lab','base_male.png','base_female.png',
       'paper-doll-data.js','paper-doll.js','hair-color.js']
with tempfile.TemporaryDirectory(prefix='palata-prototype-before-') as directory:
    folder=Path(directory)
    archive=subprocess.check_output(['git','archive',COMMIT,*paths],cwd=ROOT)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:tar.extractall(folder,filter='data')
    # Existing wardrobe sources did not change in this isolated feature branch.
    (folder/'assets').symlink_to(ROOT/'assets',target_is_directory=True)
    server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(folder)))
    threading.Thread(target=server.serve_forever,daemon=True).start();states=[];errors=[];missing=[]
    try:
        with sync_playwright() as pw:
            b=pw.chromium.launch();p=b.new_page(viewport={'width':1560,'height':2050})
            p.on('pageerror',lambda e:errors.append(str(e)))
            p.on('response',lambda r:missing.append([r.url,r.status]) if r.status>=400 else None)
            p.goto(f'http://127.0.0.1:{server.server_port}/avatar-lab/');p.wait_for_function('window.avatarLab?.ready')
            p.evaluate('''()=>{const e=avatarLab.engine;e.pause();e.setOptions({breathing:false,transitionMs:0});Object.assign(e.canvas.style,{width:'941px',height:'1672px',maxWidth:'none',minWidth:'0',position:'fixed',left:'0',top:'0',margin:'0',padding:'0',border:'0',transform:'none',maxHeight:'none'});}''')
            for gender in ['male','female']:
                p.evaluate('g=>avatarLab.engine.setGender(g)',gender)
                for pose in ['idle','melee','pistol','rifle']:
                    p.evaluate('p=>avatarLab.engine.setPose(p)',pose)
                    assert p.locator('#avatar').bounding_box()['width']==941
                    p.locator('#avatar').screenshot(path=str(OUT/f'{gender}-{pose}.png'))
                    states.append(p.evaluate('avatarLab.engine.snapshot()'))
            b.close()
    finally:server.shutdown();server.server_close()
    assert not errors and not missing,(errors,missing)
    hashes={str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest()
            for d in ['avatar-core','avatar-lab'] for p in (folder/d).rglob('*') if p.is_file()}
    (OUT/'browser-check.json').write_text(json.dumps({'source_commit':subprocess.check_output(['git','rev-parse',COMMIT],cwd=ROOT,text=True).strip(),
        'states':states,'source_hashes':hashes,'errors':errors,'http_errors':missing,
        'capture_frame':[941,1672],'note':'Actual frozen prototype rendered anew at integer camera position; historical review files untouched.'},indent=2)+'\n')
print('Frozen prototype:8 actual941x1672 frames; main unchanged.')
