const {test}=require('node:test');
const assert=require('node:assert/strict');
const E=require('../quest-engine.js');
test('switches in an accessible saved room, persists and leaves progress intact',()=>{
 const s=E.initial();s.room='A';s.flags.unlockB=true;s.cargo=['baseline'];s.transaction=4;
 assert.equal(E.apply(s,{type:'switch'}).ok,true);assert.equal(s.mode,'trip');assert.equal(s.room,'A');assert.equal(s.trip,1);
 const restored=E.restore(s);assert.equal(restored.mode,'trip');assert.equal(restored.room,'A');
 assert.equal(E.apply(s,{type:'switch'}).ok,true);assert.equal(s.mode,'patient');assert.equal(s.transaction,4);assert.deepEqual(s.cargo,['baseline']);assert.equal(s.flags.unlockB,true);
});
test('switching never bypasses locked sections',()=>{
 const s=E.initial();s.room='doctor';assert.equal(E.apply(s,{type:'switch'}).ok,true);assert.equal(s.room,'ward404');assert.equal(s.flags.unlockC,undefined);
 const unlocked=E.initial();unlocked.room='doctor';unlocked.flags.unlockC=true;E.apply(unlocked,{type:'switch'});assert.equal(unlocked.room,'doctor');
});
test('battle prevents switching without changing state',()=>{
 const s=E.initial();s.battle='nurse';const before=JSON.stringify(s);assert.equal(E.apply(s,{type:'switch'}).ok,false);assert.equal(JSON.stringify(s),before);
});
