/* Transient input model; durable training rewards remain in the profile journal. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.PalataPullupModel=api;})(globalThis,function(){
'use strict';
function initial(){return{time:0,lastTap:-Infinity,effort:0,lift:0,reps:0,target:5,phase:'up',motion:'idle',descent:0,complete:false,taps:0};}
function tap(s){
 if(s.complete||s.phase!=='up'||s.time-s.lastTap<.07)return false;
 const interval=s.time-s.lastTap;
 // Isolated/slow taps cannot bank effort from an earlier fast burst.
 s.effort=interval>.24?.28:Math.min(1,s.effort+.35);
 s.lastTap=s.time;s.taps++;return true;
}
function step(s,seconds){
 if(!Number.isFinite(seconds)||seconds<=0||(s.complete&&s.phase==='complete'))return s;
 // Consume real elapsed time, including input between render frames. Small
 // substeps preserve the same cadence threshold on slower displays.
 let remaining=Math.min(1,seconds);
 while(remaining>1e-9){
  const dt=Math.min(.01,remaining);remaining-=dt;s.time+=dt;
  if(s.phase==='down'){
   s.descent=Math.min(1,s.descent+dt/.55);const t=s.descent;
   s.lift=1-t*t*(3-2*t);s.effort=0;s.motion='down';
   if(t>=1){s.phase=s.complete?'complete':'up';s.lift=0;s.motion='idle';s.lastTap=-Infinity;}
   continue;
  }
  if(s.complete)continue;
  s.effort*=Math.exp(-3.8*dt);
  const pulling=s.time-s.lastTap<=.22&&s.effort>=.42;
  if(pulling){s.lift=Math.min(1,s.lift+s.effort*1.05*dt);s.motion='up';}
  else{s.lift=Math.max(0,s.lift-.75*dt);s.motion=s.lift>0?'down':'idle';}
  if(s.lift>=1){
   s.reps=Math.min(s.target,s.reps+1);s.complete=s.reps>=s.target;
   s.phase='down';s.motion='down';s.descent=0;s.effort=0;
  }
 }
 return s;
}
return Object.freeze({initial,tap,step});
});
