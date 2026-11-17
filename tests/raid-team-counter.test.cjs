'use strict';
const {test}=require('node:test');
const a=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');

// Reuse the existing actual-script VM fixture without registering its test suite.
// That fixture controls timeout timestamps; intervals are driven explicitly below
// at their real3.5s cadence. Browser checkpoint integration is tested separately.
const fixture=fs.readFileSync(path.join(__dirname,'game-logic.test.cjs'),'utf8');
const end=fixture.indexOf('\ntest(');
a.ok(end>0,'The shared game fixture must precede its test registrations');
const host={require,__dirname,console,URLSearchParams};
vm.runInNewContext(fixture.slice(0,end)+'\nglobalThis.makeGame=game;',host,{filename:'game-fixture.cjs'});
function game(boss='doctor'){
 const g=host.makeGame();
 g.run(`stats.baseArmor=40; recalculateEquipmentStats(); startBossFight(${JSON.stringify(boss)}); Math.random=()=>0.5;`);
 a.equal(g.run('stats.armor'),40);
 return g;
}
const read=g=>JSON.parse(g.run('JSON.stringify(pendingBossCounters())'));
const counters=g=>g.run('[...currentBattleSession.events].filter(id=>id.endsWith(":counter")).length');
function volley(g,count=3){g.run(`raidMembers.forEach(m=>{if(!m.isPlayer){m.called=false;m.active=false}});for(let i=1;i<=${count};i++){raidMembers[i].called=true;raidMembers[i].active=true;}friendsAutoAttackTick();`);}

// Doctor25damage reduced by the unchanged40armor formula is18HP.
test('three allies cause one real-time boss response per volley while their outgoing damage is unchanged',()=>{
 const g=game();g.advance(3500);volley(g);
 a.equal(g.run('bossCurrentHp'),226);a.equal(g.run('raidMembers[0].damage'),0);
 a.equal(g.run('raidMembers.filter(m=>!m.isPlayer).every(m=>m.damage===8&&m.metrics.turns===1)'),true);
 a.equal(read(g).length,1);a.equal(g.run('stats.hp'),100);g.advance(499);a.equal(g.run('stats.hp'),100);g.advance(1);
 a.equal(g.run('stats.hp'),82);a.equal(g.run('raidMembers[0].metrics.damageTaken'),18);a.equal(g.run('raidMembers[0].metrics.turns'),0);a.equal(counters(g),1);a.deepEqual(read(g),[]);
 g.advance(3000);volley(g);a.equal(g.run('bossCurrentHp'),202);g.advance(500);a.equal(g.run('stats.hp'),64);a.equal(counters(g),2);
});

test('one or three called allies create one response; an empty or inactive team creates none',()=>{
 for(const count of [1,3]){const g=game();g.advance(3500);volley(g,count);a.equal(read(g).length,1);a.equal(g.run('250-bossCurrentHp'),count*8);g.advance(500);a.equal(g.run('stats.hp'),82);a.equal(counters(g),1);}
 const g=game();g.advance(3500);volley(g,0);a.deepEqual(read(g),[]);g.advance(500);a.equal(g.run('stats.hp'),100);a.equal(counters(g),0);
 g.run('raidMembers[1].called=true;raidMembers[1].active=false;friendsAutoAttackTick()');a.deepEqual(read(g),[]);
});

test('player cooldown and500ms response remain intact with the original armor reduction',()=>{
 const g=game();g.run('performPlayerAttack();performPlayerAttack()');a.equal(g.run('bossCurrentHp'),240);a.equal(read(g).length,1);a.equal(g.run('raidMembers[0].metrics.turns'),1);
 g.advance(499);a.equal(g.run('stats.hp'),100);g.advance(1);a.equal(g.run('stats.hp'),82);a.equal(counters(g),1);
});

test('overlapping player and helper actions own two responses instead of losing or tripling timers',()=>{
 const g=game();g.run('performPlayerAttack()');g.advance(100);volley(g);
 a.equal(read(g).length,2);a.equal(g.run('bossCounterQueue.size'),2);a.equal(g.run('bossCurrentHp'),216);
 g.advance(400);a.equal(g.run('stats.hp'),82);a.equal(read(g).length,1);g.advance(100);a.equal(g.run('stats.hp'),64);a.equal(counters(g),2);a.equal(g.run('bossCounterQueue.size'),0);
});

test('an actual lethal helper volley cancels an overlapping player response and awards victory only once',()=>{
 const g=game('nurse');
 g.run('var prematureTerminalSaves=[];window.CustomEvent=function(type){this.type=type};window.dispatchEvent=event=>{if(event.type==="raid-counter-state"&&currentBattleSession.finished&&!pendingBattleReward&&!lastBattleResult)prematureTerminalSaves.push(currentBattleSession.id)}');
 for(let i=0;i<4;i++){g.advance(i===0?3500:3000);volley(g);g.advance(500);}
 a.equal(g.run('bossCurrentHp'),24);a.equal(g.run('stats.hp'),64);a.equal(counters(g),4);
 g.advance(2900);g.run('performPlayerAttack()');a.equal(g.run('bossCurrentHp'),14);a.equal(read(g).length,1);
 g.advance(100);volley(g);a.equal(g.run('isBattleActive'),false);a.equal(g.run('bossCurrentHp'),0);a.deepEqual(read(g),[]);a.equal(g.run('bossCounterQueue.size'),0);
 a.equal(g.run('prematureTerminalSaves.length'),0,'Cleanup must not checkpoint a terminal raid before the result/reward commit');
 const result=g.run('JSON.stringify(lastBattleResult)'),silver=g.run('stats.silver');a.equal(g.run('stats.bossesKilled'),1);a.equal(g.run('lastBattleResult.totalDamage'),120);
 g.advance(1000);g.run('handleVictory()');a.equal(g.run('stats.hp'),64);a.equal(counters(g),4);a.equal(g.run('stats.bossesKilled'),1);a.equal(g.run('stats.silver'),silver);a.equal(g.run('JSON.stringify(lastBattleResult)'),result);
});

// Simulate the queue portion of a checkpoint restore using the exact stored
// session/event IDs and original absolute deadlines. Full page reload belongs to
// the prototype/browser tests, not to this isolated scheduler fixture.
test('restored pending counters retain the original deadline and duplicate restoration cannot double-hit',()=>{
 const g=game();g.advance(3500);volley(g);const pending=read(g);g.advance(200);
 g.run('var originalEnd=raidEndsAt;stopBattleTimers();isBattleActive=true;raidEndsAt=originalEnd;');
 a.equal(g.run(`restoreBossCounter(${JSON.stringify(pending[0][0])},${pending[0][1]})`),true);
 a.equal(g.run(`restoreBossCounter(${JSON.stringify(pending[0][0])},${pending[0][1]})`),false);a.deepEqual(read(g),pending);
 g.advance(299);a.equal(g.run('stats.hp'),100);g.advance(1);a.equal(g.run('stats.hp'),82);a.equal(counters(g),1);
 a.equal(g.run(`restoreBossCounter(${JSON.stringify(pending[0][0])},${pending[0][1]})`),false);g.advance(1000);a.equal(g.run('stats.hp'),82);a.equal(counters(g),1);
});

test('an overdue restored response resolves once without restarting its delay',()=>{
 const g=game();g.advance(3500);volley(g);const pending=read(g);g.advance(200);g.run('var originalEnd=raidEndsAt;isBattleActive=false;stopBattleTimers()');g.advance(1000);
 g.run('isBattleActive=true;raidEndsAt=originalEnd');a.equal(g.run(`restoreBossCounter(${JSON.stringify(pending[0][0])},${pending[0][1]})`),true);a.equal(g.run('stats.hp'),100);g.advance(0);a.equal(g.run('stats.hp'),82);a.equal(counters(g),1);a.deepEqual(read(g),[]);
});

test('pending exports are detached and only recorded attack triggers and finite absolute restore times are accepted',()=>{
 const g=game();volley(g);const original=read(g);
 g.run('var exported=pendingBossCounters();exported[0][0]="fake";exported[0][1]=0;exported.push(["fake",0])');a.deepEqual(read(g),original);
 for(const expression of ['restoreBossCounter("fake",Date.now())','restoreBossCounter("fake",undefined)','restoreBossCounter("fake",NaN)','restoreBossCounter("fake",Infinity)','restoreBossCounter("fake",-1)','queueBossCounter("fake")'])a.equal(g.run(expression),false);
 g.run('var recoveryId=nextBattleEventId("recovery");recordBattleEvent(recoveryId,raidMembers[0],{healing:0})');a.equal(g.run('queueBossCounter(recoveryId)'),false);
 a.equal(g.run('queueBossCounter(pendingBossCounters()[0][0])'),false);a.equal(read(g).length,1);
});

test('a stale callback cannot delete a replacement entry with the same ID or affect a new generation',()=>{
 const g=game();volley(g);g.run('var id=pendingBossCounters()[0][0],due=pendingBossCounters()[0][1],old=bossCounterQueue.get(id),originalEnd=raidEndsAt;stopBattleTimers();isBattleActive=true;raidEndsAt=originalEnd;restoreBossCounter(id,due)');
 a.equal(g.run('resolveBossCounter(id,old)'),false);a.equal(read(g).length,1);g.advance(500);a.equal(g.run('stats.hp'),82);a.equal(counters(g),1);
 const other=game();volley(other);other.run('battleGeneration++');other.advance(500);a.equal(other.run('stats.hp'),100);a.equal(counters(other),0);a.equal(other.run('bossCounterQueue.size'),0);
});

test('flee, defeat, timeout and a new battle cancel all pending entries without post-combat damage',()=>{
 const fled=game();fled.run('performPlayerAttack()');volley(fled);a.equal(read(fled).length,2);fled.run('openFleeConfirmModal();startBossFight("nurse")');a.equal(fled.run('bossCounterQueue.size'),0);fled.advance(1000);a.equal(fled.run('stats.hp'),100);a.equal(counters(fled),0);a.equal(fled.run('stats.bossesKilled'),0);
 const lost=game();lost.run('stats.hp=1;performPlayerAttack()');volley(lost);lost.advance(500);a.equal(lost.run('isBattleActive'),false);a.equal(lost.run('stats.hp'),100);a.equal(lost.run('bossCounterQueue.size'),0);a.equal(counters(lost),1);a.equal(lost.run('raidMembers[0].metrics.damageTaken'),1);lost.advance(1000);a.equal(lost.run('stats.hp'),100);a.equal(lost.run('stats.bossesKilled'),0);
 const expired=game();volley(expired);expired.run('raidEndsAt=Date.now()+100');expired.advance(500);a.equal(expired.run('isBattleActive'),false);a.equal(expired.run('bossCounterQueue.size'),0);a.equal(expired.run('stats.hp'),100);a.equal(counters(expired),0);a.equal(expired.run('stats.bossesKilled'),0);
});

test('a saved counter event or a different live session cannot receive another response',()=>{
 const saved=game();volley(saved);saved.run('var id=pendingBossCounters()[0][0];recordBattleEvent(id+":counter",raidMembers[0],{damageTaken:18})');saved.advance(500);a.equal(saved.run('stats.hp'),100);a.equal(counters(saved),1);a.equal(saved.run('raidMembers[0].metrics.damageTaken'),18);a.deepEqual(read(saved),[]);
 const switched=game();volley(switched);switched.run('currentBattleSession={...currentBattleSession,id:"different-session",events:new Set()}');switched.advance(500);a.equal(switched.run('stats.hp'),100);a.equal(counters(switched),0);a.equal(switched.run('bossCounterQueue.size'),0);
});

test('queue changes emit the optional checkpoint event and remain safe without DOM event constructors',()=>{
 const g=game();g.run('var signals=0;window.CustomEvent=function(type){this.type=type};window.dispatchEvent=event=>{if(event.type==="raid-counter-state")signals++}');
 volley(g);a.equal(g.run('signals'),1);g.advance(500);a.equal(g.run('signals'),2);volley(g);a.equal(g.run('signals'),3);g.run('stopBattleTimers()');a.equal(g.run('signals'),4);
 const plain=game();volley(plain);plain.advance(500);a.equal(plain.run('stats.hp'),82);
});
