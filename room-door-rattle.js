/* The unseen visitor reaches the door with the last wet step, then lets go
   when the first footprint begins to evaporate. The leaf never opens here. */
(function(){
'use strict';
const root=document.querySelector('.hospital-hud'),door=root?.querySelector('.room-door-assembly');
const handle=door?.querySelector('.room-door-handle'),prints=[...(root?.querySelectorAll('.room-floor-print')||[])];
if(!handle||!prints.length)return;
const reduced=matchMedia('(prefers-reduced-motion: reduce)');
let effect=null,wake=0,sequence=null,sequenceCycle=null,active=false;
const random=(a,b)=>a+Math.random()*(b-a);
function clock(){
 const animations=prints.map(p=>p.getAnimations().find(a=>a.animationName==='room-wet-step'));
 const first=animations[0],last=animations.at(-1);if(!first||!last||first.currentTime===null)return null;
 const timing=first.effect.getTiming(),end=last.effect.getTiming(),duration=Number(timing.duration);
 const keys=first.effect.getKeyframes(),peak=Math.max(...keys.map(k=>Number(k.opacity)));
 const holds=keys.filter(k=>Number(k.opacity)===peak).map(k=>k.computedOffset);
 const arrival=Number(end.delay)-Number(timing.delay)+Number(end.duration)*holds[0],fade=duration*holds.at(-1);
 const elapsed=Number(first.currentTime)-Number(timing.delay),cycle=Math.floor(elapsed/duration);
 return {animation:first,duration,arrival,fade,elapsed,cycle,phase:((elapsed%duration)+duration)%duration};
}
function pulls(duration){
 const points=[{time:0,angle:0}];let t=0,n=0;
 while(n<30){
  const rapid=n%4===1||Math.random()<.32;
  t+=rapid?random(30,95):random(130,330);
  const down=random(35,75),release=random(55,110),hold=random(5,35),angle=random(11,29);
  if(t+down+hold+release+50>=duration)break;
  points.push({time:t,angle:0},{time:t+down,angle},{time:t+down+hold,angle:angle*.9},
   {time:t+down+hold+release*.72,angle:random(-2.8,-.8)},{time:t+down+hold+release,angle:0});
  t+=down+hold+release;n++;
 }
 points.push({time:duration,angle:0});
 return points.map(p=>({offset:p.time/duration,transform:'rotateZ('+p.angle.toFixed(3)+'deg)',easing:'cubic-bezier(.3,0,.3,1)'}));
}
function clearSchedule(){clearTimeout(wake);wake=0;}
function stop(){effect?.cancel();effect=null;active=false;door.dataset.rattling='false';}
function sync(){
 clearSchedule();
 if(reduced.matches||root.dataset.assetsReady!=='true'){stop();return;}
 if(document.hidden||root.dataset.scenePaused==='true'){effect?.pause();return;}
 const time=clock();if(!time||time.fade<=time.arrival){stop();return;}
 const interacting=door.dataset.state!=='closed'||door.classList.contains('is-revealed')||door.classList.contains('is-handle-pressed');
 if(interacting){stop();return;}
 const inWindow=time.elapsed>=0&&time.phase>=time.arrival&&time.phase<time.fade;
 if(inWindow){
  if(sequenceCycle!==time.cycle){sequence=pulls(time.fade-time.arrival);sequenceCycle=time.cycle;stop();}
  if(!effect){effect=handle.animate(sequence,{duration:time.fade-time.arrival,fill:'both'});effect.pause();}
  effect.currentTime=time.phase-time.arrival;active=true;door.dataset.rattling='true';
  if(time.animation.playState==='running'&&time.animation.playbackRate>0){
   effect.playbackRate=time.animation.playbackRate;effect.play();
   wake=setTimeout(sync,Math.max(12,(time.fade-time.phase)/time.animation.playbackRate));
  }else effect.pause();
 }else{
  stop();
  if(time.animation.playState==='running'&&time.animation.playbackRate>0){
   const wait=time.elapsed<0?-time.elapsed+time.arrival:time.phase<time.arrival?time.arrival-time.phase:time.duration-time.phase+time.arrival;
   wake=setTimeout(sync,Math.max(12,wait/time.animation.playbackRate));
  }
 }
}
new MutationObserver(sync).observe(root,{attributes:true,attributeFilter:['data-assets-ready','data-scene-paused']});
new MutationObserver(sync).observe(door,{attributes:true,attributeFilter:['class','data-state']});
reduced.addEventListener('change',sync);document.addEventListener('visibilitychange',sync);
window.addEventListener('pagehide',()=>{clearSchedule();stop();});window.addEventListener('pageshow',sync);
window.PalataDoorRattle=Object.freeze({sync,get active(){return active;},get window(){const t=clock();return t?{arrival:t.arrival,fade:t.fade,duration:t.duration}:null;}});
sync();
})();
