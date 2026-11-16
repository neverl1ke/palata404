/* Display-only patient lighting correction. Original RGBA sprites stay intact. */
(function(){'use strict';
function grade(image){
 const c=document.createElement('canvas');c.width=image.width;c.height=image.height;const ctx=c.getContext('2d',{willReadFrequently:true});ctx.drawImage(image,0,0);const frame=ctx.getImageData(0,0,c.width,c.height),a=frame.data,w=c.width,h=c.height,seed=new Uint8Array(w*h),valid=new Uint8Array(w*h);
 for(let y=210;y<474;y++)for(let x=205;x<1045;x++){
  const left=x<445,right=x>804;if(!left&&!right)continue;
  if(y>=276&&y<=329&&((left&&(x<270||x>440))||(right&&(x<808||x>984))))continue;
  const k=y*w+x,i=k*4;if(a[i+3]<20)continue;valid[k]=1;const r=a[i],g=a[i+1],b=a[i+2];seed[k]=r-g>18&&g-b>8&&r-b>35?1:0;
 }
 for(let y=210;y<474;y++)for(let x=205;x<1045;x++){
  const k=y*w+x;if(!valid[k])continue;let n=0;for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++)n+=seed[k+dy*w+dx];
  let mask=seed[k]?1:Math.max(0,Math.min(1,(n-2)/5));mask*=Math.max(0,Math.min(1,(474-y)/9));if(!mask)continue;
  const i=k*4,r=a[i],g=a[i+1],b=a[i+2],luma=.2126*r+.7152*g+.0722*b,highlight=Math.max(0,Math.min(1,(luma-145)/80)),gain=1-.12*highlight;
  for(let channel=0;channel<3;channel++){const original=a[i+channel],next=(luma+(original-luma)*.82)*gain;a[i+channel]=Math.round(original+(next-original)*mask);}
 }
 ctx.putImageData(frame,0,0);return c;
}
window.PalataRehabSkinTone=Object.freeze({grade});
})();
