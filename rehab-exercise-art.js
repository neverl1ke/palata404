/* Shared approved first-person illustrations; no stretching or source edits. */
(function(){'use strict';
const cache=new Map();
function load(name){if(!cache.has(name))cache.set(name,(async()=>{const im=new Image();im.src='assets/rehabilitation/'+name+'.png';await im.decode();return im;})().catch(e=>{cache.delete(name);throw e}));return cache.get(name)}
function create(canvas,kind,mode){const W=1672,H=941,ctx=canvas.getContext('2d',{alpha:false}),reduced=matchMedia('(prefers-reduced-motion:reduce)'),ROPE_PERIOD=1.15,smooth=v=>{v=Math.max(0,Math.min(1,v));return v*v*(3-2*v)};const p={exercise:kind,mode},art={};let t=0,disposed=false;
function drawBackground(image,jump=0){
 ctx.save();const flicker=p.mode==='trip'&&!reduced.matches?1-.018*Math.pow(Math.sin(t*4.8)*Math.sin(t*2.1),2):1;ctx.filter=flicker<1?'brightness('+flicker+')':'none';
 const margin=p.exercise==='rope'?.03:.01;
 ctx.drawImage(image,-W*margin,-H*margin+jump,W*(1+margin*2),H*(1+margin*2));ctx.restore();
}
function ropeTransform(side,phase){
 const sc=W/1254,sign=side==='left'?-1:1,active=(p.started||p.ropeSettling)&&!reduced.matches,raw=active?((phase-.90)%1+1)%1:0,q=raw-.35*Math.sin(raw*Math.PI*2)/(Math.PI*2),theta=-q*Math.PI*2,out=(1-Math.cos(theta))*.5;
 const spread=sign*(70+520*out),pivot=side==='left'?[190*sc,500*sc]:[1060*sc,500*sc],angle=sign*.18*Math.sin(theta),bob=reduced.matches?0:Math.sin(t*1.9)*2;
 // Forward rotation is the reverse of the previous orbit. Periodic pacing
 // reduces speed near the visible stance; the wrapped seam stays continuous.
 // No sleeve scaling, mesh stretching, or switching hand images.
 return {sc,spread,pivot,angle,offset:315+bob-170*Math.sin(theta)+120*out,q,theta};
}
function ropePoint(side,phase){
 const z=ropeTransform(side,phase),v=side==='left'?[363*z.sc,125*z.sc]:[890*z.sc,125*z.sc],dx=v[0]-z.pivot[0],dy=v[1]-z.pivot[1];
 return [z.spread+z.pivot[0]+dx*Math.cos(z.angle)-dy*Math.sin(z.angle),z.offset+z.pivot[1]+dx*Math.sin(z.angle)+dy*Math.cos(z.angle)];
}
function ropeArm(side,phase){
 const z=ropeTransform(side,phase);ctx.save();ctx.translate(z.spread,z.offset);ctx.translate(...z.pivot);ctx.rotate(z.angle);ctx.translate(-z.pivot[0],-z.pivot[1]);
 ctx.beginPath();ctx.rect(side==='left'?0:W/2,0,W/2,W);ctx.clip();if(p.mode==='trip')ctx.filter='brightness(.78) saturate(.87)';ctx.drawImage(art['rope-hands'],0,0,W,W);ctx.restore();
}
function drawRope(){
 const phase=p.started||p.ropeSettling?p.time/ROPE_PERIOD%1:.90,posePhase=reduced.matches?.90:phase,air=Math.pow(Math.sin(Math.max(0,Math.min(1,(t-p.jump)/.38))*Math.PI),2),j=reduced.matches?0:air*24;
 drawBackground(art['rope-'+p.mode],j);
 const a=ropePoint('left',posePhase),b=ropePoint('right',posePhase),theta=ropeTransform('left',posePhase).theta,cx=W/2,cy=H/2,near=.12;
 // Sweep a single rope loop through depth. Clip segments behind the eye plane;
 // the rope leaves through the real frame edges rather than fading in place.
 const flare=260+220*(1-Math.cos(theta));
 const points=[];for(let i=0;i<=128;i++){const u=i/128,bend=Math.sin(Math.PI*u);points.push({x:a[0]+(b[0]-a[0])*u-cx-flare*Math.sin(Math.PI*u*2),y:a[1]+(b[1]-a[1])*u-cy+H*1.25*Math.cos(theta)*bend,z:1+1.7*Math.sin(theta)*bend});}
 const project=v=>[cx+v.x/v.z,cy+v.y/v.z];
 ctx.save();ctx.lineCap='round';ctx.lineJoin='round';ctx.beginPath();
 for(let i=1;i<points.length;i++){
  let u=points[i-1],v=points[i];if(u.z<near&&v.z<near)continue;
  if(u.z<near||v.z<near){const n=(near-u.z)/(v.z-u.z),edge={x:u.x+(v.x-u.x)*n,y:u.y+(v.y-u.y)*n,z:near};if(u.z<near)u=edge;else v=edge;}
  ctx.moveTo(...project(u));ctx.lineTo(...project(v));
 }
 ctx.strokeStyle=p.mode==='trip'?'#53331f':'#674121';ctx.lineWidth=5.5;ctx.stroke();ctx.strokeStyle=p.mode==='trip'?'#a47b48':'#c3985f';ctx.lineWidth=1.3;ctx.stroke();ctx.restore();
 ropeArm('left',posePhase);ropeArm('right',posePhase);
}
function benchBarY(){
 if(p.stage==='rack')return 420;
 if(p.stage==='unrack'){const a=p.stageTime/.8;return a<.22?420-45*smooth(a/.22):375+325*smooth((a-.22)/.78);}
 if(p.stage==='rackBack'){const a=p.stageTime/.8;return a<.7?700-325*smooth(a/.7):375+45*smooth((a-.7)/.3);}
 // A deeper lower position; the upper point remains at 320, scale unchanged.
 return 700-p.lift*380;
}
function drawBench(){
 ctx.drawImage(art['bench-'+p.mode],0,0,W,H);
 // The approved foreground has its outer plate edges cropped at the canvas
 // boundary. Keep that boundary outside the view throughout the lift: scaling
 // the sprite down exposed those cut edges and narrowed it inside the rack.
 const y=benchBarY(),img=p.mode==='patient'?art['bench-patient-toned']:art['bench-hands'],width=W,height=img.height/img.width*width,barY=305/img.width*width;
 ctx.save();if(p.mode==='trip')ctx.filter='brightness(.78) saturate(.84)';ctx.drawImage(img,(W-width)/2,y-barY,width,height);ctx.restore();
 // The front lips occlude the shaft while it rests in the cups. During the set
 // the whole moving layer is in front of the rack; cups never move or turn.
 if(p.stage==='rack'){
  ctx.save();ctx.beginPath();ctx.moveTo(240,430);ctx.lineTo(325,430);ctx.lineTo(331,465);ctx.lineTo(317,491);ctx.lineTo(257,489);ctx.lineTo(240,464);ctx.closePath();ctx.moveTo(1348,430);ctx.lineTo(1434,430);ctx.lineTo(1434,464);ctx.lineTo(1417,490);ctx.lineTo(1360,489);ctx.lineTo(1348,464);ctx.closePath();ctx.clip();ctx.drawImage(art['bench-'+p.mode],0,0,W,H);ctx.restore();
 }

}

const ready=Promise.all([kind+'-'+mode,kind+'-hands'].map(async name=>{art[name]=await load(name)})).then(()=>{if(kind==='bench'&&mode==='patient')art['bench-patient-toned']=PalataRehabSkinTone.grade(art['bench-hands'])});
function draw(state){if(disposed)return;Object.assign(p,state,{exercise:kind,mode});t=state.elapsed;kind==='rope'?drawRope():drawBench()}
return {ready,draw,dispose(){disposed=true},benchBarY:()=>benchBarY()};
}
window.PalataExerciseArt=Object.freeze({create});
})();
