/* Manual input models. Durable energy and rank changes stay in RehabUI. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.PalataExerciseModel=api;})(globalThis,function(){
'use strict';
const PERIOD=1.15;
function initial(kind){return{exercise:kind,started:false,done:false,time:.90*PERIOD,elapsed:0,count:0,misses:0,cycle:-1,jump:-10,pressed:false,lift:0,stage:'rack',phase:'ready',stageTime:0,topHold:0,releaseNeeded:false,ropeSettling:false,ropeEndAt:0,ropeStopFrom:null,ropeStopElapsed:0};}
function start(s){if(s.started||s.ropeSettling||s.stage==='rackBack')return false;const elapsed=s.elapsed;Object.assign(s,initial(s.exercise),{elapsed,started:true});if(s.exercise==='bench')s.stage='unrack';return true;}
function press(s){
 if(!s.started||s.done||s.stage==='unrack')return false;
 if(s.exercise==='rope'){
  const cycle=Math.floor(s.time/PERIOD),phase=s.time/PERIOD%1;if(cycle===s.cycle)return false;s.cycle=cycle;
  const success=phase>=.79&&phase<=.98;if(success){s.count++;s.jump=s.elapsed;}else s.misses++;
  if(s.count>=10){s.done=true;s.started=false;s.ropeSettling=true;s.ropeEndAt=(Math.ceil(s.time/PERIOD-.90)+.90)*PERIOD;}
  return success;
 }
 if(!s.releaseNeeded){s.pressed=true;return true;}return false;
}
function release(s){s.pressed=false;s.releaseNeeded=false;}
function step(s,dt){
 if(!Number.isFinite(dt)||dt<=0)return;s.elapsed+=dt;
 if(s.exercise==='bench'&&s.stage==='rackBack'){s.stageTime=Math.min(.8,s.stageTime+dt);if(s.stageTime>=.8)s.stage='rack';return;}
 if(s.ropeSettling){
  const linear=Math.min(dt,Math.max(0,s.ropeEndAt-s.time-.12));s.time+=linear;dt-=linear;
  if(dt>0){if(s.ropeStopFrom===null)s.ropeStopFrom=s.time;const distance=s.ropeEndAt-s.ropeStopFrom,duration=Math.max(.08,distance*2);s.ropeStopElapsed+=dt;const u=Math.min(1,s.ropeStopElapsed/duration);s.time=s.ropeStopFrom+distance*(2*u-2*u*u*u+u*u*u*u);if(u>=1){s.time=s.ropeEndAt;s.ropeSettling=false;}}return;
 }
 if(!s.started)return;s.time+=dt;if(s.exercise!=='bench')return;
 if(s.stage==='unrack'){s.stageTime=Math.min(.8,s.stageTime+dt);if(s.stageTime>=.8)s.stage='exercise';return;}
 if(s.stage!=='exercise')return;
 if(s.phase==='down'){
  s.lift=Math.max(0,s.lift-dt*.65);
  if(s.lift===0){s.count++;s.phase='ready';s.topHold=0;s.releaseNeeded=s.pressed;if(s.count>=5){s.done=true;s.started=false;s.stage='rackBack';s.stageTime=0;}}
 }else if(s.pressed&&!s.releaseNeeded){s.lift=Math.min(1,s.lift+dt*.65);if(s.lift===1){s.topHold+=dt;if(s.topHold>=.2)s.phase='top';}}
 else if(s.phase==='top')s.phase='down';else{s.lift=Math.max(0,s.lift-dt*.6);s.topHold=0;}
}
return Object.freeze({PERIOD,initial,start,press,release,step});
});
