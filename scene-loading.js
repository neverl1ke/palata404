/* Show the room only when its current artwork, type and character can paint together. */
(function(){
'use strict';
const root=document.querySelector('.hospital-hud'),screen=document.getElementById('scene-loading');
if(!root||!screen)return;
const status=screen.querySelector('[role="status"]'),retry=screen.querySelector('button');
const failed=new Set(),images=new Map();let resolveReady,stopped=false;
const ready=new Promise(resolve=>{resolveReady=resolve;});
window.PalataSceneLoading=Object.freeze({ready,get failedAssets(){return [...failed];}});
retry.addEventListener('click',()=>location.reload());
const frame=()=>new Promise(resolve=>requestAnimationFrame(resolve));
function imageReady(source){
 const url=new URL(source,document.baseURI).href;
 if(!images.has(url)){
  const image=new Image();image.decoding='async';
  const promise=new Promise((resolve,reject)=>{image.onload=resolve;image.onerror=()=>reject(new Error(url));});
  image.src=url;
  images.set(url,promise.then(()=>image.decode()).catch(error=>{failed.add(url);throw error;}));
 }
 return images.get(url);
}
function cssImages(value){
 const urls=[];for(const m of value.matchAll(/url\(\s*(?:"([^"]*)"|'([^']*)'|([^)]*))\s*\)/g)){
  const source=(m[1]||m[2]||m[3]||'').trim();if(source&&!source.startsWith('#'))urls.push(source);
 }return urls;
}
function roomImages(){
 const sources=new Set([
  'hud-art/hud-reference-card.webp','hud-art/patient-compact.webp','hud-art/control-heading-patch.svg',
  'hud-art/patient-paper-mask.svg','assets/ui/wardrobe/clipboard-v2/board-original.png',
  'hud-art/glass-mark-0.webp','hud-art/glass-mark-1.webp','hud-art/glass-mark-2.webp','hud-art/glass-mark-4.webp'
 ]);
 for(const image of root.querySelectorAll('img'))if(!image.closest('.character-paperdoll')&&image.getAttribute('src'))sources.add(image.currentSrc||image.src);
 for(const element of [root,...root.querySelectorAll('*')]){
  if(element.closest('.character-paperdoll'))continue;
  for(const pseudo of [null,'::before','::after']){
   const style=getComputedStyle(element,pseudo);
   for(const property of ['backgroundImage','maskImage','borderImageSource'])for(const source of cssImages(style[property]))sources.add(source);
  }
 }
 return [...sources];
}
async function characterReady(host){
 while(!stopped){
  const generation=host.paperDollGeneration;
  await host.paperDollReady;
  const renderer=window.avatarCoreGamePreview?.instances.get(host);
  if(renderer?.running)await renderer.running;
  if(generation===host.paperDollGeneration&&!host.hasAttribute('data-paper-loading')&&!host.hasAttribute('data-avatar-pending')){
   const painted=[...host.querySelectorAll('canvas')].some(c=>!c.hidden&&c.width&&c.height)||
    [...host.querySelectorAll('img')].some(im=>im.complete&&im.naturalWidth&&!im.classList.contains('hidden')&&getComputedStyle(im).visibility!=='hidden');
   if(painted)return;
  }
  await frame();
 }
 throw new Error('Room preparation stopped');
}
async function prepare(){
 const sources=roomImages();root.dataset.assetCount=String(sources.length);
 const artwork=Promise.allSettled(sources.map(imageReady));
 await Promise.all([artwork,document.fonts.ready,characterReady(document.getElementById('character-paperdoll')),characterReady(document.getElementById('hud-portrait'))]);
 if(failed.size)throw new Error('Required room artwork could not be decoded');
 window.PalataRoomShadows?.refresh();
 while(!stopped&&(root.dataset.shadowReady!=='true'||!(Number(root.querySelector('.room-shadow-contact')?.dataset.soleSamples)>0)))await frame();
 await frame();await frame();
}
async function start(){
 let timeout;
 try{
  await Promise.race([prepare(),new Promise((_,reject)=>{timeout=setTimeout(()=>reject(new Error('Room preparation timed out')),60000);})]);
  clearTimeout(timeout);root.dataset.assetsReady='true';root.inert=false;root.setAttribute('aria-busy','false');
  screen.classList.add('is-ready');screen.setAttribute('aria-hidden','true');
  setTimeout(()=>{screen.hidden=true;},200);resolveReady(true);window.dispatchEvent(new Event('palata-scene-ready'));
 }catch(error){
  clearTimeout(timeout);stopped=true;root.dataset.loadError='true';status.textContent='Не удалось загрузить палату.';retry.hidden=false;
  screen.querySelector('.scene-loading-line').hidden=true;resolveReady(false);
 }
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
window.addEventListener('pagehide',()=>{stopped=true;});
})();
