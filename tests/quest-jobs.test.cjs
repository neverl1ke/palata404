const {test}=require('node:test');
const a=require('node:assert/strict');
const E=require('../quest-engine.js');
const act=(s,id)=>E.apply(s,{type:'action',id});
const work=(s,id,op,value)=>E.apply(s,{type:'work',id,op,value});
const go=(s,room)=>{if(s.room===room)return;const r=E.apply(s,{type:'move',room});a.ok(r.ok,r.message);};
function accept(s,id){go(s,E.jobs[id].giver);const r=act(s,'accept:'+id);a.ok(r.ok,r.message);return s.jobs[id];}
function step(s,id,op,value){const r=work(s,id,op,value);a.ok(r.ok,r.message);return r;}
function solve(s,id){
 let b=E.workbench(s,id);a.ok(b,id+' board should be available');
 if(b.kind==='inspection'){
  for(const item of b.items)step(s,id,'inspect',item.id);
  b=E.workbench(s,id);const item=b.items.find(x=>x.details.kit===b.request.kit&&x.details.lot===b.request.lot&&x.details.seal==='целая');
  step(s,id,'select',item.id);return step(s,id,'submit');
 }
 if(b.kind==='packing'){
  for(const type of b.request.components){const item=b.items.find(x=>x.type===type&&x.size===b.request.size&&x.condition==='чистая упаковка');step(s,id,'select',item.id);}return step(s,id,'submit');
 }
 if(b.kind==='delivery')return step(s,id,'deliver');
 if(b.kind==='compare'){
  for(const x of b.documents[0].fields){const other=b.documents[1].fields.find(y=>y.id===x.id);if(x.value!==other.value)step(s,id,'mark',x.id);}return step(s,id,'submit');
 }
 if(b.kind==='diagnostic'){
  step(s,id,'inspect','connector');step(s,id,'test');b=E.workbench(s,id);
  const report=!b.connector.connected?'disconnected':b.indicator==='on'&&b.response.includes('вызов принят')?'working':'noResponse';step(s,id,'select',report);return step(s,id,'submit');
 }
 if(b.kind==='timeline'){for(const x of b.cards.slice().sort((x,y)=>x.time.localeCompare(y.time)))step(s,id,'place',x.id);return step(s,id,'submit');}
 if(b.kind==='baseline')return step(s,id,'record');
 if(b.kind==='difference'){for(const x of b.baseline)if(x.value!==b.current.find(y=>y.id===x.id).value)step(s,id,'mark',x.id);return step(s,id,'submit');}
 throw new Error('Unrecognized board '+b.kind);
}
function complete(s,id){
 if(id==='k1'){go(s,'procedure');solve(s,'job:tag');}
 if(id==='k2'){go(s,'linen');solve(s,'job:linen');go(s,'ward406');solve(s,'job:deliver');}
 if(id==='k3'){go(s,'procedure');solve(s,'job:copies');}
 if(id==='d1'){go(s,'ward407');solve(s,'job:bell407');go(s,'ward408');solve(s,'job:bell408');}
 if(id==='d2')solve(s,'job:log');
 if(id==='d3'){go(s,'A');solve(s,'job:baseline');a.ok(E.apply(s,{type:'switch'}).ok);solve(s,'job:difference');a.ok(E.apply(s,{type:'switch'}).ok);}
 go(s,E.jobs[id].giver);
}
for(const id of Object.keys(E.jobs))test('new '+id+' requires its distinct work, produces proof and pays only at submission',()=>{
 let s=E.initial();const j=accept(s,id);a.equal(j.revision,2);a.equal(s.version,7);const stored=JSON.stringify(s);s=E.restore(JSON.parse(stored));a.equal(JSON.stringify(s.jobs[id]),JSON.stringify(j));
 a.equal(act(s,'claim:'+id).ok,false);complete(s,id);a.ok(E.ready(s,id));a.equal(E.workbench(s,'job:'+E.jobs[id].steps.at(-1)),null);
 const proof=E.requiredCargo[id];for(const cargo of proof){a.ok(s.cargo.includes(cargo));a.ok(E.cargoDescription(s,cargo));}
 const result=act(s,'claim:'+id);a.ok(result.ok,result.message);a.deepEqual(result.reward,{kind:'job',job:id,id:id+':1',...E.payouts[id]});a.equal(s.jobs[id].count,1);a.equal(s.jobs[id].active,false);for(const cargo of proof)a.ok(!s.cargo.includes(cargo));a.equal(act(s,'claim:'+id).ok,false);
 const after=E.restore(JSON.parse(JSON.stringify(s)));a.equal(after.jobs[id].count,1);a.equal(E.ready(after,id),false);
});
test('inspection does not disclose unchecked details; wrong and old-answer bypasses cannot complete it',()=>{
 const s=E.initial();accept(s,'k1');go(s,'procedure');const b=E.workbench(s,'job:tag');a.ok(b.items.every(x=>x.details===null));
 for(const event of [{type:'interact',id:'job:tag',choice:'tag17'},{type:'action',id:'job:tag'},{type:'work',id:'job:tag',op:'submit'},{type:'work',id:'job:tag',op:'inspect',value:'not-a-container'}]){
  const before=JSON.stringify(s);a.equal(E.apply(s,event).ok,false);a.equal(JSON.stringify(s),before);
 }
 step(s,'job:tag','inspect',b.items[0].id);step(s,'job:tag','select',b.items[0].id);const before=JSON.stringify(s);a.equal(work(s,'job:tag','submit').ok,false);a.equal(JSON.stringify(s),before);a.ok(!s.cargo.includes('tag'));
 go(s,'ward405');a.equal(E.workbench(s,'job:tag'),null);a.equal(work(s,'job:tag','inspect',b.items[1].id).ok,false);
});
test('partial packing is restored exactly and the parcel is consumed only by delivery in 406',()=>{
 let s=E.initial();accept(s,'k2');go(s,'linen');const b=E.workbench(s,'job:linen'),item=b.items.find(x=>x.type==='Простыня'&&x.size===b.request.size&&x.condition==='чистая упаковка');step(s,'job:linen','select',item.id);
 const before=JSON.stringify(s);a.equal(work(s,'job:linen','submit').ok,false);a.equal(JSON.stringify(s),before);s=E.restore(JSON.parse(before));a.deepEqual(E.workbench(s,'job:linen').selected,[item.id]);
 const next=E.workbench(s,'job:linen').items.find(x=>x.type==='Наволочка'&&x.size===b.request.size&&x.condition==='чистая упаковка');step(s,'job:linen','select',next.id);step(s,'job:linen','submit');a.ok(s.cargo.includes('linen'));
 a.equal(work(s,'job:deliver','deliver').ok,false);a.ok(s.cargo.includes('linen'));go(s,'ward406');step(s,'job:deliver','deliver');a.ok(!s.cargo.includes('linen'));a.ok(s.cargo.includes('delivery'));a.equal(work(s,'job:deliver','deliver').ok,false);
});
test('diagnostics require observed connection and signal; classification is absent before testing',()=>{
 const s=E.initial();accept(s,'d1');go(s,'ward407');let b=E.workbench(s,'job:bell407');a.equal(b.connector,null);a.equal(b.response,null);a.equal(b.indicator,'idle');
 for(const [op,value]of [['test'],['report','working'],['inspect','other']]){const before=JSON.stringify(s);a.equal(work(s,'job:bell407',op,value).ok,false);a.equal(JSON.stringify(s),before);}
 step(s,'job:bell407','inspect','connector');b=E.workbench(s,'job:bell407');a.ok(b.connector.connected);a.equal(b.response,null);step(s,'job:bell407','test');a.match(E.workbench(s,'job:bell407').response,/вызов принят/);
 const before=JSON.stringify(s);a.equal(work(s,'job:bell407','report','disconnected').ok,false);a.equal(JSON.stringify(s),before);step(s,'job:bell407','report','working');a.ok(s.cargo.includes('bell407'));
});
test('wrong comparison fields and chronology do not advance or consume evidence',()=>{
 const s=E.initial();accept(s,'k3');go(s,'procedure');step(s,'job:copies','mark','time');let before=JSON.stringify(s);a.equal(work(s,'job:copies','submit').ok,false);a.equal(JSON.stringify(s),before);
 accept(s,'d2');const b=E.workbench(s,'job:log');for(const card of b.cards)step(s,'job:log','place',card.id);before=JSON.stringify(s);a.equal(work(s,'job:log','submit').ok,false);a.equal(JSON.stringify(s),before);
 const first=b.cards[0].id;step(s,'job:log','move',{id:first,direction:'down'});a.notDeepEqual(E.workbench(s,'job:log').order,b.cards.map(x=>x.id));
});
test('new observation requires Patient baseline and a later Trip, with actual scene matching both cards',()=>{
 let s=E.initial();accept(s,'d3');a.ok(!s.cargo.includes('baseline'));go(s,'A');let b=E.workbench(s,'job:baseline');a.deepEqual(Object.fromEntries(b.details.map(x=>[x.id,x.value])),E.observation(s));
 E.apply(s,{type:'switch'});a.equal(E.workbench(s,'job:difference'),null);E.apply(s,{type:'switch'});step(s,'job:baseline','record');a.ok(s.cargo.includes('baseline'));a.equal(E.workbench(s,'job:difference'),null);
 s=E.restore(JSON.parse(JSON.stringify(s)));a.ok(s.jobs.d3.work.baselineCaptured);a.match(E.cargoDescription(s,'baseline'),/08:00/);E.apply(s,{type:'switch'});b=E.workbench(s,'job:difference');a.deepEqual(Object.fromEntries(b.current.map(x=>[x.id,x.value])),E.observation(s));
 const before=JSON.stringify(s);a.equal(work(s,'job:difference','submit').ok,false);a.equal(JSON.stringify(s),before);solve(s,'job:difference');a.ok(!s.cargo.includes('baseline'));a.ok(s.cargo.includes('difference'));
});
test('engine fallback guidance requires a new observation baseline while legacy cards keep their issued baseline',()=>{
 const s=E.initial();accept(s,'d3');
 let guide=E.guide(s,'d3');a.equal(guide.mode,'patient');a.equal(guide.room,'A');a.match(guide.text,/первич|исходн/i);
 go(s,'A');solve(s,'job:baseline');guide=E.guide(s,'d3');a.equal(guide.mode,'trip');a.equal(guide.room,'A');
 a.ok(E.apply(s,{type:'switch'}).ok);guide=E.guide(s,'d3');a.equal(guide.mode,'trip');a.equal(guide.room,'A');a.ok(E.workbench(s,'job:difference'));
 const legacy=E.restore({version:6,mode:'patient',room:'doctor',jobs:{d3:{active:true,done:{},count:0,startTrip:0}},cargo:['baseline']});
 a.equal(legacy.jobs.d3.revision,1);guide=E.guide(legacy,'d3');a.equal(guide.mode,'trip');a.match(guide.text,/Коридор A/);
 a.ok(E.apply(legacy,{type:'switch'}).ok);go(legacy,'A');guide=E.guide(legacy,'d3');a.equal(guide.mode,'trip');a.equal(guide.room,'A');a.ok(E.actions(legacy).some(x=>x.id==='job:difference'));
});
test('versions 1–6 retain old active progress and their final legacy step; next repeat uses new work',()=>{
 for(let version=1;version<=6;version++){
  const raw={version,mode:'patient',room:'ward406',jobs:{k2:{active:true,done:{linen:true},count:2,startTrip:0,revision:2,variant:2,work:{selected:['linen-1']}}},cargo:['linen'],flags:{unlockB:true,unlockC:true}};const bytes=JSON.stringify(raw);let s=E.restore(raw);a.equal(JSON.stringify(raw),bytes);a.equal(s.jobs.k2.revision,1);a.equal(s.jobs.k2.count,2);a.equal(s.jobs.k2.done.linen,true);a.equal(E.workbench(s,'job:deliver'),null);
  a.ok(E.apply(s,{type:'interact',id:'job:deliver',choice:'bed'}).ok);go(s,'nurse');a.ok(act(s,'claim:k2').ok);a.ok(act(s,'accept:k2').ok);a.equal(s.jobs.k2.revision,2);a.equal(s.jobs.k2.count,3);a.equal(s.flags.unlockB,true);a.equal(s.flags.unlockC,true);
 }
 const s=E.restore({version:6,mode:'patient',room:'nurse',jobs:{k1:{active:false,done:{tag:true},count:1}},cargo:[]});a.equal(act(s,'accept:k1').ok,false);a.equal(s.jobs.k1.count,1);
});
test('repeat work variants are stable across reload and only change when a new assignment is accepted',()=>{
 let s=E.initial();accept(s,'k2');const first=s.jobs.k2.variant;complete(s,'k2');a.ok(act(s,'claim:k2').ok);a.ok(act(s,'accept:k2').ok);a.notEqual(s.jobs.k2.variant,first);const next=s.jobs.k2.variant;s=E.restore(JSON.parse(JSON.stringify(s)));a.equal(s.jobs.k2.variant,next);go(s,'linen');a.equal(E.workbench(s,'job:linen').request.size,'Л');
});
test('new work fields are bounded and cannot auto-complete from unknown or malformed input',()=>{
 const s=E.restore({version:7,mode:'patient',room:'procedure',jobs:{k1:{revision:2,active:true,count:0,variant:999999,done:{unknown:true},work:{inspected:['pack-0','pack-0','intruder'],selected:['intruder'],complete:true,answer:'tag'}}},cargo:[]});a.deepEqual(s.jobs.k1.work.inspected,['pack-0']);a.deepEqual(s.jobs.k1.work.selected,[]);a.deepEqual(s.jobs.k1.done,{});a.equal(E.ready(s,'k1'),false);a.equal(work(s,'job:tag','submit').ok,false);a.ok(!s.cargo.includes('tag'));
});

test('unsupported work revisions and malformed operation IDs are rejected safely',()=>{
 a.equal(E.supportsSave({version:7,jobs:{k1:{revision:3}}}),false);a.equal(E.supportsSave({version:8}),false);a.equal(E.supportsSave({version:6,jobs:{k1:{revision:3}}}),true);a.equal(E.supportsSave({version:7,jobs:{k1:{revision:2,variant:0,work:{}}}}),true);
 a.equal(E.supportsSave({version:7,jobs:{k1:{revision:2,variant:3,work:{}}}}),false);a.equal(E.supportsSave({version:7,jobs:{k1:{revision:2,variant:0}}}),false);
 a.equal(E.supportsSave({version:7,jobs:{futureJob:{revision:1}}}),false);a.equal(E.supportsSave({version:7,jobs:[]}),false);
 const s=E.initial();accept(s,'k1');go(s,'procedure');const before=JSON.stringify(s);for(const id of [null,5,{},[]]){a.equal(E.workbench(s,id),null);a.equal(E.apply(s,{type:'work',id,op:'submit'}).ok,false);a.equal(JSON.stringify(s),before);}
});

test('all three repeat variants can be solved from evidence and survive every board reload',()=>{
 for(const id of ['k2','d1','d3']){
  let s=E.initial();
  for(let round=0;round<3;round++){
   accept(s,id);a.equal(s.jobs[id].variant,round);s=E.restore(JSON.parse(JSON.stringify(s)));complete(s,id);a.ok(E.ready(s,id));a.ok(act(s,'claim:'+id).ok);a.equal(s.jobs[id].count,round+1);s=E.restore(JSON.parse(JSON.stringify(s)));
  }
 }
});

test('unrecognized version7 job shapes are rejected without altering the original save',()=>{
 for(const value of [null,'future shape',[],false,0,7]){
  const raw={version:7,mode:'patient',room:'nurse',jobs:{k2:value},cargo:['linen'],transaction:42},before=JSON.stringify(raw);
  a.equal(E.supportsSave(raw),false);a.equal(JSON.stringify(raw),before);
 }
 const valid=E.initial();accept(valid,'k2');a.equal(E.supportsSave(valid),true);
});
