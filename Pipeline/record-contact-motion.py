"""Record actual engine RAF playback; not a video assembled from contact sheets."""
import sys,base64,json,subprocess,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tests.test_avatar_core import AvatarCoreBrowserTests as B
OUT=ROOT/'review/male-contact-surface-pass';G=OUT/'Gallery';rows=[]
B.setUpClass();b=B();b.setUp();b.full_canvas();p=b.page
try:
 for pose in ['idle','rifle','pistol','melee']:
  p.evaluate('p=>{let e=avatarLab.engine;e.pause();e.time=0;e.setOptions({breathing:true,cycleMs:4000,background:"#f8f5ed",playbackRate:1});e.setPose(p)}',pose)
  result=p.evaluate('''async pose=>{
   const e=avatarLab.engine,stream=e.canvas.captureStream(24),mime=MediaRecorder.isTypeSupported('video/webm;codecs=vp9')?'video/webm;codecs=vp9':'video/webm';
   const recorder=new MediaRecorder(stream,{mimeType:mime,videoBitsPerSecond:2500000}),chunks=[],samples=[];
   recorder.ondataavailable=v=>{if(v.data.size)chunks.push(v.data)};
   const done=new Promise(resolve=>recorder.onstop=resolve),probes={rifle:[[696+10,672+26],[714+10,706+26]],pistol:[[203+10,332+26],[201+10,335+26]],melee:[[218+10,847+26],[239+10,863+26]]}[pose]||[];
   let active=true;const monitor=()=>{if(!active)return;const f=e.frame,m=f.weapon?.matrix;
    samples.push({time:e.time,primaryError:f.primaryError,supportError:f.supportError,pixels:probes.map(([x,y])=>{let X=m[0]*x+m[2]*y+m[4],Y=m[1]*x+m[3]*y+m[5];return [...e.ctx.getImageData(Math.round(X),Math.round(Y),1,1).data]})});requestAnimationFrame(monitor)};
   recorder.start();e.pause(false);requestAnimationFrame(monitor);await new Promise(r=>setTimeout(r,4250));active=false;e.pause();recorder.stop();await done;stream.getTracks().forEach(t=>t.stop());
   const blob=new Blob(chunks,{type:mime}),data=await new Promise(r=>{let reader=new FileReader();reader.onload=()=>r(reader.result.split(',')[1]);reader.readAsDataURL(blob)});
   return {data,mime,samples,cycleMs:4000,recordingKind:'actual runtime RAF canvas.captureStream, not assembled stills'};
  }''',pose)
  data=base64.b64decode(result.pop('data'));path=G/f'{pose}-live-motion.webm';path.write_bytes(data);result['path']=path.name;result['pose']=pose;result['bytes']=len(data);assert len(result['samples'])>=20;assert result['samples'][-1]['time']>=3900
  for sample in result['samples']:
   assert sample['primaryError']<1e-6 and sample['supportError']<1e-6
   for rgba in sample['pixels']:assert max(rgba[:3])<235,(pose,sample['time'],rgba,'background leaked through a solid object probe')
  if shutil.which('ffprobe'):
   result['decode']=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_entries','stream=width,height,nb_read_frames:format=duration','-of','json',str(path)],text=True));assert result['decode']['streams'][0]['width']==941
  rows.append(result)
 (OUT/'live-motion.json').write_text(json.dumps({'recordings':rows,'all_samples_contact_checks_passed':True,'review_limit':'Recorded continuous playback and per-RAF material/contact checks; final human artistic approval is still required.'},indent=2)+'\n')
finally:b.tearDown();B.tearDownClass()
print('Recorded and decoded four actual RAF playback videos; source-material probes stayed covered')
