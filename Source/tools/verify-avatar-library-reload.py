"""Reload every library state, in deterministic independent browser shards."""
import argparse
import functools
import hashlib
import json
import threading
import time
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]


class LocalServer(ThreadingHTTPServer):
    request_queue_size=128


class LocalHandler(SimpleHTTPRequestHandler):
    protocol_version='HTTP/1.1'
    def log_message(self,*args):pass


def run(report,shard,shards,stream=False):
    result_path=report/'captures/result.json'
    assert stream or result_path.exists(),'Capture not complete; use --stream to validate committed journal entries while it runs'
    inputs=json.loads((report/'captures/inputs.json').read_text())
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in inputs.items()),'Runtime changed since capture'
    output=report/'reload';output.mkdir(exist_ok=True)
    partition={'shards':shards,'inputs_sha256':hashlib.sha256((report/'captures/inputs.json').read_bytes()).hexdigest()}
    if (output/'partition.json').exists():assert json.loads((output/'partition.json').read_text())==partition
    else:(output/'partition.json').write_text(json.dumps(partition,indent=2)+'\n')
    done_path=output/f'shard-{shard}.json';journal=output/f'shard-{shard}.jsonl'
    if done_path.exists():raise SystemExit('Completed shard exists')
    completed={json.loads(s)['key'] for s in journal.read_text().splitlines()} if journal.exists() else set()
    expected_shard=len(range(shard,3375,shards))
    def pending():
        while True:
            raw=(report/'captures/records.jsonl').read_bytes()
            if not raw.endswith(b'\n'):raw=raw.rsplit(b'\n',1)[0]+b'\n'
            rows=[json.loads(s) for s in raw.splitlines() if s]
            for row in rows[shard::shards]:
                if row['key'] not in completed:yield row
            if result_path.exists():
                assert len(rows)==json.loads(result_path.read_text())['expected']==3375
                return
            if (report/'captures/failure.json').exists():raise RuntimeError('Primary capture failed; retain logs and resume capture first')
            time.sleep(1)
    server=LocalServer(('127.0.0.1',0),functools.partial(LocalHandler,directory=str(ROOT)))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();errors=[];http=[]
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True);context=browser.new_context(viewport={'width':1100,'height':850})
            page=context.new_page()
            # Routing disables Chromium's HTTP cache for the whole context.
            # Block only external HTTPS via CDP, retaining normal local reload
            # caching. No local response body is changed or substituted.
            network=context.new_cdp_session(page);network.send('Network.enable')
            network.send('Network.setBlockedURLs',{'urls':['https://*']})
            network.send('Network.setCacheDisabled',{'cacheDisabled':False})
            page.on('pageerror',lambda e:errors.append(str(e)));page.on('response',lambda r:http.append([r.status,r.url]) if r.status>=400 else None)
            page.on('dialog',lambda d:d.accept());page.goto(f'http://127.0.0.1:{server.server_port}/index.html',wait_until='load')
            page.wait_for_function('document.readyState==="complete" && typeof paperDollState!=="undefined"')
            protected=page.evaluate('JSON.stringify({stats,inventory,equippedGear})')
            with journal.open('a') as log:
                for r in pending():
                    if r['key'] in completed:continue
                    record_start=time.monotonic()
                    # Use the same public actions as a player, without reapplying
                    # already selected values (each action rerenders both views).
                    # Every row still gets its own actual page.reload below.
                    page.evaluate('''r=>{
                      if(paperDollState.selectedGender!==r.gender)setGender(r.gender);
                      if(paperDollState.appearance.face!==r.face)equipPaperDollItem("face",r.face);
                      if(paperDollState.appearance.hair!==r.hair)equipPaperDollItem("hair",r.hair);
                      if(paperDollState.appearance.hairColor!==r.color)setHairColor(r.color);
                      if(paperDollState.patientLoadout.upperBody!=="patient-tunic"){
                        setPaperDollView("patient");equipPaperDollItem("upperBody","patient-tunic");}
                      if(paperDollState.combatLoadout.upperBody!==null){
                        setPaperDollView("combat");equipPaperDollItem("upperBody",null);}
                      if(paperDollState.activeViewMode!=="combat")setPaperDollView("combat");
                    }''',r)
                    page.reload(wait_until='load')
                    try:
                        # This installed SDK drops nested nulls in wait_for_function
                        # arguments (evaluate preserves them). JSON text keeps the
                        # native-face null exact; do not loosen the comparison.
                        expected=json.dumps({k:r[k] for k in ['gender','face','hair','color']})
                        page.wait_for_function('value=>{const r=JSON.parse(value);return document.readyState==="complete"&&typeof paperDollState!=="undefined"&&paperDollState.selectedGender===r.gender&&paperDollState.appearance.face===r.face&&paperDollState.appearance.hair===r.hair&&paperDollState.appearance.hairColor===r.color}',arg=expected)
                    except Exception:
                        actual=page.evaluate('({ready:document.readyState,state:typeof paperDollState!=="undefined"?paperDollState:null,saved:localStorage.getItem("palata404_paper_doll")})')
                        (output/f'failure-shard-{shard}.json').write_text(json.dumps({'expected':r,'actual':actual,'page_errors':errors,'http_errors':http},indent=2)+'\n')
                        raise
                    page.wait_for_function('''async()=>{for(const id of ['layer-body','layer-face','layer-hair','layer-hair-rear']){
                      const i=document.getElementById(id);if(!i||i.classList.contains('hidden'))continue;
                      if(!i.complete||!i.naturalWidth)return false;if(i.paperHairRequest){const q=i.paperHairRequest,n=q.lastIndexOf('|');if(i.getAttribute('src')!==await coloredHairSource(q.slice(0,n),q.slice(n+1),i.paperHairColorReference))return false;}}
                      return true;}''')
                    state=page.evaluate('paperDollState');assert state['activeViewMode']=='combat'
                    assert state['patientLoadout']['upperBody']=='patient-tunic' and state['combatLoadout']['upperBody'] is None
                    assert page.evaluate('JSON.stringify({stats,inventory,equippedGear})')==protected
                    assert not errors and not http,(errors,http)
                    log.write(json.dumps({'key':r['key'],'restored':True,'appearance':state['appearance'],'gender':state['selectedGender'],'patient_trip_preserved':True,'seconds':round(time.monotonic()-record_start,4)})+'\n');log.flush();completed.add(r['key'])
                    if len(completed)%50==0:print('Reload shard',shard,len(completed),'/',expected_shard,flush=True)
            assert len(completed)==expected_shard
            done_path.write_text(json.dumps({'shard':shard,'shards':shards,'expected':expected_shard,'passed':len(completed),'page_errors':errors,'http_errors':http,'engine':browser.version},indent=2)+'\n');browser.close()
    finally:server.shutdown();server.server_close();thread.join()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--report',type=Path,default=ROOT/'review/male-heads-full-library');p.add_argument('--shard',type=int,default=0);p.add_argument('--shards',type=int,default=1);p.add_argument('--stream',action='store_true');a=p.parse_args()
    assert 0<=a.shard<a.shards;run(a.report,a.shard,a.shards,a.stream)
