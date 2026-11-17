const {test}=require('node:test');
const a=require('node:assert/strict');
const E=require('../quest-engine.js');
const W=require('../quest-job-model.js');
const act=(s,id)=>E.apply(s,{type:'action',id});
const work=(s,id,op,value)=>E.apply(s,{type:'work',id,op,value});
const go=(s,room)=>{if(s.room===room)return;const r=E.apply(s,{type:'move',room});a.ok(r.ok,r.message);};
function accept(s,id){go(s,E.jobs[id].giver);const r=act(s,'accept:'+id);a.ok(r.ok,r.message);return s.jobs[id];}
function step(s,id,op,value){const r=work(s,id,op,value);a.ok(r.ok,r.message);return r;}
function solve(s,id){
 const {nextOperation}=require('./quest-workbench-solver.cjs');let result;
 a.ok(E.workbench(s,id),id+' board should be available');
 for(let count=0;count<60;count++){
  const board=E.workbench(s,id);if(!board)return result;
  a.deepEqual(board.brief,E.jobBrief(board.jobId));const operation=nextOperation(board);
  if(operation.navigate){go(s,operation.navigate);solve(s,operation.action);go(s,operation.resumeRoom);continue;}
  result=step(s,id,operation.op,operation.value);
 }
 throw Error('Work surface did not finish '+id);
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
 let s=E.initial();const j=accept(s,id);a.equal(j.revision,['k2','d1'].includes(id)?3:2);a.equal(s.version,8);const stored=JSON.stringify(s);s=E.restore(JSON.parse(stored));a.equal(JSON.stringify(s.jobs[id]),JSON.stringify(j));
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
 a.equal(work(s,'job:deliver','deliver').ok,false);a.ok(s.cargo.includes('linen'));go(s,'ward406');solve(s,'job:deliver');a.ok(!s.cargo.includes('linen'));a.ok(s.cargo.includes('delivery'));a.equal(work(s,'job:deliver','deliver').ok,false);
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
  a.ok(E.apply(s,{type:'interact',id:'job:deliver',choice:'bed'}).ok);go(s,'nurse');a.ok(act(s,'claim:k2').ok);a.ok(act(s,'accept:k2').ok);a.equal(s.jobs.k2.revision,3);a.equal(s.jobs.k2.count,3);a.equal(s.flags.unlockB,true);a.equal(s.flags.unlockC,true);
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
 a.equal(E.supportsSave({version:7,jobs:{k1:{revision:3}}}),false);a.equal(E.supportsSave({version:9}),false);a.equal(E.supportsSave({version:6,jobs:{k1:{revision:3}}}),true);a.equal(E.supportsSave({version:7,jobs:{k1:{revision:2,variant:0,work:{}}}}),true);
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

test('every commission states its hospital purpose and actual deliverable without changing rewards',()=>{
 for(const id of Object.keys(E.jobs)){
  const brief=E.jobBrief(id);a.ok(brief.giver.length);a.ok(brief.purpose.length);a.ok(brief.deliverable.length);
  const copy=E.jobBrief(id);copy.purpose='external change';a.equal(E.jobBrief(id).purpose,brief.purpose);
  const s=E.initial();go(s,E.jobs[id].giver);const result=act(s,'accept:'+id);a.ok(result.ok);
  a.ok(result.message.includes(brief.purpose));a.ok(result.message.includes(brief.deliverable));a.equal(result.reward,null);
 }
 for(const id of [null,{},'__proto__','not-a-job'])a.equal(E.jobBrief(id),null);
});

test('issued container variants retain target IDs and use unambiguous named evidence',()=>{
 for(const [variant,target]of [[0,'pack-1'],[1,'pack-3'],[2,'pack-0']]){
  let s=E.restore({version:7,mode:'patient',room:'procedure',jobs:{k1:{active:true,revision:2,variant,count:0,done:{},work:{inspected:['pack-0','pack-1','pack-2','pack-3'],selected:[target]}}},cargo:[]});
  const b=E.workbench(s,'job:tag');const matches=b.items.filter(x=>x.details.kit===b.request.kit&&x.details.lot===b.request.lot&&x.details.seal==='целая');
  a.deepEqual(matches.map(x=>x.id),[target]);a.ok(b.items.every(x=>!x.details.kit.includes('Другой')&&!x.details.lot.includes('резерв')));
  const before=JSON.stringify(s);s=E.restore(JSON.parse(before));a.deepEqual(E.workbench(s,'job:tag'),b);
  const result=step(s,'job:tag','submit');a.ok(result.message.includes(E.cargoDescription(s,'tag')));a.ok(result.message.includes(E.cargoCatalog.tag.name));
 }
});

test('failed checks explain observed evidence without revealing untouched containers or changing work',()=>{
 const s=E.initial();accept(s,'k1');go(s,'procedure');step(s,'job:tag','inspect','pack-0');step(s,'job:tag','select','pack-0');
 const before=JSON.stringify(s),result=work(s,'job:tag','submit');a.equal(result.ok,false);a.match(result.message,/партия на осмотренной упаковке отличается/);a.equal(JSON.stringify(s),before);
 const b=E.workbench(s,'job:tag');a.ok(b.items.filter(x=>x.id!=='pack-0').every(x=>x.details===null));a.ok(!result.message.includes('pack-1'));
 accept(s,'k2');go(s,'linen');const packing=E.workbench(s,'job:linen');a.match(packing.request.markingNote,/учётная маркировка/);a.ok(packing.items.every(x=>/см$/.test(x.measure)));
 step(s,'job:linen','select','linen-0');const selected=JSON.stringify(s),incomplete=work(s,'job:linen','submit');a.equal(incomplete.ok,false);a.match(incomplete.message,/выбрано вещей: 1 из 2/);a.equal(JSON.stringify(s),selected);
});

test('completed work preserves concrete findings alongside the inventory receipt for every commission',()=>{
 for(const id of Object.keys(E.jobs)){
  const s=E.initial();accept(s,id);complete(s,id);
  for(const cargo of E.requiredCargo[id]){
   const description=E.cargoDescription(s,cargo);a.ok(description);a.ok(s.log.some(message=>message.includes(description)),id+' '+cargo+' must retain observed findings');
   a.ok(s.log.some(message=>message.includes(E.cargoCatalog[cargo].name)),id+' '+cargo+' must name its receipt');
  }
  a.ok(s.log.every(message=>message.length<=500),'current persisted receipt limit must preserve complete work feedback');
 }
});

test('delivery describes the actual accepted parcel and exposes no invented contents without cargo',()=>{
 for(let variant=0;variant<3;variant++){
  let s=E.restore({version:7,mode:'patient',room:'linen',jobs:{k2:{active:true,revision:2,variant,count:variant,done:{},work:{selected:[]}}},cargo:[]});
  const packing=E.workbench(s,'job:linen'),contents=packing.items.filter(x=>x.size===packing.request.size&&x.condition==='чистая упаковка');
  for(const item of contents)step(s,'job:linen','select',item.id);step(s,'job:linen','submit');s=E.restore(JSON.parse(JSON.stringify(s)));go(s,'ward406');
  const b=E.workbench(s,'job:deliver');a.equal(b.parcel,true);a.deepEqual(b.parcelDetails,{components:packing.request.components,size:packing.request.size,items:contents.map(x=>({type:x.type,measure:x.measure}))});
  const bytes=JSON.stringify(s);b.parcelDetails.components.push('invented');a.equal(JSON.stringify(s),bytes);
  const absent=E.restore(JSON.parse(bytes));absent.cargo=[];a.equal(E.workbench(absent,'job:deliver'),null);a.equal(W.board(absent,'job:deliver').parcel,false);a.equal(W.board(absent,'job:deliver').parcelDetails,undefined);
 }
});

test('every two-item linen combination requires distinct matching clean components in all variants',()=>{
 for(let variant=0;variant<3;variant++){
  const fresh=()=>E.restore({version:7,mode:'patient',room:'linen',jobs:{k2:{active:true,revision:2,variant,count:variant,done:{},work:{selected:[]}}},cargo:[]});
  const b=E.workbench(fresh(),'job:linen');let accepted=0;
  for(let left=0;left<b.items.length;left++)for(let right=left+1;right<b.items.length;right++){
   const pair=[b.items[left],b.items[right]],s=fresh();s.jobs.k2.work.selected=pair.map(x=>x.id);
   const expected=b.request.components.every(type=>pair.some(x=>x.type===type&&x.size===b.request.size&&x.condition==='чистая упаковка'));
   const before=JSON.stringify(s),result=work(s,'job:linen','submit');a.equal(result.ok,expected,variant+' '+pair.map(x=>x.id).join(','));
   if(expected){accepted++;a.deepEqual(s.cargo,['linen']);a.equal(s.jobs.k2.done.linen,true);a.equal(result.reward,undefined);}
   else{a.equal(JSON.stringify(s),before);if(pair[0].type===pair[1].type)a.match(result.message,/два разных предмета/);}
  }
  a.equal(accepted,1,'exactly one physically usable pair in each current catalogue');
 }
});
