'use strict';
const {test}=require('node:test');
const a=require('node:assert/strict');
const E=require('../quest-engine.js');
const W=require('../quest-job-model.js');
const N=require('../quest-notes.js');
const clone=value=>JSON.parse(JSON.stringify(value));
function apply(s,event){const result=E.apply(s,event);a.equal(result.ok,true,result.message);return result;}
function go(s,room){if(s.room!==room)apply(s,{type:'move',room});}
function accepted(){const s=E.initial();go(s,'nurse');apply(s,{type:'action',id:'accept:k3'});go(s,'procedure');a.equal(s.jobs.k3.revision,3);return s;}
function work(s,op,value){const result=apply(s,{type:'work',id:'job:copies',op,value});a.equal(result.reward,undefined);return result;}
function notes(s){const before=JSON.stringify(s),out=N.forQuest(E,W,s,'k3');a.equal(JSON.stringify(s),before,'copying sources must not alter progress');return out;}
function confirmed(s){work(s,'readSources');for(const [field,choice]of Object.entries({room:'differs',time:'matchesActual',author:'unknown'}))work(s,'conclude',{field,choice});work(s,'submit');}
function frozen(value){if(value&&typeof value==='object'){a.equal(Object.isFrozen(value),true);Object.values(value).forEach(frozen);}}

test('accepted K3 notes cannot read sources, create conclusions or mark themselves seen',()=>{
 const s=accepted(),before=JSON.stringify(s);
 const guardedWork={...W,board(){throw Error('unopened case source lookup');}};
 const guardedEngine={...E,cargoDescription(){throw Error('unearned receipt');},apply(){throw Error('notes must not dispatch work');}};
 for(let i=0;i<5;i++)a.deepEqual(N.forQuest(guardedEngine,guardedWork,s,'k3'),[]);
 a.equal(JSON.stringify(s),before);a.equal(s.jobs.k3.work.sourcesRead,false);a.deepEqual(s.jobs.k3.work.conclusions,{});a.deepEqual(s.cargo,[]);
});

test('an actual case-source opening copies exactly all three documents without automatic conclusions',()=>{
 const s=accepted();work(s,'readSources');const before=JSON.stringify(s),board=E.workbench(s,'job:copies'),out=notes(s);
 a.equal(out.length,3);a.deepEqual(out.map(record=>record.id),board.documents.map(document=>document.id));
 for(const document of board.documents){const record=out.find(item=>item.id===document.id);a.equal(record.title,document.title);a.equal(record.status,'recorded');a.deepEqual(record.fields,document.fields.map(field=>({label:field.label,value:String(field.value)})));}
 a.deepEqual(s.jobs.k3.work.conclusions,{});a.equal(s.jobs.k3.done.copies,undefined);a.equal(JSON.stringify(s),before);a.equal(out.some(record=>record.status==='confirmed'),false);frozen(out);
});

test('a wrong case conclusion remains explicitly a draft and cannot alter unreadable source facts',()=>{
 const s=accepted();work(s,'readSources');work(s,'conclude',{field:'author',choice:'clara'});const out=notes(s);
 const draft=out.find(record=>record.id==='draft:author');a.ok(draft);a.equal(draft.status,'draft');a.match(draft.text,/не подтверждён/);a.equal(out.some(record=>record.status==='confirmed'),false);
 const original=out.find(record=>record.id==='source-2');a.ok(original.fields.some(field=>field.label==='Подпись'&&field.value==='Неразборчива'));
 const before=JSON.stringify(s),result=E.apply(s,{type:'work',id:'job:copies',op:'submit'});a.equal(result.ok,false);a.equal(JSON.stringify(s),before);a.deepEqual(notes(s),out);a.deepEqual(s.cargo,[]);
});

test('confirmed case notes preserve the qualified result before and after the unchanged single payout and reload',()=>{
 let s=accepted();confirmed(s);const out=notes(s);a.equal(out.length,4);a.equal(out.some(record=>record.id.startsWith('draft:')),false);
 const result=out.find(record=>record.id==='result:copies');a.equal(result.status,'confirmed');a.equal(result.text,E.cargoDescription(s,'copies'));a.match(result.text,/не подтверждено оригиналом/);a.match(result.text,/перенесено верно/);
 const before=JSON.stringify(s);for(let i=0;i<10;i++)a.deepEqual(notes(s),out);a.equal(JSON.stringify(s),before);
 go(s,'nurse');const payout=apply(s,{type:'action',id:'claim:k3'});a.deepEqual(payout.reward,{kind:'job',job:'k3',id:'k3:1',exp:15,silver:8});a.deepEqual(notes(s),out);
 s=E.restore(clone(s));a.deepEqual(notes(s),out);a.equal(s.jobs.k3.count,1);a.deepEqual(s.cargo,[]);
 const paid=JSON.stringify(s);a.equal(E.apply(s,{type:'action',id:'claim:k3'}).ok,false);a.equal(E.apply(s,{type:'action',id:'accept:k3'}).ok,false);a.equal(JSON.stringify(s),paid);
});

test('copied case records are immutable own values and repeated read-only access never creates work',()=>{
 const s=accepted();work(s,'readSources');work(s,'conclude',{field:'room',choice:'differs'});const before=JSON.stringify(s),out=notes(s);frozen(out);
 a.throws(()=>out.push({}),TypeError);a.throws(()=>{out[0].fields[0].value='tampered';},TypeError);
 const guardedEngine={...E,apply(){throw Error('read-only copy invoked an operation');}};
 for(let i=0;i<20;i++)a.deepEqual(N.forQuest(guardedEngine,W,s,'k3'),out);
 a.equal(JSON.stringify(s),before);a.equal(s.jobs.k3.work.sourcesRead,true);a.deepEqual(s.jobs.k3.work.conclusions,{room:'differs'});a.deepEqual(s.jobs.k3.done,{});a.equal(s.jobs.k3.count,0);a.deepEqual(s.cargo,[]);
});
