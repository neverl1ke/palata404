'use strict';
const {test}=require('node:test');
const a=require('node:assert/strict');
const W=require('../quest-job-model.js');
const clone=value=>JSON.parse(JSON.stringify(value));
function fresh(serial=0){return{jobs:{k3:{active:true,count:0,startTrip:0,done:{},...W.make('k3',serial)}}};}
function operate(state,op,value){
 const before=JSON.stringify(state),result=W.operate(state,'job:copies',op,value);
 a.equal(JSON.stringify(state),before,'A model operation must not mutate its input');
 if(result.ok)state.jobs.k3.work=result.work;
 return result;
}
function choose(state,field,choice){const result=operate(state,'conclude',{field,choice});a.equal(result.ok,true,result.message);return result;}
function opened(){const state=fresh();a.equal(operate(state,'readSources').ok,true);return state;}
function resolved(){const state=opened();choose(state,'room','differs');choose(state,'time','matchesActual');choose(state,'author','unknown');return state;}

// These are evidence-bearing facts in the approved case, not a copy of a private
// solution key. The distinction between planned and performed time matters.
test('new K3 exposes the approved three-source case without a hidden answer key or state mutation',()=>{
 const state=fresh(),before=JSON.stringify(state),board=W.board(state,'job:copies');
 a.equal(JSON.stringify(state),before);a.equal(board.kind,'caseCompare');a.equal(board.revision,3);a.equal(board.caseId,'46');
 a.equal(board.sourcesRead,false);a.deepEqual(board.conclusions,{});a.equal(board.documents.length,3);
 const sources=Object.fromEntries(board.documents.map(doc=>[doc.id,Object.fromEntries(doc.fields.map(field=>[field.id,field.value]))]));
 a.deepEqual(sources,{
  'source-1':{ward:'406',plan:'09:15',lot:'Б-17',status:'Назначено'},
  'source-2':{ward:'406',fact:'09:25',lot:'Б-17',signature:'Неразборчива'},
  'source-3':{ward:'407',fact:'09:25',lot:'Б-17',signature:'Клара'}
 });
 a.deepEqual(board.issues.map(issue=>issue.id),['room','time','author']);
 for(const issue of board.issues){a.equal(issue.choices.length,3);a.equal(new Set(issue.choices.map(c=>c.id)).size,3);a.ok(issue.sources.every(id=>Object.hasOwn(sources,id)));a.ok(issue.choices.every(choice=>Object.keys(choice).sort().join(',')==='id,label'));}
 a.ok(!Object.keys(board).some(key=>/answer|solution|correct|expected/i.test(key)));
 a.equal(W.validRecord('k3',state.jobs.k3),true);
});

test('merely reading a public board does not record sources, permit remote conclusions or reveal a receipt',()=>{
 const state=fresh();W.board(state,'job:copies');
 a.equal(state.jobs.k3.work.sourcesRead,false);a.equal(W.description(state,'copies'),null);
 for(const [op,value]of [['conclude',{field:'room',choice:'differs'}],['submit']]){
  const before=clone(state),result=operate(state,op,value);a.equal(result.ok,false);a.match(result.message,/откройте исходные документы/);a.deepEqual(state,before);
 }
});

test('source recording is idempotent and grants neither completion nor a reward',()=>{
 const state=fresh(),first=operate(state,'readSources');
 a.equal(first.ok,true);a.equal(first.complete,null);a.equal(first.reward,undefined);a.deepEqual(state.jobs.k3.work,{sourcesRead:true,conclusions:{}});
 const once=clone(state),second=operate(state,'readSources');a.equal(second.ok,true);a.equal(second.complete,null);a.deepEqual(state,once);
 a.equal(W.description(state,'copies'),null);a.equal(W.validRecord('k3',state.jobs.k3),true);
});

test('conclusions persist independently through restore and remain drafts until the entire case is submitted',()=>{
 const state=opened();choose(state,'room','matches');choose(state,'author','unknown');
 const before=clone(state.jobs.k3),restored=W.restore('k3',before);a.deepEqual(restored.work,before.work);a.equal(restored.revision,3);
 state.jobs.k3={...state.jobs.k3,...restored};a.equal(W.validRecord('k3',state.jobs.k3),true);
 const failure=operate(state,'submit');a.equal(failure.ok,false);a.match(failure.message,/время в копии/);a.deepEqual(state.jobs.k3.work.conclusions,{room:'matches',author:'unknown'});
 choose(state,'time','matchesActual');a.equal(W.description(state,'copies'),null);a.deepEqual(state.jobs.k3.done,{});
});

test('invalid or old mark commands cannot inject a conclusion or erase another draft answer',()=>{
 const state=opened();choose(state,'room','differs');
 const invalid=[null,[],{},'differs',{field:'room'},{field:{},choice:'differs'},{field:'room',choice:{}},{field:'noSuchField',choice:'unknown'},{field:'room',choice:'clara'},{field:'room',choice:'differs',complete:true},{field:'constructor',choice:'unknown'},JSON.parse('{"field":"__proto__","choice":"unknown"}')];
 for(const value of invalid){const before=clone(state),result=operate(state,'conclude',value);a.equal(result.ok,false);a.deepEqual(state,before);}
 const before=clone(state);a.equal(operate(state,'mark','ward').ok,false);a.deepEqual(state,before);
});

test('room, time and unsupported-name errors receive specific explanations without discarding choices',()=>{
 for(const [field,choice,pattern]of [['room','matches',/Номер палаты/],['time','error',/Направление содержит план/],['author','clara',/не означает, что Клара не могла/],['author','other',/не подтверждено оригиналом/]]){
  const state=resolved();choose(state,field,choice);const before=clone(state),failure=operate(state,'submit');
  a.equal(failure.ok,false);a.match(failure.message,pattern);a.deepEqual(state,before);a.equal(failure.complete,undefined);
 }
});

test('a supported act distinguishes the room discrepancy, matching actual time and unconfirmed original signature',()=>{
 const state=resolved(),result=operate(state,'submit');
 a.equal(result.ok,true);a.equal(result.complete,'copies');a.equal(result.reward,undefined);
 a.match(result.message,/палата расходится/);a.match(result.message,/время проведения перенесено верно/);a.match(result.message,/имя в копии не подтверждено оригиналом/);
 state.jobs.k3.done.copies=true;a.equal(W.validRecord('k3',state.jobs.k3),true);
 const description=W.description(state,'copies');a.match(description,/406\/407/);a.match(description,/09:25/);a.match(description,/Имя в копии не подтверждено оригиналом/);a.doesNotMatch(description,/Клара не выполняла|исполнитель установлен/);
 const completed=clone(state);a.equal(operate(state,'conclude',{field:'author',choice:'clara'}).ok,false);a.deepEqual(state,completed);
});

test('strict case validation rejects invented proof, unsupported fields and forged completion',()=>{
 const valid=resolved().jobs.k3;valid.done.copies=true;
 const malformed=[
  job=>{job.work.sourcesRead=false;},job=>{job.work.sourcesRead='true';},job=>{job.work.conclusions.author='clara';},job=>{delete job.work.conclusions.time;},
  job=>{job.work.conclusions.extra='differs';},job=>{job.work.extra=true;},job=>{job.done.extra=true;},job=>{job.done.copies=false;},job=>{job.work.conclusions=[];},
  job=>{job.work.conclusions.room='correct';},job=>{job.variant=3;},job=>{job.work={marked:['ward']};},job=>{job.unrecognized='answer';}
 ];
 for(const change of malformed){const job=clone(valid);change(job);a.equal(W.validRecord('k3',job),false,JSON.stringify(job));}
 const unopened=fresh().jobs.k3;unopened.work.conclusions.room='differs';a.equal(W.validRecord('k3',unopened),false);
 a.equal(W.validRecord('k3',fresh().jobs.k3),true);
});

test('restoring a completed case retains the qualified receipt without inventing an executor',()=>{
 const state=resolved();state.jobs.k3.done.copies=true;state.jobs.k3.active=false;state.jobs.k3.count=1;
 const before=JSON.stringify(state),restored={...state,jobs:{k3:{...state.jobs.k3,...W.restore('k3',state.jobs.k3)}}};
 a.equal(JSON.stringify(state),before);a.equal(W.validRecord('k3',restored.jobs.k3),true);a.equal(W.description(restored,'copies'),W.description(state,'copies'));
 a.deepEqual(W.restore('k3',restored.jobs.k3),W.restore('k3',state.jobs.k3));
});

test('legacy revision2 retains its original two-document mark flow and does not become the new case',()=>{
 a.equal(W.supportsRevision('k3',2),true);a.equal(W.supportsRevision('k3',3),true);a.equal(W.supportsRevision('k3',4),false);a.equal(W.supportsRevision('k3',1),false);
 for(let variant=0;variant<3;variant++){
  const state={jobs:{k3:{active:true,count:0,startTrip:0,done:{},revision:2,variant,work:{marked:[]}}}};
  const restored=W.restore('k3',state.jobs.k3);a.equal(restored.revision,2);a.deepEqual(restored.work,{marked:[]});
  const board=W.board(state,'job:copies');a.equal(board.kind,'compare');a.equal(board.documents.length,2);a.equal(board.sourcesRead,undefined);
  for(const field of board.documents[0].fields){const other=board.documents[1].fields.find(item=>item.id===field.id);if(field.value!==other.value)a.equal(operate(state,'mark',field.id).ok,true);}
  const result=operate(state,'submit');a.equal(result.ok,true);a.equal(result.complete,'copies');
 }
 for(const serial of [0,1,2,7]){const state=fresh(serial);a.equal(state.jobs.k3.revision,3);a.equal(W.board(state,'job:copies').caseId,'46');}
});

test('public case data and conclusion maps are detached from stored state and later boards',()=>{
 const state=resolved(),before=JSON.stringify(state),first=W.board(state,'job:copies');
 first.conclusions.author='clara';first.documents[0].fields[0].value='999';first.issues[0].choices[0].label='changed';
 a.equal(JSON.stringify(state),before);const second=W.board(state,'job:copies');a.equal(second.conclusions.author,'unknown');a.equal(second.documents[0].fields[0].value,'406');a.notEqual(second.issues[0].choices[0].label,'changed');
});
