/* Permanent rehabilitation rules. Saved inside the existing profile transaction. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.PalataRehabRules=api;})(globalThis,function(){
'use strict';
const equipment=Object.freeze({rope:{name:'Скакалка',energy:8,duration:10000,effect:'+1 максимум витривалості за ранг'},pullup:{name:'Турнік',energy:10,duration:12000,effect:'+1 базової шкоди за ранг'},bench:{name:'Жим лежачи',energy:10,duration:12000,effect:'+1 базової шкоди за ранг'},bag:{name:'Боксерська груша',energy:8,duration:10000,effect:'+1 п.п. критичного удару за ранг'}});
function normalize(raw,now=Date.now()){return Object.fromEntries(Object.keys(equipment).map(id=>{const p=raw?.[id];return[id,{completed:Number.isSafeInteger(p?.completed)?Math.max(0,Math.min(50,p.completed)):0,lastCompletedAt:Number.isSafeInteger(p?.lastCompletedAt)?(p.lastCompletedAt<=now?Math.max(0,p.lastCompletedAt):0):0}];}));}
function rank(raw,id){return Math.floor(normalize(raw)[id].completed/10);}
function bonuses(raw){const p=normalize(raw);return{damage:Math.floor(p.pullup.completed/10)+Math.floor(p.bench.completed/10),critical:Math.floor(p.bag.completed/10)/100,energy:Math.floor(p.rope.completed/10)};}
function finish(raw,id,energy,now=Date.now()){
 if(!Object.hasOwn(equipment,id))return{ok:false,error:'Невідомий тренажер.'};
 const progress=normalize(raw,now),p=progress[id],spec=equipment[id];
 if(p.completed>=50)return{ok:false,error:'Досягнуто максимального рангу.'};
 if(p.lastCompletedAt&&now-p.lastCompletedAt<60000)return{ok:false,error:'Перерва між вправами — 60 секунд.'};
 if(!Number.isFinite(energy)||energy<spec.energy)return{ok:false,error:'Недостатньо енергії.'};
 const before=bonuses(progress);p.completed++;p.lastCompletedAt=now;const after=bonuses(progress);
 return{ok:true,progress,cost:spec.energy,energyBonus:after.energy-before.energy,rank:Math.floor(p.completed/10),rankUp:p.completed%10===0};
}
return Object.freeze({equipment,normalize,rank,bonuses,finish});
});
