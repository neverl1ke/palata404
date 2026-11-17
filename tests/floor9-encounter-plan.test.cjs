'use strict';

const {test}=require('node:test');
const a=require('node:assert/strict');
const M=require('../review/floor9-bosses/source/encounter-plan.js');

// This suite exercises the isolated review prototype. It does not load the game,
// use profile storage, or award any runtime currency.
const proofIds=['a_plan','a_exam','a_return','a_clear_door','a_test_door','b_record','b_node','b_match','b_service','b_test_door'];
const encounterIds=['solo_a','solo_b','duo_c'];
const copy=value=>JSON.parse(JSON.stringify(value));
const bytes=state=>JSON.stringify(state);
const sectionProofs=section=>proofIds.filter(id=>M.blueprint.proofs[id].section===section);

function ok(state,event){
  const result=M.apply(state,event);
  a.equal(result.ok,true,`${JSON.stringify(event)}: ${result.message}`);
  a.equal(typeof result.message,'string');
  return result;
}
function denied(state,event){
  const before=bytes(state);
  const result=M.apply(state,event);
  a.equal(result.ok,false,`Expected refusal for ${JSON.stringify(event)}`);
  a.equal(typeof result.message,'string');
  a.equal(bytes(state),before,'A refused event is atomic');
  return result;
}
function mode(state,value){
  if(state.mode!==value)ok(state,{type:'mode',mode:value});
}
function section(state,value){
  if(state.section!==value)ok(state,{type:'section',section:value});
}
function prove(state,id,visiting=new Set()){
  if(state.proofs[id])return;
  a.ok(!visiting.has(id),'The proof prerequisites must be acyclic');
  visiting.add(id);
  const proof=M.blueprint.proofs[id];
  for(const prerequisite of proof.requires)prove(state,prerequisite,visiting);
  mode(state,proof.mode);
  section(state,proof.section);
  ok(state,{type:'proof',id});
  a.equal(state.proofs[id],true);
  visiting.delete(id);
}
function finishProofs(state,area){
  for(const id of sectionProofs(area))prove(state,id);
}
function start(state,encounter){
  mode(state,'trip');
  section(state,M.blueprint.encounters[encounter].section);
  ok(state,{type:'start',encounter});
  a.equal(state.battle.encounter,encounter);
  return state.battle;
}
function attackReady(state){
  if(state.battle&&state.now<state.battle.nextAttackAt){
    let remaining=state.battle.nextAttackAt-state.now;
    while(state.battle&&remaining>0){
      const ms=Math.min(10000,remaining);
      ok(state,{type:'advance',ms});
      remaining-=ms;
    }
  }
}
function fightToEnd(state,preferred='metronome'){
  for(let turns=0;state.battle&&turns<100;turns++){
    const enemy=state.battle.enemies.find(enemy=>enemy.hp>0&&enemy.id===preferred)
      ||state.battle.enemies.find(enemy=>enemy.hp>0);
    a.ok(enemy,'An ongoing battle has a living enemy');
    if(state.battle.target!==enemy.id)ok(state,{type:'target',boss:enemy.id});
    attackReady(state);
    if(state.battle)ok(state,{type:'attack'});
  }
  a.equal(state.battle,null,'The demo battle reaches a result');
}
function win(state,encounter){
  start(state,encounter);
  fightToEnd(state);
  a.equal(state.clears[encounter],true,`${encounter} can be won with the demo attack`);
}
function openAB(state=M.initial()){
  // The examination authorizes the encounter before later task proofs exist.
  prove(state,'a_exam');
  win(state,'solo_a');
  finishProofs(state,'A');
  a.equal(M.gates(state).AB.open,true);
  return state;
}
function openBC(state=openAB()){
  prove(state,'b_record');
  win(state,'solo_b');
  finishProofs(state,'B');
  a.equal(M.gates(state).BC.open,true);
  return state;
}
function recursivelyFrozen(value){
  if(value&&typeof value==='object'){
    a.equal(Object.isFrozen(value),true);
    for(const child of Object.values(value))recursivelyFrozen(child);
  }
}

test('The blueprint contains two boss identities and three fixed room encounters',()=>{
  a.deepEqual(Object.keys(M.blueprint.bosses).sort(),['metronome','threshold']);
  a.deepEqual(Object.keys(M.blueprint.encounters).sort(),[...encounterIds].sort());
  a.deepEqual(Object.keys(M.blueprint.proofs).sort(),[...proofIds].sort());
  for(const [id,area,room] of [['solo_a','A',903],['solo_b','B',906],['duo_c','C',912]]){
    const encounter=M.blueprint.encounters[id];
    a.equal(encounter.section,area);
    a.equal(String(encounter.room),String(room));
  }
  for(const proof of Object.values(M.blueprint.proofs)){
    a.ok(['A','B'].includes(proof.section));
    a.ok(['patient','trip'].includes(proof.mode));
    a.ok(Array.isArray(proof.requires));
    for(const id of proof.requires)a.ok(proofIds.includes(id));
  }
  recursivelyFrozen(M.blueprint);
});

test('Fresh states have separate mutable progress and all progress starts empty',()=>{
  const first=M.initial(),second=M.initial();
  a.equal(typeof first.brand,'string');
  a.ok(first.brand.length>0);
  a.equal(first.version,1);
  a.equal(first.mode,'patient');
  a.equal(first.section,'A');
  a.equal(first.now,0);
  a.equal(first.attempt,0);
  a.equal(first.battle,null);
  a.equal(first.lastResult,null);
  a.deepEqual(first.rewards,[]);
  a.deepEqual(first.clears,{solo_a:false,solo_b:false,duo_c:false});
  a.deepEqual(first.proofs,Object.fromEntries(proofIds.map(id=>[id,false])));
  first.proofs.a_plan=true;
  first.rewards.push({local:true});
  a.equal(second.proofs.a_plan,false);
  a.deepEqual(second.rewards,[]);
});

test('Both gates use task AND solo victory, including every individual required proof',()=>{
  for(const [gate,area,encounter] of [['AB','A','solo_a'],['BC','B','solo_b']]){
    for(const taskDone of [false,true])for(const bossDone of [false,true]){
      const state=M.initial();
      for(const id of sectionProofs(area))state.proofs[id]=taskDone;
      state.clears[encounter]=bossDone;
      const result=M.gates(state)[gate];
      a.equal(result.taskDone,taskDone,`${gate} tasks`);
      a.equal(result.bossDone,bossDone,`${gate} solo`);
      a.equal(result.open,taskDone&&bossDone,`${gate} AND truth table`);
      a.ok(Array.isArray(result.missing));
      a.equal(result.missing.length===0,result.open);
    }
    for(const missing of sectionProofs(area)){
      const state=M.initial();
      for(const id of sectionProofs(area))state.proofs[id]=id!==missing;
      state.clears[encounter]=true;
      a.equal(M.gates(state)[gate].open,false,`${missing} is required`);
    }
  }
});

test('Patient can inspect every section, and cannot start any encounter',()=>{
  const state=M.initial();
  for(const area of ['A','B','C']){
    section(state,area);
    a.equal(state.section,area);
    for(const encounter of encounterIds){
      a.equal(M.availability(state,encounter).available,false);
      denied(state,{type:'start',encounter});
    }
  }
  denied(state,{type:'attack'});
  denied(state,{type:'target',boss:'threshold'});
  a.equal(state.battle,null);
  a.deepEqual(state.rewards,[]);
});

test('Trip access is gated, and switching from Patient C anchors at the last open section',()=>{
  let state=M.initial();
  section(state,'C');
  mode(state,'trip');
  a.equal(state.section,'A');
  denied(state,{type:'section',section:'B'});
  denied(state,{type:'section',section:'C'});

  state=openAB();
  mode(state,'patient');
  section(state,'C');
  mode(state,'trip');
  a.equal(state.section,'B');
  denied(state,{type:'section',section:'C'});

  state=openBC();
  mode(state,'patient');
  section(state,'C');
  mode(state,'trip');
  a.equal(state.section,'C');
});

test('Proof prerequisites reject out-of-order actions atomically',()=>{
  a.ok(M.blueprint.proofs.a_exam.requires.includes('a_plan'));
  for(const id of proofIds){
    const proof=M.blueprint.proofs[id];
    if(!proof.requires.length)continue;
    const state=M.initial();
    mode(state,'patient');
    section(state,proof.section);
    if(proof.mode==='trip'){
      // Gate prerequisites are fixtures here; the proof being tested is still absent.
      if(proof.section==='B'){
        for(const prerequisite of sectionProofs('A'))state.proofs[prerequisite]=true;
        state.clears.solo_a=true;
      }
      mode(state,'trip');
      section(state,proof.section);
    }
    denied(state,{type:'proof',id});
  }
});

test('The first solo needs examination, without demanding future A proofs',()=>{
  const state=M.initial();
  mode(state,'trip');
  denied(state,{type:'start',encounter:'solo_a'});
  prove(state,'a_exam');
  a.ok(sectionProofs('A').some(id=>!state.proofs[id]),'Some later A tasks remain');
  mode(state,'trip');
  section(state,'A');
  a.equal(M.availability(state,'solo_a').available,true);
  win(state,'solo_a');
  a.equal(M.gates(state).AB.bossDone,true);
  a.equal(M.gates(state).AB.open,false);
  finishProofs(state,'A');
  a.equal(M.gates(state).AB.open,true);
});

test('Task-first and boss-first progress both open A→B without a circular prerequisite',()=>{
  for(const bossFirst of [false,true]){
    const state=M.initial();
    if(bossFirst){prove(state,'a_exam');win(state,'solo_a');finishProofs(state,'A');}
    else{
      finishProofs(state,'A');
      a.equal(M.gates(state).AB.taskDone,true);
      a.equal(M.gates(state).AB.open,false);
      win(state,'solo_a');
    }
    a.equal(M.gates(state).AB.open,true);
    mode(state,'trip');
    section(state,'B');
  }
});

test('B solo requires its record and access, without requiring later B proofs',()=>{
  const state=openAB();
  mode(state,'trip');
  section(state,'B');
  denied(state,{type:'start',encounter:'solo_b'});
  prove(state,'b_record');
  a.ok(sectionProofs('B').some(id=>!state.proofs[id]),'Some later B tasks remain');
  win(state,'solo_b');
  a.equal(M.gates(state).BC.bossDone,true);
  a.equal(M.gates(state).BC.open,false);
  finishProofs(state,'B');
  a.equal(M.gates(state).BC.open,true);
});

test('B tasks can finish before its solo, and C still waits for both requirements',()=>{
  const state=openAB();
  finishProofs(state,'B');
  a.equal(M.gates(state).BC.taskDone,true);
  a.equal(M.gates(state).BC.open,false);
  mode(state,'trip');
  section(state,'B');
  denied(state,{type:'section',section:'C'});
  a.equal(M.availability(state,'duo_c').available,false);
  win(state,'solo_b');
  a.equal(M.gates(state).BC.open,true);
  section(state,'C');
  a.equal(M.availability(state,'duo_c').available,true);
});

test('Demo attacks start at 20 damage and enforce their 1000ms cooldown atomically',()=>{
  const state=M.initial();
  prove(state,'a_exam');
  const battle=start(state,'solo_a');
  a.equal(battle.playerHp,100);
  a.equal(battle.maxPlayerHp,100);
  a.equal(battle.enemies.length,1);
  a.equal(battle.enemies[0].id,'threshold');
  a.equal(battle.enemies[0].hp,120);
  a.equal(battle.enemies[0].maxHp,120);
  const now=state.now;
  ok(state,{type:'attack'});
  a.equal(state.battle.enemies[0].hp,100);
  a.equal(state.battle.nextAttackAt,now+1000);
  denied(state,{type:'attack'});
  ok(state,{type:'advance',ms:999});
  denied(state,{type:'attack'});
  ok(state,{type:'advance',ms:1});
  ok(state,{type:'attack'});
  a.equal(state.battle.cue.kind,'pressure');
  a.equal(state.battle.enemies[0].hp,88,'The prepared pressure stance reduces damage to 12');
  a.equal(state.battle.nextAttackAt,now+2000);
});

test('An encounter cannot be replaced and combat cannot move or change mode',()=>{
  const state=M.initial();
  prove(state,'a_exam');
  start(state,'solo_a');
  for(const event of [
    {type:'start',encounter:'solo_a'},
    {type:'start',encounter:'solo_b'},
    {type:'mode',mode:'patient'},
    {type:'section',section:'B'},
    {type:'proof',id:'a_return'},
    {type:'target',boss:'unknown'}
  ])denied(state,event);
});

test('The C encounter contains both established bosses and needs both deaths for victory',()=>{
  const state=openBC();
  const rewardsBefore=state.rewards.length;
  const battle=start(state,'duo_c');
  a.deepEqual(battle.enemies.map(enemy=>enemy.id).sort(),['metronome','threshold']);
  a.deepEqual(battle.enemies.map(enemy=>enemy.maxHp).sort((left,right)=>left-right),[90,110]);
  const victim='metronome';
  ok(state,{type:'target',boss:victim});
  for(let attacks=0;state.battle.enemies.find(enemy=>enemy.id===victim).hp>0&&attacks<10;attacks++){
    attackReady(state);
    a.ok(state.battle);
    ok(state,{type:'attack'});
  }
  a.ok(state.battle,'One survivor keeps the shared encounter running');
  a.equal(state.battle.enemies.find(enemy=>enemy.id===victim).hp,0);
  a.equal(state.clears.duo_c,false);
  a.equal(state.rewards.length,rewardsBefore);
  denied(state,{type:'target',boss:victim});
  a.equal(state.battle.target,'threshold','Target moves to the remaining living boss');
  fightToEnd(state);
  a.equal(state.clears.duo_c,true);
  a.equal(state.rewards.length,rewardsBefore+1);
});

test('The shared cue sequence gives support its own time without an extra player hit',()=>{
  const state=openBC();
  start(state,'duo_c');
  ok(state,{type:'advance',ms:800});
  a.equal(state.battle.cue.kind,'pressure');
  a.deepEqual(state.battle.cue.actors,['threshold']);
  const first=copy(state.battle.cue);
  ok(state,{type:'advance',ms:first.resolveAt-state.now});
  a.equal(state.battle.playerHp,100-M.blueprint.bosses.threshold.damage);
  a.equal(state.battle.cue,null);
  a.ok(state.battle.nextCueAt>state.now,'The next cue has a recovery interval');
  ok(state,{type:'advance',ms:state.battle.nextCueAt-state.now});
  a.equal(state.battle.cue.kind,'signal');
  a.deepEqual(state.battle.cue.actors,['metronome']);
  a.notEqual(state.battle.cue.id,first.id);
  const hp=state.battle.playerHp;
  ok(state,{type:'advance',ms:state.battle.cue.resolveAt-state.now});
  a.equal(state.battle.playerHp,hp,'The support signal does not cause a second hit');
  a.equal(state.battle.buff,true);
  a.equal(state.battle.cue,null);
  a.ok(state.battle.nextCueAt>state.now);
});

test('Attacking Metronome cancels its pending solo signal and its original damage time',()=>{
  const state=openAB();
  prove(state,'b_record');
  start(state,'solo_b');
  a.equal(state.battle.enemies[0].maxHp,100);
  ok(state,{type:'advance',ms:800});
  a.ok(['signal','rhythm'].includes(state.battle.cue.kind));
  const resolution=state.battle.cue.resolveAt;
  ok(state,{type:'attack'});
  a.equal(state.battle.enemies[0].hp,80);
  a.equal(state.battle.cue,null);
  a.ok(state.battle.nextCueAt>state.now);
  ok(state,{type:'advance',ms:resolution-state.now});
  a.equal(state.battle.playerHp,100,'An interrupted cue never resolves later');
});

test('A dead Metronome cannot resolve its queued support or appear in later cues',()=>{
  const state=openBC();
  start(state,'duo_c');
  ok(state,{type:'target',boss:'metronome'});
  for(let hit=0;hit<4;hit++){
    attackReady(state);
    ok(state,{type:'attack'});
  }
  a.equal(state.battle.enemies.find(enemy=>enemy.id==='metronome').hp,10);
  attackReady(state);
  a.equal(state.battle.cue.kind,'signal');
  const resolution=state.battle.cue.resolveAt;
  const hp=state.battle.playerHp;
  ok(state,{type:'attack'});
  a.equal(state.battle.enemies.find(enemy=>enemy.id==='metronome').hp,0);
  a.equal(state.battle.cue,null,'Death cancels the cue owned by that actor');
  a.equal(state.battle.buff,false);
  denied(state,{type:'target',boss:'metronome'});
  ok(state,{type:'advance',ms:resolution-state.now});
  a.equal(state.battle.playerHp,hp);
  a.equal(state.battle.buff,false);
  for(let tick=0;tick<6;tick++){
    ok(state,{type:'advance',ms:500});
    if(state.battle.cue)a.deepEqual(state.battle.cue.actors,['threshold']);
  }
});

test('Killing Threshold cancels pending support instead of converting it into a solo hit',()=>{
  const state=openBC();
  start(state,'duo_c');
  // Six ordinary attacks leave Threshold at six demo HP. Wait through the next
  // pressure so that the finishing attack lands during a fresh support signal.
  for(let hit=0;hit<6;hit++){
    attackReady(state);
    ok(state,{type:'attack'});
  }
  a.equal(state.battle.enemies.find(enemy=>enemy.id==='threshold').hp,6);
  ok(state,{type:'advance',ms:state.battle.cue.resolveAt-state.now});
  a.equal(state.battle.buff,true);
  ok(state,{type:'advance',ms:state.battle.nextCueAt-state.now});
  a.equal(state.battle.cue.kind,'pressure');
  ok(state,{type:'advance',ms:state.battle.cue.resolveAt-state.now});
  ok(state,{type:'advance',ms:state.battle.nextCueAt-state.now});
  a.equal(state.battle.cue.kind,'signal');
  const oldCue=copy(state.battle.cue);
  const hp=state.battle.playerHp;
  ok(state,{type:'attack'});
  a.equal(state.battle.enemies.find(enemy=>enemy.id==='threshold').hp,0);
  a.equal(state.battle.target,'metronome');
  a.equal(state.battle.cue,null);
  a.equal(state.battle.buff,false);
  denied(state,{type:'target',boss:'threshold'});
  ok(state,{type:'advance',ms:oldCue.resolveAt-state.now});
  a.equal(state.battle.playerHp,hp,'The canceled support deadline causes no hidden hit');
  a.equal(state.battle.cue.kind,'rhythm','A solo strike receives its own new cue');
  a.notEqual(state.battle.cue.id,oldCue.id);
  a.ok(state.battle.cue.resolveAt>state.now);
  a.equal(M.restore(M.snapshot(state)).ok,true,'The surviving solo timeline is reloadable');
});

test('Killing either boss discards support already prepared for the pair',()=>{
  for(const victim of ['threshold','metronome']){
    const state=openBC();
    start(state,'duo_c');
    const battleStartedAt=state.now;
    ok(state,{type:'target',boss:victim});
    for(let hit=0;hit<(victim==='threshold'?6:4);hit++){
      attackReady(state);
      ok(state,{type:'attack'});
    }
    // The first signal resolves 5600ms into both routes, before another pressure.
    ok(state,{type:'advance',ms:battleStartedAt+5600-state.now});
    a.equal(state.battle.buff,true);
    a.equal(M.restore(M.snapshot(state)).ok,true,'Prepared support survives a valid reload');
    attackReady(state);
    ok(state,{type:'attack'});
    a.equal(state.battle.enemies.find(enemy=>enemy.id===victim).hp,0);
    a.equal(state.battle.buff,false,`The pair's support ends when ${victim} dies`);
    a.equal(M.restore(M.snapshot(state)).ok,true);
  }
});

test('Flee and defeat retain every completed proof without opening a gate',()=>{
  const state=M.initial();
  prove(state,'a_exam');
  const proofs=copy(state.proofs);
  start(state,'solo_a');
  ok(state,{type:'flee'});
  a.equal(state.battle,null);
  a.deepEqual(state.proofs,proofs);
  a.equal(state.clears.solo_a,false);
  a.equal(M.gates(state).AB.open,false);
  a.deepEqual(state.rewards,[]);
  start(state,'solo_a');
  for(let ticks=0;state.battle&&ticks<100;ticks++)ok(state,{type:'advance',ms:10000});
  a.equal(state.battle,null,'Ignoring cues eventually defeats the player');
  a.deepEqual(state.proofs,proofs);
  a.equal(state.clears.solo_a,false);
  a.deepEqual(state.rewards,[]);
});

test('Reload retains partial task progress and the exact active battle',()=>{
  let state=M.initial();
  prove(state,'a_exam');
  const proofs=copy(state.proofs);
  let restored=M.restore(M.snapshot(state));
  a.equal(restored.ok,true,restored.message);
  a.deepEqual(restored.state,state);
  a.deepEqual(restored.state.proofs,proofs);
  state=restored.state;
  start(state,'solo_a');
  ok(state,{type:'attack'});
  ok(state,{type:'advance',ms:137});
  restored=M.restore(M.snapshot(state));
  a.equal(restored.ok,true,restored.message);
  a.deepEqual(restored.state,state);
  a.notEqual(restored.state,state);
  a.notEqual(restored.state.battle,state.battle);
  const event={type:'advance',ms:863};
  a.deepEqual(M.apply(restored.state,event),M.apply(state,event));
  a.deepEqual(restored.state,state,'Reload gives the same next transition');
  a.ok(state.battle.cue,'The resumed timeline reaches a pending cue');
  const cueRestored=M.restore(M.snapshot(state));
  a.equal(cueRestored.ok,true,cueRestored.message);
  a.deepEqual(cueRestored.state,state,'Pending actor, cue, and resolution time survive reload');
});

test('First clear receipts survive reload and repeats never create another receipt',()=>{
  let state=openBC();
  win(state,'duo_c');
  a.equal(state.rewards.length,3,'Each encounter has one prototype first-clear receipt');
  const receipts=copy(state.rewards);
  const restored=M.restore(M.snapshot(state));
  a.equal(restored.ok,true,restored.message);
  state=restored.state;
  for(const encounter of encounterIds){
    win(state,encounter);
    a.deepEqual(state.rewards,receipts,`${encounter} repeat is idempotent`);
  }
  a.deepEqual(state.clears,{solo_a:true,solo_b:true,duo_c:true});
});

test('Queries and snapshots never mutate progress or expose mutable blueprint data',()=>{
  const state=openAB();
  const before=bytes(state);
  for(let pass=0;pass<3;pass++){
    const gates=M.gates(state);
    if(Object.isFrozen(gates.AB.missing))a.throws(()=>gates.AB.missing.push('local-only'),TypeError);
    else gates.AB.missing.push('local-only');
    for(const encounter of [...encounterIds,'missing']){
      const availability=M.availability(state,encounter);
      a.equal(typeof availability.available,'boolean');
      a.ok(Array.isArray(availability.missing));
      if(Object.isFrozen(availability.missing))a.throws(()=>availability.missing.push('local-only'),TypeError);
      else availability.missing.push('local-only');
    }
    a.equal(typeof M.snapshot(state),'string');
  }
  a.equal(bytes(state),before);
  a.ok(!M.gates(state).AB.missing.includes('local-only'));
});

test('Malformed and unsupported events refuse without changing state',()=>{
  const state=M.initial();
  for(const event of [
    null,{},[],{type:'unknown'},
    {type:'mode',mode:'unknown'},
    {type:'section',section:'D'},
    {type:'proof',id:'unknown'},
    {type:'start',encounter:'unknown'},
    {type:'advance',ms:0},{type:'advance',ms:-1},
    {type:'advance',ms:10001},{type:'advance',ms:NaN},
    {type:'advance',ms:Infinity},{type:'advance',ms:'1000'},
    {type:'target',boss:'threshold'},{type:'attack'},{type:'flee'}
  ])denied(state,event);
});

test('Restore rejects corrupted, foreign, future, and internally inconsistent saves',()=>{
  const fresh=M.initial();
  const altered=change=>{const state=copy(fresh);change(state);return JSON.stringify(state);};
  const invalid=[
    '',null,'{','null','[]','{}',
    altered(state=>state.brand='another-prototype'),
    altered(state=>state.version=99),
    altered(state=>state.mode='unknown'),
    altered(state=>state.section='D'),
    altered(state=>state.now=-1),
    altered(state=>state.attempt=-1),
    altered(state=>state.proofs.a_exam='yes'),
    altered(state=>delete state.proofs.a_plan),
    altered(state=>state.proofs.a_exam=true),
    altered(state=>state.clears.duo_c=true),
    altered(state=>state.rewards=[{kind:'forged'}]),
    altered(state=>state.battle={encounter:'solo_a'})
  ];
  for(const raw of invalid){
    const restored=M.restore(raw);
    a.equal(restored.ok,false,`Reject ${String(raw).slice(0,140)}`);
    a.equal(typeof restored.message,'string');
    a.ok(!restored.state,'A rejected save must not expose a playable partial state');
  }
  a.deepEqual(M.initial(),fresh,'Restore failures do not alter future initial states');
});

test('Restore rejects corrupted battle actors, cues, deadlines, and result receipts',()=>{
  const active=openBC();
  start(active,'duo_c');
  ok(active,{type:'advance',ms:800});
  const completed=openAB();
  const cases=[
    [active,state=>state.battle.enemies[0].hp=-1],
    [active,state=>state.battle.enemies[0].maxHp=999],
    [active,state=>state.battle.enemies[1].id='threshold'],
    [active,state=>state.battle.target='unknown'],
    [active,state=>state.battle.playerHp=0],
    [active,state=>state.battle.extra='unknown future field'],
    [active,state=>state.mode='patient'],
    [active,state=>state.battle.nextAttackAt=state.now+1001],
    [active,state=>state.battle.nextCueAt=state.now+1],
    [active,state=>state.battle.cue.actors=['threshold','metronome']],
    [active,state=>state.battle.cue.actors=['metronome']],
    [active,state=>state.battle.cue.resolveAt=state.now-1],
    [active,state=>state.battle.cue.resolveAt=state.now+2001],
    [active,state=>state.battle.cue.id='forged-cue'],
    [active,state=>state.battle.cue.kind='unknown'],
    [completed,state=>state.lastResult.enemies[0].hp=1],
    [completed,state=>state.lastResult.playerHp=0],
    [completed,state=>state.lastResult.receipt='floor9:first-clear:duo_c'],
    [completed,state=>state.lastResult.attempt='floor9-demo:99999'],
    [completed,state=>state.rewards.push(state.rewards[0])]
  ];
  for(const [valid,change] of cases){
    const state=copy(valid);
    change(state);
    const result=M.restore(JSON.stringify(state));
    a.equal(result.ok,false,'Corrupted active/completed battle must be refused');
    a.equal(result.state,null);
  }
});

test('Section queries reject unknown sections in both modes',()=>{
  const state=M.initial();
  for(const value of ['D','',null,undefined,903]){
    a.equal(M.accessible(state,value),false);
    denied(state,{type:'section',section:value});
  }
  mode(state,'trip');
  for(const value of ['D','',null,undefined,903])a.equal(M.accessible(state,value),false);
});

test('The last supported millisecond restores and further time fails atomically',()=>{
  const state=M.initial();
  state.now=1e12-1;
  let restored=M.restore(M.snapshot(state));
  a.equal(restored.ok,true,restored.message);
  ok(restored.state,{type:'advance',ms:1});
  a.equal(restored.state.now,1e12);
  const atLimit=M.restore(M.snapshot(restored.state));
  a.equal(atLimit.ok,true,atLimit.message);
  denied(atLimit.state,{type:'advance',ms:1});
  denied(atLimit.state,{type:'advance',ms:10000});
  state.now=1e12+1;
  restored=M.restore(M.snapshot(state));
  a.equal(restored.ok,false);
  a.equal(restored.state,null);
});

test('The last safe attempt can finish and starting beyond it fails atomically',()=>{
  const state=M.initial();
  prove(state,'a_exam');
  state.attempt=Number.MAX_SAFE_INTEGER-1;
  let restored=M.restore(M.snapshot(state));
  a.equal(restored.ok,true,restored.message);
  start(restored.state,'solo_a');
  a.equal(restored.state.attempt,Number.MAX_SAFE_INTEGER);
  a.equal(M.restore(M.snapshot(restored.state)).ok,true);
  ok(restored.state,{type:'flee'});
  restored=M.restore(M.snapshot(restored.state));
  a.equal(restored.ok,true,restored.message);
  denied(restored.state,{type:'start',encounter:'solo_a'});
  a.equal(restored.state.attempt,Number.MAX_SAFE_INTEGER);
});

test('Active battles and cues cannot import zero sequence numbers',()=>{
  const state=M.initial();
  prove(state,'a_exam');
  start(state,'solo_a');
  const noAttempt=copy(state);
  noAttempt.attempt=0;
  noAttempt.battle.id='floor9-demo:0';
  a.equal(M.restore(M.snapshot(noAttempt)).ok,false);
  ok(state,{type:'advance',ms:800});
  const noSerial=copy(state);
  noSerial.battle.serial=0;
  noSerial.battle.cue.id=noSerial.battle.id+':cue:0';
  a.equal(M.restore(M.snapshot(noSerial)).ok,false);
  a.equal(M.restore(M.snapshot(state)).ok,true,'The unmodified active cue remains valid');
});

test('A restored battle at the last safe cue sequence refuses its next cue atomically',()=>{
  const state=M.initial();
  prove(state,'a_exam');
  start(state,'solo_a');
  state.battle.serial=Number.MAX_SAFE_INTEGER;
  a.equal(state.battle.cue,null);
  const restored=M.restore(M.snapshot(state));
  a.equal(restored.ok,true,restored.message);
  denied(restored.state,{type:'advance',ms:restored.state.battle.nextCueAt-restored.state.now});
  a.equal(restored.state.battle.serial,Number.MAX_SAFE_INTEGER);
  a.equal(restored.state.battle.cue,null);
  a.equal(M.restore(M.snapshot(restored.state)).ok,true,'Refused cue creation leaves a valid snapshot');
});
