const {test}=require('node:test');
const assert=require('node:assert/strict');
const E=require('../quest-engine.js');
const N=require('../quest-navigation.js');

const state=()=>E.initial();
function active(s,id,done={}){
 s.jobs[id]={active:true,count:0,done,startTrip:0};
 return s;
}

test('wrong mode keeps the real destination instead of highlighting the current room',()=>{
 const s=active(state(),'k1');s.mode='trip';s.room='nurse';
 const result=N.guide(E,s,'k1');
 assert.equal(result.room,'procedure');assert.equal(result.mode,'patient');assert.equal(result.needsModeChange,true);
 assert.doesNotMatch(result.text,/Б.?17|Б.?71/);
});

test('side-job directions follow work and proof hand-in rather than revealing answers',()=>{
 const s=active(state(),'k2');s.room='nurse';
 assert.equal(N.guide(E,s,'k2').room,'linen');
 s.jobs.k2.done.linen=true;s.cargo=['linen'];
 assert.equal(N.guide(E,s,'k2').room,'ward406');
 s.jobs.k2.done.deliver=true;s.cargo=['delivery'];
 const ready=N.guide(E,s,'k2');assert.equal(ready.room,'nurse');assert.equal(ready.mode,'patient');
 const d=active(state(),'d1');
 assert.equal(N.guide(E,d,'d1').room,'ward407');
 d.jobs.d1.done.bell407=true;
 const second=N.guide(E,d,'d1');assert.equal(second.room,'ward408');assert.doesNotMatch(second.text,/исправна|неисправна/);
});

test('new observation first routes to a Patient baseline, then a genuinely new Trip',()=>{
 const s=active(state(),'d3');s.room='doctor';s.trip=4;
 Object.assign(s.jobs.d3,{revision:2,startTrip:4,work:{baselineCaptured:false}});
 let g=N.guide(E,s,'d3');assert.equal(g.room,'A');assert.equal(g.mode,'patient');assert.equal(g.needsModeChange,false);
 s.jobs.d3.work.baselineCaptured=true;
 g=N.guide(E,s,'d3');assert.equal(g.room,'A');assert.equal(g.mode,'trip');assert.equal(g.needsModeChange,true);
 s.mode='trip';g=N.guide(E,s,'d3');assert.equal(g.mode,'patient');assert.equal(g.requiresNewTrip,true);
 s.trip=5;g=N.guide(E,s,'d3');assert.equal(g.room,'A');assert.equal(g.mode,'trip');assert.equal(g.needsModeChange,false);
 assert.doesNotMatch(g.text,/08:00|03:00|изменилось время/);
 s.jobs.d3.done.difference=true;s.cargo=['difference'];
 g=N.guide(E,s,'d3');assert.equal(g.room,'doctor');assert.equal(g.mode,'patient');
});

test('legacy observation retains its issued baseline and old progress can be submitted',()=>{
 const s=active(state(),'d3');s.cargo=['baseline'];
 let g=N.guide(E,s,'d3');assert.equal(g.mode,'trip');assert.equal(g.room,'A');
 s.jobs.d3.revision=1;s.jobs.d3.done.difference=true;s.cargo=['difference'];
 g=N.guide(E,s,'d3');assert.equal(g.room,'doctor');assert.equal(g.mode,'patient');
 const k=state();k.jobs.k1={active:false,count:1,done:{tag:true}};
 assert.equal(N.guide(E,k,'k1').complete,true);
});

test('blocked C explains its first unmet access condition and accessible gates stay accessible',()=>{
 const s=state();s.mode='trip';s.room='ward404';
 let b=N.blocked(E,s,'C');assert.equal(b.accessible,false);assert.equal(b.section,'C');assert.equal(b.room,'A');assert.equal(b.mode,'patient');
 assert.match(b.text,/через секцию B/);assert.doesNotMatch(b.text,/прижмите.*поверните.*потяните/);
 Object.assign(s.flags,{doorKnown:true,reserveKnown:true,tripHandle:true});
 b=N.blocked(E,s,'B');assert.equal(b.room,'A');assert.equal(b.mode,'trip');
 s.flags.unlockB=true;b=N.blocked(E,s,'C');assert.equal(b.room,'procedure');assert.equal(b.mode,'patient');
 s.flags.cKeyKnown=true;b=N.blocked(E,s,'C');assert.equal(b.room,'doctor');
 s.flags.cLockKnown=true;b=N.blocked(E,s,'C');assert.equal(b.room,'B');assert.equal(b.mode,'trip');
 s.flags.unlockC=true;assert.equal(N.blocked(E,s,'C').accessible,true);
 s.flags.unlockB=false;s.flags.unlockC=false;s.mode='patient';assert.equal(N.blocked(E,s,'C').accessible,true);
 s.mode='trip';s.allSectionsUnlocked=true;assert.equal(N.blocked(E,s,'C').accessible,true);
 assert.equal(N.guide(E,s,'С3').room,'A','story tasks retain their genuine prerequisites despite test unlock');
});

test('exit guidance finds the missing route observation and preserves the doctor condition',()=>{
 const s=state();s.mode='trip';Object.assign(s.flags,{unlockB:true,unlockC:true});
 let g=N.guide(E,s,'С4');assert.equal(g.room,'doctor');assert.equal(g.mode,'trip');
 s.flags.doctorWon=true;s.visited={A:true,B:true,C:false};
 g=N.guide(E,s,'С4');assert.equal(g.room,'C');assert.equal(g.mode,'patient');
 s.visited.C=true;g=N.guide(E,s,'С4');assert.equal(g.room,'stairs');assert.equal(g.mode,'patient');
 s.flags.route=true;g=N.guide(E,s,'С4');assert.equal(g.room,'stairs');assert.equal(g.mode,'trip');
});

test('future floor is explicitly unavailable and has no navigation target',()=>{
 const s=state();const original=E.story(s),before=JSON.stringify(original),rows=N.story({...E,story:()=>original},s);
 const future=rows.find(x=>x.id==='С5');assert.equal(future.pending,true);assert.equal(future.available,false);assert.equal(future.done,false);
 const g=N.guide(E,s,'С5');assert.equal(g.room,null);assert.equal(g.pending,true);assert.equal(g.needsModeChange,false);
 assert.match(rows.find(x=>x.id==='С2').title,/привод/);assert.doesNotMatch(rows.find(x=>x.id==='С2').title,/питания/);
 assert.equal(JSON.stringify(original),before);
});

test('all directions are read-only and the default map text contains no solved sequence',()=>{
 const s=active(state(),'d3');s.jobs.d3.revision=2;s.jobs.d3.work={baselineCaptured:true};s.mode='trip';s.trip=1;
 const copy=JSON.stringify(s);
 for(const id of ['С1','П3','П4','С2','С3','С4','С5',...Object.keys(E.jobs),'unknown'])N.guide(E,s,id);
 for(const section of ['A','B','C','unknown'])N.blocked(E,s,section);
 N.story(E,s);const hint=N.mapHint(E,s);
 assert.equal(JSON.stringify(s),copy);assert.doesNotMatch(hint,/прижать.*повернуть|прижмите.*поверните|Б.?17|03:00/);
});
