'use strict';
const {test}=require('node:test');
const a=require('node:assert/strict');
const E=require('../quest-engine.js');
const V=require('../quest-state-view.js');
const {nextOperation}=require('./quest-workbench-solver.cjs');
const clone=value=>JSON.parse(JSON.stringify(value));
function apply(s,event){const r=E.apply(s,event);a.equal(r.ok,true,r.message);return r;}
function move(s,room){if(s.room!==room)apply(s,{type:'move',room});}
function work(s,id,op,value){return apply(s,{type:'work',id,op,value});}
function accept(s,id){move(s,E.jobs[id].giver);apply(s,{type:'action',id:'accept:'+id});}
function solve(s,id){for(let n=0;n<60;n++){const b=E.workbench(s,id);if(!b)return;const op=nextOperation(b);if(op.navigate){move(s,op.navigate);solve(s,op.action);move(s,op.resumeRoom);}else work(s,id,op.op,op.value);}throw Error('Unfinished '+id);}
function outcome(s,room,kind,mode=s.mode){return V.forRoom(E,s,room,mode).find(item=>item.kind===kind);}
function diagnose(s){for(const room of ['ward407','ward408']){move(s,room);solve(s,'job:bell'+room.slice(4));}move(s,'doctor');solve(s,'job:callReview');}
function service(s,room){const route=E.jobStage(s,'d1');a.equal(route.action,'job:callService'+room.slice(4));move(s,route.room);solve(s,route.action);}
function confirm(s,room){move(s,room);solve(s,'job:callRetest'+room.slice(4));}

test('consequence projection is immutable, side-effect free and hides unobserved fault seeds',()=>{
 const s=E.initial(),before=clone(s);
 for(const mode of ['patient','trip'])for(const room of Object.keys(E.rooms)){
  const list=V.forRoom(E,s,room,mode);a.ok(Object.isFrozen(list));a.deepEqual(list,[]);
 }
 a.deepEqual(s,before);a.equal(s.world.callEquipment.ward407.condition,'noResponse');
 accept(s,'d1');move(s,'ward407');work(s,'job:bell407','inspect','connector');work(s,'job:bell407','test');
 const observed=clone(s),list=V.forRoom(E,s,'ward407');a.equal(list[0].status,'attention');
 a.throws(()=>list.push({id:'invented'}),TypeError);a.throws(()=>{list[0].label='invented';},TypeError);a.deepEqual(s,observed);
});

test('observations and access override do not fabricate opened passages or a taken reserve',()=>{
 const s=E.initial();s.mode='trip';Object.assign(s.flags,{doorKnown:true,reserveKnown:true,cKeyKnown:true,cLockKnown:true,stairsSeen:true,route:true});
 const before=clone(s);
 for(const room of ['A','B','collector'])a.deepEqual(V.forRoom(E,s,room),[]);
 apply(s,{type:'unlockAll'});for(const sec of ['A','B','C'])a.equal(E.accessible(s,sec),true);
 for(const room of ['A','B','collector'])a.deepEqual(V.forRoom(E,s,room),[]);
 a.deepEqual(s.flags,before.flags);a.deepEqual(s.cargo,before.cargo);a.equal(s.transaction,before.transaction);
});

test('reserve text distinguishes a taken handle from an installed one and preserves mode provenance',()=>{
 const s=E.initial();s.mode='trip';s.flags.tripHandle=true;
 a.match(outcome(s,'collector','reserve').text,/взята.*резерва/i);a.doesNotMatch(outcome(s,'collector','reserve').text,/установлена|при вас/i);
 s.interactions.unlockB=2;a.match(outcome(s,'collector','reserve').text,/установлена.*привод/i);
 s.flags.unlockB=true;a.equal(outcome(s,'A','passage').status,'open');
 a.deepEqual(V.forRoom(E,s,'A','patient'),[]);a.deepEqual(V.forRoom(E,s,'collector','patient'),[]);
});

test('legacy opened passages do not invent missing tool provenance or bypass the other gate',()=>{
 const s=E.restore({version:6,mode:'trip',room:'ward404',jobs:{},cargo:[],flags:{unlockB:true,unlockC:true}});
 a.equal(outcome(s,'A','passage').status,'open');a.equal(outcome(s,'B','passage').status,'open');
 a.doesNotMatch(outcome(s,'A','passage').text,/рукоять.*установлена/i);
 a.doesNotMatch(outcome(s,'B','passage').text,/ключ.*оставлен/i);
 a.deepEqual(V.forRoom(E,s,'collector'),[]);
 s.flags.unlockB=false;a.equal(E.accessible(s,'C'),false);a.equal(outcome(s,'B','passage').status,'open','a saved C mechanism and actual reachable route are separate facts');
});

test('legacy completion counts and delivered parcels never become prepared beds',()=>{
 const countOnly=E.restore({version:7,mode:'patient',room:'nurse',jobs:{k2:{active:false,count:20,done:{linen:true,deliver:true}},d1:{active:false,count:12,done:{bell407:true,bell408:true}}},cargo:[]});
 for(const room of ['ward406','ward407','ward408'])a.deepEqual(V.forRoom(E,countOnly,room),[]);
 const parcel=E.restore({version:7,mode:'patient',room:'ward406',jobs:{k2:{active:true,revision:2,count:0,startTrip:0,variant:0,done:{linen:true},work:{selected:['linen-0','linen-1']}}},cargo:['linen']});
 a.deepEqual(V.forRoom(E,parcel,'ward406'),[]);work(parcel,'job:deliver','deliver');
 const delivered=outcome(parcel,'ward406','linen');a.equal(delivered.status,'delivered');a.doesNotMatch(delivered.label,/подготовлена|сменено/i);
 a.deepEqual(V.forRoom(E,parcel,'ward406','trip'),[]);
});

test('a new bed preparation supersedes the old finished record only after explicit start',()=>{
 const s=E.initial();accept(s,'k2');move(s,'linen');solve(s,'job:linen');move(s,'ward406');
 a.deepEqual(V.forRoom(E,s,'ward406'),[]);work(s,'job:deliver','startBedPreparation');
 a.equal(outcome(s,'ward406','linen').status,'preparing');a.equal(outcome(s,'ward406','linen').mark,'0/2');
 work(s,'job:deliver','selectPiece','sheet');work(s,'job:deliver','place','sheetZone');
 a.equal(outcome(s,'ward406','linen').mark,'1/2');solve(s,'job:deliver');a.equal(outcome(s,'ward406','linen').status,'prepared');
 move(s,'nurse');apply(s,{type:'action',id:'claim:k2'});const prior=clone(s.world.linen406);accept(s,'k2');
 a.equal(outcome(s,'ward406','linen').status,'prepared');move(s,'linen');solve(s,'job:linen');move(s,'ward406');
 a.equal(outcome(s,'ward406','linen').status,'prepared');work(s,'job:deliver','startBedPreparation');
 a.deepEqual(s.world.linen406,prior);a.equal(outcome(s,'ward406','linen').status,'preparing');a.equal(outcome(s,'ward406','linen').mark,'0/2');
 const restored=E.restore(clone(s));a.equal(outcome(restored,'ward406','linen').status,'preparing');a.deepEqual(V.forRoom(E,restored,'ward406','trip'),[]);
});

test('call badges reflect actual control confirmation rather than doctor permission or historical maintenance',()=>{
 const s=E.initial();accept(s,'d1');diagnose(s);const history=clone(s.world.doctorReview);
 a.equal(outcome(s,'ward407','call').status,'attention');a.equal(outcome(s,'ward408','call').status,'attention');
 service(s,'ward407');a.equal(s.world.callEquipment.ward407.condition,'working');a.equal(s.world.callEquipment.ward407.verified,false);
 a.equal(outcome(s,'ward407','call').status,'retest');move(s,'ward407');work(s,'job:callRetest407','test');
 a.equal(outcome(s,'ward407','call').status,'retest');work(s,'job:callRetest407','confirm');a.equal(outcome(s,'ward407','call').status,'verified');
 a.equal(outcome(s,'ward408','call').status,'attention');service(s,'ward408');confirm(s,'ward408');
 a.deepEqual(s.world.doctorReview,history);a.ok(history.maintenance.length>0);a.equal(outcome(s,'ward408','call').status,'verified');
 move(s,'doctor');const reward=apply(s,{type:'action',id:'claim:d1'}).reward;a.equal(reward.exp,20);a.equal(reward.silver,10);
 accept(s,'d1');a.equal(outcome(s,'ward407','call').status,'verified');a.equal(outcome(s,'ward408','call').status,'verified');
 a.deepEqual(V.forRoom(E,s,'ward407','trip'),[]);
});

test('version8 unknown and registered faults are not promoted into repaired world outcomes',()=>{
 const world={version:1,linen406:null,calls:{ward407:null,ward408:null},doctorReview:null};
 const unknown=E.restore({version:8,world,mode:'patient',room:'doctor',jobs:{},cargo:[]});
 a.equal(unknown.world.callEquipment.ward407.condition,'unassessed');a.deepEqual(V.forRoom(E,unknown,'ward407'),[]);
 const fault={order:'d1:1',room:'ward408',tested:true,connected:false,indicator:'off',responseCode:'none',report:'disconnected',reviewed:true,revision:3};
 const observed=E.restore({version:8,world:{...world,calls:{ward407:null,ward408:fault}},mode:'patient',room:'doctor',jobs:{},cargo:[]});
 a.equal(observed.world.callEquipment.ward408.verified,false);a.equal(outcome(observed,'ward408','call').status,'attention');
});
