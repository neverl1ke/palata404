const {test}=require('node:test'),a=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),Module=require('node:module');
// Real profile adapter in a deterministic VM. Browser layout is tested separately.
const base=fs.readFileSync(path.join(__dirname,'game-logic.test.cjs'),'utf8');
const fixture=new Module(path.join(__dirname,'floor10-fixture.cjs'),module);fixture.filename=path.join(__dirname,'floor10-fixture.cjs');fixture.paths=module.paths;
let harness=base.slice(0,base.indexOf("test('malformed saves"));
harness=harness.replace("appendChild(child) {", "append(...items){this.children.push(...items);},replaceChildren(...items){this.children=items;},querySelector(){return element();},cloneNode(){return element();},replaceWith(){},appendChild(child) {");
harness=harness.replace('querySelectorAll() { return []; },','querySelector(){return element();},querySelectorAll() { return []; },');
harness=harness.replace("return elements.get(id) || null;","if(!elements.has(id)&&id.startsWith('quest-'))elements.set(id,element(id));return elements.get(id)||null;");
fixture._compile(harness+'\nmodule.exports=game;',fixture.filename);
const E=require('../quest-engine.js');
const {nextOperation}=require('./quest-workbench-solver.cjs');
function game(saves={},options={}){
 const g=fixture.exports(saves);
 for(const file of ['quest-job-model.js','quest-engine.js','quest-navigation.js','quest-art.js']){
  if(file==='quest-job-model.js'&&options.withoutModel)continue;
  g.run(fs.readFileSync(path.join(__dirname,'..',file),'utf8'));
 }
 // In the browser window is globalThis; the VM fixture deliberately separates them.
 g.run('window.PalataQuestNavigation=PalataQuestNavigation;');
 g.run(fs.readFileSync(path.join(__dirname,'..','quest-prototype.js'),'utf8').replace('snapshot:()=>','dispatch, snapshot:()=>'));
 return g;
}
const state=g=>JSON.parse(g.run('JSON.stringify(window.PalataQuestPrototype.snapshot())'));
const act=(g,event)=>g.run('window.PalataQuestPrototype.dispatch('+JSON.stringify(event)+')');
const board=(g,id)=>JSON.parse(g.run('JSON.stringify(PalataQuestEngine.workbench(window.PalataQuestPrototype.snapshot(),'+JSON.stringify(id)+'))'));
const progressKey=g=>[...g.storage.keys()].find(k=>k.startsWith('palata404_floor10_progress:'));
const journalKey=g=>progressKey(g).replace('floor10_progress:','floor10_reward:');
const economicSnapshot=g=>JSON.parse(g.run('JSON.stringify({progress:window.PalataQuestPrototype.snapshot(),stats,inventory})'));
function operation(g,id){const next=nextOperation(board(g,id));a.ok(next,'Evidence offers a next operation for '+id);a.equal(act(g,{type:'work',id,...next}),true);return next;}
function untilSubmit(g,id){for(let i=0;i<40;i++){const next=nextOperation(board(g,id));a.ok(next);if(next.op==='submit'||next.op==='deliver'||next.op==='record')return next;a.equal(act(g,{type:'work',id,...next}),true);}a.fail('No final operation for '+id);}
function interaction(g,id){
 if(board(g,id)){
  for(let i=0;i<60&&board(g,id);i++)operation(g,id);
  a.equal(board(g,id),null,'Workbench finishes '+id);return;
 }
 // Grandfathered active jobs and unchanged story interactions retain their saved sequence.
 for(const step of E.interactions[id].steps)a.equal(act(g,{type:'interact',id,choice:step.answer}),true);
}
function move(g,room){if(state(g).room===room)return;a.equal(act(g,{type:'move',room}),true);}
function accept(g,id){move(g,E.jobs[id].giver);a.equal(act(g,{type:'action',id:'accept:'+id}),true);}
function complete(g){accept(g,'k2');move(g,'linen');interaction(g,'job:linen');move(g,'ward406');interaction(g,'job:deliver');move(g,'nurse');a.equal(act(g,{type:'action',id:'claim:k2'}),true);}

test('Main entry loads work model before engine and never loads a sandbox',()=>{
 const html=fs.readFileSync(path.join(__dirname,'..','index.html'),'utf8');
 a.ok(html.indexOf('quest-job-model.js')<html.indexOf('quest-engine.js'));
 a.ok(html.indexOf('quest-prototype.js')>html.indexOf('room-scene.js'));
 a.doesNotMatch(html,/quest-sandbox|prototypes\/floor10/);
});
test('Legacy profile keeps money and mode; isolated test profile ignored',()=>{
 const g=game({'palata404_stats':JSON.stringify({silver:777,exp:42,madness:100}),'palata404_quest_test_v1:quest_progress':JSON.stringify({...E.initial(),room:'doctor',flags:{unlockB:true,unlockC:true}})});
 a.equal(g.run('stats.silver'),777);a.equal(g.run('stats.exp'),42);a.equal(state(g).mode,'trip');a.equal(state(g).room,'ward404');a.ok(!state(g).flags.unlockC);
});
test('Actual profile receives repeat cargo rewards exactly once across reload',()=>{
 let g=game();complete(g);a.equal(g.run('stats.silver'),158);a.equal(g.run('stats.exp'),15);a.equal(g.run('inventory.find(i=>i.name===MEDICAL_ITEMS.hp_10.name).count'),1);
 g=game(Object.fromEntries(g.storage));a.equal(act(g,{type:'action',id:'claim:k2'}),false);complete(g);
 a.equal(g.run('stats.silver'),166);a.equal(g.run('stats.exp'),30);a.equal(g.run('inventory.find(i=>i.name===MEDICAL_ITEMS.hp_10.name).count'),2);a.equal(state(g).cargo.length,0);
});
test('Failed mid-work journal write restores selections, progress, stock and inventory',()=>{
 const g=game();accept(g,'k1');move(g,'procedure');const before=economicSnapshot(g);
 g.failedKeys.add(journalKey(g));const next=nextOperation(board(g,'job:tag'));
 a.equal(act(g,{type:'work',id:'job:tag',...next}),false);
 a.deepEqual(economicSnapshot(g),before);a.equal(g.storage.has(journalKey(g)),false);
});
test('Failed final packing journal cannot grant the parcel or lose selected linen',()=>{
 const g=game();accept(g,'k2');move(g,'linen');const final=untilSubmit(g,'job:linen');const before=economicSnapshot(g);
 g.failedKeys.add(journalKey(g));a.equal(act(g,{type:'work',id:'job:linen',...final}),false);
 a.deepEqual(economicSnapshot(g),before);a.ok(!state(g).cargo.includes('linen'));
});
test('Interrupted profile write restores the same work variant and selection before one reward',()=>{
 let g=game();accept(g,'k2');move(g,'linen');g.failedKeys.add('palata404_stats');operation(g,'job:linen');
 const savedJob=state(g).jobs.k2;const before=economicSnapshot(g);a.ok(g.storage.has(journalKey(g)));
 const next=nextOperation(board(g,'job:linen'));a.equal(act(g,{type:'work',id:'job:linen',...next}),false);a.deepEqual(economicSnapshot(g),before);
 g=game(Object.fromEntries(g.storage));a.deepEqual(state(g).jobs.k2,savedJob);a.equal(g.run('stats.silver'),150);a.equal(g.storage.has(journalKey(g)),false);
 interaction(g,'job:linen');g=game(Object.fromEntries(g.storage));a.ok(state(g).cargo.includes('linen'));
 move(g,'ward406');interaction(g,'job:deliver');move(g,'nurse');a.equal(act(g,{type:'action',id:'claim:k2'}),true);
 g=game(Object.fromEntries(g.storage));a.equal(act(g,{type:'action',id:'claim:k2'}),false);a.equal(g.run('stats.silver'),158);a.equal(g.run('stats.exp'),15);a.equal(g.run('inventory.find(i=>i.name===MEDICAL_ITEMS.hp_10.name).count'),1);
});
test('Interrupted reward profile write recovers receipt without duplicate payout',()=>{
 let g=game();accept(g,'k2');move(g,'linen');interaction(g,'job:linen');move(g,'ward406');interaction(g,'job:deliver');move(g,'nurse');
 g.failedKeys.add('palata404_stats');act(g,{type:'action',id:'claim:k2'});a.ok(g.storage.has(journalKey(g)));
 g=game(Object.fromEntries(g.storage));a.equal(g.run('stats.silver'),158);a.equal(g.run('stats.exp'),15);a.equal(act(g,{type:'action',id:'claim:k2'}),false);a.equal(g.storage.has(journalKey(g)),false);
});
test('Existing parcel must also exist in actual inventory before delivery work',()=>{
 const g=game();accept(g,'k2');move(g,'linen');interaction(g,'job:linen');move(g,'ward406');
 g.run('inventory=inventory.filter(i=>i.questCargo!=="linen")');const before=economicSnapshot(g);
 a.equal(act(g,{type:'work',id:'job:deliver',op:'deliver'}),false);a.deepEqual(economicSnapshot(g),before);a.ok(!state(g).cargo.includes('delivery'));
});
test('Baseline must be observed and carried before a new Trip comparison',()=>{
 let g=game();accept(g,'d3');a.ok(!state(g).cargo.includes('baseline'));
 a.equal(act(g,{type:'work',id:'job:difference',op:'submit'}),false);
 move(g,'A');interaction(g,'job:baseline');a.ok(state(g).cargo.includes('baseline'));
 a.equal(act(g,{type:'switch'}),true);g.run('inventory=inventory.filter(i=>i.questCargo!=="baseline")');const before=economicSnapshot(g);
 const next=nextOperation(board(g,'job:difference'));a.equal(act(g,{type:'work',id:'job:difference',...next}),false);a.deepEqual(economicSnapshot(g),before);
 g=game(Object.fromEntries(g.storage));interaction(g,'job:difference');a.ok(state(g).cargo.includes('difference'));a.ok(!state(g).cargo.includes('baseline'));
 a.equal(act(g,{type:'work',id:'job:difference',op:'submit'}),false);
 a.equal(act(g,{type:'switch'}),true);move(g,'doctor');g.run('inventory=inventory.filter(i=>i.questCargo!=="difference")');
 a.equal(act(g,{type:'action',id:'claim:d3'}),false);a.equal(g.run('stats.silver'),150);a.equal(g.run('stats.exp'),0);
});
test('Failed baseline journal cannot grant a card or advance the fresh-Trip checkpoint',()=>{
 const g=game();accept(g,'d3');move(g,'A');const before=economicSnapshot(g);
 g.failedKeys.add(journalKey(g));a.equal(act(g,{type:'work',id:'job:baseline',op:'record'}),false);
 a.deepEqual(economicSnapshot(g),before);a.ok(!state(g).cargo.includes('baseline'));
 g.failedKeys.delete(journalKey(g));a.equal(act(g,{type:'work',id:'job:baseline',op:'record'}),true);a.ok(state(g).cargo.includes('baseline'));
});
test('An active old parcel can be delivered and claimed before the next revised assignment',()=>{
 let g=game();const saves=Object.fromEntries(g.storage),key=progressKey(g);
 saves[key]=JSON.stringify({...E.initial(),version:6,room:'ward406',flags:{unlockB:true,unlockC:true},cargo:['linen'],jobs:{k2:{active:true,done:{linen:true},count:3,startTrip:0}},interactions:{'job:linen':1}});
 g=game(saves);a.equal(state(g).jobs.k2.revision,1);a.equal(state(g).jobs.k2.count,3);a.equal(board(g,'job:deliver'),null);a.ok(state(g).cargo.includes('linen'));
 interaction(g,'job:deliver');move(g,'nurse');a.equal(act(g,{type:'action',id:'claim:k2'}),true);a.equal(state(g).jobs.k2.count,4);
 a.equal(g.run('stats.silver'),158);a.equal(g.run('stats.exp'),15);a.ok(state(g).flags.unlockB&&state(g).flags.unlockC);
 a.equal(act(g,{type:'action',id:'accept:k2'}),true);a.equal(state(g).jobs.k2.revision,2);a.equal(state(g).jobs.k2.count,4);
});
test('Repeated call reports retain their observed diagnosis rather than a fixed old item label',()=>{
 const g=game();
 for(let pass=0;pass<2;pass++){
  accept(g,'d1');move(g,'ward407');interaction(g,'job:bell407');
  const report=JSON.parse(g.run('JSON.stringify(inventory.find(i=>i.questCargo==="bell407"))'));
  a.doesNotMatch(report.name,/исправна|неисправна/);
  if(pass===1)a.match(report.desc,/Разъём отсоединён/);
  move(g,'ward408');interaction(g,'job:bell408');move(g,'doctor');a.equal(act(g,{type:'action',id:'claim:d1'}),true);
 }
 a.equal(state(g).jobs.d1.count,2);a.equal(g.run('stats.silver'),170);a.equal(g.run('stats.exp'),40);
});
test('Unrecognized pending journal blocks work and retains its exact bytes',()=>{
 let g=game();accept(g,'k2');move(g,'linen');const final=untilSubmit(g,'job:linen');const saves=Object.fromEntries(g.storage),key=journalKey(g),raw='{"version":99,"future":"keep"}';saves[key]=raw;
 g=game(saves);const before=economicSnapshot(g);a.equal(act(g,{type:'work',id:'job:linen',...final}),false);a.deepEqual(economicSnapshot(g),before);a.equal(g.storage.get(key),raw);
});
test('Unknown future floor save remains byte-for-byte and refuses new economic actions',()=>{
 let g=game();const key=progressKey(g),saves=Object.fromEntries(g.storage),raw='{"version":99,"future":"keep"}';saves[key]=raw;
 g=game(saves);move(g,'nurse');a.equal(act(g,{type:'action',id:'accept:k2'}),false);a.equal(act(g,{type:'work',id:'job:linen',op:'submit'}),false);a.equal(g.storage.get(key),raw);a.equal(g.run('stats.silver'),150);
});
test('A future work-order revision inside version 7 cannot be migrated away',()=>{
 let g=game();const key=progressKey(g),saves=Object.fromEntries(g.storage);
 const raw=JSON.stringify({...E.initial(),room:'linen',jobs:{k2:{active:true,revision:99,work:{future:'retain'},done:{},count:0,startTrip:0}}});saves[key]=raw;
 g=game(saves);a.equal(g.storage.get(key),raw);a.equal(act(g,{type:'work',id:'job:linen',op:'submit'}),false);a.equal(g.storage.get(key),raw);
});
test('Recovery refuses a future work revision without applying its profile snapshot',()=>{
 let g=game();const saves=Object.fromEntries(g.storage),key=journalKey(g),progress={...E.initial(),transaction:1,jobs:{k2:{active:true,revision:99,work:{future:'retain'},done:{},count:0,startTrip:0}}};
 const profile=JSON.parse(g.run('JSON.stringify(stats)'));profile.silver=999;
 const raw=JSON.stringify({version:2,owner:g.run('raidArchiveOwnerId'),receipt:{kind:'quest',id:'transaction:1'},progress,stats:profile,inventory:[]});saves[key]=raw;
 g=game(saves);a.equal(g.run('stats.silver'),150);a.equal(g.storage.get(key),raw);
});
test('Missing work-model resource cannot downgrade a saved work order',()=>{
 let g=game();accept(g,'k2');move(g,'linen');operation(g,'job:linen');const key=progressKey(g),raw=g.storage.get(key),savedJob=state(g).jobs.k2;
 g=game(Object.fromEntries(g.storage),{withoutModel:true});a.equal(g.storage.get(key),raw);a.equal(act(g,{type:'work',id:'job:linen',op:'submit'}),false);a.equal(g.storage.get(key),raw);
 g=game(Object.fromEntries(g.storage));a.deepEqual(state(g).jobs.k2,savedJob);a.equal(g.run('stats.silver'),150);
});
for(const boss of ['nurse','doctor'])test('Live '+boss+' raid resumes and awards repeated wins once',()=>{
 let g=game();const saves=Object.fromEntries(g.storage),key=progressKey(g);saves[key]=JSON.stringify({...E.initial(),mode:'trip',room:boss,flags:{unlockB:true,unlockC:true}});g=game(saves);
 for(let pass=0;pass<2;pass++){
  a.equal(act(g,{type:'action',id:'boss:'+boss}),true);a.equal(g.run('isBattleActive'),true);const id=g.run('currentBattleSession.id');g.run('bossCurrentHp-=7;window.dispatchEvent?.({type:"pagehide"});');g.run('performPlayerAttack()');const hp=g.run('bossCurrentHp');
  g=game(Object.fromEntries(g.storage));a.equal(g.run('isBattleActive'),true);a.equal(g.run('currentBattleSession.id'),id);a.equal(g.run('bossCurrentHp'),hp);
  g.run('bossCurrentHp=0;handleVictory()');a.equal(g.run('bossKillsCount.'+boss),pass+1);const silver=g.run('stats.silver');g.run('handleVictory()');a.equal(g.run('stats.silver'),silver);
  g=game(Object.fromEntries(g.storage));a.equal(g.run('bossKillsCount.'+boss),pass+1);a.equal(g.run('stats.silver'),silver);a.equal(state(g).battle,null);
 }
});
