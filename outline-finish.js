/* Approved thin edge treatment, cached once per source before fitting,
 * recolouring and animation. Original artwork and interior detail are intact. */
(function(){
 'use strict';
 const cache=new Map(),images=new Map(),CACHE_LIMIT=32;
 function remember(map,key,value){map.delete(key);map.set(key,value);while(map.size>CACHE_LIMIT)map.delete(map.keys().next().value);return value;}
 function recalled(map,key){const value=map.get(key);if(value)remember(map,key,value);return value;}
 function eligible(source){
  if(!source||/^(blob:|data:)/.test(source))return false;
  const url=new URL(source,document.baseURI),i=url.pathname.indexOf('/assets/');
  return i>=0&&window.PalataOutlineManifest?.[decodeURIComponent(url.pathname.slice(i+1))]===true;
 }
 // Three separable, fractional box passes approximate the approved 1.1-pixel
 // Gaussian alpha kernel. RGB is never spatially blurred.
 function smooth(input,w,h){
  let a=input.slice(),b=new Uint8Array(a.length);const side=.2016666666666667,center=1-2*side;
  for(const vertical of [false,true])for(let pass=0;pass<3;pass++){
   for(let y=0;y<h;y++)for(let x=0;x<w;x++){
    const i=y*w+x,lo=vertical?(Math.max(0,y-1)*w+x):(y*w+Math.max(0,x-1)),hi=vertical?(Math.min(h-1,y+1)*w+x):(y*w+Math.min(w-1,x+1));
    b[i]=Math.round(a[lo]*side+a[i]*center+a[hi]*side);
   }
   const temp=a;a=b;b=temp;
  }
  return a;
 }
 function process(frame){
  const {width:w,height:h,data}=frame,a=new Uint8Array(w*h),eroded=new Uint8Array(w*h);
  for(let i=0;i<a.length;i++)a[i]=data[i*4+3];
  for(let y=0;y<h;y++)for(let x=0;x<w;x++){
   let minimum=255;for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++)minimum=Math.min(minimum,a[Math.max(0,Math.min(h-1,y+dy))*w+Math.max(0,Math.min(w-1,x+dx))]);
   eroded[y*w+x]=minimum;
  }
  const sm=smooth(a,w,h),er=smooth(eroded,w,h);
  for(let i=0;i<a.length;i++){
   const old=a[i]/255,alpha=old<.15?old:Math.max(0,Math.min(1,(sm[i]/255-.15)/.70)),band=Math.max(0,Math.min(1,(alpha-er[i]/255)/Math.max(alpha,.001)));
   data[i*4+3]=Math.round(alpha*255);
   for(let c=0;c<3;c++)data[i*4+c]=Math.round(data[i*4+c]*(1-band*.65));
  }
  return frame;
 }
 async function source(original){
  if(!eligible(original))return original;
  const key=new URL(original,document.baseURI).href,cached=recalled(cache,key);
  if(cached)return cached;
  let task;
  task=(async()=>{
   const image=new Image();image.src=key;await image.decode();
   const canvas=document.createElement('canvas');canvas.width=image.naturalWidth;canvas.height=image.naturalHeight;
   const ctx=canvas.getContext('2d');ctx.drawImage(image,0,0);
   ctx.putImageData(process(ctx.getImageData(0,0,canvas.width,canvas.height)),0,0);
   const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/png'));if(!blob)throw Error('Edge encoding failed');
   // Data URLs can outlive an LRU entry safely. Revoking blob URLs while a DOM
   // layer, native image cache or fitting task still uses one can break it.
   return await new Promise((resolve,reject)=>{
    const reader=new FileReader();
    reader.onload=()=>typeof reader.result==='string'?resolve(reader.result):reject(new Error('Edge encoding failed'));
    reader.onerror=()=>reject(new Error('Edge encoding failed'));
    reader.readAsDataURL(blob);
   });
  })().catch(error=>{
   if(cache.get(key)===task)cache.delete(key);
   console.warn('Thin outline:',original,error.message);return original;
  });
  return remember(cache,key,task);
 }
 async function bitmap(image,original){
  const processed=await source(original);if(processed===original)return image;
  const cached=recalled(images,processed);if(cached)return cached;
  let task;
  task=(async()=>{const next=new Image();next.src=processed;await next.decode();return next;})().catch(error=>{
   if(images.get(processed)===task)images.delete(processed);
   console.warn('Thin outline decode:',original,error.message);return image;
  });
  return remember(images,processed,task);
 }
 window.PalataOutline=Object.freeze({source,bitmap,process});
})();
