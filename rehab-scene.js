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
const fragment=`precision highp float;varying vec2 v;uniform sampler2D photo;uniform vec2 size;uniform vec4 motion;uniform float lamp;uniform vec3 windows;
float box(vec2 p,vec4 r,float f){return smoothstep(r.x,r.x+f,p.x)*(1.-smoothstep(r.z-f,r.z,p.x))*smoothstep(r.y,r.y+f,p.y)*(1.-smoothstep(r.w-f,r.w,p.y));}
void main(){vec2 p=vec2(v.x*size.x,(1.-v.y)*size.y);vec2 d=vec2(0.);
float rope=box(p,vec4(12.,260.,110.,590.),12.);d.x+=motion.x*rope*clamp((p.y-260.)/330.,0.,1.);
float bar=box(p,vec4(650.,130.,1028.,224.),12.);d.y+=motion.y*bar;
float bench=box(p,vec4(981.,373.,1338.,713.),18.);d.y+=motion.z*bench*clamp((713.-p.y)/340.,0.,1.);
float dummy=box(p,vec4(1460.,155.,1615.,684.),14.);d.x+=motion.w*dummy*clamp((p.y-155.)/529.,0.,1.);
vec2 uv=vec2((p.x-d.x)/size.x,1.-(p.y-d.y)/size.y);vec4 c=texture2D(photo,uv);
float bulb=box(p,vec4(760.,0.,904.,136.),20.);float spill=exp(-dot((p-vec2(835.,260.))/vec2(400.,420.),(p-vec2(835.,260.))/vec2(400.,420.)));
c.rgb*=1.+lamp*(bulb+.22*spill);
float w1=box(p,vec4(259.,298.,271.,315.),2.);float w2=box(p,vec4(262.,389.,274.,410.),2.);float w3=box(p,vec4(318.,392.,330.,414.),2.);
c.rgb+=vec3(1.,.59,.19)*(windows.x*w1+windows.y*w2+windows.z*w3);gl_FragColor=c;}`;
function shader(gl,type,source){const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS)){const message=gl.getShaderInfoLog(s);gl.deleteShader(s);throw Error('Scene shader: '+message);}return s;}
function mount(host,mode,onSelect){
 current?.dispose();
 const image=host.querySelector('.scene-painting');if(!image)return;
 const canvas=document.createElement('canvas');canvas.className='rehab-live-canvas';canvas.setAttribute('aria-hidden','true');canvas.hidden=true;host.append(canvas);
 const targets=[];let hover=-1,training=-1,disposed=false,raf=null,gl=null,program=null,texture=null,buffer=null,shaders=[],lastDraw=0;
 const strength=[0,0,0,0],values=[0,0,0,0];let frames=0;
 const visible=()=>host.isConnected&&!document.hidden&&!host.closest('.hidden');
 function layout(){if(!image.naturalWidth)return;const w=host.clientWidth,h=host.clientHeight,s=Math.min(w/image.naturalWidth,h/image.naturalHeight),dx=(w-image.naturalWidth*s)/2,dy=(h-image.naturalHeight*s)/2;ids.forEach((id,i)=>{const [l,t,r,b]=regions[id],button=targets[i];Object.assign(button.style,{left:(l*s+dx)+'px',top:(t*s+dy)+'px',width:((r-l)*s)+'px',height:((b-t)*s)+'px'});});}
 function select(i){onSelect(ids[i]);}
 ids.forEach((id,i)=>{const b=document.createElement('button');b.type='button';b.className='rehab-equipment';b.dataset.rehabEquipment=id;const name=id==='bag'&&mode==='trip'?'Манекен':PalataRehabRules.equipment[id].name;b.setAttribute('aria-label',name+' — тренування');b.title=name;const label=document.createElement('span');label.textContent=name;b.append(label);b.addEventListener('pointerenter',()=>{hover=i;start();});b.addEventListener('pointerleave',()=>{if(hover===i)hover=-1;});b.addEventListener('focus',()=>{hover=i;start();});b.addEventListener('blur',()=>{if(hover===i)hover=-1;});b.onclick=()=>select(i);targets.push(b);host.append(b);});
 function draw(time,neutral=false){
  if(!gl||!program||disposed)return;
  const animate=!neutral&&!reduced.matches;
  for(let i=0;i<4;i++){strength[i]+=((animate&&(i===hover||i===training)?1:0)-strength[i])*.2;values[i]=animate?Math.sin(time/([340,230,270,610][i]))*[1.7,.65,.6,2.2][i]*strength[i]:0;}
  const phase=time%19000;const dip=animate&&phase>7800&&phase<8200?Math.sin((phase-7800)/400*Math.PI):0;
  const lamp=animate?-dip*(mode==='trip'?.15:.055):0;
  const ws=animate?[0,1,2].map(i=>.13*Math.max(0,Math.sin(time/(2800+i*650)+i*2))):[0,0,0];
  gl.uniform4fv(gl.getUniformLocation(program,'motion'),values);gl.uniform1f(gl.getUniformLocation(program,'lamp'),lamp);gl.uniform3fv(gl.getUniformLocation(program,'windows'),ws);gl.drawArrays(gl.TRIANGLE_STRIP,0,4);frames++;host.dataset.rehabFrames=String(frames);host.dataset.rehabMotion=values.map(n=>n.toFixed(3)).join(',');host.dataset.rehabLamp=String(lamp);host.dataset.rehabWindows=ws.join(',');
 }
 function tick(t){raf=null;if(disposed)return;if(!host.isConnected){dispose();return;}if(!visible())return;if(t-lastDraw>1000/24){lastDraw=t;draw(t);}if(!reduced.matches)raf=requestAnimationFrame(tick);}
 function start(){if(!disposed&&gl&&program&&visible()&&raf===null&&!reduced.matches)raf=requestAnimationFrame(tick);}
 function visibility(){if(!visible()||reduced.matches){cancelAnimationFrame(raf);raf=null;if(reduced.matches)draw(0,true);}else start();}
 const observer=new ResizeObserver(layout);observer.observe(host);
 const screen=host.closest('#quest-location-screen');const blocker=new MutationObserver(visibility);if(screen)blocker.observe(screen,{attributes:true,attributeFilter:['class']});
 document.addEventListener('visibilitychange',visibility);reduced.addEventListener('change',visibility);
 function dispose(){if(disposed)return;disposed=true;cancelAnimationFrame(raf);observer.disconnect();blocker.disconnect();document.removeEventListener('visibilitychange',visibility);reduced.removeEventListener('change',visibility);if(gl){if(texture)gl.deleteTexture(texture);if(buffer)gl.deleteBuffer(buffer);if(program)gl.deleteProgram(program);shaders.forEach(s=>gl.deleteShader(s));gl.getExtension('WEBGL_lose_context')?.loseContext();}if(current?.host===host)current=null;}
 canvas.addEventListener('webglcontextlost',event=>{event.preventDefault();if(disposed)return;cancelAnimationFrame(raf);raf=null;canvas.hidden=true;image.style.visibility='';host.dataset.rehabRenderer='static';program=null;gl=null;});
 const state={host,dispose,sample:time=>draw(time),setTraining(id){training=ids.indexOf(id);start();},drawNeutral:()=>draw(0,true)};current=state;
 image.decode().then(()=>{
  if(disposed||!host.isConnected)return;
  canvas.width=image.naturalWidth;canvas.height=image.naturalHeight;layout();
  try{
   gl=canvas.getContext('webgl',{alpha:false,antialias:false,preserveDrawingBuffer:true});if(!gl)throw Error('WebGL unavailable');
   shaders=[shader(gl,gl.VERTEX_SHADER,vertex),shader(gl,gl.FRAGMENT_SHADER,fragment)];program=gl.createProgram();shaders.forEach(s=>gl.attachShader(program,s));gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error('Scene program unavailable');gl.useProgram(program);
   buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);const a=gl.getAttribLocation(program,'a');gl.enableVertexAttribArray(a);gl.vertexAttribPointer(a,2,gl.FLOAT,false,0,0);
   texture=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,texture);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,true);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,image);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);gl.uniform2f(gl.getUniformLocation(program,'size'),canvas.width,canvas.height);gl.viewport(0,0,canvas.width,canvas.height);draw(0,true);canvas.hidden=false;image.style.visibility='hidden';host.dataset.rehabRenderer='webgl';start();
  }catch(error){canvas.hidden=true;image.style.visibility='';host.dataset.rehabRenderer='static';host.dataset.rehabFallback=error.message;gl=null;}
 }).catch(()=>{host.dataset.rehabRenderer='asset-error';});
}
window.PalataRehabScene=Object.freeze({mount,dispose:()=>current?.dispose(),setTraining:id=>current?.setTraining(id),drawNeutral:()=>current?.drawNeutral(),sample:time=>current?.sample(time)});
})();
