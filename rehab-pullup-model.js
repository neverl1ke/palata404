/* Transient input model; durable training rewards remain in the profile journal. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.PalataPullupModel=api;})(globalThis,function(){
'use strict';
function initial(){return{time:0,lastTap:-Infinity,effort:0,lift:0,reps:0,target:5,phase:'up',descent:0,complete:false,taps:0};}
function tap(s){if(s.complete||s.phase!=='up'||s.time-s.lastTap<.07)return false;s.lastTap=s.time;s.effort=Math.min(1,s.effort+.26);s.taps++;return true;}
function step(s,seconds){
 const dt=Math.max(0,Math.min(.05,Number.isFinite(seconds)?seconds:0));s.time+=dt;if(s.complete)return s;
 if(s.phase==='down'){
  s.descent=Math.min(1,s.descent+dt/.45);const t=s.descent;s.lift=1-t*t*(3-2*t);s.effort=0;
  if(t>=1){s.phase='up';s.lift=0;}return s;
 }
 s.effort*=Math.exp(-1.35*dt);s.lift=Math.min(1,s.lift+s.effort*dt*.95);
 if(s.time-s.lastTap>1.6&&s.effort<.06)s.lift=Math.max(0,s.lift-.14*dt);
 if(s.lift>=1){s.reps++;s.effort=0;if(s.reps>=s.target){s.complete=true;s.phase='complete';}else{s.phase='down';s.descent=0;}}
 return s;
}
return Object.freeze({initial,tap,step});
});
