const {test}=require('node:test'),a=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),crypto=require('node:crypto');
const E=require('../quest-engine.js'),c={};vm.createContext(c);vm.runInContext(fs.readFileSync('quest-art.js','utf8'),c);const art=c.PalataFloorArt;
const {nextOperation}=require('./quest-workbench-solver.cjs');
for(const row of JSON.parse(fs.readFileSync('assets/floor10-approved/provenance.json')))test('Original bytes '+row.runtime,()=>a.equal(crypto.createHash('sha256').update(fs.readFileSync(''+row.runtime)).digest('hex'),row.sha256));
test('17 scenes resolve both modes',()=>{a.equal(Object.keys(E.rooms).length,17);for(const id of Object.keys(E.rooms))for(const mode of ['patient','trip'])a.ok(fs.existsSync(''+art.resolve(id,mode).background));});
test('Six approved physical room pairs resolve independently',()=>{for(const id of Object.keys(E.rooms)){a.equal(art.resolve(id,'trip').paired,['doctor','nurse','collector','procedure','gym','ward406'].includes(id));if(art.resolve(id,'trip').paired)a.notEqual(art.resolve(id,'trip').background,art.resolve(id,'patient').background);}});
test('Both bosses use supplied Trip arena/sprite/portrait without stats changes',()=>{const b={nurse:{hp:120,dossier:{name:'retain'}},doctor:{hp:250,dossier:{name:'retain'}}};art.configureBosses(b);for(const id of Object.keys(b)){a.equal(b[id].sprite,art.resolve(id,'trip').sprite);a.equal(b[id].bg,art.resolve(id,'trip').background);a.equal(b[id].avatar,art.resolve(id,'trip').portrait);a.equal(b[id].dossier.name,'retain');}a.equal(b.nurse.hp,120);a.equal(b.doctor.hp,250);});
test('544 open ordered routes',()=>{for(const mode of ['patient','trip'])for(const from of Object.keys(E.rooms))for(const to of Object.keys(E.rooms)){if(from===to)continue;const s=E.initial();Object.assign(s,{mode,room:from});s.flags={unlockB:true,unlockC:true};a.ok(E.routePoints(s,to).length>1,from+' -> '+to);}});
test('Closed intermediate B blocks stale open C',()=>{const s=E.initial();s.mode='trip';s.flags.unlockC=true;a.deepEqual(E.routePoints(s,'doctor'),[]);a.equal(E.apply(s,{type:'move',room:'doctor'}).ok,false);});
test('Versions 1–7 migrate without mutating input',()=>{for(let version=1;version<=7;version++){const raw={version,mode:'trip',room:'doctor',battle:'doctor',flags:{unlockB:true,unlockC:true},jobs:{},other:'keep'},before=JSON.stringify(raw),s=E.restore(raw);a.equal(s.room,'doctor');a.equal(s.battle,'doctor');a.equal(JSON.stringify(raw),before);}});
test('Both bosses repeat; Clara never opens C',()=>{const s=E.initial();s.mode='trip';s.flags.unlockB=true;for(const boss of ['nurse','doctor']){s.room=boss;if(boss==='doctor')s.flags.unlockC=true;for(let i=0;i<2;i++){a.ok(E.apply(s,{type:'action',id:'boss:'+boss}).ok);a.ok(E.apply(s,{type:'battleEnd',victory:true}).ok);if(boss==='nurse')a.ok(!s.flags.unlockC);}}});
test('Doctor hotspots fit and do not overlap in both states',()=>{const src=fs.readFileSync('quest-scenes.js','utf8'),ctx={};vm.createContext(ctx);vm.runInContext(src.slice(src.indexOf('const objects='),src.indexOf("let currentMode="))+';globalThis.g={objects,tripObjects};',ctx);for(const box of [ctx.g.objects.doctor,ctx.g.tripObjects.doctor]){const all=Object.values(box);for(const [x,y,w,h]of all)a.ok(x-w/2>=0&&x+w/2<=100&&y-h/2>=0&&y+h/2<=100);for(let i=0;i<all.length;i++)for(let j=i+1;j<all.length;j++){const [x,y,w,h]=all[i],[u,v,q,r]=all[j];a.ok(Math.abs(x-u)>=(w+q)/2||Math.abs(y-v)>=(h+r)/2);}}});
const locations={tag:'procedure',linen:'linen',deliver:'ward406',copies:'procedure',bell407:'ward407',bell408:'ward408',log:'doctor',difference:'A'};
function interact(s,id){
 let result;
 if(E.workbench(s,id)){
  // Follow inspectable evidence, not the model's private solution generators.
  for(let guard=0;guard<100;guard++){
   const board=E.workbench(s,id);if(!board)return result;
   const next=nextOperation(board);
   if(next.navigate){a.ok(E.apply(s,{type:'move',room:next.navigate}).ok);interact(s,next.action);a.ok(E.apply(s,{type:'move',room:next.resumeRoom}).ok);continue;}
   result=E.apply(s,{type:'work',id,...next});a.ok(result.ok,result.message);
  }
  throw Error('Work order did not terminate: '+id);
 }
 // The old sequence remains supported for a genuinely migrated active order.
 for(const step of E.interactions[id].steps){result=E.apply(s,{type:'interact',id,choice:step.answer});a.ok(result.ok,result.message);}return result;
}
for(const [id,job] of Object.entries(E.jobs))test('Complete '+id+' with cargo, reload, unique/repeat reward',()=>{let s=E.initial();for(let pass=0;pass<(job.repeat?2:1);pass++){s.mode='patient';s.room=job.giver;a.ok(E.apply(s,{type:'action',id:'accept:'+id}).ok);a.equal(s.jobs[id].revision,['k2','d1'].includes(id)?3:2);a.equal(E.apply(s,{type:'action',id:'claim:'+id}).ok,false);if(id==='d3'){s.room='A';interact(s,'job:baseline');a.ok(s.cargo.includes('baseline'));s=E.restore(JSON.parse(JSON.stringify(s)));}for(const step of job.steps){s.room=locations[step];if(step==='difference'){s.mode='trip';s.trip++;}interact(s,'job:'+step);s=E.restore(JSON.parse(JSON.stringify(s)));}s.mode='patient';s.room=job.giver;const result=E.apply(s,{type:'action',id:'claim:'+id});a.ok(result.ok);a.equal(result.reward.id,id+':'+(pass+1));a.ok(result.reward.exp>0&&result.reward.silver>0);for(const cargo of E.requiredCargo[id])a.ok(!s.cargo.includes(cargo));a.equal(E.apply(s,{type:'action',id:'claim:'+id}).ok,false);s=E.restore(JSON.parse(JSON.stringify(s)));a.equal(E.apply(s,{type:'action',id:'claim:'+id}).ok,false);}if(!job.repeat)a.equal(E.apply(s,{type:'action',id:'accept:'+id}).ok,false);});
test('legacy active parcel orders finish under their original revision and next accept uses a workbench',()=>{
 for(let version=1;version<=6;version++){
  const raw={version,mode:'patient',room:'ward406',flags:{unlockB:true,unlockC:true},jobs:{k2:{active:true,count:2,done:{linen:true},startTrip:0}},cargo:['linen']},before=JSON.stringify(raw);
  let s=E.restore(raw);a.equal(JSON.stringify(raw),before);a.equal(s.jobs.k2.revision,1);a.ok(s.cargo.includes('linen'));a.equal(E.workbench(s,'job:deliver'),null);
  interact(s,'job:deliver');a.ok(s.cargo.includes('delivery'));a.ok(!s.cargo.includes('linen'));s=E.restore(JSON.parse(JSON.stringify(s)));s.room='nurse';const claim=E.apply(s,{type:'action',id:'claim:k2'});a.ok(claim.ok);a.equal(claim.reward.id,'k2:3');a.equal(s.flags.unlockB,true);a.equal(s.flags.unlockC,true);
  a.ok(E.apply(s,{type:'action',id:'accept:k2'}).ok);a.equal(s.jobs.k2.revision,3);s.room='linen';a.equal(E.workbench(s,'job:linen').kind,'packing');
 }
});
test('Migrating old completed counts does not manufacture prepared beds, call diagnoses or doctor reviews',()=>{
 for(const version of [1,6,7]){
  const raw={version,mode:'patient',room:'nurse',jobs:{k2:{active:false,count:12,done:{linen:true,deliver:true}},d1:{active:false,count:9,done:{bell407:true,bell408:true}}},cargo:[]},before=JSON.stringify(raw);
  const s=E.restore(raw);a.equal(JSON.stringify(raw),before);a.equal(s.jobs.k2.count,12);a.equal(s.jobs.d1.count,9);
  a.deepEqual(s.world,{version:1,linen406:null,calls:{ward407:null,ward408:null},doctorReview:null});
  a.deepEqual(E.roomEffects(s,'ward406','patient'),[]);a.deepEqual(E.roomEffects(s,'doctor','patient'),[]);
 }
});
test('Inventory and item details stack above fullscreen quest room',()=>{const css=fs.readFileSync('quest-prototype.css','utf8');function z(id){const rule=css.match(new RegExp('#'+id+'\\{[^}]*z-index:(\\d+)'));a.ok(rule,id);return Number(rule[1]);}a.ok(z('inventory-modal')>z('quest-location-screen'));a.ok(z('item-info-modal')>z('inventory-modal'));});

test("Modal override beats legacy important rule",()=>{const css=fs.readFileSync("quest-prototype.css","utf8");a.match(css,/#inventory-modal\{z-index:850!important\}/);a.match(css,/#item-info-modal\{z-index:860!important\}/);});

test('Task journal clears fullscreen room and inventory',()=>{const css=fs.readFileSync('quest-prototype.css','utf8');a.match(css,/#tasks-modal\{z-index:900!important\}/);});

// Runtime raid checkpoint recovery regressions.
const assert=a;
const code=fs.readFileSync(require('node:path').join(__dirname,'../quest-prototype.js'),'utf8');
const resumeSource=code.slice(code.indexOf('function raidInventorySnapshot('),code.indexOf('function resumeCounter('));
function checkpoint(){return {
 version:1,owner:'fixture-owner',boss:'nurse',hp:900,maxHp:1000,playerHp:55,endsAt:200000,cooldown:0,ammo:9,reloadAt:0,
 profile:{damage:35,cooldown:4,capacity:10,reload:2.5,critical:.05,miss:.05,criticalMultiplier:1.5},
 session:{id:'raid-fixture',bossKey:'nurse',startedAt:100,serial:1,events:['raid-fixture:1:attack'],finished:false},
 members:[{id:'player',damage:35,metrics:{damageTaken:0,healing:0,turns:1,madnessStart:100}}],
 counters:[],inventory:[{name:'Known weapon',category:'weapon',instanceId:'weapon-one',count:1,modules:{aiming:'accuracy'}},{name:'Medicine',category:'meds',count:3}]
};}
function harness({backup=true}={}){
 const writes=new Map(),original=[{name:'Profile weapon',category:'weapon',count:1},{name:'Profile medicine',category:'meds',count:7}];
 const c={state:{battle:'nurse',room:'nurse',flags:{}},inventory:structuredClone(original),stats:{hp:81,maxHp:100},
 raidArchiveOwnerId:'fixture-owner',lastBattleResult:null,readRaidArchive:()=>[],stored:'exact-original-save-bytes',key:'quest-key',
 safeStorageSet:(k,v)=>{if(!backup)return false;writes.set(k,v);return true;},protectedSave:false,saveFailed:false,notice:'',
 restoringRaid:false,originalFight:()=>{c.started++},started:0,stopBattleTimers(){},isBattleActive:false,currentBossKey:null,bossCurrentHp:0,bossMaxHp:0,
 currentBattleSession:null,raidMembers:[{id:'player',damage:0,metrics:{damageTaken:0,healing:0,turns:0,madnessStart:100}}],battleWeaponProfile:null,battleWeaponAmmo:0,
 raidEndsAt:0,attackCooldownEndsAt:0,playerAttackCooldown:false,weaponReloadEndsAt:0,battleGeneration:1,weaponReloadTimer:null,counters:new Map(),
 raidTimerInterval:null,friendAttackInterval:null,setInterval:()=>1,setTimeout:()=>2,Date,Map,Number,
 updateRaidTimerTick(){},friendsAutoAttackTick(){},updateBattleUI(){},updateRaidListUI(){},reopenNurseBattle(){},renderWeaponBattleState(){},save(){},resumeCounter(){}};
 vm.createContext(c);vm.runInContext("'use strict';\n"+resumeSource,c);return {c,writes,original};
}
test('malformed raid inventory cannot replace valid profile items, and raw save is backed up',()=>{
 for(const bad of [[{}],[{name:'Medicine',count:0}],[{name:'Medicine',count:-3}],[{name:'',count:1}]]){
  const {c,writes,original}=harness(),r=checkpoint();r.inventory=bad;c.resumeRaid(r);
  assert.deepEqual(c.inventory,original);assert.equal(c.started,0);assert.equal(c.isBattleActive,false);assert.equal(c.state.battle,null);assert.equal(c.state.room,'ward404');
  assert.equal(writes.get('quest-key:recovery'),'exact-original-save-bytes');
 }
});
test('valid checkpoint preserves every inventory item, weapon identity and module while resuming',()=>{
 const {c}=harness(),r=checkpoint(),before=JSON.stringify(r);c.resumeRaid(r);
 assert.equal(c.started,1);assert.equal(c.isBattleActive,true);assert.equal(c.stats.hp,55);
 assert.equal(JSON.stringify(c.inventory),JSON.stringify(r.inventory));assert.equal(JSON.stringify(r),before);assert.equal(c.currentBattleSession.id,r.session.id);
});
test('older positive string counts and omitted counts migrate without losing items',()=>{
 const {c}=harness(),r=checkpoint();r.inventory=[{name:'Legacy medicine',count:'2'},{name:'Legacy keepsake',custom:'retained'}];c.resumeRaid(r);
 assert.equal(c.started,1);assert.equal(c.inventory.length,2);assert.equal(c.inventory[0].count,2);assert.equal(c.inventory[1].count,1);assert.equal(c.inventory[1].custom,'retained');
});
test('a legitimately empty inventory remains valid',()=>{
 const {c}=harness(),r=checkpoint();r.inventory=[];c.resumeRaid(r);assert.equal(c.started,1);assert.equal(c.inventory.length,0);
});
test('failed recovery backup protects original progress instead of overwriting it',()=>{
 const {c,writes,original}=harness({backup:false}),r=checkpoint();r.inventory=[{}];c.resumeRaid(r);
 assert.equal(c.protectedSave,true);assert.equal(c.saveFailed,true);assert.equal(writes.size,0);assert.deepEqual(c.inventory,original);assert.equal(c.started,0);
});
