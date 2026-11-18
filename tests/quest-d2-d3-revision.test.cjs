'use strict';

// The revised orders are solved from the same records shown on their public
// boards. Historical fixtures keep the contract that was actually issued.
const {test}=require('node:test');
const a=require('node:assert/strict');
const E=require('../quest-engine.js');
const W=require('../quest-job-model.js');
const clone=value=>JSON.parse(JSON.stringify(value));
const fields=list=>Object.fromEntries(list.map(field=>[field.id,field.value]));

function apply(s,event){const result=E.apply(s,event);a.equal(result.ok,true,result.message);return result;}
function go(s,room){if(s.room!==room)apply(s,{type:'move',room});}
function patient(s){if(s.mode==='trip')apply(s,{type:'switch'});}
function accept(s,id,issuedRevision=3){
 patient(s);go(s,E.jobs[id].giver);apply(s,{type:'action',id:'accept:'+id});
 if(issuedRevision===3){
  // This file verifies contracts already issued by the historical build.
  // Fresh revision-4 behavior is covered by quest-observations-v4.test.cjs.
  const j=s.jobs[id];
  Object.assign(j,W.restore(id,{revision:3,variant:j.variant,work:{}}));
 }
 return s.jobs[id];
}
function work(s,id,op,value){const result=apply(s,{type:'work',id,op,value});a.ok(!result.reward,'observations and corrections must not award an extra payout');return result;}
function reject(s,event){const before=clone(s),result=E.apply(s,event);a.equal(result.ok,false,'unsupported or incomplete work must be rejected');a.deepEqual(s,before,'rejection changed the saved work or world');return result;}
function board(s,id,kind){const result=E.workbench(s,id);a.ok(result,id+' must be available');if(kind)a.equal(result.kind,kind);return result;}
function reload(s){a.equal(E.supportsSave(s),true);const before=clone(s),result=E.restore(before);for(const key of ['jobs','world','cargo','mode','room','trip'])a.deepEqual(result[key],s[key]);a.deepEqual(E.restore(clone(result)),result,'restoring a supported checkpoint must be idempotent');return result;}
function paid(s,id,serial=1){patient(s);go(s,E.jobs[id].giver);const result=apply(s,{type:'action',id:'claim:'+id});a.deepEqual(result.reward,{kind:'job',job:id,id:id+':'+serial,...E.payouts[id]});reject(s,{type:'action',id:'claim:'+id});return result;}
function orderedEvidence(b){
 const readable=b.cards.filter(card=>typeof card.time==='string').sort((left,right)=>left.time.localeCompare(right.time));
 const unreadable=b.cards.filter(card=>card.time===null);a.equal(unreadable.length,1);
 const obscured=unreadable[0];a.equal(obscured.reverseRead,true);a.ok(obscured.reverseText);
 const after=readable.filter(card=>obscured.reverseText.includes(card.room)&&/проверк[аи] сигнала/i.test(card.note));
 const before=readable.filter(card=>obscured.reverseText.includes(card.room)&&/передача белья/i.test(card.note));
 a.equal(after.length,1);a.equal(before.length,1);a.ok(readable.indexOf(after[0])<readable.indexOf(before[0]));
 const order=readable.map(card=>card.id);order.splice(order.indexOf(after[0].id)+1,0,obscured.id);return order;
}
function observe(s,entry='switch'){
 patient(s);go(s,'A');const b=board(s,'job:baseline','baseline'),baseline=fields(b.details);a.deepEqual(E.observation(s),baseline);
 work(s,'job:baseline','record');a.deepEqual(s.jobs.d3.work.baseline,baseline);const baselineTrip=s.jobs.d3.startTrip;
 reject(s,{type:'work',id:'job:baseline',op:'record'});
 if(entry==='move'){go(s,'ward404');apply(s,{type:'switch'});a.equal(s.jobs.d3.work.observed,null);go(s,'A');}
 else apply(s,{type:'switch'});
 a.equal(s.room,'A');a.equal(s.mode,'trip');a.ok(s.jobs.d3.work.observedTrip>baselineTrip);
 const difference=board(s,'job:difference','difference');a.equal(difference.observationCaptured,true);
 a.deepEqual(fields(difference.baseline),baseline);a.deepEqual(fields(difference.current),s.jobs.d3.work.observed);a.deepEqual(E.observation(s),s.jobs.d3.work.observed);
 return difference;
}
function changes(b){const baseline=fields(b.baseline),current=fields(b.current);return Object.keys(baseline).filter(key=>baseline[key]!==current[key]);}
function solveComparison(s,b=board(s,'job:difference','difference')){const changed=changes(b);if(changed.length)for(const field of changed)work(s,'job:difference','mark',field);else work(s,'job:difference','noChanges');const result=work(s,'job:difference','submit');a.equal(E.cargoName(s,'difference'),'Карточка наблюдения · результат');a.ok(result.message.includes(E.cargoName(s,'difference')),'the receipt must use the neutral result name');return changed;}
function historical(version,id,revision,workState,extra={}){const raw={version,mode:'patient',room:id==='d2'?'doctor':'A',jobs:{[id]:{active:true,revision,count:0,startTrip:0,variant:0,done:{},work:workState}},cargo:id==='d3'?['baseline']:[],...extra};if(version>=8)raw.world={version:1,linen406:null,calls:{ward407:null,ward408:null},doctorReview:null};a.equal(E.supportsSave(raw),true);return E.restore(raw);}

test('D2 exposes one unreadable original time and reveals its source only on explicit reverse inspection',()=>{
 let s=E.initial();a.equal(accept(s,'d2').revision,3);let b=board(s,'job:log','timeline');
 const obscured=b.cards.filter(card=>card.timeState==='unreadable');a.equal(obscured.length,1);a.equal(obscured[0].id,'entry-b');a.equal(obscured[0].time,null);a.equal(obscured[0].reverseAvailable,true);a.equal(obscured[0].reverseRead,false);a.equal(obscured[0].reverseText,null);
 for(const card of b.cards.filter(card=>card.timeState==='readable')){a.match(card.time,/^\d{2}:\d{2}$/);a.equal(card.reverseAvailable,false);a.equal(card.reverseRead,false);a.equal(card.reverseText,null);reject(s,{type:'work',id:'job:log',op:'readReverse',value:card.id});}
 reject(s,{type:'work',id:'job:log',op:'readReverse',value:'missing-record'});
 work(s,'job:log','readReverse',obscured[0].id);b=board(s,'job:log','timeline');a.equal(b.cards.find(card=>card.id===obscured[0].id).time,null);a.ok(b.cards.find(card=>card.id===obscured[0].id).reverseText);
 const readState=clone(s.jobs.d2.work);work(s,'job:log','readReverse',obscured[0].id);a.deepEqual(s.jobs.d2.work,readState,'reading twice must not duplicate sources');s=reload(s);a.deepEqual(s.jobs.d2.work,readState);const savedCard=board(s,'job:log','timeline').cards.find(card=>card.id===obscured[0].id);a.equal(savedCard.time,null);a.ok(savedCard.reverseText);
});

test('D2 requires all four sources, reverse evidence and a supported order before its unchanged single payout',()=>{
 let s=E.initial();accept(s,'d2');let b=board(s,'job:log','timeline');const obscured=b.cards.find(card=>card.time===null);
 reject(s,{type:'work',id:'job:log',op:'submit'});reject(s,{type:'action',id:'claim:d2'});
 // A lucky guessed order is still not a verified source.
 for(const id of b.cards.map(card=>card.id).sort())work(s,'job:log','place',id);
 reject(s,{type:'work',id:'job:log',op:'submit'});a.equal(s.jobs.d2.done.log,undefined);a.deepEqual(s.cargo,[]);
 work(s,'job:log','readReverse',obscured.id);b=board(s,'job:log','timeline');const supported=orderedEvidence(b);a.equal(new Set(supported).size,4);
 for(const id of s.jobs.d2.work.order.slice())work(s,'job:log','remove',id);
 for(const id of supported.slice().reverse())work(s,'job:log','place',id);reject(s,{type:'work',id:'job:log',op:'submit'});
 for(const id of s.jobs.d2.work.order.slice())work(s,'job:log','remove',id);
 for(const id of supported.slice(0,3))work(s,'job:log','place',id);reject(s,{type:'work',id:'job:log',op:'submit'});s=reload(s);work(s,'job:log','place',supported[3]);
 const before=clone(s.jobs.d2.work);work(s,'job:log','place',supported[3]);a.deepEqual(s.jobs.d2.work,before);
 const submitted=work(s,'job:log','submit');a.match(submitted.message,/время.*не установлено/i);a.equal(s.jobs.d2.done.log,true);a.deepEqual(s.cargo,['log']);a.match(E.cargoDescription(s,'log'),/не установлено/i);
 s=reload(s);paid(s,'d2');a.deepEqual(E.payouts.d2,{exp:10,silver:5});s=reload(s);reject(s,{type:'action',id:'accept:d2'});a.equal(s.jobs.d2.count,1);
});

test('D3 captures evidence on a real switch or room entry, never by merely opening a board',()=>{
 for(const entry of ['switch','move']){
  let s=E.initial();a.equal(accept(s,'d3').revision,3);a.equal(s.jobs.d3.work.baseline,null);a.equal(s.jobs.d3.work.observed,null);
  go(s,'A');board(s,'job:baseline','baseline');E.observation(s);a.equal(s.jobs.d3.work.baseline,null);a.equal(s.jobs.d3.work.observed,null);
  const b=observe(s,entry),captured=clone(s.jobs.d3.work),firstTrip=s.jobs.d3.work.observedTrip;a.equal(b.allowNoChanges,true);a.match(b.instruction,/или.*нет/i,'instructions must allow a legitimate no-change result');
  s=reload(s);for(let i=0;i<2;i++){apply(s,{type:'switch'});a.deepEqual(E.observation(s),captured.baseline);apply(s,{type:'switch'});a.deepEqual(E.observation(s),captured.observed);}
  go(s,'ward404');go(s,'A');a.deepEqual(s.jobs.d3.work,captured);a.equal(s.jobs.d3.work.observedTrip,firstTrip);a.ok(s.trip>firstTrip);s=reload(s);a.deepEqual(s.jobs.d3.work,captured);
 }
});

test('D3 distinguishes explicit no-change findings, one change and three changes across actual repeat orders',()=>{
 let s=E.initial();a.deepEqual(E.payouts.d3,{exp:20,silver:10});
 for(let cycle=0;cycle<3;cycle++){
  accept(s,'d3');a.equal(s.jobs.d3.revision,3);a.equal(s.jobs.d3.variant,cycle);const b=observe(s,cycle%2?'move':'switch'),changed=changes(b);a.equal(changed.length,[0,1,3][cycle]);
  reject(s,{type:'work',id:'job:difference',op:'submit'});a.equal(s.jobs.d3.done.difference,undefined);a.ok(s.cargo.includes('baseline'));
  if(changed.length){work(s,'job:difference','noChanges');reject(s,{type:'work',id:'job:difference',op:'submit'});work(s,'job:difference','mark',changed[0]);a.equal(s.jobs.d3.work.noChanges,false);a.deepEqual(s.jobs.d3.work.marked,[changed[0]]);work(s,'job:difference','mark',changed[0]);}
  else{work(s,'job:difference','mark','time');reject(s,{type:'work',id:'job:difference',op:'submit'});work(s,'job:difference','noChanges');a.equal(s.jobs.d3.work.noChanges,true);a.deepEqual(s.jobs.d3.work.marked,[]);work(s,'job:difference','noChanges');reject(s,{type:'work',id:'job:difference',op:'submit'});}
  if(changed.length===3){work(s,'job:difference','mark',changed[0]);reject(s,{type:'work',id:'job:difference',op:'submit'});work(s,'job:difference','mark',changed[0]);}
  solveComparison(s,b);a.equal(s.jobs.d3.done.difference,true);a.deepEqual(s.cargo,['difference']);if(!changed.length)a.match(E.cargoDescription(s,'difference'),/различий не обнаружено/i);
  s=reload(s);paid(s,'d3',cycle+1);a.deepEqual(s.cargo,[]);s=reload(s);
 }
});

test('D3 cannot observe a new Trip without a patient baseline or compare it in the wrong state',()=>{
 const s=E.initial();accept(s,'d3');go(s,'A');apply(s,{type:'switch'});a.equal(s.jobs.d3.work.observed,null);reject(s,{type:'work',id:'job:difference',op:'noChanges'});reject(s,{type:'work',id:'job:difference',op:'submit'});
 apply(s,{type:'switch'});work(s,'job:baseline','record');a.equal(s.jobs.d3.startTrip,s.trip);a.equal(s.jobs.d3.work.observed,null);
 reject(s,{type:'work',id:'job:difference',op:'submit'});apply(s,{type:'switch'});a.ok(s.jobs.d3.work.observedTrip>s.jobs.d3.startTrip);
 go(s,'ward404');reject(s,{type:'work',id:'job:difference',op:'noChanges'});go(s,'A');apply(s,{type:'switch'});reject(s,{type:'work',id:'job:difference',op:'noChanges'});
});

test('new D2/D3 saves reject unsupported work fields, invented observations and ambiguous completion',()=>{
 const timeline=E.initial();accept(timeline,'d2');const comparison=E.initial();accept(comparison,'d3');observe(comparison);
 const cases=[
  [timeline,raw=>{raw.jobs.d2.work.inventedTime='08:20';}],
  [timeline,raw=>{raw.jobs.d2.work.reverseRead=['entry-a'];}],
  [timeline,raw=>{raw.jobs.d2.work.order=['entry-a','entry-a'];}],
  [timeline,raw=>{raw.jobs.d2.done.log=true;}],
  [comparison,raw=>{raw.jobs.d3.work.futureCause='confirmed';}],
  [comparison,raw=>{raw.jobs.d3.work.baseline.time='invented';}],
  [comparison,raw=>{raw.jobs.d3.work.baseline.extra='source';}],
  [comparison,raw=>{delete raw.jobs.d3.work.observed.route;}],
  [comparison,raw=>{raw.jobs.d3.work.observedTrip=raw.jobs.d3.startTrip;}],
  [comparison,raw=>{raw.jobs.d3.startTrip=raw.trip+1;}],
  [comparison,raw=>{raw.jobs.d3.work.observedTrip=raw.trip+1;}],
  [comparison,raw=>{raw.jobs.d3.work.noChanges=true;raw.jobs.d3.work.marked=['time'];}],
  [comparison,raw=>{raw.jobs.d3.work.noChanges=true;raw.jobs.d3.work.observed=null;raw.jobs.d3.work.observedTrip=null;}],
  [comparison,raw=>{raw.jobs.d3.done.difference=true;}]
 ];
 for(const [source,edit]of cases){const raw=clone(source);edit(raw);const before=clone(raw);a.equal(E.supportsSave(raw),false,JSON.stringify(raw.jobs));a.deepEqual(raw,before);}
 for(const source of [timeline,comparison]){const old=clone(source);old.version=8;old.world.version=1;delete old.world.callEquipment;a.equal(E.supportsSave(old),false,'new revision3 may not be disguised as a v8 save');a.equal(E.supportsSave(source),true);reload(source);}
});

test('issued revision2 D2 and D3 partial work preserves the former evidence and completion rules',()=>{
 let d2=historical(8,'d2',2,{order:['entry-a']});a.equal(d2.jobs.d2.revision,2);let b=board(d2,'job:log','timeline');a.ok(b.cards.every(card=>typeof card.time==='string'));reject(d2,{type:'work',id:'job:log',op:'readReverse',value:'entry-b'});
 const order=b.cards.slice().sort((left,right)=>left.time.localeCompare(right.time)).map(card=>card.id);for(const id of order)if(!d2.jobs.d2.work.order.includes(id))work(d2,'job:log','place',id);d2=reload(d2);work(d2,'job:log','submit');paid(d2,'d2');d2=reload(d2);reject(d2,{type:'action',id:'accept:d2'});
 let d3=historical(8,'d3',2,{baselineCaptured:true,marked:[]});a.equal(d3.jobs.d3.revision,2);a.equal(E.cargoName(d3,'difference'),E.cargoCatalog.difference.name);apply(d3,{type:'switch'});b=board(d3,'job:difference','difference');a.equal(changes(b).length,1,'old variant0 must retain its issued time change');reject(d3,{type:'work',id:'job:difference',op:'noChanges'});
 for(const key of changes(b))work(d3,'job:difference','mark',key);d3=reload(d3);work(d3,'job:difference','submit');paid(d3,'d3');accept(d3,'d3',4);a.equal(d3.jobs.d3.revision,4);
});

test('issued revision1 actions and completed nonrepeat journals remain usable after migration',()=>{
 let d2=historical(6,'d2',1,{});a.equal(d2.jobs.d2.revision,1);a.equal(E.workbench(d2,'job:log'),null);const orderChoice=E.interactions['job:log'].steps[0].choices.find(([,label])=>label==='407 → 408');a.ok(orderChoice);apply(d2,{type:'interact',id:'job:log',choice:orderChoice[0]});d2=reload(d2);paid(d2,'d2');d2=reload(d2);reject(d2,{type:'action',id:'accept:d2'});
 let d3=historical(6,'d3',1,{});a.equal(d3.jobs.d3.revision,1);a.equal(E.cargoName(d3,'difference'),E.cargoCatalog.difference.name);apply(d3,{type:'switch'});const changedTime=E.interactions['job:difference'].steps[0].choices.find(([,label])=>/изменилось время/i.test(label));a.ok(changedTime);apply(d3,{type:'interact',id:'job:difference',choice:changedTime[0]});d3=reload(d3);paid(d3,'d3');accept(d3,'d3',4);a.equal(d3.jobs.d3.revision,4);
});
