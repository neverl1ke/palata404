'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const E=require('../quest-engine.js');
const Navigation=require('../quest-navigation.js');

const copy=value=>JSON.parse(JSON.stringify(value));
function apply(s,event){
 const result=E.apply(s,event);
 assert.equal(result.ok,true,result.message);
 return result;
}
function reject(s,event){
 const before=copy(s);
 const result=E.apply(s,event);
 assert.equal(result.ok,false);
 assert.deepEqual(s,before);
 return result.message;
}
function work(s,id,op,value){return apply(s,{type:'work',id:'job:'+id,op,value});}
function move(s,room){if(s.room!==room)apply(s,{type:'move',room});}
function accept(s,id){move(s,'doctor');apply(s,{type:'action',id:'accept:'+id});assert.equal(s.jobs[id].revision,4);}
function restore(s){
 const serialized=JSON.stringify(s);
 assert.equal(E.supportsSave(JSON.parse(serialized)),true,serialized);
 const next=E.restore(JSON.parse(serialized));
 for(const field of ['jobs','cargo','world','mode','room','trip'])assert.deepEqual(next[field],s[field]);
 return next;
}
function claim(s,id,serial){
 if(s.mode==='trip')apply(s,{type:'switch'});
 move(s,'doctor');
 const result=apply(s,{type:'action',id:'claim:'+id});
 assert.deepEqual(result.reward,{kind:'job',job:id,id:id+':'+serial,...E.payouts[id]});
 reject(s,{type:'action',id:'claim:'+id});
}
const board=(s,id)=>E.workbench(s,'job:'+id);

test('D2 r4 preserves all evidence while reordering and rewards the corrected order once',()=>{
 let s=E.initial();
 accept(s,'d2');
 let sheet=board(s,'log');
 assert.equal(sheet.timelineMap,true);
 const unreadable=sheet.cards.find(card=>card.time===null);
 assert.equal(unreadable.reverseText,null);
 const beforeReverse=Navigation.guide(E,s,'d2');
 assert.equal(beforeReverse.room,'doctor');
 assert.match(beforeReverse.hint,/прочитайте оборот/);
 for(const room of ['407','406','408','Пост'])work(s,'log','place',sheet.cards.find(card=>card.room===room).id);
 assert.match(reject(s,{type:'work',id:'job:log',op:'submit'}),/оборот/);
 work(s,'log','readReverse',unreadable.id);
 sheet=board(s,'log');
 assert.equal(sheet.cards.length,4);
 assert.match(sheet.cards.find(card=>card.id===unreadable.id).reverseText,/407.*406/);
 assert.match(Navigation.guide(E,s,'d2').hint,/с учётом событий на обороте/);
 const misplaced=reject(s,{type:'work',id:'job:log',op:'submit'});
 assert.match(misplaced,/408.*его обороте/);
 assert.doesNotMatch(misplaced,/407|406/);
 const early=sheet.cards.find(card=>card.room==='407').id;
 work(s,'log','move',{id:early,direction:'down'});
 assert.match(reject(s,{type:'work',id:'job:log',op:'submit'}),/читаемым временем/);
 work(s,'log','move',{id:early,direction:'up'});
 s=restore(s);
 work(s,'log','move',{id:unreadable.id,direction:'up'});
 assert.match(work(s,'log','submit').message,/время.*не установлено/i);
 claim(restore(s),'d2',1);
});

function capture(s,subject,room,op){
 const offer=board(s,'baseline');
 assert.equal(offer.kind,'subjectChoice');
 assert.equal(offer.options.find(option=>option.id===subject).available,true);
 work(s,'baseline','chooseSubject',subject);
 assert.equal(E.jobStage(s,'d3').room,room);
 move(s,room);
 const initial=board(s,'baseline');
 assert.equal(initial.kind,'subjectBaseline');
 assert.deepEqual(initial.details,[]);
 reject(s,{type:'work',id:'job:baseline',op:'record'});
 work(s,'baseline',op);
 assert.ok(board(s,'baseline').details.length>0);
 work(s,'baseline','record');
 apply(s,{type:'switch'});
 if(s.room!==room)move(s,room);
 assert.equal(board(s,'difference').kind,'subjectDifference');
 assert.deepEqual(board(s,'difference').current,[]);
 reject(s,{type:'work',id:'job:difference',op:'submit'});
 work(s,'difference',op);
 return board(s,'difference');
}

test('D3 r4 sign needs two explicit readings and accepts a match or real differences without guessing',()=>{
 let s=E.initial();
 for(const cycle of [0,1,2]){
  accept(s,'d3');
  const options=board(s,'baseline').options;
  assert.deepEqual(options.filter(x=>x.available).map(x=>x.id),['signA']);
  assert.match(options.find(x=>x.id==='bed406').reason,/в Трипе.*секцию B/);
  assert.match(options.find(x=>x.id==='call407').reason,/в Трипе.*секцию C/);
  reject(s,{type:'work',id:'job:baseline',op:'chooseSubject',value:'bed406'});
  const evidence=capture(s,'signA','A','inspect');
  assert.deepEqual(evidence.current.map(x=>[x.id,x.value]),Object.entries(E.observation(s)));
  const changed=evidence.current.filter(row=>evidence.baseline.find(x=>x.id===row.id).value!==row.value);
  assert.equal(changed.length,[0,1,3][cycle]);
  const observedTrip=s.jobs.d3.work.observedTrip;
  s=restore(s);
  if(changed.length){
   work(s,'difference','noChanges');
   reject(s,{type:'work',id:'job:difference',op:'submit'});
   for(const row of changed)work(s,'difference','mark',row.id);
  } else work(s,'difference','noChanges');
  work(s,'difference','inspect');
  assert.equal(s.jobs.d3.work.observedTrip,observedTrip);
  work(s,'difference','submit');
  s=restore(s);
  claim(s,'d3',cycle+1);
  s=restore(s);
 }
});

test('D3 r4 optional bed fixture records a frozen linen order before a replacement',()=>{
 let s=E.initial();
 s.flags.unlockB=true;
 accept(s,'d3');
 assert.match(board(s,'baseline').options.find(x=>x.id==='bed406').reason,/поручению Клары.*квитанцию/);
 s.world.linen406={order:'k2:1',delivered:true,prepared:true,mark:'М',items:[{type:'Простыня',measure:'150 × 215 см'},{type:'Наволочка',measure:'70 × 70 см'}],reviewed:true,revision:5};
 capture(s,'bed406','ward406','lift');
 const prior=copy(s.jobs.d3.work);
 s.world.linen406.order='k2:2';
 s=restore(s);
 assert.deepEqual(s.jobs.d3.work,prior);
 assert.equal(s.jobs.d3.work.provenance.order,'k2:1');
 work(s,'difference','noChanges');
 work(s,'difference','submit');
 claim(s,'d3',1);
});

test('D3 r4 call fixture requires selecting no reply from readable text and rejects the wrong address',()=>{
 let s=E.initial();
 s.flags.unlockB=s.flags.unlockC=true;
 s.jobs.d3={active:false,count:2,done:{},revision:1,startTrip:0};
 accept(s,'d3');
 assert.match(board(s,'baseline').options.find(x=>x.id==='call407').reason,/407.*поручении врача.*контрольный вызов/);
 s.world.callEquipment.ward407={condition:'working',revision:1,verified:true};
 const evidence=capture(s,'call407','ward407','call');
 assert.equal(evidence.current.find(row=>row.id==='reply').value,'Ответа не было');
 assert.equal(evidence.current.find(row=>row.id==='indicator').value,'Горит');
 work(s,'difference','selectReply','ward407');
 reject(s,{type:'work',id:'job:difference',op:'submit'});
 work(s,'difference','selectReply','none');
 s=restore(s);
 work(s,'difference','submit');
 claim(s,'d3',3);
});

test('v10 issued D2 and D3 r3 keep their prior boards and partial evidence',()=>{
 const s=E.initial();
 s.version=10;
 s.room='doctor';
 s.jobs.d2={active:true,count:0,startTrip:0,revision:3,variant:0,done:{},work:{order:['entry-a','entry-b'],reverseRead:['entry-b']}};
 s.jobs.d3={active:true,count:0,startTrip:0,revision:3,variant:0,done:{},work:{baselineCaptured:false,marked:[],baseline:null,observed:null,observedTrip:null,noChanges:false}};
 assert.equal(E.supportsSave(s),true);
 const loaded=E.restore(copy(s));
 assert.deepEqual(loaded.jobs,s.jobs);
 assert.equal(board(loaded,'log').timelineMap,undefined);
 move(loaded,'A');
 assert.equal(board(loaded,'baseline').kind,'baseline');
 work(loaded,'baseline','record');
 apply(loaded,{type:'switch'});
 assert.equal(board(loaded,'difference').kind,'difference');
 assert.equal(board(loaded,'difference').observationCaptured,true);
});
