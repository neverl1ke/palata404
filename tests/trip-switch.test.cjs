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
 const unlocked=E.initial();unlocked.room='doctor';unlocked.flags.unlockB=true;unlocked.flags.unlockC=true;E.apply(unlocked,{type:'switch'});assert.equal(unlocked.room,'doctor');
});
test('battle prevents switching without changing state',()=>{
 const s=E.initial();s.battle='nurse';const before=JSON.stringify(s);assert.equal(E.apply(s,{type:'switch'}).ok,false);assert.equal(JSON.stringify(s),before);
});
test('patient always has all sections; trip opens A then B then C',()=>{
 const s=E.initial();for(const sec of ['A','B','C'])assert.equal(E.accessible(s,sec),true);
 E.apply(s,{type:'switch'});assert.equal(E.accessible(s,'A'),true);assert.equal(E.accessible(s,'B'),false);assert.equal(E.accessible(s,'C'),false);
 s.flags.unlockC=true;assert.equal(E.accessible(s,'C'),false);s.flags.unlockB=true;assert.equal(E.accessible(s,'B'),true);assert.equal(E.accessible(s,'C'),true);
 E.apply(s,{type:'switch'});for(const sec of ['A','B','C'])assert.equal(E.accessible(s,sec),true);
});
test('separate access override persists, exposes raids and does not award quests',()=>{
 const s=E.initial();s.mode='trip';const flags=JSON.stringify(s.flags),cargo=JSON.stringify(s.cargo);
 E.apply(s,{type:'unlockAll'});for(const sec of ['A','B','C'])assert.equal(E.accessible(s,sec),true);
 s.room='doctor';assert.ok(E.actions(s).some(x=>x.id==='boss:doctor'));
 assert.equal(E.restore(s).allSectionsUnlocked,true);assert.equal(JSON.stringify(s.flags),flags);assert.equal(JSON.stringify(s.cargo),cargo);assert.equal(s.transaction,0);
 E.apply(s,{type:'unlockAll'});assert.equal(s.room,'ward404');assert.equal(E.accessible(s,'B'),false);assert.equal(E.accessible(s,'C'),false);
});
