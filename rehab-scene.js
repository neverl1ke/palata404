/* Approved full-resolution art stays immutable. Local, edge-pinned texture
 * displacement gives the pictured equipment subtle movement without duplicating
 * it over an unchanged copy or repainting the rest of the room. */
(function(){
'use strict';
let current=null;
const ids=['rope','pullup','bench','bag'];
const regions={rope:[12,260,110,590],pullup:[650,130,1028,224],bench:[981,373,1338,713],bag:[1460,155,1615,684]};
const reduced=matchMedia('(prefers-reduced-motion: reduce)');
const vertex='attribute vec2 a;varying vec2 v;void main(){v=(a+1.)*.5;gl_Position=vec4(a,0.,1.);}';
const fragment=`precision highp float;varying vec2 v;uniform sampler2D photo;uniform sampler2D mattes;uniform vec2 size;uniform vec4 motion;uniform float lamp;uniform vec3 windows;uniform float ambient;uniform float clock;uniform float trip;uniform float weather;
float box(vec2 p,vec4 r,float f){return smoothstep(r.x,r.x+f,p.x)*(1.-smoothstep(r.z-f,r.z,p.x))*smoothstep(r.y,r.y+f,p.y)*(1.-smoothstep(r.w-f,r.w,p.y));}
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float ellipse(vec2 p,vec2 center,vec2 radius){return 1.-smoothstep(.8,1.1,length((p-center)/radius));}
float lightArea(vec2 p,vec4 r,float night){return box(p,r+vec4(-6.,-6.,6.,6.)*night,mix(1.,4.,night));}
void main(){vec2 p=vec2(v.x*size.x,(1.-v.y)*size.y);vec2 d=vec2(0.);vec3 mask=texture2D(mattes,v).rgb;
d.x+=motion.x*mask.r*clamp((p.y-260.)/330.,0.,1.);
d.x+=motion.w*mask.g*clamp((p.y-155.)/529.,0.,1.);
vec2 uv=vec2((p.x-d.x)/size.x,1.-(p.y-d.y)/size.y);vec4 c=texture2D(photo,uv);vec3 painted=c.rgb;
float bulb=box(p,vec4(760.,0.,904.,136.),20.);float spill=exp(-dot((p-vec2(835.,260.))/vec2(400.,420.),(p-vec2(835.,260.))/vec2(400.,420.)));
c.rgb*=1.+lamp*(.35+.65*bulb+.2*spill);
float glass=mask.b*ambient;
c.rgb=mix(c.rgb,c.rgb*vec3(.67,.72,.80),glass*weather*.6);c.rgb=mix(c.rgb,vec3(.43,.48,.52),glass*weather*.08);
vec2 rainCell=vec2((p.x+p.y*.13)/11.,p.y/70.+clock*2.2),rainId=floor(rainCell);float seed=hash(rainId);float rain=(1.-smoothstep(.02,.065,abs(fract(rainCell.x)-.5)))*(1.-smoothstep(.12,.3,fract(rainCell.y+seed)))*step(.3,seed)*smoothstep(.55,.85,weather);
c.rgb+=vec3(.17,.21,.25)*rain*glass*.3;
vec4 a=mix(vec4(223.,323.,234.,341.),vec4(226.,316.,233.,328.),trip),b=mix(vec4(254.,323.,266.,341.),vec4(263.,398.,271.,411.),trip),e=mix(vec4(254.,366.,266.,385.),vec4(315.,288.,323.,299.),trip);
float wa=lightArea(p,a,trip)*glass,wb=lightArea(p,b,trip)*glass,we=lightArea(p,e,trip)*glass;
float lit=wa*windows.x+wb*windows.y+we*windows.z,off=wa*(1.-windows.x)+wb*(1.-windows.y)+we*(1.-windows.z);
// Daylight already illuminates an unlit window. Never paint a dark rectangle
// over its glass, mullions or facade. Only the blue glazing picks up warm light.
float glazing=smoothstep(.012,.055,min(painted.b-painted.r,painted.g-painted.r));
// Trip windows contain painted-in lamplight. Fade that warm emission alone,
// keeping the original frame, reflections and surrounding building untouched.
float emission=smoothstep(.10,.30,painted.r-painted.b)*smoothstep(.24,.40,max(painted.r,max(painted.g,painted.b)));
float luminance=dot(c.rgb,vec3(.2126,.7152,.0722));
vec3 unlit=mix(c.rgb,vec3(luminance)*vec3(.20,.25,.29),emission);
c.rgb=mix(c.rgb,unlit,off*trip);
c.rgb+=vec3(.095,.060,.018)*lit*glazing*(1.-trip);
float pass=mod(clock,32.);float walking=smoothstep(10.,11.,pass)*(1.-smoothstep(18.,19.,pass));vec4 cell=mix(e,b,trip);float q=clamp((pass-10.)/9.,0.,1.);vec2 person=vec2(mix(cell.x+2.,cell.z-2.,q),cell.y+(cell.w-cell.y)*.42);
float silhouette=max(ellipse(p,person,vec2(1.,1.4)),ellipse(p,person+vec2(0.,3.),vec2(1.25,2.6)))*walking*glass*box(p,cell,1.)*mix(glazing,emission,trip);c.rgb*=1.-silhouette*mix(.18,.55,trip);
c.rgb+=vec3(.8,.58,.3)*bulb*ambient*(.008+.004*sin(clock*.9))*(1.+lamp);
gl_FragColor=c;}`;
function shader(gl,type,source){const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS)){const message=gl.getShaderInfoLog(s);gl.deleteShader(s);throw Error('Scene shader: '+message);}return s;}
function mount(host,mode,onSelect){
 current?.dispose();
 const image=host.querySelector('.scene-painting');if(!image)return;
 const canvas=document.createElement('canvas');canvas.className='rehab-live-canvas';canvas.setAttribute('aria-hidden','true');canvas.hidden=true;host.append(canvas);
 const targets=[];let hover=-1,training=-1,disposed=false,raf=null,gl=null,program=null,texture=null,maskTexture=null,buffer=null,shaders=[],lastDraw=0;
 const strength=[0,0,0,0],values=[0,0,0,0];let frames=0;
 const visible=()=>host.isConnected&&!document.hidden&&!host.closest('.hidden')&&!document.querySelector('.rehab-boxing[open],.rehab-pullups[open],.rehab-exercise[open]');
 function layout(){if(!image.naturalWidth)return;const w=host.clientWidth,h=host.clientHeight,s=Math.min(w/image.naturalWidth,h/image.naturalHeight),dx=(w-image.naturalWidth*s)/2,dy=(h-image.naturalHeight*s)/2;ids.forEach((id,i)=>{const [l,t,r,b]=regions[id],button=targets[i];Object.assign(button.style,{left:(l*s+dx)+'px',top:(t*s+dy)+'px',width:((r-l)*s)+'px',height:((b-t)*s)+'px'});});}
 function select(i){if(ids[i]==='bag')window.PalataBoxing.open(mode);else if(ids[i]==='pullup')window.PalataPullups.open(mode);else window.PalataExercises.open(ids[i],mode);}
 ids.forEach((id,i)=>{const b=document.createElement('button');b.type='button';b.className='rehab-equipment';b.dataset.rehabEquipment=id;const name=id==='bag'&&mode==='trip'?'Манекен':PalataRehabRules.equipment[id].name;b.setAttribute('aria-label',name+' — тренування');b.title=name;const label=document.createElement('span');label.textContent=name;b.append(label);b.addEventListener('pointerenter',()=>{hover=i;start();});b.addEventListener('pointerleave',()=>{if(hover===i)hover=-1;});b.addEventListener('focus',()=>{hover=i;start();});b.addEventListener('blur',()=>{if(hover===i)hover=-1;});b.onclick=()=>select(i);targets.push(b);host.append(b);});
 function draw(time,neutral=false){
  if(!gl||!program||disposed)return;
  const animate=!neutral&&!reduced.matches;
  for(let i=0;i<4;i++){strength[i]+=((animate&&(i===0||i===3)&&(i===hover||i===training)?1:0)-strength[i])*.2;values[i]=animate?Math.sin(time/([340,230,270,610][i]))*[1.7,.65,.6,2.2][i]*strength[i]:0;}
  const phase=time%14000;const dip=!animate?0:phase>7600&&phase<8350?Math.sin((phase-7600)/750*Math.PI):phase>8550&&phase<9200?.65*Math.sin((phase-8550)/650*Math.PI):0;
  const lamp=animate?-dip*(mode==='trip'?.38:.16):0;
  const ws=animate?[0,1,2].map(i=>Math.max(0,Math.min(1,(Math.sin(time/(3500+i*750)+i*1.9)+.15)/.3))):[0,0,0],weather=animate?.5-.5*Math.cos(time/48000*Math.PI*2):0;
  if(animate){const pass=time%32000,walking=Math.max(0,Math.min(1,(pass-10000)/1000,(19000-pass)/1000)),index=mode==='trip'?1:2;ws[index]=Math.max(ws[index],walking);}
  gl.uniform4fv(gl.getUniformLocation(program,'motion'),values);gl.uniform1f(gl.getUniformLocation(program,'lamp'),lamp);gl.uniform3fv(gl.getUniformLocation(program,'windows'),ws);gl.uniform1f(gl.getUniformLocation(program,'ambient'),animate?1:0);gl.uniform1f(gl.getUniformLocation(program,'clock'),time/1000);gl.uniform1f(gl.getUniformLocation(program,'trip'),mode==='trip'?1:0);gl.uniform1f(gl.getUniformLocation(program,'weather'),weather);gl.drawArrays(gl.TRIANGLE_STRIP,0,4);frames++;host.dataset.rehabFrames=String(frames);host.dataset.rehabMotion=values.map(n=>n.toFixed(3)).join(',');host.dataset.rehabLamp=String(lamp);host.dataset.rehabWindows=ws.join(',');host.dataset.rehabWeather=weather<.25?'clear':weather<.65?'overcast':'rain';host.dataset.rehabSilhouette=animate&&time%32000>10000&&time%32000<19000?'passing':'none';
 }
 function tick(t){raf=null;if(disposed)return;if(!host.isConnected){dispose();return;}if(!visible())return;if(t-lastDraw>1000/24){lastDraw=t;draw(t);}if(!reduced.matches)raf=requestAnimationFrame(tick);}
 function start(){if(!disposed&&gl&&program&&visible()&&raf===null&&!reduced.matches)raf=requestAnimationFrame(tick);}
 function visibility(){if(!visible()||reduced.matches){cancelAnimationFrame(raf);raf=null;if(reduced.matches)draw(0,true);}else start();}
 const observer=new ResizeObserver(layout);observer.observe(host);
 const screen=host.closest('#quest-location-screen');const blocker=new MutationObserver(visibility);if(screen)blocker.observe(screen,{attributes:true,attributeFilter:['class']});
 document.addEventListener('visibilitychange',visibility);reduced.addEventListener('change',visibility);
 function dispose(){if(disposed)return;disposed=true;cancelAnimationFrame(raf);observer.disconnect();blocker.disconnect();document.removeEventListener('visibilitychange',visibility);reduced.removeEventListener('change',visibility);if(gl){if(texture)gl.deleteTexture(texture);if(maskTexture)gl.deleteTexture(maskTexture);if(buffer)gl.deleteBuffer(buffer);if(program)gl.deleteProgram(program);shaders.forEach(s=>gl.deleteShader(s));gl.getExtension('WEBGL_lose_context')?.loseContext();}if(current?.host===host)current=null;}
 canvas.addEventListener('webglcontextlost',event=>{event.preventDefault();if(disposed)return;cancelAnimationFrame(raf);raf=null;canvas.hidden=true;image.style.visibility='';host.dataset.rehabRenderer='static';program=null;gl=null;});
 const state={host,dispose,resume:visibility,sample:time=>draw(time),setTraining(id){training=ids.indexOf(id);start();},drawNeutral:()=>draw(0,true)};current=state;
 image.decode().then(()=>{
  if(disposed||!host.isConnected)return;
  canvas.width=image.naturalWidth;canvas.height=image.naturalHeight;layout();
  try{
   gl=canvas.getContext('webgl',{alpha:false,antialias:false,preserveDrawingBuffer:true});if(!gl)throw Error('WebGL unavailable');
   shaders=[shader(gl,gl.VERTEX_SHADER,vertex),shader(gl,gl.FRAGMENT_SHADER,fragment)];program=gl.createProgram();shaders.forEach(s=>gl.attachShader(program,s));gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error('Scene program unavailable');gl.useProgram(program);
   buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);const a=gl.getAttribLocation(program,'a');gl.enableVertexAttribArray(a);gl.vertexAttribPointer(a,2,gl.FLOAT,false,0,0);
   texture=gl.createTexture();gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,texture);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,true);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,image);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);gl.uniform1i(gl.getUniformLocation(program,'photo'),0);
   maskTexture=gl.createTexture();gl.activeTexture(gl.TEXTURE1);gl.bindTexture(gl.TEXTURE_2D,maskTexture);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,PalataRehabSceneMasks.create(image,mode));gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);gl.uniform1i(gl.getUniformLocation(program,'mattes'),1);
   gl.uniform2f(gl.getUniformLocation(program,'size'),canvas.width,canvas.height);gl.viewport(0,0,canvas.width,canvas.height);draw(0,true);canvas.hidden=false;image.style.visibility='hidden';host.dataset.rehabRenderer='webgl';start();
  }catch(error){canvas.hidden=true;image.style.visibility='';host.dataset.rehabRenderer='static';host.dataset.rehabFallback=error.message;gl=null;}
 }).catch(()=>{host.dataset.rehabRenderer='asset-error';});
}
window.PalataRehabScene=Object.freeze({mount,resume:()=>current?.resume(),dispose:()=>current?.dispose(),setTraining:id=>current?.setTraining(id),drawNeutral:()=>current?.drawNeutral(),sample:time=>current?.sample(time)});
})();
