#!/usr/bin/env python3
"""Reproduce exact original distal-hand foreground alpha for the pajama rifle tops.

--check (default) compares regenerated decoded pixels with reviewed PNG/WebP files.
--write explicitly updates the two source masks and lossless runtime masks.
No avatar, garment, or weapon RGB pixels are edited by this tool.
"""
from __future__ import annotations
import argparse,base64,functools,hashlib,http.server,json,shutil,tempfile,threading
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage
from playwright.sync_api import sync_playwright
W,H=941,1672
ROOT=Path(__file__).resolve().parents[1]
ROIS={
'malePrimary':[[379,546],[433,546],[470,563],[510,585],[526,608],[518,636],[489,655],[443,663],[412,648],[376,616]],
'maleSupportThumb':[[735,628],[746,629],[760,637],[771,648],[778,656],[776,662],[768,660],[763,653],[753,645],[740,640],[733,636]],
'maleSupportPalm':[[686,675],[691,670],[696,660],[702,657],[709,653],[716,654],[719,660],[722,650],[728,647],[734,650],[738,660],[742,666],[747,664],[753,666],[758,675],[765,689],[770,704],[767,714],[759,722],[750,726],[742,724],[736,725],[728,727],[722,724],[718,720],[711,723],[704,720],[696,716],[690,708],[687,699]],
'femalePrimary':[[361,510],[448,510],[487,533],[537,559],[539,588],[506,612],[435,626],[390,596],[362,574]],
'femaleSupport':[[678,622],[706,602],[743,583],[775,594],[789,626],[791,682],[755,701],[706,701],[680,679],[670,650]],
}
KNOWN={'male':{'source':'919dd073ca5028c165f2237194c39ec84ecffc0c735cccb0e7a1d5bfa22b5023','runtime':'ce0e3b27047ad369f767d9d15a751a846c7431fbe56452d32ea14f5c9dc998c0','rgba':'a1c350122c615d98b687736a58ad62b8f7cf7e4c6c2511b3c6a45d2befbdbbf1'},'female':{'source':'5c352a5734f9dd30971887d27157d63d16248ff71c71389c2be021a823575df4','runtime':'803bb04b11cd965ff5c57be652b2cabf0b482433b35d9f72081856b6ea6a90ad','rgba':'0344fed5d36442fbfb80d7d95b0a6b1beb36fe6805e6c5b0c7ad626e6291f3f0'}}

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def rgba(path):return Image.open(path).convert('RGBA').crop((0,0,W,H))
def approved(source):return ROOT/'avatar-core/approved'/source.removeprefix('./')
def polygon(name):
 im=Image.new('L',(W*4,H*4));ImageDraw.Draw(im).polygon([(x*4,y*4)for x,y in ROIS[name]],fill=255)
 return np.array(im.resize((W,H),Image.Resampling.LANCZOS))

def male_support_png(output):
 class Quiet(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
 handler=functools.partial(Quiet,directory=str(ROOT))
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler)
 thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 try:
  with sync_playwright() as p:
   exe=shutil.which('chromium') or shutil.which('chromium-browser')
   browser=p.chromium.launch(headless=True,**({'executable_path':exe}if exe else {}),args=['--no-sandbox'])
   page=browser.new_page();page.goto(f'http://127.0.0.1:{server.server_port}/__hand_mask_blank__',wait_until='domcontentloaded')
   result=page.evaluate("""async()=>{
    const {trial}=await(await import('/avatar-core/approved/config.mjs')).config('male');
    const W=941,H=1672,mesh=trial.meshes.left,nv=trial.supportRetarget.positions['1.07'];
    const im=new Image();im.src=trial.stageImages.After.left;await im.decode();
    const canvas=document.createElement('canvas');canvas.width=W;canvas.height=H;
    const g=canvas.getContext('webgl',{alpha:true,premultipliedAlpha:true,antialias:false,preserveDrawingBuffer:true});if(!g)throw Error('WebGL required');
    const shader=(type,s)=>{const q=g.createShader(type);g.shaderSource(q,s);g.compileShader(q);if(!g.getShaderParameter(q,g.COMPILE_STATUS))throw Error(g.getShaderInfoLog(q));return q};
    const program=g.createProgram();g.attachShader(program,shader(g.VERTEX_SHADER,'attribute vec2 p;attribute vec2 uv;varying vec2 v;void main(){v=uv;gl_Position=vec4(p.x/941.0*2.0-1.0,1.0-p.y/1672.0*2.0,0,1);}'));g.attachShader(program,shader(g.FRAGMENT_SHADER,'precision highp float;uniform sampler2D tex;varying vec2 v;void main(){gl_FragColor=texture2D(tex,v);}'));g.linkProgram(program);if(!g.getProgramParameter(program,g.LINK_STATUS))throw Error(g.getProgramInfoLog(program));g.useProgram(program);
    const tex=g.createTexture();g.bindTexture(g.TEXTURE_2D,tex);g.pixelStorei(g.UNPACK_PREMULTIPLY_ALPHA_WEBGL,true);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_MIN_FILTER,g.LINEAR);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_MAG_FILTER,g.LINEAR);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_WRAP_S,g.CLAMP_TO_EDGE);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_WRAP_T,g.CLAMP_TO_EDGE);g.texImage2D(g.TEXTURE_2D,0,g.RGBA,g.RGBA,g.UNSIGNED_BYTE,im);
    const v=[];for(const tri of mesh.triangles)for(const i of tri)v.push(nv[i][0],nv[i][1],mesh.afterVertices[i][0]/W,mesh.afterVertices[i][1]/H);
    const buffer=g.createBuffer();g.bindBuffer(g.ARRAY_BUFFER,buffer);g.bufferData(g.ARRAY_BUFFER,new Float32Array(v),g.DYNAMIC_DRAW);
    const pos=g.getAttribLocation(program,'p'),uv=g.getAttribLocation(program,'uv');g.enableVertexAttribArray(pos);g.vertexAttribPointer(pos,2,g.FLOAT,false,16,0);g.enableVertexAttribArray(uv);g.vertexAttribPointer(uv,2,g.FLOAT,false,16,8);
    g.viewport(0,0,W,H);g.disable(g.BLEND);g.clearColor(0,0,0,0);g.clear(g.COLOR_BUFFER_BIT);g.drawArrays(g.TRIANGLES,0,v.length/4);
    const png=canvas.toDataURL();g.getExtension('WEBGL_lose_context')?.loseContext();return png;
   }""")
   Path(output).write_bytes(base64.b64decode(result.split(',',1)[1]));browser.close()
 finally:server.shutdown();server.server_close();thread.join()

def female_support():
 im=rgba(ROOT/'avatar-core/approved/female/Hands/left-foreground.png')
 angle=np.deg2rad(2.5);c,s=np.cos(angle),np.sin(angle)
 rot=np.array([[c,-s],[s,c]],dtype=float)
 offset=np.array([742.1903106342786,649.0776064477784])-rot@np.array([783,651])
 inverse=rot.T;translation=-inverse@offset
 coeff=(inverse[0,0],inverse[0,1],translation[0],inverse[1,0],inverse[1,1],translation[1])
 return im.transform((W,H),Image.Transform.AFFINE,coeff,resample=Image.Resampling.BILINEAR)

def hand_alpha(source,native,roi):
 src=np.array(source);dst=np.array(native)
 alpha=src[:,:,3].copy();alpha[alpha>=235]=255
 match=(np.max(np.abs(src[:,:,:3].astype(np.int16)-dst[:,:,:3].astype(np.int16)),axis=2)<=6)&(dst[:,:,3]>128)
 out=(alpha.astype(float)*(roi.astype(float)/255)*match).astype(np.uint8)
 labels,count=ndimage.label(out>3,structure=np.ones((3,3),dtype=np.uint8));sizes=np.bincount(labels.ravel())
 for i in range(1,count+1):
  if sizes[i]<14:out[labels==i]=0
 return out

def build(references,temp,qa=None):
 trial=json.loads((ROOT/'avatar-core/approved/male/trial.json').read_text())
 support=Path(temp)/'male-support-original-isolated.png';male_support_png(support)
 sources={'male':[rgba(approved(trial['stageImages']['After']['right'])),rgba(support)],'female':[rgba(ROOT/'avatar-core/approved/female/Hands/right-foreground.png'),female_support()]}
 selections={'male':[polygon('malePrimary'),np.maximum(polygon('maleSupportThumb'),polygon('maleSupportPalm'))],'female':[polygon('femalePrimary'),polygon('femaleSupport')]}
 result={};stats={}
 for gender in ['male','female']:
  native=rgba(Path(references)/f'{gender}-rifle.png')
  parts=[hand_alpha(src,native,roi)for src,roi in zip(sources[gender],selections[gender])]
  alpha=np.maximum(*parts);pixels=np.full((H,W,4),255,dtype=np.uint8);pixels[:,:,3]=alpha
  mask=Image.fromarray(pixels,'RGBA');result[gender]=mask
  stats[gender]={'bounds':mask.getchannel('A').getbbox(),'nonzeroPixels':int(np.count_nonzero(alpha)),'rgbaSha256':hashlib.sha256(mask.tobytes()).hexdigest(),'matchesPreviousRgba':hashlib.sha256(mask.tobytes()).hexdigest()==KNOWN[gender]['rgba']}
  if qa:
   qa=Path(qa);qa.mkdir(parents=True,exist_ok=True)
   background=Image.new('RGBA',(W,H),(112,119,124,255));original=native.copy();original.putalpha(mask.getchannel('A'));background.alpha_composite(original);background.save(qa/f'{gender}-hand-restore-check.png')
   overlay=native.copy();red=Image.new('RGBA',(W,H),(255,0,0,0));red.putalpha(mask.getchannel('A').point(lambda x:round(x*.5)));overlay.alpha_composite(red);overlay.save(qa/f'{gender}-selection-overlay.png')
   for i,source in enumerate(sources[gender]):source.save(qa/f'{gender}-source-{i}.png')
 return result,stats

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 mode=parser.add_mutually_exclusive_group();mode.add_argument('--check',action='store_true');mode.add_argument('--write',action='store_true')
 parser.add_argument('--references',type=Path,default=ROOT/'review/pajamas-implementation-20261111/references')
 parser.add_argument('--qa-dir',type=Path)
 args=parser.parse_args()
 with tempfile.TemporaryDirectory(prefix='pajamas-hands-') as temp:images,stats=build(args.references,temp,args.qa_dir)
 source_dir=ROOT/'review/pajamas-implementation-20261111/hand-masks'
 for gender,im in images.items():
  source=source_dir/f'{gender}-rifle.png';runtime=ROOT/f'assets/wardrobe/clothing/patient/pajamas/{gender}/foreground-hands-rifle.webp'
  if args.write:
   source.parent.mkdir(parents=True,exist_ok=True);runtime.parent.mkdir(parents=True,exist_ok=True)
   im.save(source);im.save(runtime,format='WEBP',lossless=True,method=6,exact=True)
  else:
   for path in [source,runtime]:
    assert path.exists(),f'Missing reviewed mask: {path}'
    assert np.array_equal(np.array(im),np.array(Image.open(path).convert('RGBA'))),f'Mask pixels differ: {path}'
  stats[gender].update({'source':str(source.relative_to(ROOT)),'sourceSha256':sha(source),'runtime':str(runtime.relative_to(ROOT)),'runtimeSha256':sha(runtime),'matchesPreviousSource':sha(source)==KNOWN[gender]['source'],'matchesPreviousRuntime':sha(runtime)==KNOWN[gender]['runtime']})
 manifest={'method':'Original native distal-hand alpha only; exact reviewed4x ROIs, nativeRGBmatch<=6, isolated-source alpha, originalmale ARAP1.07 support, rigidfemale2.5deg support. No body/cloth/weaponRGB modifications.','reproducer':'tools/pajamas-hand-masks.py','registration':{'width':W,'height':H,'origin':[0,0]},'previousKnownHashes':KNOWN,'masks':stats}
 if args.write:(source_dir/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps(manifest,indent=2))

if __name__=='__main__':main()
