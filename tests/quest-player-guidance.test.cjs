'use strict';
const {test}=require('node:test');
const a=require('node:assert/strict');
const E=require('../quest-engine.js');
const clone=value=>JSON.parse(JSON.stringify(value));
function apply(s,event){const result=E.apply(s,event);a.equal(result.ok,true,result.message);a.equal(result.reward??null,null);return result;}
function go(s,room){apply(s,{type:'move',room});}
function inspectStairs(s){apply(s,{type:'interact',id:'stairsPatient',choice:'sign'});apply(s,{type:'interact',id:'stairsPatient',choice:'mark'});}

test('a fresh early stair inspection derives its route on the last real Patient sector visit',()=>{
 const s=E.initial();go(s,'stairs');inspectStairs(s);
 a.deepEqual(s.visited,{A:true,C:true});a.equal(s.flags.stairsSeen,true);a.equal(s.flags.route,false);
 const before=clone(s);go(s,'B');a.deepEqual(s.visited,{A:true,B:true,C:true});a.equal(s.flags.route,true);
 for(const key of ['jobs','world','cargo','transaction','collectorCount'])a.deepEqual(s[key],before[key],key+' changed while walking');
 a.equal(s.flags.unlockB,undefined);a.equal(s.flags.unlockC,undefined);a.equal(s.flags.doctorWon,undefined);a.equal(s.flags.exit,undefined);
 a.equal(E.accessible({...s,mode:'trip'},'B'),false);a.equal(E.accessible({...s,mode:'trip'},'C'),false);
 go(s,'stairs');a.equal(E.actions(s).some(action=>action.id==='stairsPatient'),false,'the completed inspection need not be repeated');
 const restored=E.restore(clone(s));a.equal(restored.flags.route,true);a.deepEqual(restored.visited,s.visited);
});

test('failed travel and wrong stair choices remain fully atomic and do not derive knowledge',()=>{
 const s=E.initial();s.mode='trip';s.visited={A:true,B:true,C:true};s.flags.stairsSeen=true;s.flags.route=false;
 const before=clone(s);a.equal(E.apply(s,{type:'move',room:'B'}).ok,false);a.deepEqual(s,before);
 s.mode='patient';go(s,'stairs');s.flags.stairsSeen=false;s.flags.route=false;
 const wrong=clone(s);a.equal(E.apply(s,{type:'interact',id:'stairsPatient',choice:'wall'}).ok,false);a.deepEqual(s,wrong);
});

test('restore derives a stale route from complete saved facts without changing raw bytes or unrelated progress',()=>{
 const raw={...E.initial(),room:'B',visited:{A:true,B:true,C:true},flags:{stairsSeen:true,route:false},transaction:17,cargo:['log']};
 const serialized=JSON.stringify(raw),restored=E.restore(raw);
 a.equal(JSON.stringify(raw),serialized);a.equal(restored.flags.route,true);a.equal(restored.flags.stairsSeen,true);
 a.equal(restored.transaction,17);a.deepEqual(restored.cargo,['log']);a.deepEqual(restored.jobs,{});a.deepEqual(restored.world,raw.world);
 a.deepEqual(E.restore(clone(restored)),restored,'normalization must be idempotent');
});

test('missing visits or an absent stair inspection cannot invent a route or unlock a gate',()=>{
 for(const missing of ['A','B','C','stairsSeen']){
  const raw={...E.initial(),visited:{A:true,B:true,C:true},flags:{stairsSeen:true,route:false}};
  if(missing==='stairsSeen')raw.flags.stairsSeen=false;else raw.visited[missing]=false;
  const result=E.restore(raw);a.equal(result.flags.route,false,missing);a.equal(result.flags.exit,false);a.equal(result.flags.doctorWon,false);
  a.equal(E.accessible({...result,mode:'trip'},'B'),false);a.equal(E.accessible({...result,mode:'trip'},'C'),false);
 }
});

test('legacy positive route knowledge survives incomplete visit records, subsequent actions and reload',()=>{
 for(const version of [1,6,9]){
  const raw={...E.initial(),version,room:'collector',visited:{},flags:{route:true},collectorCount:0,collectorAt:0};
  const serialized=JSON.stringify(raw),restored=E.restore(raw);a.equal(restored.flags.route,true);a.equal(JSON.stringify(raw),serialized);
  const response=E.apply(restored,{type:'action',id:'collect'},60001);a.equal(response.ok,true);a.equal(restored.flags.route,true);
  a.equal(restored.flags.exit,false);a.equal(restored.flags.unlockB,false);a.equal(restored.flags.unlockC,false);
  const again=E.restore(clone(restored));a.equal(again.flags.route,true);a.deepEqual(E.restore(clone(again)),again);
 }
});

test('Trip travel does not count as a missing Patient sector visit',()=>{
 const s=E.initial();go(s,'stairs');inspectStairs(s);apply(s,{type:'switch'});apply(s,{type:'unlockAll'});
 const before=clone(s.visited);go(s,'B');a.deepEqual(s.visited,before);a.equal(s.flags.route,false);
 apply(s,{type:'switch'});go(s,'nurse');a.equal(s.visited.B,true);a.equal(s.flags.route,true);
 a.equal(s.flags.unlockB,undefined);a.equal(s.flags.unlockC,undefined);
});
