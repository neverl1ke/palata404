'use strict';

const {test}=require('node:test');
const a=require('node:assert/strict');
const {spawnSync}=require('node:child_process');
const modelPath=require.resolve(process.env.FLOOR9_TASK_MODEL||'../review/floor9-tasks/source/tasks.js');
const M=require(modelPath);

// Only the standalone review model is loaded. These cases do not load the game,
// use profile storage, complete Q2, or exercise the frozen boss encounters.
const taskIds=['support','service','holder'];
const frozenRooms=['903','906','912'];
const copy=value=>JSON.parse(JSON.stringify(value));
const bytes=value=>JSON.stringify(value);
const board=(s,task)=>M.board(s,task);

function scope(s){
  a.deepEqual(Object.keys(s).sort(),['brand','cases','receipts','version']);
  a.equal(s.version,1);
  a.deepEqual(Object.keys(s.cases).sort(),[...taskIds].sort());
  a.equal(board(s,'support').routeTested,false,'parking a tool is never a route test or Q2 completion');
}
function unchangedOthers(before,s,task){
  for(const other of taskIds.filter(id=>id!==task))a.deepEqual(s.cases[other],before.cases[other],`${task} must not change ${other}`);
  for(let index=0;index<before.receipts.length;index++)a.deepEqual(s.receipts[index],before.receipts[index],'an existing receipt is immutable');
  scope(s);
}
function act(s,task,op,value){
  const before=copy(s),event={task,op};
  if(value!==undefined)event.value=value;
  const result=M.apply(s,event);
  a.equal(result.ok,true,`${bytes(event)}: ${result.message}`);
  a.equal(typeof result.message,'string');
  unchangedOthers(before,s,task);
  return result;
}
function denied(s,task,op,value){
  const before=bytes(s),event={task,op};
  if(value!==undefined)event.value=value;
  const result=M.apply(s,event);
  a.equal(result.ok,false,`Expected refusal for ${bytes(event)}`);
  a.equal(typeof result.message,'string');
  a.equal(bytes(s),before,'a refused operation must be atomic');
  scope(s);
  return result;
}
function item(s,task,id){
  const value=board(s,task).items.find(entry=>entry.id===id);
  a.ok(value,`${task} exposes neutral item ${id}`);
  return value;
}
function seen(s,task,ids){for(const id of ids)act(s,task,'inspect',id);}
function receipt(s,task){
  const value=board(s,task).receipt;
  a.ok(value,`${task} exposes its durable completion receipt`);
  a.equal(s.receipts.filter(entry=>bytes(entry)===bytes(value)).length,1,'the visible receipt occurs exactly once');
  a.equal(typeof value,'string');
  a.ok(value.length>0);
  return value;
}
function reload(s){
  const encoded=M.snapshot(s);
  a.equal(typeof encoded,'string');
  a.deepEqual(JSON.parse(encoded),s,'the save contains only this prototype state');
  const result=M.restore(encoded);
  a.equal(result.ok,true,result.message);
  a.equal(typeof result.message,'string');
  a.deepEqual(result.state,s);
  a.notEqual(result.state,s,'restoring creates independent mutable progress');
  return result.state;
}
function finishSupport(s){
  seen(s,'support',board(s,'support').items.map(value=>value.id));
  const b=board(s,'support');
  const match=kind=>b.items.find(value=>value.kind===kind&&value.details.connector===b.request.connector&&value.details.condition==='intact');
  act(s,'support','support',match('support').id);act(s,'support','tip',match('tip').id);
  act(s,'support','assemble');act(s,'support','bench');
  act(s,'support','park',b.request.rack);
  return receipt(s,'support');
}
function finishService(s){
  act(s,'service','records');act(s,'service','node');
  const b=board(s,'service'),match=b.requests.find(value=>value.details.node===b.node.id&&value.details.symptom===b.node.symptom);
  a.ok(match,'the inspected node and records identify a matching request');
  act(s,'service','request',match.id);act(s,'service','send');
  act(s,'service','retest');act(s,'service','report',board(s,'service').observation.movement);
  act(s,'service','submit');
  return receipt(s,'service');
}
function fitHolder(s){
  act(s,'holder','card');seen(s,'holder',board(s,'holder').items.map(value=>value.id));
  const b=board(s,'holder');
  const match=kind=>b.items.find(value=>value.kind===kind&&value.details.connector===b.request.mount&&value.details.condition==='intact'&&(kind!=='insert'||value.details.cup===b.request.cup));
  act(s,'holder','base',match('base').id);act(s,'holder','insert',match('insert').id);
  act(s,'holder','assemble');act(s,'holder','fit');
}
function finishHolder(s){
  fitHolder(s);const b=board(s,'holder');act(s,'holder','carry');act(s,'holder','mount',b.request.tray);
  act(s,'holder','cup');act(s,'holder','shelf',b.request.shelf);
  act(s,'holder','verify');
  return receipt(s,'holder');
}
function recursivelyFrozen(value){
  if(value&&typeof value==='object'){
    a.equal(Object.isFrozen(value),true);
    for(const child of Object.values(value))recursivelyFrozen(child);
  }
}

test('the three independent preparation surfaces avoid every frozen boss room',()=>{
  const s=M.initial(),second=M.initial();
  a.equal(typeof s.brand,'string');a.ok(s.brand.length>0);
  scope(s);a.deepEqual(s.receipts,[]);
  a.deepEqual([...M.blueprint.frozenRooms].sort(),[...frozenRooms].sort());
  a.deepEqual(M.blueprint.integration,{activeFloor9:false,gameWrites:false,bossAccessWrites:false,realRewards:false});
  recursivelyFrozen(M.blueprint);
  for(const task of taskIds){
    const b=board(s,task);
    a.equal(b.id,task);a.equal(b.done,false);a.equal(b.receipt,null);
    a.ok(Array.isArray(b.rooms)&&b.rooms.length>0);
    for(const room of b.rooms)a.ok(!frozenRooms.includes(String(room)),`${task} stays outside frozen room ${room}`);
    a.deepEqual(b.progress,s.cases[task]);
  }
  s.cases.support.seen.push('s1');
  a.deepEqual(second.cases.support.seen,[],'fresh sessions do not share arrays');
});

test('item names and public options hide uninspected fit and condition evidence',()=>{
  const s=M.initial();
  for(const task of ['support','holder']){
    const b=board(s,task);
    a.equal(b.items.length,6);
    for(const value of b.items){
      a.equal(value.inspected,false);a.equal(value.details,null);
      a.doesNotMatch(value.name,/N[23]|R[34]|C[23]|intact|damaged|cracked|правильн|пошкодж|тріснут|ціл(?:а|ий|е)/i,'a neutral label must not reveal the answer');
      for(const key of ['correct','answer','solution'])a.equal(Object.hasOwn(value,key),false);
    }
  }
  for(const request of board(s,'service').requests){
    a.equal(request.details,null);
    a.doesNotMatch(request.name,/B17|B71|stopmark/i);
    for(const key of ['correct','answer','solution'])a.equal(Object.hasOwn(request,key),false);
  }
  a.equal(board(s,'holder').request,null,'the household request comes from reading the card');
  a.equal(board(s,'service').node,null);a.equal(board(s,'service').observation,null);
  act(s,'support','inspect','s1');
  a.deepEqual(item(s,'support','s1').details,{connector:'N2',condition:'intact'});
  a.equal(item(s,'support','t1').details,null,'inspecting one object does not reveal another');
  act(s,'holder','card');
  a.deepEqual(board(s,'holder').request,{mount:'R4',cup:'C2',tray:'T2',shelf:'P2'});
});

test('board projections cannot edit progress, hidden evidence, requests, or receipts',()=>{
  const s=M.initial();act(s,'support','inspect','s1');
  const before=bytes(s),b=board(s,'support');
  const edits=[()=>b.progress.seen.push('t1'),()=>{b.request.connector='FORGED';},()=>{b.items.find(value=>value.id==='s1').details.connector='FORGED';},()=>{b.done=true;}];
  for(const edit of edits){try{edit();}catch(error){a.ok(error instanceof TypeError);}}
  a.equal(bytes(s),before);
  a.equal(board(s,'support').request.connector,'N2');
  a.equal(item(s,'support','s1').details.connector,'N2');
  finishSupport(s);const completed=bytes(s),completedBoard=board(s,'support');
  try{completedBoard.receipt='FORGED';}catch(error){a.ok(error instanceof TypeError);}
  a.equal(bytes(s),completed,'a receipt projection cannot forge the durable receipt');
});

test('support preparation requires inspected compatible intact pieces, a bench test, and the named rack',()=>{
  const s=M.initial();
  for(const [op,value] of [['support','s1'],['tip','t1'],['assemble'],['bench'],['park','rack-n2'],['submit']])denied(s,'support',op,value);
  seen(s,'support',['s1','s2','s3','t1','t2','t3']);
  const b=board(s,'support');
  const valid=b.items.filter(value=>value.details.connector===b.request.connector&&value.details.condition==='intact');
  a.deepEqual(valid.map(value=>value.id).sort(),['s1','t1'],'visible measurements identify one intact pair');
  for(const [support,tip] of [['s2','t2'],['s1','t2'],['s3','t1'],['s1','t3']]){
    act(s,'support','support',support);act(s,'support','tip',tip);
    denied(s,'support','assemble');
  }
  act(s,'support','support','s1');act(s,'support','tip','t1');
  act(s,'support','assemble');
  a.equal(s.cases.support.done,false);a.deepEqual(s.receipts,[]);
  denied(s,'support','park','rack-n2');act(s,'support','bench');
  a.equal(s.cases.support.done,false);denied(s,'support','submit');
  denied(s,'support','park','rack-n3');act(s,'support','park','rack-n2');
  a.equal(s.cases.support.done,true);a.equal(s.cases.support.parked,true);
  const completed=bytes(s),r=receipt(s,'support');
  for(let count=0;count<3;count++)act(s,'support','submit');
  a.equal(bytes(s),completed);a.deepEqual(receipt(s,'support'),r);
  denied(s,'support','support','s2');
});

test('a changed support selection clears only its dependent preparation and preserves observations',()=>{
  const s=M.initial();
  act(s,'service','records');act(s,'holder','card');
  seen(s,'support',['s1','t1','s2','t2']);
  act(s,'support','support','s1');act(s,'support','tip','t1');
  act(s,'support','assemble');act(s,'support','bench');
  const observations=copy(s.cases.support.seen),other=copy(s.cases);
  act(s,'support','support','s1');
  a.equal(s.cases.support.assembled,true);a.equal(s.cases.support.bench,true,'reselecting the same part is harmless');
  act(s,'support','inspect','s3');
  a.equal(s.cases.support.bench,true,'new evidence does not change an existing assembly');
  act(s,'support','support','s2');
  a.equal(s.cases.support.assembled,false);a.equal(s.cases.support.bench,false);a.equal(s.cases.support.parked,false);
  for(const id of observations)a.ok(s.cases.support.seen.includes(id));
  a.deepEqual(s.cases.service,other.service);a.deepEqual(s.cases.holder,other.holder);
  denied(s,'support','bench');denied(s,'support','park','rack-n2');
  act(s,'support','support','s1');act(s,'support','assemble');act(s,'support','bench');
  act(s,'support','tip','t2');
  a.equal(s.cases.support.assembled,false);a.equal(s.cases.support.bench,false);
});

test('service submission requires both sources, a matched request, observed retest, and the matching report',()=>{
  for(const onlySource of ['records','node']){
    const s=M.initial();act(s,'service',onlySource);
    if(onlySource==='records')act(s,'service','request','r1');else denied(s,'service','request','r1');
    denied(s,'service','send');
  }
  const s=M.initial();
  for(const [op,value] of [['send'],['retest'],['report','free'],['submit']])denied(s,'service',op,value);
  act(s,'service','records');act(s,'service','node');
  const b=board(s,'service');
  a.equal(b.node.id,'B17');a.equal(b.node.symptom,'stopmark');
  const matches=request=>request.details.node===b.node.id&&request.details.symptom===b.node.symptom;
  const correct=b.requests.filter(matches),wrong=b.requests.filter(request=>!matches(request));
  a.equal(correct.length,1);a.equal(wrong.length,2);
  for(const request of wrong){act(s,'service','request',request.id);denied(s,'service','send');}
  a.equal(board(s,'service').observation,null);a.equal(s.cases.service.sent,false);
  act(s,'service','request',correct[0].id);act(s,'service','send');
  a.equal(s.cases.service.sent,true);a.equal(s.cases.service.done,false);a.deepEqual(s.receipts,[]);
  denied(s,'service','request','r2');denied(s,'service','report','free');denied(s,'service','submit');
  act(s,'service','retest');
  a.equal(board(s,'service').observation.movement,'free','the retest produces visible evidence for the report');
  act(s,'service','report','blocked');denied(s,'service','submit');
  a.equal(s.cases.service.done,false);a.deepEqual(s.receipts,[]);
  act(s,'service','report','free');act(s,'service','submit');
  a.equal(s.cases.service.done,true);
  const completed=bytes(s),r=receipt(s,'service');
  act(s,'service','submit');a.equal(bytes(s),completed);a.deepEqual(receipt(s,'service'),r);
});

test('holder selection comes from the card and observed fit, with assembly and fit before carrying',()=>{
  const s=M.initial();
  for(const [op,value] of [['base','b1'],['insert','i1'],['assemble'],['fit'],['carry'],['mount','T2'],['cup'],['shelf','P2'],['verify'],['submit']])denied(s,'holder',op,value);
  act(s,'holder','card');seen(s,'holder',['b1','b2','b3','i1','i2','i3']);
  const b=board(s,'holder');
  const candidates=b.items.filter(value=>value.details.connector===b.request.mount&&value.details.condition==='intact'&&(!value.details.cup||value.details.cup===b.request.cup));
  a.deepEqual(candidates.map(value=>value.id).sort(),['b1','i1']);
  for(const [base,insert] of [['b2','i1'],['b3','i1'],['b1','i2'],['b1','i3']]){
    act(s,'holder','base',base);act(s,'holder','insert',insert);
    denied(s,'holder','assemble');
  }
  act(s,'holder','base','b1');act(s,'holder','insert','i1');
  denied(s,'holder','fit');denied(s,'holder','carry');
  act(s,'holder','assemble');denied(s,'holder','carry');act(s,'holder','fit');
  a.equal(s.cases.holder.done,false);a.deepEqual(s.receipts,[]);
  act(s,'holder','carry');
  a.equal(s.cases.holder.delivered,true);a.equal(board(s,'holder').currentScene,'911');
  denied(s,'holder','base','b2');denied(s,'holder','insert','i2');
  a.equal(s.cases.holder.done,false);a.deepEqual(s.receipts,[]);
});

test('holder completion requires mounting and household use at 911, then survives revisits and reloads',()=>{
  let s=M.initial();fitHolder(s);act(s,'holder','carry');
  denied(s,'holder','verify');denied(s,'holder','submit');
  act(s,'holder','view','910');
  for(const [op,value] of [['mount','T2'],['cup'],['shelf','P2'],['verify']])denied(s,'holder',op,value);
  act(s,'holder','view','911');denied(s,'holder','mount','T3');
  act(s,'holder','mount','T2');denied(s,'holder','verify');
  act(s,'holder','cup');denied(s,'holder','verify');denied(s,'holder','shelf','P3');
  act(s,'holder','shelf','P2');
  a.equal(s.cases.holder.done,false);a.deepEqual(s.receipts,[]);
  s=reload(s);act(s,'holder','verify');
  a.equal(s.cases.holder.verified,true);a.equal(s.cases.holder.done,true);
  const r=copy(receipt(s,'holder'));
  for(const scene of ['910','911','910','911']){
    act(s,'holder','view',scene);a.equal(board(s,'holder').currentScene,scene);
    a.equal(board(s,'holder').done,true);a.deepEqual(receipt(s,'holder'),r);
  }
  s=reload(s);const completed=bytes(s);act(s,'holder','submit');
  a.equal(bytes(s),completed);a.deepEqual(receipt(s,'holder'),r);
});

test('changing holder parts before carrying invalidates assembly and fit while preserving source evidence',()=>{
  const s=M.initial();act(s,'support','inspect','s1');act(s,'service','records');fitHolder(s);
  const evidence=copy(s.cases.holder.seen),others=copy(s.cases);
  act(s,'holder','base','b1');
  a.equal(s.cases.holder.assembled,true);a.equal(s.cases.holder.fit,true,'the same part does not invalidate its fit');
  act(s,'holder','base','b2');
  a.equal(s.cases.holder.assembled,false);a.equal(s.cases.holder.fit,false);
  a.deepEqual(s.cases.holder.seen,evidence);a.equal(s.cases.holder.cardRead,true);
  a.deepEqual(s.cases.support,others.support);a.deepEqual(s.cases.service,others.service);
  denied(s,'holder','carry');
  act(s,'holder','base','b1');act(s,'holder','assemble');act(s,'holder','fit');
  act(s,'holder','insert','i2');
  a.equal(s.cases.holder.assembled,false);a.equal(s.cases.holder.fit,false);denied(s,'holder','carry');
});

test('saving partial work preserves evidence and dependency gates without completing another case',()=>{
  let s=M.initial();
  seen(s,'support',['s1','t1']);act(s,'support','support','s1');act(s,'support','tip','t1');act(s,'support','assemble');
  act(s,'service','records');act(s,'service','node');act(s,'service','request','r1');act(s,'service','send');
  fitHolder(s);act(s,'holder','carry');act(s,'holder','mount','T2');
  s=reload(s);
  for(const task of taskIds)a.equal(s.cases[task].done,false);
  a.deepEqual(s.receipts,[]);denied(s,'support','park','rack-n2');denied(s,'service','submit');denied(s,'holder','verify');
  act(s,'support','bench');act(s,'support','park','rack-n2');
  act(s,'service','retest');act(s,'service','report','free');act(s,'service','submit');
  act(s,'holder','cup');act(s,'holder','shelf','P2');act(s,'holder','verify');
  a.equal(s.receipts.length,3);reload(s);
});

test('each case has one stable receipt regardless of completion order and repeated submission',()=>{
  const finish={support:finishSupport,service:finishService,holder:finishHolder},results=[];
  for(const order of [taskIds,[...taskIds].reverse()]){
    let s=M.initial();const receipts={};
    for(const task of order){receipts[task]=copy(finish[task](s));s=reload(s);}
    a.equal(s.receipts.length,3);a.equal(new Set(s.receipts).size,3);
    const before=bytes(s);
    for(const task of taskIds)for(let count=0;count<2;count++)act(s,task,'submit');
    a.equal(bytes(s),before);results.push(receipts);
  }
  a.deepEqual(results[0],results[1]);
});

test('restore rejects foreign schemas, inconsistent completion, and duplicate or forged receipts',()=>{
  const finished=M.initial();finishSupport(finished);finishService(finished);finishHolder(finished);
  const mutations=[
    raw=>{raw.brand='other-game';},raw=>{raw.version=2;},raw=>{raw.world={gates:{BC:true}};},
    raw=>{delete raw.cases.holder;},raw=>{raw.cases.support.seen=[];},raw=>{raw.cases.support.seen.push('s1');},
    raw=>{raw.cases.support.selectedSupport='t1';},raw=>{raw.cases.support.selectedTip='t3';},
    raw=>{raw.cases.support.assembled=false;},raw=>{raw.cases.support.bench=false;},raw=>{raw.cases.support.parked=false;},raw=>{raw.cases.support.done=false;},
    raw=>{raw.cases.service.recordsRead=false;},raw=>{raw.cases.service.nodeSeen=false;},
    raw=>{raw.cases.service.selected='r2';},raw=>{raw.cases.service.selected='r3';},raw=>{raw.cases.service.selected=null;},
    raw=>{raw.cases.service.sent=false;},raw=>{raw.cases.service.ack='forged';},
    raw=>{raw.cases.service.tested=false;},raw=>{raw.cases.service.report='blocked';},
    raw=>{raw.cases.holder.cardRead=false;},raw=>{raw.cases.holder.seen=[];},raw=>{raw.cases.holder.base='b2';},raw=>{raw.cases.holder.insert='i3';},
    raw=>{raw.cases.holder.assembled=false;},raw=>{raw.cases.holder.fit=false;},raw=>{raw.cases.holder.delivered=false;},
    raw=>{raw.cases.holder.mounted=false;},raw=>{raw.cases.holder.cup=false;},raw=>{raw.cases.holder.shelf=null;},
    raw=>{raw.cases.holder.verified=false;},raw=>{raw.cases.holder.shelf='P3';},
    raw=>{raw.cases.holder.view='912';},raw=>{raw.cases.holder.futureAward=true;},
    raw=>{raw.receipts=[];},raw=>{raw.receipts.push(copy(raw.receipts[0]));},
    raw=>{raw.receipts[0]='forged';},raw=>{raw.receipts.push({id:'forged',task:'support'});}
  ];
  const bad=[null,{}, {version:10,profile:{silver:100},world:{gates:{BC:true}}}];
  for(const mutate of mutations){const raw=copy(finished);mutate(raw);bad.push(raw);}
  const premature=M.initial();premature.cases.support.done=true;bad.push(premature);
  for(const raw of bad){
    const before=bytes(raw),result=M.apply(raw,{task:'support',op:'submit'});
    a.equal(result.ok,false);a.equal(bytes(raw),before,'invalid state must also be refused atomically by apply');
  }
  for(const encoded of ['', '{', ...bad.map(bytes)]){
    const result=M.restore(encoded);
    a.equal(result.ok,false,`Refuse invalid prototype save: ${encoded}`);
    a.equal(typeof result.message,'string');
  }
  a.deepEqual(M.restore(M.snapshot(finished)).state,finished,'refused saves do not damage valid state');
});

test('unsupported values and operations cannot mutate the task model or create world progress',()=>{
  const s=M.initial();
  for(const task of taskIds){
    denied(s,task,'unknown');denied(s,task,'inspect','unknown-item');
    denied(s,task,'gate','BC');denied(s,task,'boss','solo_a');denied(s,task,'reward',100);
  }
  for(const event of [null,{}, {task:'unknown',op:'submit'}, {task:'support',op:'support',value:'s99'}, {task:'holder',op:'view',value:'912'}]){
    const before=bytes(s),result=M.apply(s,event);
    a.equal(result.ok,false);a.equal(typeof result.message,'string');a.equal(bytes(s),before);
  }
  a.deepEqual(s.receipts,[]);scope(s);
});

test('inherited and non-string task IDs cannot access boards or mutate shared prototypes',()=>{
  // Keep a future regression isolated: an inherited lookup could otherwise
  // mutate Object.prototype before an atomic-state assertion notices it.
  const script=String.raw`
    'use strict';
    const a=require('node:assert/strict'),M=require(process.argv[1]),s=M.initial();
    const targets=[Object.prototype,Function.prototype,Object,Function,Object.prototype.toString,Object.prototype.hasOwnProperty];
    const original=targets.map(target=>Object.getOwnPropertyDescriptor(target,'cardRead'));
    const ids=['__proto__','constructor','toString','hasOwnProperty',null,undefined,0,true,{},[],new String('holder'),Symbol('holder')];
    for(const task of ids){
      const before=M.snapshot(s);
      a.equal(M.board(s,task),null);
      const result=M.apply(s,{task,op:'card'});
      a.equal(result.ok,false);a.equal(typeof result.message,'string');
      a.equal(M.snapshot(s),before,'rejected task IDs leave the full snapshot unchanged');
      targets.forEach((target,index)=>a.deepEqual(Object.getOwnPropertyDescriptor(target,'cardRead'),original[index],'shared cardRead properties must not change'));
    }
    a.equal(M.board(null,'holder'),null);
    a.equal(M.board(s,'holder').progress.cardRead,false);
  `;
  const result=spawnSync(process.execPath,['-e',script,modelPath],{encoding:'utf8'});
  a.equal(result.error,undefined);
  a.equal(result.status,0,result.stderr||result.stdout);
});

test('repeating completed preparation steps preserves checks and describes the current result truthfully',()=>{
  const s=M.initial();
  function repeat(task,op,value){
    const before=M.snapshot(s),result=act(s,task,op,value);
    a.equal(M.snapshot(s),before,'repeating an already completed step preserves the entire state');
    a.doesNotMatch(result.message,/ещ[её]\s+на\s+столе|пока\s+не\s+размещена|ещ[её]\s+не\s+проверена|теперь\s+нужна\s+проверка/i,'feedback must not describe an earlier incomplete step');
    return result;
  }
  seen(s,'support',['s1','t1']);act(s,'support','support','s1');act(s,'support','tip','t1');
  act(s,'support','assemble');act(s,'support','bench');
  repeat('support','assemble');repeat('support','support','s1');repeat('support','tip','t1');
  a.equal(s.cases.support.bench,true);a.equal(s.cases.support.done,false);

  act(s,'service','records');act(s,'service','node');act(s,'service','request','r1');
  act(s,'service','send');act(s,'service','retest');act(s,'service','report','free');
  repeat('service','send');
  a.equal(s.cases.service.tested,true);a.equal(s.cases.service.report,'free');
  a.equal(board(s,'service').observation.movement,'free');

  fitHolder(s);repeat('holder','assemble');
  a.equal(s.cases.holder.fit,true);
  act(s,'holder','carry');act(s,'holder','mount','T2');act(s,'holder','cup');act(s,'holder','shelf','P2');
  for(const [op,value] of [['mount','T2'],['cup'],['assemble']])repeat('holder',op,value);
  a.equal(board(s,'holder').objectLocation,'shelf-P2');
  a.equal(s.cases.holder.mounted,true);a.equal(s.cases.holder.cup,true);
  a.equal(s.cases.holder.shelf,'P2');a.equal(s.cases.holder.verified,false);a.equal(s.cases.holder.done,false);
  a.deepEqual(s.receipts,[],'replayed preparation steps create no completion receipt');
  act(s,'holder','verify');a.equal(s.receipts.length,1);receipt(s,'holder');
});
