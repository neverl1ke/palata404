const {test}=require('node:test'),a=require('node:assert/strict'),{game}=require('./quest-game-fixture.cjs');
function route(g){for(const [k,v] of [['room','A'],['action','inspectDoor'],['room','collector'],['action','supplyNote'],['room','B'],['room','procedure'],['action','record'],['room','B'],['room','C'],['room','doctor'],['action','observation'],['room','stairs'],['action','stairsPatient'],['room','C'],['room','B'],['room','A'],['room','ward404']])g.click(k,v);}
test('actual adapter, map action buttons, existing combat and reward persistence',()=>{const original='{"silver":1234}';const g=game({palata404_stats:original});route(g);g.switch();g.click('room','collector');g.click('action','takeHandle');g.click('room','A');g.click('action','unlockB');g.click('room','B');g.click('action','unlockC');g.click('room','C');g.click('room','doctor');g.click('action','boss:doctor');a.equal(g.run('isBattleActive'),true);g.run('bossCurrentHp=0;handleVictory()');a.equal(g.state().flags.doctorWon,true);const silver=g.run('stats.silver');g.run('handleVictory()');a.equal(g.run('stats.silver'),silver);g.click('room','stairs');g.click('action','exit');a.equal(g.state().flags.exit,true);a.equal(g.storage.get('palata404_stats'),original);const reload=game(Object.fromEntries(g.storage));a.equal(reload.state().flags.exit,true);a.equal(reload.state().room,'stairs');a.equal(reload.state().mode,'trip');});
test('legacy direct entry cannot bypass trip gates; map close cannot enable remote switch',()=>{const g=game();g.run('startDoctorFight()');a.equal(g.run('isBattleActive'),false);g.click('room','A');g.run('toggleMapModal(false)');g.switch();a.equal(g.state().mode,'patient');g.run('devSetMadness(100)');a.equal(g.run('stats.madness'),0);});
test('retreat records actual raid without reward and returns to 404 in trip',()=>{const g=game();route(g);g.switch();g.click('room','collector');g.click('action','takeHandle');g.click('room','A');g.click('action','unlockB');g.click('room','B');g.click('room','nurse');g.click('action','boss:nurse');const before=g.run('stats.silver');g.run("recordUnrewardedRaid('escape');isBattleActive=false;stopBattleTimers();updateUI()");a.equal(g.state().room,'ward404');a.equal(g.state().mode,'trip');a.equal(g.run('stats.silver'),before);});
test('unavailable storage shows warning and still supports session navigation',()=>{const g=game({},true);g.click('room','A');a.match(g.elements.get('quest-save').textContent,/недоступно/);a.equal(g.state().room,'A');});
test('sandbox clear only removes prefixed data and entry cannot redirect to main game',()=>{const g=game({palata404_stats:'{"silver":777}',other:'keep'});g.run('window.localStorage.clear()');a.equal(g.storage.get('palata404_stats'),'{"silver":777}');a.equal(g.storage.get('other'),'keep');a.equal(g.storage.size,2);const fs=require('node:fs'),path=require('node:path');const html=fs.readFileSync(path.join(__dirname,'../quest-test.html'),'utf8');a.ok(!html.includes('src="landscape-entry.js'));a.ok(html.indexOf('quest-sandbox.js')<html.indexOf('src="script.js'));a.match(fs.readFileSync(path.join(__dirname,'../quest-shell.js'),'utf8'),/new URL\('quest-test.html'/);});

function nurse(g){route(g);g.switch();g.click('room','collector');g.click('action','takeHandle');g.click('room','A');g.click('action','unlockB');g.click('room','nurse');g.click('action','boss:nurse');}
test('live raid reload retains identity, HP, deadline, damage, cooldown and pending counter',()=>{
 const g=game();nurse(g);g.run('performPlayerAttack()');const before=g.run('({id:currentBattleSession.id,hp:bossCurrentHp,ends:raidEndsAt,cooldown:attackCooldownEndsAt,damage:raidMembers[0].damage,player:stats.hp})');
 const r=game(Object.fromEntries(g.storage));a.equal(r.run('isBattleActive'),true);a.equal(r.run('currentBattleSession.id'),before.id);a.equal(r.run('bossCurrentHp'),before.hp);a.equal(r.run('raidEndsAt'),before.ends);a.equal(r.run('attackCooldownEndsAt'),before.cooldown);a.equal(r.run('raidMembers[0].damage'),before.damage);
 r.advance(500);a.ok(r.run('stats.hp')<before.player);const hp=r.run('stats.hp');r.advance(500);a.equal(r.run('stats.hp'),hp);
 r.run('bossCurrentHp=0;handleVictory()');const silver=r.run('stats.silver');const again=game(Object.fromEntries(r.storage));a.equal(again.run('isBattleActive'),false);a.equal(again.run('stats.silver'),silver);again.run('handleVictory()');a.equal(again.run('stats.silver'),silver);
});
test('unknown and malformed quest saves are never overwritten',()=>{
 for(const raw of ['{broken',JSON.stringify({version:999,treasure:42})]){const key='palata404_quest_test_v1:quest_progress';const g=game({[key]:raw});g.click('room','A');a.equal(g.storage.get(key),raw);}
});
test('legacy incomplete battle keeps a recovery copy and no invented reward',()=>{
 const key='palata404_quest_test_v1:quest_progress',raw=JSON.stringify({version:1,mode:'trip',room:'nurse',battle:'nurse',flags:{unlockB:true},materials:7});const g=game({[key]:raw});a.equal(g.storage.get('palata404_quest_test_v1:quest_progress_recovery'),raw);a.equal(g.state().materials,7);a.equal(g.run('isBattleActive'),false);a.equal(g.state().room,'ward404');
});
test('repeated real raids have distinct IDs, payouts once per raid, and do not open C',()=>{
 const g=game();nurse(g);const id=g.run('currentBattleSession.id');g.run('bossCurrentHp=0;handleVictory()');const silver=g.run('stats.silver');a.equal(!!g.state().flags.unlockC,false);g.click('action','boss:nurse');a.notEqual(g.run('currentBattleSession.id'),id);g.run('bossCurrentHp=0;handleVictory()');a.ok(g.run('stats.silver')>silver);a.equal(g.run('readRaidArchive().length'),2);
});

test('damaged live checkpoint is backed up without crashing or paying a reward',()=>{
 const g=game();nurse(g);const key='palata404_quest_test_v1:quest_progress';const raw=JSON.parse(g.storage.get(key));raw.raid.counters={broken:true};g.storage.set(key,JSON.stringify(raw));const r=game(Object.fromEntries(g.storage));a.equal(r.run('isBattleActive'),false);a.equal(r.state().room,'ward404');a.equal(r.storage.get('palata404_quest_test_v1:quest_progress_recovery'),JSON.stringify(raw));
});
test('stale pre-victory checkpoint reconciles with reward ledger without paying twice',()=>{
 const g=game();nurse(g);const key='palata404_quest_test_v1:quest_progress',checkpoint=g.storage.get(key);g.run('bossCurrentHp=0;handleVictory()');const silver=g.run('stats.silver');g.storage.set(key,checkpoint);const r=game(Object.fromEntries(g.storage));a.equal(r.run('isBattleActive'),false);a.equal(r.run('stats.silver'),silver);
});
test('interrupted reward journal retries its snapshot once after reload',()=>{
 const g=game();nurse(g);g.failedKeys.add('palata404_quest_test_v1:palata404_stats');g.run('bossCurrentHp=0;handleVictory()');const silver=g.run('stats.silver');a.ok(g.storage.has('palata404_quest_test_v1:palata404_pending_battle_reward'));const r=game(Object.fromEntries(g.storage));a.equal(r.run('stats.silver'),silver);a.equal(r.run('isBattleActive'),false);const r2=game(Object.fromEntries(r.storage));a.equal(r2.run('stats.silver'),silver);
});
test('elapsed raid deadline restores as timeout, with no new reward',()=>{
 const g=game();nurse(g);const key='palata404_quest_test_v1:quest_progress',raw=JSON.parse(g.storage.get(key));raw.raid.endsAt=1;g.storage.set(key,JSON.stringify(raw));const silver=g.run('stats.silver');const r=game(Object.fromEntries(g.storage));a.equal(r.run('isBattleActive'),false);a.equal(r.state().room,'ward404');a.equal(r.run('stats.silver'),silver);a.equal(r.run('readRaidArchive()[0].outcome'),'timeout');
});
test('reload resumes magazine refill without granting immediate ammo',()=>{
 const g=game();nurse(g);g.run('battleWeaponProfile={...getBattleAttackProfile(),capacity:3,reload:1};battleWeaponAmmo=1;startWeaponReload()');const r=game(Object.fromEntries(g.storage));a.equal(r.run('battleWeaponAmmo'),1);r.advance(999);a.equal(r.run('battleWeaponAmmo'),1);r.advance(1);a.equal(r.run('battleWeaponAmmo'),3);
});

test('collector pays existing currencies once, cooldown survives reload, old profile stays untouched',()=>{
 const original='{"silver":999}';const g=game({palata404_stats:original});const silver=g.run('stats.silver'),pills=g.run('stats.pills');g.click('room','collector');g.click('action','collect');a.equal(g.run('stats.silver'),silver+15);a.equal(g.run('stats.pills'),pills+1);a.equal(g.state().collectorCount,1);a.equal(g.state().materials,0);a.equal(g.storage.get('palata404_stats'),original);
 const r=game(Object.fromEntries(g.storage));a.equal(r.run('stats.silver'),silver+15);a.equal(r.state().collectorCount,1);a.equal(r.run('PalataQuestEngine.actions(window.PalataQuestPrototype.snapshot()).some(x=>x.id==="collect")'),false);r.advance(60000);r.click('action','collect');a.equal(r.run('stats.silver'),silver+30);a.equal(r.state().collectorCount,2);
});
test('collector journal recovers interrupted payout and preserves later spending',()=>{
 const g=game();g.click('room','collector');const silver=g.run('stats.silver');g.failedKeys.add('palata404_quest_test_v1:palata404_stats');g.click('action','collect');a.ok(g.storage.has('palata404_quest_test_v1:quest_reward_transaction'));g.run('stats.silver-=5;updateUI()');const r=game(Object.fromEntries(g.storage));a.equal(r.run('stats.silver'),silver+10);a.equal(r.state().collectorCount,1);a.equal(r.storage.has('palata404_quest_test_v1:quest_reward_transaction'),false);const r2=game(Object.fromEntries(r.storage));a.equal(r2.run('stats.silver'),silver+10);
});
test('failed reward journal does not persist half a payout; retry settles once',()=>{
 const g=game();g.click('room','collector');const silver=g.run('stats.silver');g.failedKeys.add('palata404_quest_test_v1:quest_reward_transaction');g.click('action','collect');const r=game(Object.fromEntries(g.storage));a.equal(r.run('stats.silver'),silver);a.equal(r.state().collectorCount,0);g.failedKeys.clear();g.run('updateUI()');const settled=game(Object.fromEntries(g.storage));a.equal(settled.run('stats.silver'),silver+15);a.equal(settled.state().collectorCount,1);
});
test('legacy test materials never silently convert and new job completion has no invented reward',()=>{
 const key='palata404_quest_test_v1:quest_progress';const g=game({[key]:JSON.stringify({version:2,materials:77,jobs:{k1:{active:true,done:{tag:true},count:0}}})});const silver=g.run('stats.silver'),parts=g.run('stats.equipmentParts');g.click('room','nurse');g.click('action','claim:k1');a.equal(g.state().materials,77);a.equal(g.run('stats.silver'),silver);a.equal(g.run('stats.equipmentParts'),parts);a.equal(g.state().jobs.k1.count,1);
});
test('collector silver can be spent by the existing medical shop',()=>{
 const g=game();g.run('stats.silver=0;updateUI()');g.click('room','collector');g.click('action','collect');g.advance(60000);g.click('action','collect');a.equal(g.run('stats.silver'),30);g.run("buyMedicalItem('hp_10',30,'silver')");a.equal(g.run('stats.silver'),0);a.ok(g.run("inventory.some(i=>i.name===MEDICAL_ITEMS.hp_10.name&&i.count>0)"));
});
