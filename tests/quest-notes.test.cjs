'use strict';
// The notebook is a view of persisted evidence, not a second route to a result.
const {test}=require('node:test');
const a=require('node:assert/strict');
const E=require('../quest-engine.js');
const W=require('../quest-job-model.js');
const N=require('../quest-notes.js');
const solver=require('./quest-workbench-solver.cjs');
const clone=value=>JSON.parse(JSON.stringify(value));
const text=records=>JSON.stringify(records);
function apply(s,event){const result=E.apply(s,event);a.equal(result.ok,true,result.message);return result;}
function go(s,room){if(s.room!==room)apply(s,{type:'move',room});}
function accept(s,id){if(s.mode!=='patient')apply(s,{type:'switch'});go(s,E.jobs[id].giver);apply(s,{type:'action',id:'accept:'+id});}
function work(s,id,op,value){const result=apply(s,{type:'work',id,op,value});a.equal(result.reward,undefined,'reading or performing work cannot award an extra payout');return result;}
function solve(s,id){for(let i=0;i<50;i++){const board=E.workbench(s,id);if(!board)return;const next=solver.nextOperation(board);a.ok(!next.navigate,'this fixture deliberately avoids shortage redirects');work(s,id,next.op,next.value);}a.fail('work did not finish '+id);}
function notes(s,id){const before=JSON.stringify(s),out=N.forQuest(E,W,s,id);a.equal(JSON.stringify(s),before,'reading notes changed raw state');return out;}
function deepFrozen(value){if(value&&typeof value==='object'){a.equal(Object.isFrozen(value),true);for(const child of Object.values(value))deepFrozen(child);}}
function record(s,id,key){return notes(s,id).find(item=>item.id===key);}

test('an unworked accepted order reveals no hidden source or generated observation',()=>{
 for(const id of ['k1','k2','k3','d1','d2','d3']){
  const s=E.initial();accept(s,id);const before=JSON.stringify(s);
  const guardedEngine={...E,cargoDescription(){throw Error('unearned cargo description');}};
  const guardedWork={...W,observation(){throw Error('generated observation');},board(){throw Error('an unworked order has no inspected board');}};
  a.deepEqual(N.forQuest(guardedEngine,guardedWork,s,id),[],id);
  a.equal(JSON.stringify(s),before);
 }
 const initial=E.initial();for(const id of ['unknown','k1','С1','С2','П3','С3','С4'])a.deepEqual(notes(initial,id),[]);
});

test('K1 copies only inspected markings and does not treat a selected unopened pack as observed',()=>{
 const s=E.initial();accept(s,'k1');go(s,'procedure');work(s,'job:tag','select','pack-0');a.deepEqual(notes(s,'k1'),[]);
 work(s,'job:tag','inspect','pack-1');const board=E.workbench(s,'job:tag'),inspected=board.items.find(item=>item.id==='pack-1');
 const out=notes(s,'k1');a.equal(out.filter(item=>item.id.startsWith('pack-')).length,1);
 const pack=out.find(item=>item.id==='pack-1');a.ok(pack);a.equal(pack.status,'recorded');
 for(const value of Object.values(inspected.details))a.ok(text(pack).includes(value));
 a.equal(out.some(item=>item.id==='pack-0'),false);
 const again=E.restore(clone(s));a.deepEqual(notes(again,'k1'),out);deepFrozen(out);
});

test('D1 connector inspection, actual test and draft diagnosis have separate provenance',()=>{
 const s=E.initial();accept(s,'d1');go(s,'ward407');a.deepEqual(notes(s,'d1'),[]);
 work(s,'job:bell407','inspect','connector');const inspected=record(s,'d1','diagnostic:407');a.ok(inspected);a.equal(inspected.fields.length,1);
 a.equal(inspected.fields[0].value,E.workbench(s,'job:bell407').connector.text);a.equal(inspected.status,'recorded');
 work(s,'job:bell407','test');const b=E.workbench(s,'job:bell407'),tested=record(s,'d1','diagnostic:407');
 a.equal(tested.fields.length,3);a.ok(text(tested).includes(b.response));a.notDeepEqual(inspected,tested);
 const selected=b.reports.find(item=>item.id==='working');work(s,'job:bell407','select',selected.id);
 const draft=record(s,'d1','report-draft:407');a.equal(draft.status,'draft');a.equal(draft.text,selected.label);a.equal(record(s,'d1','diagnostic:407').status,'recorded');
 solve(s,'job:bell407');a.equal(record(s,'d1','diagnostic:407').status,'confirmed');a.equal(record(s,'d1','report-draft:407'),undefined);
});

test('D1 service evidence and retest responses appear only after their real actions',()=>{
 const s=E.initial();accept(s,'d1');
 for(const room of ['ward407','ward408']){go(s,room);solve(s,'job:bell'+room.slice(4));}
 go(s,'doctor');work(s,'job:callReview','authorize');a.ok(record(s,'d1','authorization'));
 const stage=E.jobStage(s,'d1'),suffix=stage.action.slice(-3);go(s,stage.room);
 a.equal(record(s,'d1','service-source:'+suffix),undefined);
 a.equal(record(s,'d1','retest:'+suffix),undefined);
 work(s,stage.action,'inspectEvidence');const board=E.workbench(s,stage.action),source=record(s,'d1','service-source:'+suffix);a.ok(source);
 for(const key of ['equipmentId','connector','postAddress'])a.ok(text(source).includes(board.evidence[key]));
 const correct=board.options.find(option=>['equipmentId','connector','postAddress'].every(key=>option[key]===board.evidence[key]));
 work(s,stage.action,'select',correct.id);a.equal(record(s,'d1','service:'+suffix),undefined,'selection must not imply performed service');
 work(s,stage.action,'submit');a.ok(record(s,'d1','service:'+suffix));a.equal(record(s,'d1','retest:'+suffix),undefined);
 go(s,'ward'+suffix);work(s,'job:callRetest'+suffix,'test');a.equal(record(s,'d1','retest:'+suffix).status,'recorded');
 work(s,'job:callRetest'+suffix,'confirm');a.equal(record(s,'d1','retest:'+suffix).status,'confirmed');
});

test('D2 retains only chosen leaflets or explicitly read reverses and never invents obscured time',()=>{
 const s=E.initial();accept(s,'d2');a.deepEqual(notes(s,'d2'),[]);
 const board=E.workbench(s,'job:log'),card=board.cards.find(item=>item.time!==null);work(s,'job:log','place',card.id);
 let out=notes(s,'d2');a.equal(out.filter(item=>!item.id.includes(':')).length,1);a.ok(text(out).includes(card.time));a.equal(out.some(item=>item.id==='entry-b:reverse'),false);
 work(s,'job:log','readReverse','entry-b');out=notes(s,'d2');const reverse=out.find(item=>item.id==='entry-b:reverse');a.ok(reverse);a.ok(reverse.text.includes('после')||reverse.text.includes('После'));
 const unreadable=out.find(item=>item.id==='entry-b');a.ok(unreadable.fields.some(field=>field.label==='Время'&&field.value==='Не установлено'));
 a.deepEqual(notes(E.restore(clone(s)),'d2'),out);
});

test('D3 uses actual frozen snapshots and cannot create a repeat observation by reading notes',()=>{
 const s=E.initial();accept(s,'d3');go(s,'A');a.deepEqual(notes(s,'d3'),[]);
 work(s,'job:baseline','record');const initial=notes(s,'d3');a.equal(initial.length,1);a.equal(initial[0].id,'baseline');a.equal(record(s,'d3','observed'),undefined);
 go(s,'ward404');apply(s,{type:'switch'});a.deepEqual(notes(s,'d3'),initial);a.equal(s.jobs.d3.work.observed,null);
 go(s,'A');const out=notes(s,'d3');a.equal(out.length,2);a.ok(record(s,'d3','observed'));
 a.deepEqual(Object.values(s.jobs.d3.work.observed).sort(),record(s,'d3','observed').fields.map(field=>field.value).sort());
 a.deepEqual(notes(E.restore(clone(s)),'d3'),out);deepFrozen(out);
});

test('K2 notes distinguish selected drafts, packed kit, placed bedding and staff-approved substitution',()=>{
 const s=E.initial();accept(s,'k2');go(s,'linen');work(s,'job:linen','select','linen-0');
 const selected=record(s,'k2','linen-0');a.ok(selected);a.equal(selected.status,'draft');a.equal(record(s,'k2','result:linen'),undefined);
 solve(s,'job:linen');a.equal(record(s,'k2','linen-0').status,'confirmed');a.ok(record(s,'k2','result:linen'));a.equal(record(s,'k2','result:deliver'),undefined);
 go(s,'ward406');work(s,'job:deliver','startBedPreparation');work(s,'job:deliver','selectPiece','sheet');work(s,'job:deliver','place','sheetZone');
 a.match(record(s,'k2','bed').text,/Простыня/);a.doesNotMatch(record(s,'k2','bed').text,/Наволочка/);a.equal(record(s,'k2','result:deliver'),undefined);
 solve(s,'job:deliver');a.ok(record(s,'k2','result:deliver'));go(s,'nurse');apply(s,{type:'action',id:'claim:k2'});
 accept(s,'k2');a.deepEqual(notes(s,'k2'),[]);go(s,'linen');work(s,'job:linen','noteShortage');a.ok(record(s,'k2','shortage'));a.equal(record(s,'k2','reserve'),undefined);
 go(s,'nurse');work(s,'job:linenReserve','select','reserve-same-size');a.equal(record(s,'k2','reserve'),undefined);
 work(s,'job:linenReserve','submit');a.equal(record(s,'k2','reserve').status,'confirmed');a.match(record(s,'k2','reserve').text,/70 × 70 см/);
});

test('K3 drafts do not expose unseen source values or manufacture a confirmed discrepancy',()=>{
 const s=E.initial();accept(s,'k3');go(s,'procedure');a.deepEqual(notes(s,'k3'),[]);
 work(s,'job:copies','mark','time');const out=notes(s,'k3');a.equal(out.length,1);a.equal(out[0].status,'draft');a.match(out[0].text,/Время/);
 a.doesNotMatch(text(out),/09:15|Б-17|Клара/);a.equal(out.some(item=>item.status==='confirmed'),false);
 solve(s,'job:copies');const confirmed=notes(s,'k3');a.equal(confirmed.length,1);a.equal(confirmed[0].status,'confirmed');a.match(confirmed[0].text,/подпись/i);
});

test('story notebook follows completed interaction steps, not debug access or unrelated unlock flags',()=>{
 const s=E.initial();apply(s,{type:'unlockAll'});for(const id of ['С1','С2','П3','С3','П4','С4'])a.deepEqual(notes(s,id),[]);
 go(s,'A');apply(s,{type:'interact',id:'inspectDoor',choice:'door'});
 let out=notes(s,'С1');a.equal(out.length,1);a.equal(out[0].text,E.interactions.inspectDoor.steps[0].text);a.equal(out.some(item=>item.text===E.interactions.inspectDoor.steps[1].text),false);
 apply(s,{type:'interact',id:'inspectDoor',choice:'door'});out=notes(s,'С1');a.equal(out.length,2);a.equal(out[1].text,E.interactions.inspectDoor.steps[1].text);
 a.deepEqual(notes(E.restore(clone(s)),'С1'),out);a.deepEqual(notes(s,'П3'),[]);
});

test('completed current work remains readable after payout; accepting a new repeat replaces it honestly',()=>{
 const s=E.initial();accept(s,'d3');go(s,'A');work(s,'job:baseline','record');apply(s,{type:'switch'});solve(s,'job:difference');apply(s,{type:'switch'});go(s,'doctor');
 const before=notes(s,'d3');a.ok(before.some(item=>item.status==='confirmed'));const paid=apply(s,{type:'action',id:'claim:d3'});a.deepEqual(paid.reward,{kind:'job',job:'d3',id:'d3:1',...E.payouts.d3});
 a.deepEqual(notes(s,'d3'),before);a.deepEqual(notes(E.restore(clone(s)),'d3'),before);
 accept(s,'d3');a.deepEqual(notes(s,'d3'),[]);a.equal(s.jobs.d3.count,1);a.equal(s.jobs.d3.variant,1);
});

test('legacy job progress is not enough to reconstruct missing detailed evidence',()=>{
 const raw={version:6,mode:'patient',room:'doctor',jobs:{d3:{active:true,done:{},count:0,startTrip:0}},cargo:['baseline'],flags:{unlockB:true,unlockC:true}};
 const serialized=JSON.stringify(raw),s=E.restore(raw);a.equal(s.jobs.d3.revision,1);a.deepEqual(notes(s,'d3'),[]);a.equal(JSON.stringify(raw),serialized);
 const revision2=E.restore({version:7,mode:'patient',room:'doctor',jobs:{d3:{active:true,done:{baseline:true},count:0,startTrip:0,revision:2,variant:0,work:{baselineCaptured:true,marked:[]}}},cargo:['baseline']});
 const out=notes(revision2,'d3');a.equal(out.length,1);a.doesNotMatch(text(out),/08:00|Палаты 404–406|03:00/);a.match(out[0].text,/старом формате/);
});

test('all nested notebook records are immutable copies and repeated reads do not advance evidence or economy',()=>{
 const s=E.initial();accept(s,'k1');go(s,'procedure');work(s,'job:tag','inspect','pack-1');const before=JSON.stringify(s),out=notes(s,'k1');deepFrozen(out);
 a.throws(()=>out.push({}),TypeError);a.throws(()=>{out[0].fields[0].value='tampered';},TypeError);
 for(let i=0;i<20;i++)a.deepEqual(notes(s,'k1'),out);
 a.equal(JSON.stringify(s),before);a.equal(s.transaction,0);a.deepEqual(s.cargo,[]);a.deepEqual(s.jobs.k1.done,{});a.equal(s.jobs.k1.count,0);
});
