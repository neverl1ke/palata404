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
const ns='http://www.w3.org/2000/svg';
function svgNode(tag,attributes={}){const node=document.createElementNS(ns,tag);for(const [k,v] of Object.entries(attributes))node.setAttribute(k,v);return node;}
function helpArtwork(generation,withWriting){
 const svg=svgNode('svg',{class:'room-glass-help',viewBox:'0 0 200 120','aria-label':withWriting?'HELP':'Condensation'}),defs=svgNode('defs');
 const maskId='room-help-wipe-'+generation,edgeId='room-help-edge-'+generation;
 const edge=svgNode('filter',{id:edgeId,x:'-10%',y:'-10%',width:'120%',height:'120%'});
 edge.append(svgNode('feTurbulence',{type:'fractalNoise',baseFrequency:'.075',numOctaves:'2',seed:String(generation%9+1),result:'grain'}),svgNode('feDisplacementMap',{in:'SourceGraphic',in2:'grain',scale:'1.4',xChannelSelector:'R',yChannelSelector:'G'}),svgNode('feGaussianBlur',{stdDeviation:'.25'}));
 const mask=svgNode('mask',{id:maskId,maskUnits:'userSpaceOnUse',x:'0',y:'0',width:'200',height:'120'});
 mask.append(svgNode('rect',{width:'200',height:'120',fill:'white'}));
 const writing=svgNode('g',{fill:'none',stroke:'black','stroke-width':'7.5','stroke-linecap':'round','stroke-linejoin':'round',filter:'url(#'+edgeId+')'});
 const strokes=['M36 43C34 51 36 59 32 70Q30 79 31 85','M61 33Q55 44 59 59Q62 75 56 89','M34 62Q43 59 58 64','M99 39Q91 36 80 43','M80 43C77 55 82 68 77 89Q87 90 100 86','M80 65Q88 60 97 64','M118 36Q116 49 121 62Q119 74 120 86Q126 91 141 87','M155 91Q151 72 157 55L155 39Q167 35 178 43Q186 57 174 64Q165 68 155 62'];
 const widths=[6.2,7.4,5.3,6.5,6,5.6,7.2,6.5];
 const paths=(withWriting?strokes:[]).map((d,n)=>svgNode('path',{class:'room-help-stroke',d,pathLength:'1','stroke-width':String(widths[n]),transform:'rotate('+((Math.random()-.5)*2.5).toFixed(2)+' 100 60)'}));writing.append(...paths);mask.append(writing);
 const trails=svgNode('g',{fill:'none',stroke:'black','stroke-width':'1.4','stroke-linecap':'round',filter:'url(#'+edgeId+')'});
 const drops=svgNode('g',{class:'room-condensation-drops',fill:'#d6d9d0','fill-opacity':'.30',stroke:'#eef0e3','stroke-opacity':'.32','stroke-width':'.45'});
 const streams=[[67,69,102],[141,82,117],[174,62,104]].map(([x,y,end],n)=>{
  const trail=svgNode('path',{class:'room-condensation-trail',d:'M'+x+' '+y+'Q'+(x-.8)+' '+((y+end)/2)+' '+(x+.6)+' '+end,pathLength:'1'});
  const bead=svgNode('ellipse',{class:'room-condensation-drop',cx:x,cy:y,rx:n===1?'1.1':'.85',ry:'1.8',opacity:'0'});trails.append(trail);drops.append(bead);return {trail,bead,distance:end-y};
 });mask.append(trails);defs.append(edge,mask);svg.append(defs);
 const fog=svgNode('g',{mask:'url(#'+maskId+')'});fog.append(svgNode('image',{class:'room-help-fog',href:'hud-art/glass-mark-4.webp',x:String(-38+Math.random()*6),y:String(-27+Math.random()*4),width:'270',height:'170',preserveAspectRatio:'none'}));svg.append(fog,drops);return {svg,paths,streams};
}
function showContact(index=nextSurface++%surfaces.length,requestedKind){
 if(reduced.matches||document.hidden||root.dataset.scenePaused==='true')return false;
 const i=Math.abs(Number(index)||0)%surfaces.length,surface=surfaces[i],slot=position(i);
 const requested=['hand','help','fog'].includes(requestedKind)?requestedKind:(sequence%2===0?'help':'hand');
 const kind=!surface.classList.contains('room-door-glass')&&requested==='help'?'fog':requested,generation=++sequence,isHand=kind==='hand';
 // A pane may carry one written message; a new message replaces its fading predecessor.
 if(kind==='help')for(const old of active)if(old.node.parentElement===surface&&old.node.dataset.kind==='help'){old.animations.forEach(a=>a.cancel());old.node.remove();active.delete(old);}
 const node=document.createElement(kind==='hand'?'img':'div'),variant=kind==='hand'?Math.floor(Math.random()*3):4;
 node.className='room-glass-mark is-'+kind;node.setAttribute('aria-hidden','true');
 let x=slot.point[0],y=slot.point[1],width=i===2?28:48,artwork=null;
 if(kind==='hand'){node.src='hud-art/glass-mark-'+variant+'.webp';node.alt='';}
 else{width=i===2?60:68;const halfHeight=surface.clientWidth*width/100*.6/surface.clientHeight*50;x=Math.max(width/2+1,Math.min(99-width/2,x));y=Math.max(halfHeight+2,Math.min(98-halfHeight,y));artwork=helpArtwork(generation,kind==='help');node.append(artwork.svg);}
 node.style.left=x+'%';node.style.top=y+'%';node.style.width=width+'%';node.style.setProperty('--mark-turn',((Math.random()-.5)*(isHand?34:6)).toFixed(1)+'deg');
 node.dataset.slot=String(slot.id);node.dataset.generation=String(generation);node.dataset.kind=kind;surface.append(node);surface.dataset.lastContact=String(slot.id);
 const animation=node.animate([{opacity:0,offset:0},{opacity:isHand?.48:.64,offset:.22},{opacity:isHand?.40:.54,offset:.64},{opacity:0,offset:1}],{duration:isHand?12000:16500,easing:'ease-in-out'});
 let cursor=2400;
 const draws=artwork?artwork.paths.map(path=>{const duration=Math.min(620,Math.max(240,path.getTotalLength()*4));const draw=path.animate([{strokeDashoffset:'1px'},{strokeDashoffset:'0px'}],{duration,delay:cursor,fill:'forwards',easing:'ease-in-out'});cursor+=duration+110;return draw;}):[];
 if(artwork)artwork.streams.forEach(({trail,bead,distance},n)=>{const timing={duration:5800+n*350,delay:6200+n*900,fill:'forwards',easing:'linear'};draws.push(trail.animate([{strokeDashoffset:'1px'},{strokeDashoffset:'0px'}],timing),bead.animate([{transform:'translateY(0px)',opacity:0,offset:0},{transform:'translateY('+distance*.2+'px)',opacity:.7,offset:.2},{transform:'translateY('+distance+'px)',opacity:0,offset:1}],timing));});
 const animations=[animation,...draws],entry={node,animations};active.add(entry);animation.onfinish=()=>{active.delete(entry);draws.forEach(a=>a.cancel());node.remove();};
 return {surface:i,slot:slot.id,variant,kind,generation};
}
function tick(){timer=0;showContact();schedule(6000+Math.random()*2200);}
function schedule(delay){clearTimeout(timer);if(!reduced.matches&&!document.hidden&&root.dataset.scenePaused!=='true')timer=setTimeout(tick,delay);}
function playback(){
 const paused=reduced.matches||document.hidden||root.dataset.scenePaused==='true';clearTimeout(timer);timer=0;
 for(const entry of active){if(reduced.matches){entry.animations.forEach(a=>a.cancel());entry.node.remove();active.delete(entry);}else for(const a of entry.animations){if(paused&&a.playState==='running')a.pause();else if(!paused&&a.playState==='paused')a.play();}}
 if(!paused)schedule(2600+Math.random()*1800);
}
new MutationObserver(playback).observe(root,{attributes:true,attributeFilter:['data-scene-paused']});document.addEventListener('visibilitychange',playback);reduced.addEventListener('change',playback);
window.addEventListener('pagehide',()=>{clearTimeout(timer);for(const e of active){e.animations.forEach(a=>a.cancel());e.node.remove();}active.clear();});window.addEventListener('pageshow',playback);
window.PalataAtmosphere=Object.freeze({showContact});playback();
})();
