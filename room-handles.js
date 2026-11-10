/* Extrude the exact original handle contours; the original pixels remain the front face. */
(function(){
'use strict';
const ns='http://www.w3.org/2000/svg';
const shapes={pull:{w:14,h:58,depth:4.8,d:'M5 3Q9 2 10 5Q10 8 8 9L7 10Q4 11 4 16V40Q4 43 7 44L9 46V50Q6 52 4 49L4 46Q1 44 1 40V17Q1 11 5 9L5 8Q3 7 5 3Z'},lever:{w:35,h:15,depth:3.6,d:'M5 1C2 1 1 3 1 6C1 9 4 11 7 10L29 10Q34 10 34 7L33 4L8 4Q7 1 5 1Z'}};
// Metal returns follow the original trapezoid, including the sloped top/bottom.
document.querySelectorAll('.room-cabinet-leaf').forEach(host=>{
 const right=host.classList.contains('room-cabinet-leaf-right'),w=70,h=right?465:444;
 const points=right?[[0,9],[69,0],[70,465],[1,453]]:[[0,9],[68,0],[70,444],[3,434]];
 const facets=points.map(()=>{const node=document.createElement('i');node.className='room-cabinet-metal-return';host.append(node);return node;});
 function fit(){const style=getComputedStyle(host),sx=parseFloat(style.width)/w,sy=parseFloat(style.height)/h,depth=4*sx;if(!sx||!sy)return;host.style.setProperty('--cabinet-depth',depth+'px');
  facets.forEach((node,i)=>{const a=points[i],b=points[(i+1)%4],dx=(b[0]-a[0])*sx,dy=(b[1]-a[1])*sy,l=Math.hypot(dx,dy),ux=dx/l,uy=dy/l;
   node.style.width=l+'px';node.style.height=depth+'px';node.style.transform='matrix3d('+[ux,uy,0,0,0,0,-1,0,-uy,ux,0,0,a[0]*sx,a[1]*sy,0,1].join(',')+')';
  });host.dataset.returnsReady='true';}
 new ResizeObserver(fit).observe(host);fit();
});
document.querySelectorAll('.room-cabinet-handle,.room-door-handle').forEach(host=>{
 const shape=shapes[host.classList.contains('room-door-handle')?'lever':'pull'];
 const path=document.createElementNS(ns,'path');path.setAttribute('d',shape.d);
 const length=path.getTotalLength(),count=52,points=Array.from({length:count+1},(_,i)=>path.getPointAtLength(length*i/count));
 const face=host.querySelector('.room-handle-face'),shadow=face.cloneNode();shadow.className='room-handle-shadow';host.prepend(shadow);
 const facets=Array.from({length:count},()=>{const el=document.createElement('i');el.className='room-handle-side';host.insertBefore(el,face);return el;});
 function fit(){
  const style=getComputedStyle(host),sx=parseFloat(style.width)/shape.w,sy=parseFloat(style.height)/shape.h;if(!sx||!sy)return;
  const depth=shape.depth*sx;host.style.setProperty('--handle-depth',depth+'px');
  facets.forEach((el,i)=>{const p=points[i],q=points[i+1],dx=(q.x-p.x)*sx,dy=(q.y-p.y)*sy,l=Math.hypot(dx,dy);if(l<.01){el.hidden=true;return;}
   el.hidden=false;const ux=dx/l,uy=dy/l;el.style.width=(l+.08)+'px';el.style.height=depth+'px';el.style.transform='matrix3d('+[ux,uy,0,0,0,0,1,0,uy,-ux,0,0,p.x*sx,p.y*sy,0,1].join(',')+')';
   el.style.filter='brightness('+(.52+.42*Math.max(0,-uy*.6+ux*.7)).toFixed(3)+')';
  });host.dataset.meshReady='true';
 }
 new ResizeObserver(fit).observe(host);fit();
});
})();
