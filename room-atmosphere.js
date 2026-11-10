/* Ambient glass contacts only: no game/save state, bounded nodes and paused timers. */
(function(){
'use strict';
const root=document.querySelector('.hospital-hud');if(!root)return;
const surfaces=[...root.querySelectorAll('.room-window-left,.room-window-right,.room-door-glass')];
const reduced=matchMedia('(prefers-reduced-motion: reduce)');let timer=0,nextSurface=0,sequence=0;
const slots=surfaces.map((_,i)=>i===2?[[20,27],[50,27],[80,27],[20,65],[50,65],[80,65]]:[24,50,76].flatMap(x=>[15,37,59,81].map(y=>[x,y])));
const bags=surfaces.map(()=>[]),last=surfaces.map(()=>-1),active=new Set();
function position(i){
 if(!bags[i].length){bags[i]=slots[i].map((_,n)=>n);for(let k=bags[i].length-1;k>0;k--){const j=Math.floor(Math.random()*(k+1));[bags[i][k],bags[i][j]]=[bags[i][j],bags[i][k]];}if(bags[i].at(-1)===last[i]&&bags[i].length>1)[bags[i][0],bags[i][bags[i].length-1]]=[bags[i].at(-1),bags[i][0]];}
 const id=bags[i].pop();last[i]=id;return {id,point:slots[i][id]};
}
function showContact(index=nextSurface++%surfaces.length){
 if(reduced.matches||document.hidden||root.dataset.scenePaused==='true')return false;
 const i=Math.abs(Number(index)||0)%surfaces.length,surface=surfaces[i],slot=position(i),node=document.createElement('img');
 const variant=Math.floor(Math.random()*6);node.className='room-glass-mark';node.src='hud-art/glass-mark-'+variant+'.webp';node.alt='';node.setAttribute('aria-hidden','true');
 node.style.left=slot.point[0]+'%';node.style.top=slot.point[1]+'%';node.style.width=(i===2?28:48)+'%';node.style.setProperty('--mark-turn',((Math.random()-.5)*34).toFixed(1)+'deg');
 node.dataset.slot=String(slot.id);node.dataset.generation=String(++sequence);surface.append(node);surface.dataset.lastContact=String(slot.id);
 const animation=node.animate([{opacity:0,offset:0},{opacity:.68,offset:.24},{opacity:.56,offset:.57},{opacity:0,offset:1}],{duration:10500+Math.random()*1800,easing:'ease-in-out'});
 const entry={node,animation};active.add(entry);animation.onfinish=()=>{active.delete(entry);node.remove();};
 return {surface:i,slot:slot.id,variant,generation:sequence};
}
function tick(){timer=0;showContact();schedule(4300+Math.random()*2500);}
function schedule(delay){clearTimeout(timer);if(!reduced.matches&&!document.hidden&&root.dataset.scenePaused!=='true')timer=setTimeout(tick,delay);}
function playback(){
 const paused=reduced.matches||document.hidden||root.dataset.scenePaused==='true';clearTimeout(timer);timer=0;
 for(const entry of active){if(reduced.matches){entry.animation.cancel();entry.node.remove();active.delete(entry);}else if(paused)entry.animation.pause();else entry.animation.play();}
 if(!paused)schedule(2600+Math.random()*1800);
}
new MutationObserver(playback).observe(root,{attributes:true,attributeFilter:['data-scene-paused']});document.addEventListener('visibilitychange',playback);reduced.addEventListener('change',playback);
window.addEventListener('pagehide',()=>{clearTimeout(timer);for(const e of active){e.animation.cancel();e.node.remove();}active.clear();});window.addEventListener('pageshow',playback);
window.PalataAtmosphere=Object.freeze({showContact});playback();
})();
