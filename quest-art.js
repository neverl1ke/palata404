/* Exact supplied originals for floor 10 scenes, arenas and dossier cards. */
(function(root){
'use strict';
const actors={nurse:'Клара',doctor:'Дежурный врач'};
function resolve(room,mode){
 if(Object.hasOwn(actors,room)){
  const base='assets/floor10-approved/'+room+'/',state=mode==='trip'?'Trip':'Normal';
  return {background:base+'Background_'+state+'.png',sprite:base+'Sprite_'+state+'.png',portrait:base+'Dossier_'+state+'.png',paired:true};
 }
 const paired=['collector','procedure'].includes(room);
 return {background:'assets/quest-scenes/'+room+(paired&&mode==='patient'?'-patient-pilot':'')+'.webp',paired};
}
function renderPerson(host,room,mode){if(!Object.hasOwn(actors,room))return;const image=document.createElement('img');image.className='quest-npc quest-npc-'+room+' quest-npc-'+mode;image.src=resolve(room,mode).sprite;image.alt=actors[room]+' · '+(mode==='trip'?'Трип':'Пациент');image.draggable=false;host.append(image);}
function renderPortrait(host,room,mode){if(!Object.hasOwn(actors,room))return;const card=document.createElement('details');card.className='quest-npc-portrait';const heading=document.createElement('summary');heading.textContent='Портрет · '+actors[room];const image=document.createElement('img');image.src=resolve(room,mode).portrait;image.alt=actors[room]+' · портрет '+(mode==='trip'?'Трипа':'Пациента');card.append(heading,image);host.append(card);}
function configureBosses(bosses){for(const room of Object.keys(actors)){const art=resolve(room,'trip');Object.assign(bosses[room],{sprite:art.sprite,bg:art.background,avatar:art.portrait});bosses[room].dossier={...bosses[room].dossier,cardImg:art.portrait};}}
root.PalataFloorArt=Object.freeze({resolve,renderPerson,renderPortrait,configureBosses});
})(typeof window==='object'?window:globalThis);
