'use strict';
const {test}=require('node:test');
const a=require('node:assert/strict');
const E=require('../quest-engine.js');
const {nextOperation}=require('./quest-workbench-solver.cjs');
const clone=x=>JSON.parse(JSON.stringify(x));
function apply(s,event){const r=E.apply(s,event);a.equal(r.ok,true,r.message);return r;}
function move(s,room){if(s.room!==room)apply(s,{type:'move',room});}
function accept(s,id){move(s,E.jobs[id].giver);return apply(s,{type:'action',id:'accept:'+id});}
function work(s,id,op,value){return apply(s,{type:'work',id,op,value});}
function solve(s,id){for(let i=0;i<60;i++){const b=E.workbench(s,id);if(!b)return;const o=nextOperation(b);if(o.navigate){move(s,o.navigate);solve(s,o.action);move(s,o.resumeRoom);}else work(s,id,o.op,o.value);}throw Error('Unfinished '+id);}
function rejected(s,event){const before=JSON.stringify(s),result=E.apply(s,event);a.equal(result.ok,false);a.equal(JSON.stringify(s),before);return result;}

test('version11 world starts unknown and preserves facts without accepting future schemas',()=>{
 const initial=E.initial();a.equal(initial.version,11);a.equal(E.supportsSave(initial),true);a.deepEqual(E.roomEffects(initial,'ward406'),[]);a.deepEqual(E.roomEffects(initial,'doctor'),[]);
 for(const version of [1,6,7]){const legacy=E.restore({version,mode:'patient',room:'nurse',jobs:{k2:{active:false,count:12},d1:{active:false,count:9}},world:{version:1,linen406:{prepared:true}},cargo:[]});a.equal(legacy.world.linen406,null);a.deepEqual(legacy.world.calls,{ward407:null,ward408:null});a.equal(legacy.world.doctorReview,null);}
 for(const raw of [{...initial,version:12},{...initial,world:{...initial.world,version:3}},{...initial,world:{...initial.world,futureEffect:true}},{...initial,jobs:{k2:{active:true,revision:4,variant:0,work:{}}}}]){const before=JSON.stringify(raw);a.equal(E.supportsSave(raw),false);a.equal(JSON.stringify(raw),before);}
});

test('new bed preparation needs the right item and zone, survives a partial reload, and consumes one parcel once',()=>{
 let s=E.initial();accept(s,'k2');a.equal(s.jobs.k2.revision,5);move(s,'linen');solve(s,'job:linen');move(s,'ward406');a.equal(E.workbench(s,'job:deliver').kind,'bedmaking');
 rejected(s,{type:'work',id:'job:deliver',op:'deliver'});rejected(s,{type:'work',id:'job:deliver',op:'place',value:'sheetZone'});
 rejected(s,{type:'work',id:'job:deliver',op:'selectPiece',value:'sheet'});work(s,'job:deliver','startBedPreparation');work(s,'job:deliver','chooseMethod','window');work(s,'job:deliver','selectPiece','sheet');rejected(s,{type:'work',id:'job:deliver',op:'place',value:'pillowZone'});work(s,'job:deliver','spreadSheet');
 a.equal(s.world.linen406,null);a.deepEqual(s.jobs.k2.work.placed,['sheet']);a.ok(s.cargo.includes('linen'));a.match(E.cargoDescription(s,'linen'),/Уже использовано: простыня/);
 s=E.restore(clone(s));a.deepEqual(s.jobs.k2.work.placed,['sheet']);rejected(s,{type:'work',id:'job:deliver',op:'selectPiece',value:'sheet'});
 work(s,'job:deliver','selectPiece','pillowcase');const result=work(s,'job:deliver','place','pillowZone');a.equal(result.completed,'deliver');a.equal(result.reward,undefined);
 a.ok(!s.cargo.includes('linen'));a.deepEqual(s.cargo.filter(x=>x==='delivery'),['delivery']);a.equal(s.world.linen406.prepared,true);a.equal(s.world.linen406.order,'k2:1');a.equal(s.world.linen406.items.length,2);a.equal(E.supportsSave(s),true);
 rejected(s,{type:'work',id:'job:deliver',op:'place',value:'pillowZone'});move(s,'nurse');const paid=apply(s,{type:'action',id:'claim:k2'});a.deepEqual(paid.reward,{kind:'job',job:'k2',id:'k2:1',...E.payouts.k2});a.match(paid.message,/Клара: подготовку кровати/);
 const fact=clone(s.world.linen406);accept(s,'k2');a.deepEqual(s.world.linen406,fact);s=E.restore(clone(s));a.deepEqual(s.world.linen406,fact);a.equal(E.roomEffects(s,'ward406')[0].prepared,true);a.deepEqual(E.roomEffects(s,'ward406','trip'),[]);
});

test('missing linen requires a recorded shortage and an explicitly matching authorized reserve',()=>{
 const s=E.initial();s.jobs.k2={active:false,revision:2,count:1,done:{},startTrip:0,variant:0,work:{selected:[]}};accept(s,'k2');a.equal(s.jobs.k2.variant,1);move(s,'linen');let b=E.workbench(s,'job:linen');a.equal(b.request.missingComponent,'Наволочка с маркировкой Л');a.equal(b.authorizedSubstitution,undefined);
 rejected(s,{type:'work',id:'job:linen',op:'select',value:'linen-1'});move(s,'nurse');a.equal(E.workbench(s,'job:linenReserve'),null);move(s,'linen');work(s,'job:linen','noteShortage');a.equal(E.jobStage(s,'k2').room,'nurse');a.ok(E.workbench(s,'job:linen'));
 move(s,'nurse');b=E.workbench(s,'job:linenReserve');a.equal(b.kind,'clarification');work(s,'job:linenReserve','select','reserve-small');rejected(s,{type:'work',id:'job:linenReserve',op:'submit'});a.equal(s.jobs.k2.work.reserveGranted,false);
 work(s,'job:linenReserve','select','reserve-same-size');const granted=work(s,'job:linenReserve','submit');a.equal(granted.completed,'linenReserve');a.equal(granted.reward,undefined);a.deepEqual(s.cargo,[]);a.equal(s.world.linen406,null);
 a.equal(E.jobStage(s,'k2').room,'linen');move(s,'linen');b=E.workbench(s,'job:linen');a.equal(b.authorizedSubstitution.itemId,'linen-1');a.equal(b.items.find(x=>x.id==='linen-1').unavailable,false);solve(s,'job:linen');move(s,'ward406');work(s,'job:deliver','startBedPreparation');solve(s,'job:deliver');a.equal(s.world.linen406.mark,'Л');a.equal(s.world.linen406.items.find(x=>x.type==='Наволочка').measure,'70 × 70 см');
});

test('issued revision3 diagnostic facts and doctor review retain their old contract without automatic repairs',()=>{
 let s=E.restore({version:8,world:{version:1,linen406:null,calls:{ward407:null,ward408:null},doctorReview:null},mode:'patient',room:'doctor',jobs:{d1:{active:true,revision:3,variant:0,count:0,startTrip:0,done:{},work:{}}},cargo:[]});a.equal(s.jobs.d1.revision,3);move(s,'ward407');work(s,'job:bell407','inspect','connector');work(s,'job:bell407','test');a.equal(s.world.calls.ward407.report,null);a.equal(s.world.calls.ward407.responseCode,'acknowledged');a.equal(s.world.doctorReview,null);
 rejected(s,{type:'work',id:'job:bell407',op:'report',value:'noResponse'});a.equal(s.world.calls.ward407.report,null);solve(s,'job:bell407');move(s,'ward408');solve(s,'job:bell408');a.equal(s.world.calls.ward408.report,'disconnected');a.equal(E.roomEffects(s,'ward408')[0].maintenance,false);
 move(s,'doctor');const result=apply(s,{type:'action',id:'claim:d1'});a.match(result.message,/Врач: по палатам 408/);a.deepEqual(s.world.doctorReview.maintenance,['ward408']);a.equal(E.roomEffects(s,'ward408')[0].maintenance,true);a.match(E.roomEffects(s,'doctor')[0].text,/повторная проверка ещё не подтверждены/);
 const review=clone(s.world.doctorReview);accept(s,'d1');move(s,'ward407');work(s,'job:bell407','inspect','connector');work(s,'job:bell407','test');a.equal(s.world.calls.ward407.order,'d1:2');a.deepEqual(s.world.doctorReview,review);a.equal(E.roomEffects(s,'ward408')[0].maintenance,true);
 s=E.restore(clone(s));a.equal(E.supportsSave(s),true);a.deepEqual(s.world.doctorReview,review);const effects=E.roomEffects(s,'doctor');effects[0].calls.ward408.report='working';a.equal(s.world.doctorReview.calls.ward408.report,'disconnected');a.deepEqual(E.roomEffects(s,'doctor','trip'),[]);
});

test('issued version7 work stays revision2 and only records what its old delivery proves',()=>{
 let s=E.restore({version:7,mode:'patient',room:'ward406',jobs:{k2:{active:true,revision:2,count:2,startTrip:0,variant:2,done:{linen:true},work:{selected:['linen-0','linen-1']}}},cargo:['linen']});a.equal(s.jobs.k2.revision,2);a.equal(E.workbench(s,'job:deliver').kind,'delivery');work(s,'job:deliver','deliver');a.equal(s.world.linen406.prepared,false);a.equal(s.world.linen406.order,'k2:3');a.equal(s.world.linen406.revision,2);a.equal(E.supportsSave(s),true);
 move(s,'nurse');apply(s,{type:'action',id:'claim:k2'});const fact=clone(s.world.linen406);accept(s,'k2');a.equal(s.jobs.k2.revision,5);a.deepEqual(s.world.linen406,fact);
});

test('world facts reject malformed future data instead of silently converting it into a positive result',()=>{
 const s=E.initial();accept(s,'d1');move(s,'ward407');solve(s,'job:bell407');const raw=clone(s);
 for(const edit of [r=>{r.world.calls.ward407.report='future-diagnosis';},r=>{r.world.calls.ward407.responseCode=r.world.calls.ward407.responseCode==='none'?'acknowledged':'none';},r=>{r.world.calls.ward407.kind='invented';},r=>{r.world.linen406={order:'k2:1',delivered:true,prepared:true,revision:3,mark:'М',items:[]};}]){const bad=clone(raw);edit(bad);a.equal(E.supportsSave(bad),false);a.deepEqual(E.roomEffects(bad,'ward407'),[]);}
});
