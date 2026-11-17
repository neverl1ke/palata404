/* Approved bed artwork shares the exact room registration and masks.
   Progress is owned by the quest model; no artwork can complete an operation. */
(function(){
'use strict';
const NS='http://www.w3.org/2000/svg';let sequence=0;
function enabled(){return art().approved===true;}
function geometry(){
 const g=window.PalataQuestBedGeometry;
 return (g?.source?.width??g?.width)===1536&&(g?.source?.height??g?.height)===1024&&g.crop&&g.masks?.sheet&&g.masks?.pillowcase?g:null;
}
function art(){return window.PalataQuestBedArtCandidates||{};}
function svgNode(tag,attributes){const e=document.createElementNS(NS,tag);for(const[key,value]of Object.entries(attributes||{}))e.setAttribute(key,String(value));return e;}
function shape(part,g){const mask=g.masks[part];return typeof mask==='string'?mask:mask?.path;}
function remaining(placed){return ['sheet','pillowcase'].filter(id=>!(placed||[]).includes(id));}
function build(options,base){
 const g=geometry();if(!enabled()||!g||(options.mode&&options.mode!=='patient'))return null;
 const source=options.source||'assets/quest-world/ward406-patient.webp',width=g.source?.width??g.width,height=g.source?.height??g.height,crop=options.crop?g.crop:{x:0,y:0,width,height};
 const svg=svgNode('svg',{viewBox:[crop.x,crop.y,crop.width,crop.height].join(' '),preserveAspectRatio:base?'xMidYMid meet':'none'});
 svg.classList.add(base?'quest-bed-closeup-art':'quest-bed-room-layer');svg.style.setProperty('--bed-crop-aspect',crop.width+'/'+crop.height);svg.dataset.bedArtApproved='true';svg.dataset.bedPreparation=options.preparationStarted?'started':'not-started';svg.dataset.bedPlaced=(options.placed||[]).join(',');
 if(base){svg.setAttribute('role','img');svg.setAttribute('aria-label',options.preparationStarted?'Кровать 406 · размещено '+(options.placed||[]).length+' из 2 вещей':'Кровать 406 до начала смены белья');svg.append(svgNode('image',{href:source,width,height}));}else svg.setAttribute('aria-hidden','true');
 const unplaced=options.preparationStarted?remaining(options.placed):[],candidates=art();
 if(unplaced.length){
  const defs=svgNode('defs');svg.append(defs);
  for(const part of unplaced){const path=shape(part,g),bare=candidates.bareByPiece?.[part]||candidates.barePatient;if(!path||!bare)continue;const id='quest-bed-piece-mask-'+(++sequence)+'-'+part,clip=svgNode('clipPath',{id,clipPathUnits:'userSpaceOnUse'});clip.append(svgNode('path',{d:path,'fill-rule':g.fillRule||'evenodd','clip-rule':g.fillRule||'evenodd'}));defs.append(clip);const image=svgNode('image',{href:bare,width,height,'clip-path':'url(#'+id+')'});image.dataset.bedBarePiece=part;image.addEventListener('error',()=>{svg.dataset.bedArtUnavailable='true';image.remove();},{once:true});svg.append(image);}
 }
 return svg;
}
function create(options={}){return build(options,true);}
function createRoomLayer(options={}){if(!options.preparationStarted||!remaining(options.placed).length)return null;return build({...options,crop:false},false);}
function placementStyle(part){
 const g=geometry(),z=g?.zones?.[part],c=g?.crop;if(!z||!c)return null;
 return {left:((z.x-c.x)/c.width*100)+'%',top:((z.y-c.y)/c.height*100)+'%',width:(z.width/c.width*100)+'%',height:(z.height/c.height*100)+'%'};
}
function pendingStyle(part){const g=geometry(),z=g?.pending?.[part];if(!z)return null;return {left:(z.x/1536*100)+'%',top:(z.y/1024*100)+'%',width:(z.width/1536*100)+'%',height:(z.height/1024*100)+'%'};}
function createPiece(type,condition){
 if(!enabled()||!['sheet','pillowcase'].includes(type)||condition&&!/clean|чист/.test(String(condition)))return null;
 const source=art().pieces?.[type];if(!source)return null;
 const image=document.createElement('img');image.src=source;image.alt='';image.className='workbench-object-illustration quest-bed-piece-art';image.dataset.bedArtApproved='true';image.dataset.linenPiece=type;image.decoding='async';return image;
}
window.PalataQuestBedView=Object.freeze({enabled,reviewEnabled:enabled,create,createRoomLayer,placementStyle,pendingStyle,createPiece});
})();
