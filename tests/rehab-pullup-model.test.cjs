const{test}=require('node:test'),a=require('node:assert/strict'),P=require('../rehab-pullup-model.js');
function simulate(interval,limit=40){const s=P.initial();let next=0;while(s.time<limit&&!s.complete){if(s.time+1e-8>=next){P.tap(s);next+=interval;}P.step(s,1/120);}return s;}
function partial(){const s=P.initial();let next=0;while(s.lift<.5){if(s.time>=next){P.tap(s);next+=.12;}P.step(s,1/120);}return s;}
test('fast distinct clicks complete five repetitions; slow clicks cannot finish',()=>{
 const fast=simulate(.12),slower=simulate(.16),slow=simulate(.65);
 a.ok(fast.complete);a.ok(slower.complete);a.equal(fast.reps,5);a.ok(fast.time<slower.time);
 a.equal(slow.reps,0);a.equal(slow.complete,false);a.equal(slow.lift,0);
});
test('idle and isolated taps never lift or grant a repetition',()=>{
 for(const tap of[false,true]){const s=P.initial();if(tap)P.tap(s);for(let i=0;i<3600;i++)P.step(s,1/60);a.equal(s.reps,0);a.equal(s.complete,false);a.equal(s.lift,0);}
});
test('losing the rapid cadence starts descent within 220 ms rather than banking upward effort',()=>{
 const s=partial();P.step(s,.24);a.equal(s.motion,'down');const h=s.lift;P.step(s,.1);a.ok(s.lift<h);
 P.step(s,1);a.equal(s.lift,0);a.equal(s.reps,0);
});
test('a late slow click does not reverse a failed attempt into an ascent',()=>{
 const s=partial();P.step(s,.32);const h=s.lift;a.ok(P.tap(s));P.step(s,.04);a.ok(s.lift<h);a.equal(s.motion,'down');
});
test('the peak immediately enters automatic descent and does not accept clicks until the bottom',()=>{
 const s=P.initial();s.lift=.999;s.effort=1;s.lastTap=0;P.step(s,.01);
 a.equal(s.reps,1);a.equal(s.phase,'down');const top=s.lift;P.step(s,.01);a.ok(s.lift<top);a.equal(P.tap(s),false);
 P.step(s,.6);a.equal(s.lift,0);a.equal(s.phase,'up');a.equal(s.reps,1);a.equal(s.effort,0);
});
test('the fifth repetition also returns to the hanging pose and the completed set stays capped',()=>{
 const s=simulate(.1);a.equal(s.reps,5);a.ok(s.complete);a.equal(s.phase,'down');P.step(s,.7);
 a.equal(s.lift,0);a.equal(s.phase,'complete');const copy=JSON.stringify(s);a.equal(P.tap(s),false);P.step(s,NaN);P.step(s,1);a.equal(JSON.stringify(s),copy);
});
test('simultaneous click spam is capped and full elapsed frames still recognize an input pause',()=>{
 const s=P.initial();a.ok(P.tap(s));for(let i=0;i<100;i++)a.equal(P.tap(s),false);a.equal(s.taps,1);
 const d=partial();const oldTime=d.time;P.step(d,.4);a.ok(d.time-oldTime>.399);a.equal(d.motion,'down');
});
