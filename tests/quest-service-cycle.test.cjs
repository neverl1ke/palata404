'use strict';

// D1 service and K2 preparation are exercised through their public boards and
// engine operations. Fixtures declare physical starting conditions; choices are
// then derived from the same visible evidence available to the player.
const {test}=require('node:test');
const a=require('node:assert/strict');
const E=require('../quest-engine.js');
const clone=value=>JSON.parse(JSON.stringify(value));
const rooms=['ward407','ward408'];

function apply(s,event){const result=E.apply(s,event);a.equal(result.ok,true,result.message);return result;}
function go(s,room){if(s.room!==room)apply(s,{type:'move',room});}
function accept(s,id){go(s,E.jobs[id].giver);apply(s,{type:'action',id:'accept:'+id});return s.jobs[id];}
function work(s,id,op,value){const result=apply(s,{type:'work',id,op,value});a.ok(!result.reward,'work must not create an additional payout');return result;}
function rejected(s,event){const before=clone(s),result=E.apply(s,event);a.equal(result.ok,false,'operation should be unavailable or unsupported');a.deepEqual(s,before,'rejected operation changed durable work or world');return result;}
function board(s,id,kind){const value=E.workbench(s,id);a.ok(value,id+' should expose its work surface');if(kind)a.equal(value.kind,kind);return value;}
function restore(s){a.equal(E.supportsSave(s),true);const before=clone(s),after=E.restore(clone(s));a.deepEqual(after.jobs,before.jobs);a.deepEqual(after.world,before.world);a.deepEqual(after.cargo,before.cargo);return after;}
function physical(conditions){const s=E.initial();for(const room of rooms)s.world.callEquipment[room]={condition:conditions[room],revision:0,verified:conditions[room]==='working'};a.equal(E.supportsSave(s),true);return s;}

function reportFromEvidence(b){
 a.ok(b.connector,'inspection must expose the connection observation');
 if(b.connector.connected===null)return 'unassessed';
 if(b.connector.connected===false)return 'disconnected';
 if(b.indicator==='on'&&typeof b.response==='string'&&/вызов принят/i.test(b.response))return 'working';
 if(b.indicator==='on'&&typeof b.response==='string'&&/не поступил/i.test(b.response))return 'noResponse';
 throw Error('No supported conclusion can be derived from the visible observation: '+JSON.stringify(b));
}
function initialReport(s,room){
 go(s,room);const id='job:bell'+room.slice(4);let b=board(s,id,'diagnostic');
 a.equal(b.connector,null);a.equal(b.response,null);
 rejected(s,{type:'work',id,op:'test'});
 const inspected=work(s,id,'inspect','connector');work(s,id,'test');b=board(s,id,'diagnostic');
 const report=reportFromEvidence(b);a.ok(b.reports.some(option=>option.id===report));
 if(report==='unassessed'){
  a.doesNotMatch(inspected.message+' '+b.connector.text,/разъ[её]м отсоедин[её]н|пост ответил|вызов принят/i,'unknown observations must not invent a disconnected connector or a successful reply');
  work(s,id,'select','working');const wrong=rejected(s,{type:'work',id,op:'submit'});
  a.doesNotMatch(wrong.message,/пост ответил|вызов принят/i,'unknown-case guidance must not describe a successful post reply');
 }
 work(s,id,'select',report);work(s,id,'submit');
 if(report==='unassessed')a.doesNotMatch(E.cargoDescription(s,id.slice(4)),/разъ[её]м отсоедин[её]н|пост ответил|вызов принят/i,'the saved report must retain uncertainty');
 return report;
}
function initialReports(s){return Object.fromEntries(rooms.map(room=>[room,initialReport(s,room)]));}
function authorize(s){go(s,'doctor');board(s,'job:callReview','callReview');return work(s,'job:callReview','authorize');}
function serviceEvidence(s,room,location){
 go(s,location);const id='job:callService'+room.slice(4);let b=board(s,id,'callService');
 a.ok(!b.evidence,'the service cause must first be inspected');
 rejected(s,{type:'work',id,op:'submit'});
 work(s,id,'inspectEvidence');b=board(s,id,'callService');
 a.ok(b.evidence);a.ok(b.equipment);
 a.equal(b.evidence.equipmentId,b.equipment.id);
 const match=option=>option.equipmentId===b.evidence.equipmentId&&option.connector===b.evidence.connector&&option.postAddress===b.evidence.postAddress;
 a.ok(b.options.every(option=>!Object.hasOwn(option,'correct')&&!Object.hasOwn(option,'answer')),'public options must not contain a solution marker');
 const correct=b.options.filter(match);a.equal(correct.length,1,'the visible equipment, connector and post address should identify one compatible option');
 const wrong=b.options.filter(option=>!match(option));a.ok(wrong.length,'the decision must include incompatible components or registrations');
 return {id,b,correct:correct[0],wrong};
}
function service(s,room,location){const selection=serviceEvidence(s,room,location);work(s,selection.id,'select',selection.correct.id);work(s,selection.id,'submit');return selection;}
function retest(s,room){
 go(s,room);const id='job:callRetest'+room.slice(4);let b=board(s,id,'callRetest');
 a.equal(b.response,null);a.equal(b.responseAddress,null);
 rejected(s,{type:'work',id,op:'confirm'});
 work(s,id,'test');b=board(s,id,'callRetest');
 a.equal(b.responseAddress,'ПОСТ-'+room.slice(4));a.match(b.response,/вызов принят/i);
 work(s,id,'confirm');
 const effect=E.roomEffects(s,room).find(item=>item.id==='call:'+room);
 a.ok(effect);a.equal(effect.verified,true);a.equal(effect.needsRetest,false);a.match(effect.response,/вызов принят/i);
 a.doesNotMatch(effect.text,/ответ поста не поступил|ещ[её] не подтвержд[её]н/i,'the current room note must describe the verified retest, not the old failed response');
 return id;
}
function packLinen(s){
 go(s,'linen');let b=board(s,'job:linen','packing');
 if(b.request.missingComponent&&!b.reserveGranted){
  work(s,'job:linen','noteShortage');go(s,'nurse');const reserve=board(s,'job:linenReserve','clarification');
  const choice=reserve.options.find(option=>option.measure===reserve.request.neededMeasure);a.ok(choice);
  work(s,'job:linenReserve','select',choice.id);work(s,'job:linenReserve','submit');go(s,'linen');b=board(s,'job:linen','packing');
 }
 for(const type of b.request.components){
  const item=b.items.find(item=>item.type===type&&!item.unavailable&&item.condition==='чистая упаковка'&&(item.size===b.request.size||item.id===b.authorizedSubstitution?.itemId));
  a.ok(item,'the approved request must have an available clean '+type);work(s,'job:linen','select',item.id);
 }
 work(s,'job:linen','submit');a.ok(s.cargo.includes('linen'));
}

test('v9 separates persistent equipment from call snapshots and protects future schemas',()=>{
 const s=E.initial();a.equal(s.version,9);a.equal(s.world.version,2);a.equal(E.supportsSave(s),true);
 a.equal(s.world.callEquipment.ward407.condition,'noResponse');a.equal(s.world.callEquipment.ward408.condition,'disconnected');
 for(const room of rooms){a.equal(s.world.callEquipment[room].revision,0);a.equal(s.world.callEquipment[room].verified,false);}
 accept(s,'d1');a.equal(s.jobs.d1.revision,4);
 for(const edit of [raw=>{raw.version=10;},raw=>{raw.world.version=3;},raw=>{raw.jobs.d1.revision=5;},raw=>{raw.version=8;},raw=>{raw.world.callEquipment.ward407.condition='future-state';},raw=>{raw.jobs.d1.work.order='d1:999';},raw=>{raw.jobs.d1.work.services.ward407.responseAddress='ПОСТ-999';},raw=>{raw.jobs.d1.work.futureServicePhase=true;}]){
  const raw=clone(s);edit(raw);const before=clone(raw);a.equal(E.supportsSave(raw),false);a.deepEqual(raw,before);
 }
});

test('D1 needs doctor authorization and a room-matched observed service before its one existing reward',()=>{
 let s=physical({ward407:'disconnected',ward408:'noResponse'});accept(s,'d1');
 go(s,'doctor');rejected(s,{type:'work',id:'job:callReview',op:'authorize'});
 a.deepEqual(initialReports(s),{ward407:'disconnected',ward408:'noResponse'});
 a.equal(E.ready(s,'d1'),false);go(s,'doctor');rejected(s,{type:'action',id:'claim:d1'});
 authorize(s);const originalReview=clone(s.world.doctorReview);a.equal(originalReview.order,'d1:1');s=restore(s);
 a.equal(s.jobs.d1.count,0);a.equal(E.ready(s,'d1'),false);
 go(s,'nurse');rejected(s,{type:'work',id:'job:callService407',op:'inspectEvidence'});
 go(s,'technical');rejected(s,{type:'work',id:'job:callService408',op:'inspectEvidence'});
 let selection=serviceEvidence(s,'ward407','technical');const beforeEquipment=clone(s.world.callEquipment);
 for(const wrong of selection.wrong){work(s,selection.id,'select',wrong.id);rejected(s,{type:'work',id:selection.id,op:'submit'});a.deepEqual(s.world.callEquipment,beforeEquipment);}
 work(s,selection.id,'select',selection.correct.id);work(s,selection.id,'submit');
 a.deepEqual(s.world.callEquipment.ward407,{condition:'working',revision:1,verified:false});
 a.equal(E.roomEffects(s,'ward407').find(item=>item.id==='call:ward407').needsRetest,true);
 rejected(s,{type:'work',id:selection.id,op:'submit'});a.equal(s.world.callEquipment.ward407.revision,1);
 a.equal(E.ready(s,'d1'),false);s=restore(s);retest(s,'ward407');a.equal(s.world.callEquipment.ward407.verified,true);
 a.equal(E.ready(s,'d1'),false);selection=service(s,'ward408','nurse');a.equal(s.world.callEquipment.ward408.verified,false);
 s=restore(s);retest(s,'ward408');a.equal(s.world.callEquipment.ward408.verified,true);
 a.deepEqual(s.world.doctorReview,originalReview,'servicing must not rewrite the initial signed observations');
 a.equal(s.world.doctorReview.calls.ward407.report,'disconnected');a.equal(s.world.doctorReview.calls.ward408.report,'noResponse');
 const finalReview=E.roomEffects(s,'doctor').find(item=>item.id==='doctorReview');a.deepEqual(finalReview.unresolved,[]);a.match(finalReview.text,/контрольные вызовы подтверждены/i);
 a.deepEqual(s.cargo.slice().sort(),['bell407','bell408']);a.equal(E.ready(s,'d1'),true);
 go(s,'doctor');const result=apply(s,{type:'action',id:'claim:d1'});
 a.deepEqual(result.reward,{kind:'job',job:'d1',id:'d1:1',exp:20,silver:10});a.equal(s.jobs.d1.count,1);
 a.deepEqual(s.world.doctorReview,originalReview);a.deepEqual(s.cargo,[]);
 for(const room of rooms){a.equal(s.world.calls[room].order,'d1:1');a.equal(s.world.calls[room].reviewed,true);a.equal(s.world.calls[room].report,'working');}
 a.equal(E.roomEffects(s,'ward407').find(item=>item.id==='call:ward407').maintenance,false);
 rejected(s,{type:'action',id:'claim:d1'});s=restore(s);a.equal(E.ready(s,'d1'),false);
});

test('D1 unassessed equipment requires staff assessment rather than an invented working report',()=>{
 const s=physical({ward407:'unassessed',ward408:'unassessed'});accept(s,'d1');a.deepEqual(initialReports(s),{ward407:'unassessed',ward408:'unassessed'});authorize(s);
 for(const room of rooms){const selected=serviceEvidence(s,room,'technical');a.ok(selected.b.evidence.observedRegistration!==undefined);work(s,selected.id,'select',selected.correct.id);work(s,selected.id,'submit');retest(s,room);}
 a.equal(E.ready(s,'d1'),true);a.ok(rooms.every(room=>s.world.callEquipment[room].condition==='working'&&s.world.callEquipment[room].verified));
});

test('healthy initial calls need no fabricated service or extra payment',()=>{
 const s=physical({ward407:'working',ward408:'working'});accept(s,'d1');a.deepEqual(initialReports(s),{ward407:'working',ward408:'working'});
 a.equal(E.ready(s,'d1'),false);authorize(s);a.equal(E.ready(s,'d1'),true);
 go(s,'technical');a.equal(E.workbench(s,'job:callService407'),null);a.equal(E.workbench(s,'job:callService408'),null);
 go(s,'doctor');const result=apply(s,{type:'action',id:'claim:d1'});a.deepEqual(result.reward,{kind:'job',job:'d1',id:'d1:1',exp:20,silver:10});
 a.ok(rooms.every(room=>s.world.callEquipment[room].revision===0));
});

test('later D1 variants cannot spontaneously undo verified service',()=>{
 let s=physical({ward407:'disconnected',ward408:'noResponse'});accept(s,'d1');initialReports(s);authorize(s);
 service(s,'ward407','technical');retest(s,'ward407');service(s,'ward408','nurse');retest(s,'ward408');go(s,'doctor');apply(s,{type:'action',id:'claim:d1'});
 const repaired=clone(s.world.callEquipment);
 for(let cycle=0;cycle<3;cycle++){
  s=restore(s);accept(s,'d1');a.deepEqual(s.world.callEquipment,repaired);a.deepEqual(initialReports(s),{ward407:'working',ward408:'working'});authorize(s);a.equal(E.ready(s,'d1'),true);
  a.deepEqual(s.world.callEquipment,repaired);go(s,'doctor');const result=apply(s,{type:'action',id:'claim:d1'});a.equal(result.reward.exp,20);a.equal(result.reward.silver,10);
 }
});

test('stale orders, changed equipment revisions and a wrong post address cannot confirm a repair',()=>{
 let s=physical({ward407:'disconnected',ward408:'working'});accept(s,'d1');initialReports(s);authorize(s);
 const selected=serviceEvidence(s,'ward407','technical');work(s,selected.id,'select',selected.correct.id);
 let stale=clone(s);stale.jobs.d1.work.services.ward407.authorization.order='d1:999';rejected(stale,{type:'work',id:selected.id,op:'submit'});
 stale=clone(s);stale.world.callEquipment.ward407.revision++;rejected(stale,{type:'work',id:selected.id,op:'submit'});
 work(s,selected.id,'submit');go(s,'ward407');work(s,'job:callRetest407','test');
 stale=clone(s);stale.jobs.d1.work.services.ward407.responseAddress='ПОСТ-408';rejected(stale,{type:'work',id:'job:callRetest407',op:'confirm'});
 stale=clone(s);stale.world.callEquipment.ward407.revision++;rejected(stale,{type:'work',id:'job:callRetest407',op:'confirm'});
 work(s,'job:callRetest407','confirm');a.equal(s.world.callEquipment.ward407.verified,true);
});

test('v8 observed equipment migrates without treating old unknown faults as repaired',()=>{
 const observed=(room,report)=>({order:'d1:2',room,tested:true,connected:report==='faultUnspecified'?null:report!=='disconnected',indicator:['working','noResponse'].includes(report)?'on':'off',responseCode:report==='working'?'acknowledged':'none',report,reviewed:false,revision:report==='faultUnspecified'?1:3});
 for(const [left,right] of [['working','disconnected'],['noResponse','faultUnspecified']]){
  const raw={version:8,mode:'patient',room:'doctor',jobs:{},cargo:[],world:{version:1,linen406:null,calls:{ward407:observed('ward407',left),ward408:observed('ward408',right)},doctorReview:null}};
  a.equal(E.supportsSave(raw),true);const before=clone(raw),s=E.restore(raw);a.deepEqual(raw,before);a.equal(s.version,9);a.equal(s.world.version,2);
  a.deepEqual(s.world.calls,raw.world.calls);a.equal(s.world.callEquipment.ward407.condition,left);a.equal(s.world.callEquipment.ward408.condition,right==='faultUnspecified'?'unassessed':right);
  a.equal(s.world.callEquipment.ward408.verified,false);a.equal(E.supportsSave(s),true);
 }
 const unknown=E.restore({version:8,mode:'patient',room:'doctor',jobs:{},cargo:[],world:{version:1,linen406:null,calls:{ward407:null,ward408:null},doctorReview:null}});
 for(const room of rooms){a.equal(unknown.world.callEquipment[room].condition,'unassessed','migration must not replace absent old observations with the new-player fault seed');a.equal(unknown.world.callEquipment[room].verified,false);}
});

test('already issued D1 revisions still finish their old paid contract before a new revision4 order',()=>{
 for(const revision of [1,2,3]){
  const version=revision===1?6:revision===2?7:8,job={active:true,revision,count:2,done:{bell407:true,bell408:true},startTrip:0,variant:0,work:{diagnostics:{bell407:{inspected:true,tested:true,selected:['working']},bell408:{inspected:true,tested:true,selected:['disconnected']}}}};
  const raw={version,mode:'patient',room:'doctor',jobs:{d1:job},cargo:['bell407','bell408'],...(version===8?{world:{version:1,linen406:null,calls:{ward407:null,ward408:null},doctorReview:null}}:{})};
  let s=E.restore(raw);a.equal(s.jobs.d1.revision,revision);a.equal(E.ready(s,'d1'),true);
  const paid=apply(s,{type:'action',id:'claim:d1'});a.deepEqual(paid.reward,{kind:'job',job:'d1',id:'d1:3',exp:20,silver:10});s=restore(s);accept(s,'d1');a.equal(s.jobs.d1.revision,4);
 }
});

test('K2 revision4 requires an explicit start and preserves partial placement through reload',()=>{
 let s=E.initial();accept(s,'k2');a.equal(s.jobs.k2.revision,4);packLinen(s);go(s,'ward406');
 a.equal(board(s,'job:deliver','bedmaking').preparationStarted,false);
 rejected(s,{type:'work',id:'job:deliver',op:'selectPiece',value:'sheet'});rejected(s,{type:'work',id:'job:deliver',op:'place',value:'sheetZone'});
 work(s,'job:deliver','startBedPreparation');work(s,'job:deliver','selectPiece','sheet');rejected(s,{type:'work',id:'job:deliver',op:'place',value:'pillowZone'});work(s,'job:deliver','place','sheetZone');
 const progress=clone(s.jobs.k2.work);work(s,'job:deliver','startBedPreparation');a.deepEqual(s.jobs.k2.work,progress,'starting twice must not clear a placed sheet');s=restore(s);
 a.equal(s.jobs.k2.work.preparationStarted,true);a.deepEqual(s.jobs.k2.work.placed,['sheet']);a.equal(s.world.linen406,null);a.ok(s.cargo.includes('linen'));
 work(s,'job:deliver','selectPiece','pillowcase');work(s,'job:deliver','place','pillowZone');
 a.equal(s.world.linen406.prepared,true);a.equal(s.world.linen406.revision,4);a.ok(!s.cargo.includes('linen'));a.ok(s.cargo.includes('delivery'));
});

test('a repeated K2 order does not dirty the last prepared bed before explicit preparation starts',()=>{
 let s=E.initial();accept(s,'k2');packLinen(s);go(s,'ward406');work(s,'job:deliver','startBedPreparation');
 for(const [piece,zone] of [['sheet','sheetZone'],['pillowcase','pillowZone']]){work(s,'job:deliver','selectPiece',piece);work(s,'job:deliver','place',zone);}
 go(s,'nurse');const paid=apply(s,{type:'action',id:'claim:k2'});a.deepEqual(paid.reward,{kind:'job',job:'k2',id:'k2:1',...E.payouts.k2});
 const prepared=clone(s.world.linen406);accept(s,'k2');a.deepEqual(s.world.linen406,prepared);a.equal(s.jobs.k2.work.preparationStarted,false);
 go(s,'ward406');a.equal(E.bedPresentation(s).prepared,true);rejected(s,{type:'work',id:'job:deliver',op:'startBedPreparation'});a.deepEqual(s.world.linen406,prepared);
 packLinen(s);go(s,'ward406');a.deepEqual(s.world.linen406,prepared);work(s,'job:deliver','startBedPreparation');a.deepEqual(s.world.linen406,prepared);
 const presentation=E.bedPresentation(s);a.equal(presentation.preparationStarted,true);a.equal(presentation.previousPrepared,true);a.equal(presentation.prepared,false);
 s=restore(s);a.deepEqual(s.world.linen406,prepared);a.equal(E.bedPresentation(s).prepared,false);
});

test('old revision2 and revision3 linen parcels retain their issued delivery rules',()=>{
 for(const revision of [2,3]){
  const version=revision===2?7:8,raw={version,mode:'patient',room:'ward406',jobs:{k2:{active:true,revision,count:0,done:{linen:true},startTrip:0,variant:0,work:{selected:['linen-0','linen-1'],placed:[],selectedPiece:null}}},cargo:['linen'],...(version===8?{world:{version:1,linen406:null,calls:{ward407:null,ward408:null},doctorReview:null}}:{})};
  let s=E.restore(raw);a.equal(s.jobs.k2.revision,revision);
  if(revision===2){a.equal(board(s,'job:deliver').kind,'delivery');work(s,'job:deliver','deliver');a.equal(s.world.linen406.prepared,false);}
  else{a.equal(board(s,'job:deliver').kind,'bedmaking');for(const [piece,zone]of [['sheet','sheetZone'],['pillowcase','pillowZone']]){work(s,'job:deliver','selectPiece',piece);work(s,'job:deliver','place',zone);}a.equal(s.world.linen406.prepared,true);}
  go(s,'nurse');apply(s,{type:'action',id:'claim:k2'});s=restore(s);accept(s,'k2');a.equal(s.jobs.k2.revision,4);
 }
});
