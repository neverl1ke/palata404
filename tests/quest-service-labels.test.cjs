"use strict";

const {test}=require('node:test');
const a=require('node:assert/strict');
const E=require('../quest-engine.js');
const clone=value=>JSON.parse(JSON.stringify(value));
const rooms=['ward407','ward408'];

// Captured before the label-only edit at 5fbb87e. The persisted service-a/b/c
// contract must retain every option's original fields, including distractors.
const historicalOptions={
 "0:ward407:noResponse":[{"id":"service-a","equipmentId":"CALL-407","connector":"КС-2","postAddress":"ПОСТ-407"},{"id":"service-b","equipmentId":"CALL-408","connector":"КС-2","postAddress":"ПОСТ-407"},{"id":"service-c","equipmentId":"CALL-407","connector":"КС-2","postAddress":"ПОСТ-408"}],
 "0:ward407:disconnected":[{"id":"service-a","equipmentId":"CALL-407","connector":"КС-2","postAddress":"ПОСТ-407"},{"id":"service-b","equipmentId":"CALL-408","connector":"КС-2","postAddress":"ПОСТ-407"},{"id":"service-c","equipmentId":"CALL-407","connector":"КС-3","postAddress":"ПОСТ-407"}],
 "0:ward408:noResponse":[{"id":"service-a","equipmentId":"CALL-408","connector":"КС-2","postAddress":"ПОСТ-408"},{"id":"service-b","equipmentId":"CALL-407","connector":"КС-2","postAddress":"ПОСТ-408"},{"id":"service-c","equipmentId":"CALL-408","connector":"КС-2","postAddress":"ПОСТ-407"}],
 "0:ward408:disconnected":[{"id":"service-a","equipmentId":"CALL-408","connector":"КС-2","postAddress":"ПОСТ-408"},{"id":"service-b","equipmentId":"CALL-407","connector":"КС-2","postAddress":"ПОСТ-408"},{"id":"service-c","equipmentId":"CALL-408","connector":"КС-3","postAddress":"ПОСТ-408"}],
 "1:ward407:noResponse":[{"id":"service-a","equipmentId":"CALL-408","connector":"КС-2","postAddress":"ПОСТ-407"},{"id":"service-b","equipmentId":"CALL-407","connector":"КС-2","postAddress":"ПОСТ-408"},{"id":"service-c","equipmentId":"CALL-407","connector":"КС-2","postAddress":"ПОСТ-407"}],
 "1:ward407:disconnected":[{"id":"service-a","equipmentId":"CALL-408","connector":"КС-2","postAddress":"ПОСТ-407"},{"id":"service-b","equipmentId":"CALL-407","connector":"КС-3","postAddress":"ПОСТ-407"},{"id":"service-c","equipmentId":"CALL-407","connector":"КС-2","postAddress":"ПОСТ-407"}],
 "1:ward408:noResponse":[{"id":"service-a","equipmentId":"CALL-407","connector":"КС-2","postAddress":"ПОСТ-408"},{"id":"service-b","equipmentId":"CALL-408","connector":"КС-2","postAddress":"ПОСТ-407"},{"id":"service-c","equipmentId":"CALL-408","connector":"КС-2","postAddress":"ПОСТ-408"}],
 "1:ward408:disconnected":[{"id":"service-a","equipmentId":"CALL-407","connector":"КС-2","postAddress":"ПОСТ-408"},{"id":"service-b","equipmentId":"CALL-408","connector":"КС-3","postAddress":"ПОСТ-408"},{"id":"service-c","equipmentId":"CALL-408","connector":"КС-2","postAddress":"ПОСТ-408"}],
 "2:ward407:noResponse":[{"id":"service-a","equipmentId":"CALL-407","connector":"КС-2","postAddress":"ПОСТ-408"},{"id":"service-b","equipmentId":"CALL-407","connector":"КС-2","postAddress":"ПОСТ-407"},{"id":"service-c","equipmentId":"CALL-408","connector":"КС-2","postAddress":"ПОСТ-407"}],
 "2:ward407:disconnected":[{"id":"service-a","equipmentId":"CALL-407","connector":"КС-3","postAddress":"ПОСТ-407"},{"id":"service-b","equipmentId":"CALL-407","connector":"КС-2","postAddress":"ПОСТ-407"},{"id":"service-c","equipmentId":"CALL-408","connector":"КС-2","postAddress":"ПОСТ-407"}],
 "2:ward408:noResponse":[{"id":"service-a","equipmentId":"CALL-408","connector":"КС-2","postAddress":"ПОСТ-407"},{"id":"service-b","equipmentId":"CALL-408","connector":"КС-2","postAddress":"ПОСТ-408"},{"id":"service-c","equipmentId":"CALL-407","connector":"КС-2","postAddress":"ПОСТ-408"}],
 "2:ward408:disconnected":[{"id":"service-a","equipmentId":"CALL-408","connector":"КС-3","postAddress":"ПОСТ-408"},{"id":"service-b","equipmentId":"CALL-408","connector":"КС-2","postAddress":"ПОСТ-408"},{"id":"service-c","equipmentId":"CALL-407","connector":"КС-2","postAddress":"ПОСТ-408"}],
};
function apply(s,event){const result=E.apply(s,event);a.equal(result.ok,true,result.message);return result;}
function go(s,room){if(s.room!==room)apply(s,{type:'move',room});}
function work(s,id,op,value){const result=apply(s,{type:'work',id,op,value});a.equal(result.reward,undefined);return result;}
function preparedService(variant,room,cause){
 const s=E.initial();
 for(const target of rooms)s.world.callEquipment[target]={condition:target===room?cause:'working',revision:0,verified:target!==room};
 // A prior issued-and-closed order chooses the same stable variant as an old
 // save. Acceptance still goes through the public engine, not private helpers.
 if(variant)s.jobs.d1={active:false,count:variant,done:{}};
 go(s,'doctor');apply(s,{type:'action',id:'accept:d1'});
 for(const target of rooms){
  go(s,target);const id='job:bell'+target.slice(4);
  work(s,id,'inspect','connector');work(s,id,'test');
  const b=E.workbench(s,id),report=!b.connector.connected?'disconnected':b.indicator==='on'&&/вызов принят/.test(b.response)?'working':'noResponse';
  work(s,id,'select',report);work(s,id,'submit');
 }
 go(s,'doctor');work(s,'job:callReview','authorize');
 go(s,cause==='noResponse'?'nurse':'technical');
 const id='job:callService'+room.slice(4);work(s,id,'inspectEvidence');
 return {s,id,board:E.workbench(s,id)};
}
const key=(v,room,cause)=>[v,room,cause].join(':');
const fields=options=>options.map(({label,...rest})=>rest);

test('D1 neutral record titles do not identify the answer and keep all historical option slots',()=>{
 const correctLabels=new Set();
 for(const v of [0,1,2])for(const room of rooms)for(const cause of ['noResponse','disconnected']){
  const {board:b}=preparedService(v,room,cause),record=key(v,room,cause);
  a.deepEqual(fields(b.options),historicalOptions[record],record+' changed persisted option semantics');
  a.deepEqual(b.options.map(x=>x.label),[1,2,3].map(n=>'Запись №'+room.slice(4)+'-0'+n));
  a.ok(b.options.every(x=>!/(штатн|сосед|друг|правил|ошиб|закрепить)/i.test(x.label)),record);
  const matching=b.options.filter(x=>['equipmentId','connector','postAddress'].every(k=>x[k]===b.evidence[k]));
  a.equal(matching.length,1);correctLabels.add(matching[0].label.slice(-2));
 }
 a.deepEqual([...correctLabels].sort(),['01','02','03'],'a stable record number must not identify the correct option');
});

test('every saved D1 service selection retains its old fields and outcome after restore',()=>{
 for(const v of [0,1,2])for(const room of rooms)for(const cause of ['noResponse','disconnected']){
  const {s,id,board:b}=preparedService(v,room,cause);
  for(const option of b.options){
   const selected=clone(s);work(selected,id,'select',option.id);
   a.equal(E.supportsSave(selected),true);
   const bytes=JSON.stringify(selected),restored=E.restore(clone(selected));
   a.equal(JSON.stringify(selected),bytes,'restore may not alter the raw save');
   a.deepEqual(restored.jobs.d1.work.services[room].selected,[option.id]);
   const after=E.workbench(restored,id);
   a.deepEqual(fields(after.options),historicalOptions[key(v,room,cause)]);
   const stable=after.options.find(x=>x.id===option.id);a.deepEqual(stable,option);
   const fits=['equipmentId','connector','postAddress'].every(k=>option[k]===b.evidence[k]);
   const before=clone(restored),result=E.apply(restored,{type:'work',id,op:'submit'});
   a.equal(result.ok,fits,`${key(v,room,cause)} ${option.id}`);
   a.equal(result.reward,undefined);
   if(fits){
    a.equal(restored.jobs.d1.work.services[room].performed,true);
    a.equal(restored.world.callEquipment[room].condition,'working');
    a.equal(restored.jobs.d1.count,v,'servicing is not a paid handoff');
    a.equal(E.ready(restored,'d1'),false,'the saved selection still requires a real control call');
   }else a.deepEqual(restored,before,'a restored incompatible selection must fail without losing progress');
  }
 }
});
