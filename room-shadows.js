/* Project the actual visible approved avatar, including its clothing/animation. */
(function(){
'use strict';
const root=document.querySelector('.hospital-hud'),host=document.getElementById('character-paperdoll');
const cast=root?.querySelector('.room-shadow-cast'),contact=root?.querySelector('.room-shadow-contact');
if(!root||!host||!cast||!contact)return;
const buffer=document.createElement('canvas');buffer.width=320;buffer.height=Math.round(320*1672/941);
const ctx=buffer.getContext('2d',{willReadFrequently:true});
const targets=[cast,contact].map(container=>{const canvas=document.createElement('canvas');canvas.width=buffer.width;canvas.height=buffer.height;canvas.setAttribute('aria-hidden','true');container.append(canvas);return {container,canvas,context:canvas.getContext('2d')};});
let raf=0,dirty=true,last=0,renderKey='',lastFoot=.995;
const reduced=matchMedia('(prefers-reduced-motion: reduce)');
const masks=new Map();
function request(){dirty=true;if(!raf&&!document.hidden&&root.dataset.scenePaused!=='true')raf=requestAnimationFrame(tick);}
function activeCanvas(){return [...host.querySelectorAll('canvas')].find(c=>!c.hidden&&c.width&&c.height&&getComputedStyle(c).display!=='none');}
function polygon(context,text,x,y,w,h){
 if(!text.startsWith('polygon('))return;
 const body=text.slice(text.indexOf('(')+1,-1).replace(/^(?:evenodd|nonzero),\s*/,'');
 const points=body.split(',').map(pair=>pair.trim().split(/\s+/));
 if(points.some(p=>p.length!==2))return;
 context.beginPath();points.forEach((p,i)=>{const px=x+parseFloat(p[0])*(p[0].includes('%')?w/100:1),py=y+parseFloat(p[1])*(p[1].includes('%')?h/100:1);if(i)context.lineTo(px,py);else context.moveTo(px,py);});context.closePath();context.clip();
}
function imageMask(source){
 if(!source)return null;
 if(!masks.has(source)){const im=new Image();im.onload=request;im.src=source;masks.set(source,im);}
 const im=masks.get(source);return im.complete&&im.naturalWidth?im:null;
}
const layerBuffer=document.createElement('canvas');layerBuffer.width=buffer.width;layerBuffer.height=buffer.height;
const layerCtx=layerBuffer.getContext('2d');
function drawLayer(image,frame){
 const style=getComputedStyle(image),rect=image.getBoundingClientRect();
 if(!image.complete||!image.naturalWidth||style.display==='none'||style.visibility==='hidden'||!rect.width||!rect.height||Number(style.opacity)===0)return;
 const sx=buffer.width/frame.width,sy=buffer.height/frame.height;
 const x=(rect.left-frame.left)*sx,y=(rect.top-frame.top)*sy,w=rect.width*sx,h=rect.height*sy;
 layerCtx.clearRect(0,0,buffer.width,buffer.height);layerCtx.save();polygon(layerCtx,style.clipPath,x,y,w,h);layerCtx.globalAlpha=Number(style.opacity);
 let dx=x,dy=y,dw=w,dh=h;
 if(style.objectFit==='contain'){const k=Math.min(w/image.naturalWidth,h/image.naturalHeight);dw=image.naturalWidth*k;dh=image.naturalHeight*k;dx+=(w-dw)/2;dy+=(h-dh)/2;}
 layerCtx.drawImage(image,dx,dy,dw,dh);
 const mask=imageMask(image.paperDollMaskSource);
 if(mask){layerCtx.globalCompositeOperation='destination-in';layerCtx.drawImage(mask,x,y,w,h);}
 layerCtx.restore();ctx.drawImage(layerBuffer,0,0);
}
function draw(frame,live){
 ctx.clearRect(0,0,buffer.width,buffer.height);
 if(live){const r=live.getBoundingClientRect();ctx.drawImage(live,(r.left-frame.left)*buffer.width/frame.width,(r.top-frame.top)*buffer.height/frame.height,r.width*buffer.width/frame.width,r.height*buffer.height/frame.height);}
 else{
  const frozen=host.querySelector('.paper-doll-frozen');
  const images=[...(frozen||host).querySelectorAll(frozen?'.paper-doll-frozen-layer':':scope > .char-layer')];
  images.sort((a,b)=>Number(getComputedStyle(a).zIndex)-Number(getComputedStyle(b).zIndex));images.forEach(im=>drawLayer(im,frame));
 }
 // Retain the heel-to-toe contour. Flattening both feet onto the lowest toe row
 // makes the heels appear suspended, even when the source pose is unchanged.
 let foot=lastFoot,pixels=null;
 try{pixels=ctx.getImageData(0,0,buffer.width,buffer.height);let row=-1;for(let y=buffer.height-1;y>=buffer.height*.85&&row<0;y--)for(let x=0;x<buffer.width;x++)if(pixels.data[(y*buffer.width+x)*4+3]>96){row=y;break;}if(row>=0)foot=(row+1)/buffer.height;}catch(_){/* An origin-protected canvas keeps the registered cast. */}
 lastFoot=foot;
 const [castTarget,contactTarget]=targets;
 castTarget.context.clearRect(0,0,buffer.width,buffer.height);castTarget.context.drawImage(buffer,0,0);
 contactTarget.context.clearRect(0,0,buffer.width,buffer.height);
 if(pixels){
  const support=contactTarget.context.createImageData(buffer.width,buffer.height),floor=Math.min(buffer.height-1,Math.ceil(buffer.height*foot));
  const heelLimit=Math.floor(buffer.height*(foot-.072));let samples=0,minSole=floor;
  for(let x=0;x<buffer.width;x++){
   let sole=-1;for(let y=floor;y>=heelLimit;y--)if(pixels.data[(y*buffer.width+x)*4+3]>96){sole=y;break;}
   if(sole<0)continue;samples++;minSole=Math.min(minSole,sole);
   for(let d=-1;d<=6;d++){
    const y=sole+d;if(y<0||y>=buffer.height)continue;
    const alpha=Math.round(220*Math.exp(-Math.pow((d-1)/2.8,2))),i=(y*buffer.width+x)*4;
    support.data[i+3]=Math.max(support.data[i+3],alpha);
   }
  }
  contactTarget.context.putImageData(support,0,0);
  contact.dataset.soleSamples=String(samples);contact.dataset.soleDepth=String(floor-minSole);
 }
 const viewport=root.querySelector('.hud-main').getBoundingClientRect(),w=frame.width,h=frame.height,ground=h*foot;
 targets.forEach(({container})=>{container.style.left=(frame.left-viewport.left)/viewport.width*100+'%';container.style.top=(frame.top-viewport.top)/viewport.height*100+'%';container.style.width=w/viewport.width*100+'%';container.style.height=h/viewport.height*100+'%';});
 const lightX=viewport.left+viewport.width*.501;
 const shift=Math.max(-w*.45,Math.min(w*.45,(frame.left+w/2-lightX)*1.5));
 const back=-Math.min(h*.115,viewport.height*.068),taper=.64;
 const transform=PalataRoomProjection.rectangleToQuad(w,ground,[[w/2+shift-w*taper/2,ground+back],[w/2+shift+w*taper/2,ground+back],[w,ground],[0,ground]]);
 if(transform)targets[0].canvas.style.transform=transform;
 targets[1].canvas.style.transform='none';
 root.dataset.shadowReady='true';
}
function tick(now){
 raf=0;if(document.hidden||root.dataset.scenePaused==='true')return;
 const live=activeCanvas(),key=host.paperDollVisualKey+'|'+host.paperDollGeneration+'|'+host.hasAttribute('data-paper-loading')+'|'+Boolean(host.paperDollFrozen)+'|'+Boolean(live);
 if(now-last>80&&(dirty||live||key!==renderKey)){
  const frame=host.getBoundingClientRect();if(frame.width&&frame.height){draw(frame,live);dirty=false;renderKey=key;last=now;}
 }
 if((live&&!reduced.matches)||dirty)raf=requestAnimationFrame(tick);
}
new MutationObserver(request).observe(host,{subtree:true,childList:true,attributes:true,attributeFilter:['class','style','src','hidden','data-avatar-core-ready','data-paper-loading']});
new MutationObserver(()=>{if(root.dataset.scenePaused==='true'){cancelAnimationFrame(raf);raf=0;}else request();}).observe(root,{attributes:true,attributeFilter:['data-scene-paused']});
const resize=new ResizeObserver(request);resize.observe(root);resize.observe(host);
host.addEventListener('load',request,true);window.addEventListener('paper-doll-render',request);
document.addEventListener('visibilitychange',()=>{if(document.hidden){cancelAnimationFrame(raf);raf=0;}else request();});
reduced.addEventListener('change',request);
window.addEventListener('pagehide',()=>{cancelAnimationFrame(raf);raf=0;});window.addEventListener('pageshow',request);
window.PalataRoomShadows=Object.freeze({refresh:request});request();
})();
