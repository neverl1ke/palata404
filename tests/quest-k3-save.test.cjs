'use strict';
// Versioned compatibility and reward invariants around the approved K3 case.
const {test}=require('node:test');
const a=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),Module=require('node:module');
const E=require('../quest-engine.js');
const W=require('../quest-job-model.js');
const clone=value=>JSON.parse(JSON.stringify(value));
function apply(s,event){const result=E.apply(s,event);a.equal(result.ok,true,result.message);return result;}
function go(s,room){if(s.room!==room)apply(s,{type:'move',room});}
function accept(s){go(s,'nurse');apply(s,{type:'action',id:'accept:k3'});go(s,'procedure');return s;}
function work(s,op,value){const result=apply(s,{type:'work',id:'job:copies',op,value});a.equal(result.reward,undefined);return result;}
function rejected(s,event){const before=JSON.stringify(s),result=E.apply(s,event);a.equal(result.ok,false);a.equal(JSON.stringify(s),before);return result;}
function conclude(s){work(s,'readSources');for(const [field,choice]of Object.entries({room:'differs',time:'matchesActual',author:'unknown'}))work(s,'conclude',{field,choice});work(s,'submit');}
function worldAt(version){return version===8?{version:1,linen406:null,calls:{ward407:null,ward408:null},doctorReview:null}:E.initial().world;}
function historical(version,revision,workState={},done={},count=0){return{version,world:worldAt(version),mode:'patient',room:'procedure',visited:{A:true,B:true},jobs:{k3:{active:true,revision,variant:0,count,startTrip:0,done,work:workState}},cargo:done.copies?['copies']:[],transaction:0};}
function restoreSupported(raw){const bytes=JSON.stringify(raw);a.equal(E.supportsSave(raw),true);const out=E.restore(raw);a.equal(JSON.stringify(raw),bytes,'restore mutated the original save');a.equal(out.version,10);a.deepEqual(E.restore(clone(out)),out,'restored checkpoint must remain idempotent');return out;}

test('save version10 is current while versions1 through9 retain their supported basic progress',()=>{
 a.equal(E.initial().version,10);a.equal(E.supportsSave(E.initial()),true);
 for(let version=1;version<=10;version++){
  const raw={version,world:worldAt(version),mode:'patient',room:'nurse',visited:{A:true,B:true},flags:{doorKnown:true},cargo:[],transaction:3};
  const out=restoreSupported(raw);a.equal(out.room,'nurse');a.equal(out.flags.doorKnown,true);a.equal(out.transaction,3);
 }
 a.equal(E.supportsSave({...E.initial(),version:11}),false);
});

test('new K3 orders persist the approved revision and source-backed partial conclusions',()=>{
 let s=accept(E.initial());a.equal(s.jobs.k3.revision,3);a.deepEqual(s.jobs.k3.work,{sourcesRead:false,conclusions:{}});a.equal(E.cargoDescription(s,'copies'),null);
 rejected(s,{type:'work',id:'job:copies',op:'conclude',value:{field:'room',choice:'differs'}});
 rejected(s,{type:'work',id:'job:copies',op:'mark',value:'signature'});
 work(s,'readSources');work(s,'conclude',{field:'room',choice:'differs'});
 const original=clone(s.jobs.k3);s=restoreSupported(clone(s));a.deepEqual(s.jobs.k3,original);a.deepEqual(s.cargo,[]);a.equal(E.ready(s,'k3'),false);
 const before=clone(s);work(s,'readSources');a.deepEqual(s.jobs.k3,before.jobs.k3,'reading sources again must not clear conclusions');
 rejected(s,{type:'work',id:'job:copies',op:'submit'});a.equal(E.cargoDescription(s,'copies'),null);
});

test('K3 revision3 is rejected under every downgraded schema including pre-model save versions',()=>{
 const source=accept(E.initial());work(source,'readSources');work(source,'conclude',{field:'room',choice:'differs'});
 for(let version=1;version<10;version++){
  const raw={...clone(source),version,world:worldAt(version)},bytes=JSON.stringify(raw);
  a.equal(E.supportsSave(raw),false,'K3r3 may not masquerade as v'+version);
  const safe=E.restore(raw);a.equal(JSON.stringify(raw),bytes);a.equal(safe.jobs.k3,undefined,'unsupported revision must not become a legacy ready order');a.deepEqual(safe.cargo,[]);a.equal(Boolean(E.ready(safe,'k3')),false);
 }
});

test('malformed source flags, conclusions and forged completion fail closed without changing raw bytes',()=>{
 const source=accept(E.initial());
 const cases=[
  {work:{sourcesRead:'true',conclusions:{}}},
  {work:{sourcesRead:false,conclusions:{room:'differs'}}},
  {work:{sourcesRead:true,conclusions:[]}},
  {work:{sourcesRead:true,conclusions:{room:'differs',answer:'correct'}}},
  {work:{sourcesRead:true,conclusions:{room:'intruder'}}},
  {work:{sourcesRead:true,conclusions:{time:5}}},
  {work:{sourcesRead:true,conclusions:{},marked:['signature']}},
  {work:{sourcesRead:true,conclusions:{}},done:{copies:true}},
  {work:{sourcesRead:true,conclusions:{room:'differs',time:'matchesActual',author:'clara'}},done:{copies:true}},
  {work:{sourcesRead:false,conclusions:{room:'differs',time:'matchesActual',author:'unknown'}},done:{copies:true}},
  {work:{sourcesRead:true,conclusions:{room:'differs',time:'matchesActual',author:'unknown'}},done:{copies:true,other:true}},
 ];
 for(const change of cases){
  const raw=clone(source);Object.assign(raw.jobs.k3,change);if(change.done?.copies)raw.cargo=['copies'];const bytes=JSON.stringify(raw);
  a.equal(E.supportsSave(raw),false,JSON.stringify(change));const safe=E.restore(raw);a.equal(JSON.stringify(raw),bytes);a.equal(safe.jobs.k3,undefined);a.equal(Boolean(E.ready(safe,'k3')),false);a.deepEqual(safe.cargo,[]);
 }
});

test('new K3 result qualifies room, actual time and unknown authorship, with the existing cargo and one payout',()=>{
 let s=accept(E.initial());conclude(s);a.equal(E.ready(s,'k3'),true);a.deepEqual(s.cargo,['copies']);a.deepEqual(E.requiredCargo.k3,['copies']);
 const description=E.cargoDescription(s,'copies');a.match(description,/406\/407/);a.match(description,/09:25.*верно/);a.match(description,/не подтверждено оригиналом/);a.match(description,/неразборчива/);a.doesNotMatch(description,/подписала Клара|Клара подписала/);
 s=restoreSupported(clone(s));go(s,'nurse');const paid=apply(s,{type:'action',id:'claim:k3'});a.deepEqual(paid.reward,{kind:'job',job:'k3',id:'k3:1',exp:15,silver:8});
 a.equal(s.jobs.k3.active,false);a.equal(s.jobs.k3.count,1);a.deepEqual(s.cargo,[]);a.equal(E.cargoDescription(s,'copies'),description);
 s=restoreSupported(clone(s));rejected(s,{type:'action',id:'claim:k3'});rejected(s,{type:'action',id:'accept:k3'});
});

test('issued K3 revision2 keeps its original fields and saved marks through completion and one reward',()=>{
 for(const version of [7,8,9,10]){
  let s=restoreSupported(historical(version,2,{marked:['signature']}));a.equal(s.jobs.k3.revision,2);a.deepEqual(s.jobs.k3.work,{marked:['signature']});
  const board=E.workbench(s,'job:copies');a.equal(board.kind,'compare');a.equal(board.documents.length,2);a.equal(board.sourcesRead,undefined);
  work(s,'submit');a.equal(E.ready(s,'k3'),true);a.match(E.cargoDescription(s,'copies'),/подпись/);s=restoreSupported(clone(s));a.equal(s.jobs.k3.revision,2);
  go(s,'nurse');const paid=apply(s,{type:'action',id:'claim:k3'});a.deepEqual(paid.reward,{kind:'job',job:'k3',id:'k3:1',exp:15,silver:8});s=restoreSupported(clone(s));rejected(s,{type:'action',id:'claim:k3'});rejected(s,{type:'action',id:'accept:k3'});
 }
});

test('issued K3 revision1 and previously completed nonrepeat orders never migrate into a new case',()=>{
 for(const version of [1,6]){
  let s=restoreSupported(historical(version,1));a.equal(s.jobs.k3.revision,1);a.equal(E.workbench(s,'job:copies'),null);
  apply(s,{type:'interact',id:'job:copies',choice:'missingSignature'});a.equal(s.jobs.k3.done.copies,true);a.equal(E.ready(s,'k3'),true);s=restoreSupported(clone(s));a.equal(s.jobs.k3.revision,1);
  go(s,'nurse');const paid=apply(s,{type:'action',id:'claim:k3'});a.equal(paid.reward.exp,15);a.equal(paid.reward.silver,8);rejected(s,{type:'action',id:'accept:k3'});
 }
 const raw=historical(9,2,{marked:['signature']},{copies:true},1);raw.jobs.k3.active=false;raw.room='nurse';raw.cargo=[];
 const s=restoreSupported(raw);a.equal(s.jobs.k3.revision,2);a.equal(s.jobs.k3.count,1);rejected(s,{type:'action',id:'accept:k3'});rejected(s,{type:'action',id:'claim:k3'});
});

test('existing D2 D3 revision3 and K2 D1 revision4 retain their previous minimum save gates',()=>{
 for(const id of ['d2','d3','k2','d1']){
  const s=E.initial();go(s,E.jobs[id].giver);apply(s,{type:'action',id:'accept:'+id});const raw={...clone(s),version:9};a.equal(E.supportsSave(raw),true,id+' supported v9');a.equal(E.restore(raw).jobs[id].revision,s.jobs[id].revision);
  raw.version=8;raw.world=worldAt(8);a.equal(E.supportsSave(raw),false,id+' newer revision cannot become v8');
 }
 for(const id of ['k2','d1']){
  const revised=W.restore(id,{revision:3,variant:0,work:{}}),raw={...E.initial(),version:8,world:worldAt(8),jobs:{[id]:{active:true,count:0,startTrip:0,done:{},...revised}}};
  a.equal(E.supportsSave(raw),true);a.equal(E.restore(raw).jobs[id].revision,3);
 }
});

// Reuse the existing real profile adapter VM setup, stopping before any tests
// are registered. This fixture is intentionally not a browser-play claim.
function adapterFixture(){
 const source=fs.readFileSync(path.join(__dirname,'floor10-main.test.cjs'),'utf8');const end=source.indexOf("test('Main entry");a.ok(end>0);
 const fixture=new Module(path.join(__dirname,'quest-k3-save-adapter-fixture.cjs'),module);fixture.filename=path.join(__dirname,'quest-k3-save-adapter-fixture.cjs');fixture.paths=module.paths;
 fixture._compile(source.slice(0,end)+'\nmodule.exports={game,state,act,move,accept,progressKey,economicSnapshot};',fixture.filename);return fixture.exports;
}

test('the actual profile adapter preserves downgraded or malformed K3 save bytes and cannot pay them',()=>{
 const F=adapterFixture();let healthy=F.game();F.accept(healthy,'k3');a.equal(F.state(healthy).jobs.k3.revision,3,'first prove current adapter/model are ready');
 const valid=accept(E.initial());work(valid,'readSources');
 for(const change of ['downgraded','malformed']){
  const raw=clone(valid);if(change==='downgraded')raw.version=9;else{raw.jobs.k3.work.conclusions={room:'differs',time:'matchesActual',author:'clara'};raw.jobs.k3.done.copies=true;raw.cargo=['copies'];}
  const bytes=JSON.stringify(raw),saves=Object.fromEntries(healthy.storage),key=F.progressKey(healthy);saves[key]=bytes;
  let g=F.game(saves);const before=F.economicSnapshot(g);a.equal(g.storage.get(key),bytes);a.equal(F.act(g,{type:'action',id:'accept:k3'}),false);a.equal(F.act(g,{type:'action',id:'claim:k3'}),false);a.deepEqual(F.economicSnapshot(g),before);a.equal(g.storage.get(key),bytes);
  g=F.game(Object.fromEntries(g.storage));a.equal(g.storage.get(key),bytes);a.equal(F.state(g).jobs.k3,undefined);a.equal(g.run('stats.silver'),healthy.run('stats.silver'));
 }
});
