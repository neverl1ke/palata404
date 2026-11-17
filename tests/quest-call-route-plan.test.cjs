'use strict';

const {test}=require('node:test');
const a=require('node:assert/strict');
const E=require('../quest-engine.js');
const {nextOperation}=require('./quest-workbench-solver.cjs');
const clone=value=>JSON.parse(JSON.stringify(value));
const rooms=['ward407','ward408'];

function apply(s,event){const result=E.apply(s,event);a.equal(result.ok,true,result.message);return result;}
function go(s,room){if(s.room!==room)apply(s,{type:'move',room});}
function solve(s,id){
 for(let i=0;i<30;i++){
  const b=E.workbench(s,id);if(!b)return;
  const operation=nextOperation(b);a.ok(!operation.navigate);
  const result=apply(s,{type:'work',id,...operation});a.equal(result.reward,undefined);
 }
 throw Error('Unfinished work '+id);
}
function start(conditions){
 const s=E.initial();
 if(conditions)for(const room of rooms)s.world.callEquipment[room]={condition:conditions[room],revision:0,verified:conditions[room]==='working'};
 go(s,'doctor');apply(s,{type:'action',id:'accept:d1'});return s;
}
function reportBoth(s){for(const room of rooms){go(s,room);solve(s,'job:bell'+room.slice(-3));}go(s,'doctor');}
function authorized(conditions){const s=start(conditions);reportBoth(s);solve(s,'job:callReview');return s;}
function plan(s){return E.jobStage(s,'d1').plan;}
function checkAvailable(s){
 const before=JSON.stringify(s),stage=E.jobStage(s,'d1');
 a.ok(Object.isFrozen(stage.plan));
 for(const stop of stage.plan){
  a.ok(Object.isFrozen(stop));
  a.deepEqual(Object.keys(stop).sort(),['action','mode','phase','room','text']);
  a.equal(stop.mode,'patient');a.ok(['service','retest'].includes(stop.phase));
  const at=clone(s);go(at,stop.room);
  a.ok(E.actions(at).some(action=>action.id===stop.action),stop.action+' is not a real action at '+stop.room);
  a.ok(E.workbench(at,stop.action),stop.action+' must expose its actual work surface');
 }
 a.equal(JSON.stringify(s),before,'projecting the plan must leave the source state unchanged');
 return stage;
}
function service(s,room){go(s,s.jobs.d1.work.initial[room].condition==='noResponse'?'nurse':'technical');solve(s,'job:callService'+room.slice(-3));}
function retest(s,room){go(s,room);solve(s,'job:callRetest'+room.slice(-3));}

test('D1 exposes no plan or hidden service causes before the actual doctor authorization',()=>{
 const s=start();let stage=E.jobStage(s,'d1');
 a.equal(stage.action,'job:bell407');a.equal(stage.plan,undefined);
 a.doesNotMatch(JSON.stringify(stage),/noResponse|disconnected|CALL-|ПОСТ-/);
 reportBoth(s);stage=E.jobStage(s,'d1');a.equal(stage.action,'job:callReview');a.equal(stage.plan,undefined);
 const before=clone(s);a.equal(E.apply(s,{type:'work',id:'job:callService407',op:'inspectEvidence'}).ok,false);a.deepEqual(s,before);
});

test('authorized D1 guides both services first and lists only already available stops',()=>{
 const s=authorized();let stage=checkAvailable(s);
 a.equal(stage.action,'job:callService407');
 a.deepEqual(stage.plan.map(stop=>[stop.action,stop.phase]),[['job:callService407','service'],['job:callService408','service']]);
 a.equal(stage.plan.some(stop=>stop.action.startsWith('job:callRetest')),false);
 service(s,'ward407');stage=checkAvailable(s);
 a.equal(stage.action,'job:callService408','the guide should not require a return to407 between service visits');
 a.deepEqual(stage.plan.map(stop=>[stop.action,stop.phase]),[['job:callService408','service'],['job:callRetest407','retest']]);
 service(s,'ward408');stage=checkAvailable(s);
 a.deepEqual(stage.plan.map(stop=>stop.action),['job:callRetest407','job:callRetest408']);
 a.equal(E.ready(s,'d1'),false,'route planning cannot certify the required control calls');
});

test('an available local D1 retest remains first, including a tested partial legacy-v9 save',()=>{
 let s=authorized();service(s,'ward407');go(s,'ward407');
 let stage=checkAvailable(s);a.equal(stage.action,'job:callRetest407');a.equal(stage.plan[1].action,'job:callService408');
 apply(s,{type:'work',id:'job:callRetest407',op:'test'});
 const raw={...clone(s),version:9},bytes=JSON.stringify(raw);a.equal(E.supportsSave(raw),true);
 s=E.restore(raw);a.equal(JSON.stringify(raw),bytes);
 stage=checkAvailable(s);a.equal(stage.action,'job:callRetest407');a.match(stage.text,/подтвердите/);
 apply(s,{type:'work',id:stage.action,op:'confirm'});
 a.equal(E.jobStage(s,'d1').action,'job:callService408');
 a.equal(s.jobs.d1.work.services.ward407.confirmed,true);
});

test('D1 plan records are immutable view data and cannot perform remote work or grant rewards',()=>{
 const s=authorized(),before=clone(s),stage=checkAvailable(s);
 a.throws(()=>stage.plan.push({room:'doctor'}),TypeError);
 a.throws(()=>{stage.plan[0].room='doctor';},TypeError);
 a.equal(E.apply(s,{type:'work',id:stage.plan[0].action,op:'inspectEvidence'}).ok,false);
 a.deepEqual(s,before);a.equal(E.ready(s,'d1'),false);
});

function finish(s,batch){
 const visits=[];
 const move=room=>{if(s.room!==room)visits.push(room);go(s,room);};
 if(batch){
  for(let i=0;i<8&&!E.ready(s,'d1');i++){
   const stage=checkAvailable(s);move(stage.room);solve(s,stage.action);
  }
 }else{
  // The former room-by-room itinerary uses the same currently available
  // operations. It is a technical reference, not a player completion time.
  for(const room of rooms){if(s.jobs.d1.work.initial[room].condition==='working')continue;
   move(s.jobs.d1.work.initial[room].condition==='noResponse'?'nurse':'technical');solve(s,'job:callService'+room.slice(-3));
   move(room);solve(s,'job:callRetest'+room.slice(-3));
  }
 }
 a.equal(E.ready(s,'d1'),true);move('doctor');
 const stage=E.jobStage(s,'d1');a.equal(stage.action,'claim:d1');a.deepEqual(stage.plan,[]);a.ok(Object.isFrozen(stage.plan));
 const reward=apply(s,{type:'action',id:'claim:d1'}).reward;
 a.deepEqual(reward,{kind:'job',job:'d1',id:'d1:1',exp:20,silver:10});
 const after=clone(s);a.equal(E.apply(s,{type:'action',id:'claim:d1'}).ok,false);a.deepEqual(s,after);
 return{visits,reward,state:s};
}

test('batched and former itineraries produce identical facts, cargo and one unchanged payout',()=>{
 for(const conditions of [null,{ward407:'disconnected',ward408:'noResponse'},{ward407:'noResponse',ward408:'noResponse'},{ward407:'disconnected',ward408:'disconnected'}]){
  const s=authorized(conditions),batch=finish(clone(s),true),former=finish(clone(s),false);
  for(const field of ['world','jobs','cargo','transaction'])a.deepEqual(batch.state[field],former.state[field],field);
  a.deepEqual(batch.reward,former.reward);
  if(conditions&&conditions.ward407===conditions.ward408){
   a.equal(batch.visits.length,former.visits.length-1,'same staff room should not need a second visit');
  }
 }
});

test('healthy calls add no fake service stops and a single fault keeps its existing service/retest sequence',()=>{
 for(const conditions of [{ward407:'working',ward408:'working'},{ward407:'working',ward408:'disconnected'},{ward407:'noResponse',ward408:'working'}]){
  const s=authorized(conditions),faulty=rooms.filter(room=>conditions[room]!=='working');
  a.equal(plan(s).length,faulty.length);
  if(!faulty.length){a.equal(E.ready(s,'d1'),true);a.equal(E.jobStage(s,'d1').action,'claim:d1');}
  else{a.equal(plan(s)[0].action,'job:callService'+faulty[0].slice(-3));service(s,faulty[0]);a.equal(plan(s)[0].action,'job:callRetest'+faulty[0].slice(-3));}
 }
});

test('issued D1 revisions1–3 retain their old guidance contract and are not rewritten by plan reads',()=>{
 for(const [version,revision]of [[6,1],[7,2],[8,3]]){
  const raw={version,mode:'patient',room:'doctor',jobs:{d1:{active:true,revision,count:0,done:{},startTrip:0,variant:0,work:{diagnostics:{}}}},cargo:[]};
  const s=E.restore(raw);a.equal(s.jobs.d1.revision,revision);
  const before=JSON.stringify(s);a.equal(E.jobStage(s,'d1'),null);
  const guide=E.guide(s,'d1');a.equal(guide.room,'ward407');a.equal(guide.plan,undefined);
  a.equal(JSON.stringify(s),before);
 }
});
