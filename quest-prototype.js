/* Floor 10 adapter for the current game profile. Does not import sandbox saves. */
(function(){
'use strict';

const E=PalataQuestEngine,key='palata404_floor10_progress:'+encodeURIComponent(raidArchiveOwnerId),byId=id=>document.getElementById(id);
let raw,protectedSave=false;const stored=safeStorageGet(key);try{raw=JSON.parse(stored);protectedSave=!!raw&&![1,2,3,4,5,6].includes(raw.version);}catch(_){protectedSave=stored!==null;}let state=E.restore(raw);if(!stored)state.mode=stats.madness>=100?'trip':'patient';let tab='story',taskMode=null,focusQuest=null,focusRoom=null,notice='',locationView=false,interaction=null,travelling=false,saveFailed=false;
// This collector payout matches script.js handleNodeClick. The 60-second cadence
// and all side-job payouts remain explicitly unapproved prototype proposals.
const collectorPayout=Object.freeze({silver:15,pills:1}),rewardKey='palata404_floor10_reward:'+encodeURIComponent(raidArchiveOwnerId);
let pendingQuestReward=null,rewardRecoveryError=false;
try{
 const journalText=safeStorageGet(rewardKey);
 if(journalText){const journal=JSON.parse(journalText);
  const collector=journal.receipt?.kind==='collector'&&Number.isSafeInteger(journal.progress?.collectorCount)&&journal.progress.collectorCount>0&&journal.receipt.id==='collector:'+journal.progress.collectorCount;
  const quest=journal.receipt?.kind==='quest'&&Number.isSafeInteger(journal.progress?.transaction)&&journal.progress.transaction>0&&journal.receipt.id==='transaction:'+journal.progress.transaction;
  const validInventory=Array.isArray(journal.inventory)&&journal.inventory.every(x=>x&&typeof x.name==='string'&&Number.isSafeInteger(x.count)&&x.count>0);
  if(!protectedSave&&[1,2].includes(journal.version)&&journal.owner===raidArchiveOwnerId&&(collector||journal.version===2&&quest)&&[3,4,5,6].includes(journal.progress?.version)&&journal.stats&&['silver','pills','exp','level'].every(k=>Number.isSafeInteger(journal.stats[k])&&journal.stats[k]>=0)&&(journal.version===1||validInventory)){
   raw=journal.progress;state=E.restore(raw);Object.assign(stats,normalizeStats(journal.stats));if(journal.version===2)inventory=normalizeInventory(journal.inventory);pendingQuestReward=journal.receipt;
  }else rewardRecoveryError=true;
 }
}catch(_){rewardRecoveryError=true;}
function syncCargo(){
 inventory=inventory.filter(x=>!x.questCargo);
 for(const id of state.cargo)inventory.push({...E.cargoCatalog[id],category:'quest',count:1,questCargo:id});
}
if(!protectedSave&&!rewardRecoveryError)syncCargo();
const originalSaveProgress=saveGameProgress;
saveGameProgress=function(){
 if(restoringRaid)return false;
 if(pendingQuestReward){
  // Keep the pending snapshot current on every ordinary game save, so spending,
  // combat or another update cannot be rolled back by an older reward journal.
  if(!safeStorageSet(rewardKey,JSON.stringify({version:2,owner:raidArchiveOwnerId,receipt:pendingQuestReward,stats,inventory,progress:state})))return false;
 }
 if(!originalSaveProgress())return false;
 if(pendingQuestReward){
  if(!safeStorageSet(key,JSON.stringify(state))||!safeStorageRemove(rewardKey))return false;
  pendingQuestReward=null;
 }
 return true;
};
window.PalataFloorArt.configureBosses(bossesDatabase);
const originalUpdate=updateUI,originalFight=startBossFight,originalVictory=handleVictory,originalUnrewarded=recordUnrewardedRaid;
const tasks=byId('tasks-modal').querySelector('.modal-content');tasks.classList.remove('tasks-placeholder');tasks.classList.add('quest-sheet');
tasks.innerHTML='<div class="modal-header"><h3 id="tasks-title">Задания · 10-й этаж</h3><button onclick="closeTasks()" aria-label="Закрыть задания">✕</button></div><p class="quest-note">Размеры наград поручений предварительные; баланс ещё настраивается.</p><nav class="quest-tabs" aria-label="Категории заданий"><button data-quest-tab="story">Сюжет</button><button data-quest-tab="nurse">Клара</button><button data-quest-tab="doctor">Врач</button></nav><nav class="quest-tabs"><button data-task-mode="patient">Пациент</button><button data-task-mode="trip">Трип</button></nav><div id="quest-list"></div><p id="quest-save" role="status"></p><button onclick="toggleMapModal(true)">К действиям на этаже</button>';
const map=byId('map-floors-view');map.classList.add('quest-floor');byId('map-modal').querySelector('.map-clipboard-body').classList.add('quest-map-sheet');
const mapHome=byId('map-modal').querySelector('.map-clipboard-body');const locationScreen=document.createElement('main');locationScreen.id='quest-location-screen';locationScreen.classList.add('hidden');locationScreen.setAttribute('aria-label','Локация');document.body.append(locationScreen);
const officialHeader=document.createElement('div');officialHeader.className='quest-official-header';officialHeader.innerHTML='<document-header variant="left" department="ПЛАН ДЕСЯТОГО ЭТАЖА" scale="compact"></document-header><document-stamp type="service" rotate="-5"></document-stamp><document-stamp type="seal" rotate="8"></document-stamp>';byId('map-modal').querySelector('.map-clipboard-header').append(officialHeader);byId('map-modal').setAttribute('aria-label','Карта этажей');byId('map-modal').querySelector('.btn-close-map').setAttribute('aria-label','Закрыть окно');
// A single quest checkpoint holds position and the live raid together. Production
// payouts remain exclusively owned by handleVictory's durable reward journal.
const counters=new Map();let restoringRaid=false,collectorWake=null;
function checkpoint(){
 if(!state.battle||!currentBattleSession)return null;
 return {version:1,owner:raidArchiveOwnerId,boss:currentBossKey,hp:bossCurrentHp,maxHp:bossMaxHp,playerHp:stats.hp,
  endsAt:raidEndsAt,cooldown:attackCooldownEndsAt,ammo:battleWeaponAmmo,reloadAt:weaponReloadEndsAt,
  profile:{...getBattleAttackProfile()},session:{...currentBattleSession,events:[...currentBattleSession.events]},
  members:JSON.parse(JSON.stringify(raidMembers)),inventory:JSON.parse(JSON.stringify(inventory)),
  counters:[...counters].filter(([id])=>!currentBattleSession.events.has(id+':counter'))};
}
function resumeRaid(r){
 if(!state.battle)return;
 const completed=r?.session?.id&&(lastBattleResult?.battleId===r.session.id?lastBattleResult:readRaidArchive().find(x=>x.battleId===r.session.id));
 if(completed){if(completed.outcome==='victory'&&state.battle==='doctor')state.flags.doctorWon=true;if(completed.outcome!=='victory')state.room='ward404';state.battle=null;return;}
 const finite=n=>Number.isFinite(n)&&n>=0;
 if(!r||r.version!==1||r.owner!==raidArchiveOwnerId||r.boss!==state.battle||r.session?.bossKey!==r.boss||typeof r.session?.id!=='string'||r.session.finished||!Array.isArray(r.session.events)||!Array.isArray(r.members)||!Array.isArray(r.inventory)||![r.hp,r.maxHp,r.playerHp,r.endsAt,r.cooldown,r.ammo,r.reloadAt].every(finite)||!r.profile||!finite(r.profile.cooldown)||!finite(r.profile.capacity)||!Number.isSafeInteger(r.session.serial)||r.session.serial<0||!r.session.events.every(x=>typeof x==='string'&&x.startsWith(r.session.id+':'))||!Array.isArray(r.counters)||!r.counters.every(x=>Array.isArray(x)&&x.length===2&&typeof x[0]==='string'&&x[0].startsWith(r.session.id+':')&&finite(x[1]))||!r.members.every(x=>x&&raidMembers.some(m=>m.id===x.id)&&finite(x.damage)&&x.metrics&&['damageTaken','healing','turns','madnessStart'].every(k=>x.metrics[k]===null||finite(x.metrics[k])))||!r.inventory.every(x=>x&&typeof x==='object'&&!Array.isArray(x))||r.hp>r.maxHp||r.maxHp<=0||!['damage','reload','critical','miss','criticalMultiplier'].every(k=>finite(r.profile[k]))){
  // Keep the original bytes available before migrating a legacy/incomplete battle.
  if(stored&&!safeStorageSet(key+':recovery',stored)){protectedSave=true;saveFailed=true;}
  state.battle=null;state.room='ward404';notice='Старый рейд не содержит контрольной точки. Копия сохранения оставлена для восстановления.';return;
 }
 // Starting restores only arena UI and timers; overwrite its new metrics before input.
 restoringRaid=true;originalFight(r.boss);stopBattleTimers();isBattleActive=true;
 currentBossKey=r.boss;bossCurrentHp=r.hp;bossMaxHp=r.maxHp;stats.hp=Math.min(stats.maxHp,r.playerHp);
 inventory=r.inventory;currentBattleSession={...r.session,events:new Set(r.session.events)};
 for(const member of raidMembers){const prior=r.members.find(x=>x.id===member.id);if(prior)Object.assign(member,prior);}
 battleWeaponProfile=r.profile;battleWeaponAmmo=r.ammo;raidEndsAt=r.endsAt;attackCooldownEndsAt=r.cooldown;
 playerAttackCooldown=Date.now()<r.cooldown;
 weaponReloadEndsAt=r.reloadAt;
 if(r.reloadAt){const generation=battleGeneration;const finish=()=>{if(!isBattleActive||generation!==battleGeneration)return;battleWeaponAmmo=r.profile.capacity;weaponReloadEndsAt=0;renderWeaponBattleState();save();};if(r.reloadAt<=Date.now())finish();else weaponReloadTimer=setTimeout(finish,r.reloadAt-Date.now());}
 for(const [id,at] of r.counters||[]){if(typeof id!=='string'||!finite(at)||currentBattleSession.events.has(id+':counter'))continue;counters.set(id,at);setTimeout(()=>resumeCounter(id),Math.max(0,at-Date.now()));}
 raidTimerInterval=setInterval(updateRaidTimerTick,1000);friendAttackInterval=setInterval(friendsAutoAttackTick,3500);
 restoringRaid=false;updateRaidTimerTick();if(isBattleActive){updateBattleUI();updateRaidListUI();reopenNurseBattle();}
}
function resumeCounter(id){
 counters.delete(id);if(!isBattleActive)return;updateRaidTimerTick();if(!isBattleActive)return;
 const damage=Math.max(1,Math.ceil(bossesDatabase[currentBossKey].damage*100/(100+stats.armor)));
 if(!recordBattleEvent(id+':counter',raidMembers.find(m=>m.isPlayer),{damageTaken:Math.min(stats.hp,damage)}))return;
 stats.hp=Math.max(0,stats.hp-damage);
 if(!stats.hp){recordUnrewardedRaid('defeat');isBattleActive=false;stopBattleTimers();stats.hp=stats.maxHp;closeNurseBattle();}
 updateUI();save();
}
const attack=performPlayerAttack;performPlayerAttack=function(){const serial=currentBattleSession?.serial;const result=attack.apply(this,arguments);if(isBattleActive&&currentBattleSession?.serial!==serial){const id=currentBattleSession.id+':'+currentBattleSession.serial+':attack';if(currentBattleSession.events.has(id))counters.set(id,Date.now()+500);}save();return result;};
const helpers=friendsAutoAttackTick;friendsAutoAttackTick=function(){const r=helpers.apply(this,arguments);save();return r;};
const reload=startWeaponReload;startWeaponReload=function(){const r=reload.apply(this,arguments);save();return r;};
window.addEventListener('pagehide',save);
function save(){if(restoringRaid)return false;if(protectedSave){saveFailed=true;return false;}state.raid=checkpoint();saveFailed=rewardRecoveryError||(pendingQuestReward?!saveGameProgress():!safeStorageSet(key,JSON.stringify(state)));return !saveFailed;}
function sync(){stats.madness=state.mode==='trip'?100:0;currentRoom={id:state.room==='ward404'?'room_404':state.room,name:E.rooms[state.room][1],desc:'10-й этаж · секция '+E.rooms[state.room][0]};}
function renderTasks(){
 const list=byId('quest-list'),mode=taskMode||state.mode;list.replaceChildren();
 const rows=tab==='story'?E.story(state).filter(r=>r.mode===mode):Object.entries(E.jobs).filter(([,j])=>j.giver===tab).filter(([id])=>mode==='patient'||id==='d3').map(([id,j])=>{
  const p=state.jobs[id],tripStep=mode==='trip';
  return {id,title:j.title+(id==='d3'?(tripStep?' · наблюдение':' · получить и сдать'):''),done:tripStep?!!p?.done.difference:!!p?.count&&!p.active,
   detail:tripStep?(p?.active?'Коридор A: запишите отличие во время нового входа в Трип. Сдача — у врача в Пациенте.':'Сначала получите поручение у врача в Пациенте.'):`${j.repeat?'Повторяемое':'Разовое'} · ${p?.active?'Активно: '+j.steps.filter(x=>p.done[x]).length+'/'+j.steps.length:'Взять у '+(tab==='nurse'?'Клары (B)':'врача (C)')+' в Пациенте'} · Сдано: ${p?.count||0}. Награда: ${E.rewardText(id)}.`,repeat:j.repeat,waiting:!tripStep&&id==='d3'&&p?.active&&!E.ready(state,id)};
 });
 for(const r of rows){
  const a=document.createElement('article');a.className='quest-card';a.dataset.questId=r.id;
  const h=document.createElement('h4');h.textContent=(r.done?'✓ ':'○ ')+r.id+' '+r.title;
  const p=document.createElement('p');p.textContent=r.detail;a.append(h,p);
  if(r.waiting){const hint=document.createElement('p');hint.textContent='Поручение получено. Наблюдение выполняется во вкладке «Трип»; после него вернитесь к врачу для сдачи.';a.append(hint);}
  else if(!r.done||r.repeat&&mode==='patient'){
   const g=E.guide(state,r.id),hint=document.createElement('p');hint.textContent='Следующий шаг: '+E.rooms[g.room][1]+'. '+g.text;
   a.append(hint,button('Показать на карте',()=>{focusQuest=r.id;focusRoom=null;notice='Точка задания подсвечена. ';toggleMapModal(true);}));
  }else{const done=document.createElement('p');done.textContent='Завершено. Повторять эти действия не нужно.';a.append(done);}
  list.append(a);
 }
 tasks.querySelectorAll('[data-quest-tab]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.questTab===tab)));
 tasks.querySelectorAll('[data-task-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.taskMode===mode)));
 if(!list.children.length)list.textContent='В этом режиме нет поручений этой категории. Просмотр другого режима не переключает игру.';
 byId('quest-save').textContent=saveFailed?'Сохранение недоступно или формат новее этой версии. Исходные данные не заменяются.':'';
}

function button(label,fn,disabled=false){const b=document.createElement('button');b.type='button';b.textContent=label;b.disabled=disabled;b.addEventListener('click',fn);return b;}
function beginAction(id){if(!E.interactions[id])return dispatch({type:'action',id});if(id==='unlockB'&&(!state.flags.doorKnown||!state.flags.reserveKnown||!state.flags.tripHandle)){focusQuest='lockB';notice='Нужны знание исправного механизма и аварийная рукоять из ординаторской A. ';locationView=false;renderMap();return;}if(id==='unlockC'&&(!state.flags.cKeyKnown||!state.flags.cLockKnown)){focusQuest='lockC';notice='Нужны опись хранения ключа в процедурной и памятка о замке у врача. ';locationView=false;renderMap();return;}interaction=id;locationView=true;renderMap();}
function renderInteraction(host){const spec=E.interactions[interaction],index=state.interactions[interaction]||0,step=spec.steps[index];if(!step){interaction=null;return;}const h=document.createElement('h4');h.textContent=spec.title+' · шаг '+(index+1)+'/'+spec.steps.length;const p=document.createElement('p');p.textContent=step.text;host.append(h,p);for(const [choice,label] of step.choices){const b=button(label,()=>{const id=interaction;const ok=dispatch({type:'interact',id,choice});if(ok){if((state.interactions[id]||0)===spec.steps.length||id==='exercise'&&state.interactions.exercise===0)interaction=null;renderMap();}else b.setAttribute('aria-invalid','true');});b.dataset.choice=choice;if(window.PalataQuestScenes)PalataQuestScenes.decorateChoice(b,choice);host.append(b);}const feedback=document.createElement('p');feedback.className='interaction-feedback';feedback.setAttribute('role','status');host.append(feedback,button('Отложить осмотр',()=>{interaction=null;renderMap();}));}

function roomActions(host){if(interaction){renderInteraction(host);return;}for(const a of E.actions(state)){const b=button(a.label,()=>beginAction(a.id));b.dataset.action=a.id;if(window.PalataQuestScenes)PalataQuestScenes.decorate(b,a.id);host.append(b);}if(state.room==='ward404')host.append(button(state.mode==='trip'?'Выйти из Трипа':'Войти в Трип',switchMode));if(state.room==='collector'){const p=document.createElement('p');p.textContent='Сборщик: 15 серебра и 1 таблетка в ваш профиль. Следующая выдача через '+Math.max(0,Math.ceil((state.collectorAt+60000-Date.now())/1000))+' с. Частота выдачи пока тестовая; запас за время отсутствия не накапливается.';host.append(p);}if(!host.children.length)host.textContent='Сейчас тут нет новых действий. Откройте задания, чтобы найти следующий шаг.';}
function renderLocation(){locationScreen.classList.remove('hidden');locationScreen.append(map);byId('map-modal').classList.add('hidden');map.replaceChildren();map.classList.add('quest-location');const info=document.createElement('section');info.className='scene-paper document-paper';const header=document.createElement('document-header');header.setAttribute('variant','left');header.setAttribute('department','КАРТОЧКА ЛОКАЦИИ');header.setAttribute('scale','compact');const title=document.createElement('h3');title.textContent=E.rooms[state.room][1];const mode=document.createElement('p');mode.textContent=(state.mode==='trip'?'Трип':'Пациент')+' · секция '+E.rooms[state.room][0];const message=document.createElement('p');message.className='quest-note';message.setAttribute('role','status');message.textContent='Выберите предмет. Enter или пробел активируют выбранную цель. Прогресс сохраняется после каждого шага.';const seal=document.createElement('document-stamp');seal.setAttribute('type','seal');seal.setAttribute('rotate','-8');info.append(header,title,mode,message,seal,button('Вернуться к карте',()=>{interaction=null;locationView=false;renderMap();}),button('Открыть задания',openTasks));const bag=document.createElement('section');bag.className='quest-cargo-panel';bag.setAttribute('aria-label','Предметы поручений');const bagTitle=document.createElement('h4');bagTitle.textContent='При себе · инвентарь';bag.append(bagTitle);for(const item of inventory.filter(x=>x.questCargo)){const row=document.createElement('p');row.dataset.cargo=item.questCargo;row.textContent=item.name+' ×'+item.count;bag.append(row);}if(!inventory.some(x=>x.questCargo)){const empty=document.createElement('p');empty.textContent='Предметов поручений пока нет.';bag.append(empty);}const receipt=document.createElement('p');receipt.className='quest-receipt';receipt.setAttribute('role','status');receipt.textContent=state.lastReceipt||'Собирайте предметы в комнатах и используйте их по поручению.';bag.append(receipt,button('Открыть инвентарь',openInventory));const balance=document.createElement('p');balance.textContent='Уровень '+stats.level+' · EXP '+stats.exp+'/'+stats.nextLvlExp+' · Серебро '+stats.silver;bag.append(balance);info.append(bag);window.PalataFloorArt.renderPortrait(info,state.room,state.mode);const scene=document.createElement('section');if(window.PalataQuestScenes)PalataQuestScenes.render(scene,state.room,state.mode,text=>{message.textContent=text;});const acts=document.createElement('div');acts.className='quest-actions scene-actions';roomActions(acts);scene.append(acts);if(window.PalataQuestScenes?.renderCargo)PalataQuestScenes.renderCargo(scene,state,interaction);if(window.PalataQuestScenes?.finish)PalataQuestScenes.finish(scene,info,interaction,state.interactions[interaction]||0);map.append(scene,info);}

async function travel(id){if(travelling||isBattleActive)return;const points=E.routePoints(state,id);if(!points.length)return;travelling=true;const figure=map.querySelector('.quest-blueprint'),marker=document.createElement('span');marker.className='quest-traveller';marker.textContent='●';marker.setAttribute('aria-label','Движение персонажа');figure.append(marker);map.setAttribute('aria-busy','true');const keyframes=points.map(p=>({left:((p[0]-70)/1610*100)+'%',top:((p[1]-280)/850*100)+'%'}));try{if(marker.animate&&!matchMedia('(prefers-reduced-motion: reduce)').matches){await marker.animate(keyframes,{duration:Math.max(700,Math.min(2400,points.length*230)),fill:'forwards',easing:'linear'}).finished;}}catch(_){}finally{travelling=false;map.setAttribute('aria-busy','false');}interaction=null;locationView=true;dispatch({type:'move',room:id});}

function renderMap(){if(travelling)return;if(locationView){renderLocation();return;}if(!locationScreen.classList.contains('hidden')){mapHome.append(map);locationScreen.classList.add('hidden');byId('map-modal').classList.remove('hidden');}map.classList.remove('quest-location');byId('map-title-text').textContent='10-Й ЭТАЖ';byId('map-floors-view').classList.remove('hidden');byId('map-single-floor-view').classList.add('hidden');map.replaceChildren();const status=document.createElement('h3');status.textContent=`${state.mode==='trip'?'Трип':'Пациент'} · ${E.rooms[state.room][1]}`;map.append(status);const note=document.createElement('p');note.textContent=(state.mode==='patient'?'Пациент: штриховки нет, все секции доступны. ':'Трип: B '+(state.flags.unlockB?'открыта: засов освобождён':'закрыта: заевший привод, нужна аварийная рукоять')+'; C '+(state.flags.unlockC?'открыта':'заперта: нужен запасной ключ из тележки B')+'. ')+'Пациент: A–B–C, без спуска. Трип: '+['A','B','C'].filter(x=>E.accessible({...state,mode:'trip'},x)).join('–')+'. Переключение только в 404. Серебро: '+stats.silver+' · Таблетки: '+stats.pills+(state.materials?' · Архив старых тестовых материалов: '+state.materials:'')+'.';map.append(note);const figure=document.createElement('figure');figure.className='quest-blueprint';figure.setAttribute('aria-label','План десятого этажа редакции 04 с интерактивными точками');
const img=document.createElement('img');img.src='quest-plan.svg';img.alt='Общий план Пациента и Трипа: секции A, B, C; палаты 404–408, медпункт, процедурная, кабинет врача и лестница.';img.className='quest-blueprint-image';figure.append(img);
for(const [id,spec] of Object.entries(E.mapLabels)){const [l,t,r,b]=spec.box;const label=document.createElement('span');label.className='quest-plan-label';label.dataset.labelRoom=id;label.lang='ru';label.textContent=spec.text;label.title=spec.full;label.setAttribute('aria-label',spec.full);label.style.left=((l-70)/1610*100)+'%';label.style.top=((t-280)/850*100)+'%';label.style.width=((r-l)/1610*100)+'%';label.style.height=((b-t)/850*100)+'%';figure.append(label);}const origin=document.createElement('span');origin.className='quest-plan-origin-mask';origin.setAttribute('aria-hidden','true');figure.append(origin);
for(const sec of ['B','C'])if(!E.accessible(state,sec)){const shade=document.createElement('div');shade.className='quest-locked-zone';shade.dataset.section=sec;shade.style.clipPath='polygon('+E.sectionPolygons[sec].map(p=>((p[0]-70)/1610*100)+'% '+((p[1]-280)/850*100)+'%').join(',')+')';shade.setAttribute('aria-label','Секция '+sec+' закрыта');figure.append(shade);}
const reachable=E.destinations(state),guidance=focusQuest?E.guide(state,focusQuest):null,target=guidance?.room||focusRoom;

for(const [id,point] of Object.entries(E.pins)){
 const current=id===state.room,locked=!E.accessible(state,E.rooms[id][0]),available=reachable.includes(id);
 const label=locked?'×':id==='A'||id==='B'||id==='C'?id:id.startsWith('ward')?id.slice(4):id==='stairs'?'↓':'•';
 const pin=button(label,()=>{if(locked){focusQuest='lock'+E.rooms[id][0];notice='Секция '+E.rooms[id][0]+' закрыта в Трипе. ';renderMap();}else if(current){interaction=null;locationView=true;renderMap();}else if(!available){focusQuest=null;focusRoom=id;notice=E.directions(state,id);renderMap();}else{notice='';travel(id);}},false);pin.dataset.room=id;
 pin.className='quest-map-pin'+(current?' is-current':locked?' is-locked':available?' is-reachable':' is-distant');
 if(id===target)pin.classList.add('is-target');pin.style.left=((point[0]-70)/1610*100)+'%';pin.style.top=((point[1]-280)/850*100)+'%';
 pin.title=E.rooms[id][1]+(current?' · вы тут':locked?' · секция закрыта в Трипе':available?' · перейти':' · сначала перейдите в коридор');
 pin.setAttribute('aria-label',pin.title);if(current)pin.setAttribute('aria-current','location');figure.append(pin);
}
for(const [sec,x] of [['A',16],['B',49],['C',81]]){const label=document.createElement('span');label.className='plan-section-caption';label.textContent='СЕКЦИЯ '+sec;label.style.left=x+'%';figure.append(label);}map.append(figure);const legend=document.createElement('p');legend.className='quest-map-legend';legend.textContent='УСЛОВНЫЕ ОБОЗНАЧЕНИЯ\n● Синяя отметка — вы здесь\n● Зелёная — проход доступен\n○ Любой переход — по коридорам\n× Штриховка — закрыто в Трипе\n◎ Золотой контур — цель задания';const sidebar=document.createElement('aside');sidebar.className='quest-map-sidebar';sidebar.setAttribute('aria-label','Действия и подсказка карты');sidebar.tabIndex=0;const names=document.createElement('p');names.className='quest-room-key';names.textContent='КОМНАТЫ\n'+Object.values(E.mapLabels).map(x=>x.text+' — '+x.full).join('\n');sidebar.append(legend);map.append(sidebar);
const heading=document.createElement('h4');heading.textContent='Действия в этой комнате';sidebar.append(heading);const acts=document.createElement('div');acts.className='quest-actions';for(const a of E.actions(state)){const b=button(a.label,()=>beginAction(a.id));b.dataset.action=a.id;acts.append(b);}acts.append(button('Войти в текущую комнату',()=>{locationView=true;renderMap();}));if(state.room==='collector'){const p=document.createElement('p');const seconds=Math.max(0,Math.ceil((state.collectorAt+60000-Date.now())/1000));p.textContent='Сборщик: 15 серебра и 1 таблетка за выдачу. '+(seconds?'До следующего сбора: '+seconds+' с. Обновите карту.':'Нажмите «Получить припасы сборщика».')+' Частота — тестовая: раз в минуту, без накопления.';acts.append(p);}if(!acts.children.length)acts.textContent=state.room==='ward404'?'Закройте карту и нажмите красный переключатель в палате 404.':'Нет новых действий. Журнал подскажет следующий шаг.';sidebar.append(acts,button('Открыть задания',openTasks));const history=document.createElement('p');history.className='quest-note';history.setAttribute('role','status');history.textContent=notice+(guidance?guidance.text+' '+E.directions(state,guidance.room):focusRoom?E.directions(state,focusRoom):E.mapHint(state));sidebar.append(history,names);}
function scheduleCollector(){clearTimeout(collectorWake);const remaining=state.collectorAt+60000-Date.now();if(remaining>0)collectorWake=setTimeout(()=>{if(state.room==='collector'&&!interaction&&!travelling&&!isBattleActive)renderMap();},remaining);}
function refresh(){sync();originalUpdate();save();byId('current-location-name').textContent=E.rooms[state.room][1];byId('current-location-desc').textContent=(state.mode==='trip'?'Трип':'Пациент')+' · секция '+E.rooms[state.room][0];const b=document.querySelector('.room-trip-switch');b.disabled=false;b.setAttribute('aria-pressed',String(state.mode==='trip'));b.setAttribute('aria-label',state.mode==='trip'?'Выйти из Трипа':'Войти в Трип');b.querySelector('.room-action-label').textContent=state.mode==='trip'?'Выйти из Трипа':'Войти в Трип';b.title=state.room==='ward404'?'Переключить режим':'Сначала вернитесь в 404';renderTasks();renderMap();scheduleCollector();}
function dispatch(event){
 if(travelling)return false;
 if(isBattleActive&&event.type!=='battleEnd'){showCustomToast('Завершите рейд.');return false;}
 const economic=(event.type==='action'||event.type==='interact')&&(event.id==='collect'||/^(accept:|claim:|job:)/.test(event.id));
 if(economic&&(protectedSave||rewardRecoveryError||pendingQuestReward&&!saveGameProgress())){showCustomToast('Действие приостановлено: сначала восстановите сохранение предметов и награды.');return false;}
 // Consumers require the actual inventory item as well as quest progress.
 const needed=event.id==='job:deliver'?['linen']:event.id==='job:difference'?['baseline']:event.id?.startsWith('claim:')?E.requiredCargo[event.id.slice(6)]:[];
 if(economic&&needed?.some(id=>!inventory.some(x=>x.questCargo===id&&x.count>0))){showCustomToast('Нужного предмета нет в инвентаре. Получите его в указанной комнате.');return false;}
 const before=economic?{state:JSON.parse(JSON.stringify(state)),stats:JSON.parse(JSON.stringify(stats)),inventory:JSON.parse(JSON.stringify(inventory))}:null;
 const result=E.apply(state,event);
 if(result.ok){
  if(economic){
   syncCargo();
   if(result.reward?.kind==='collector')for(const [currency,amount] of Object.entries(collectorPayout))stats[currency]+=amount;
   if(result.reward?.kind==='job'){
    stats.silver+=result.reward.silver;addExperience(result.reward.exp,false);
    if(result.reward.medical){const item=MEDICAL_ITEMS[result.reward.medical],existing=inventory.find(x=>x.name===item.name&&x.category==='meds');if(existing)existing.count++;else inventory.push({...item,count:1});}
   }
   state.transaction++;state.lastReceipt=result.message;
   const receipt=result.reward?.kind==='collector'?result.reward:{kind:'quest',id:'transaction:'+state.transaction};
   // Write the complete result before any profile/progress write. Recovery applies
   // the snapshot, never repeats addExperience or adds the items a second time.
   if(!safeStorageSet(rewardKey,JSON.stringify({version:2,owner:raidArchiveOwnerId,receipt,stats,inventory,progress:state}))){
    state=before.state;Object.assign(stats,before.stats);inventory=before.inventory;showCustomToast('Не удалось сохранить: предметы и награда не изменены. Повторите действие.');return false;
   }
   pendingQuestReward=receipt;
  }
  save();refresh();
  if(event.type==='action'&&event.id.startsWith('boss:')){counters.clear();originalFight(state.battle);save();if(!isBattleActive){state.battle=null;save();refresh();}}
 }
 showCustomToast(result.message);return result.ok;
}

updateUI=refresh;
openTasks=function(){if(travelling)return false;if(closeOtherModals(['tasks-modal'])===false)return false;taskMode=state.mode;renderTasks();byId('tasks-modal').classList.remove('hidden');return true;};
toggleMapModal=function(show){if(travelling){showCustomToast('Дождитесь прибытия.');return;}if(show){interaction=null;locationView=false;if(isBattleActive){reopenNurseBattle();return;}if(closeOtherModals(['map-modal'])===false)return;renderMap();}byId('map-modal').classList.toggle('hidden',!show);};
showFloorsList=renderMap;openFloorMap=()=>toggleMapModal(true);handleLocationClick=()=>toggleMapModal(true);openMedicalHub=()=>toggleMapModal(true);handleNodeClick=()=>toggleMapModal(true);
// Legacy medical navigation cannot teleport the prototype's authoritative position.
selectRoom=()=>toggleMapModal(true);openProcedureRoom=()=>toggleMapModal(true);
startBossFight=function(boss){if(isBattleActive){reopenNurseBattle();return;}dispatch({type:'action',id:'boss:'+boss});};
openBossDossier=function(boss){if(!E.actions(state).some(a=>a.id==='boss:'+boss)){showCustomToast('Рейд доступен в комнате босса в Трипе после открытия секции.');return;}startBossFight(boss);};
handleVictory=function(){const active=isBattleActive,battle=currentBattleSession?.id;originalVictory();if(active&&lastBattleResult?.battleId===battle&&state.battle)dispatch({type:'battleEnd',victory:true});};
recordUnrewardedRaid=function(){const result=originalUnrewarded.apply(this,arguments);if(state.battle){E.apply(state,{type:'battleEnd',victory:false});save();sync();}return result;};
const consume=consumeMedicalItem;consumeMedicalItem=function(item){if(item?.effectType==='madness'){showCustomToast('Режим меняется только в 404.');return false;}return consume(item);};devSetMadness=()=>showCustomToast('Режим меняется только в 404.');
// Replace only this page's listener so the shared room-scene code stays untouched.
const oldButton=document.querySelector('.room-trip-switch'),newButton=oldButton.cloneNode(true);oldButton.replaceWith(newButton);newButton.addEventListener('click',switchMode);
function switchMode(){if(isBattleActive){showCustomToast('Сначала завершите рейд.');return;}if(wardrobeSession){showCustomToast('Сначала примените или отмените примерку.');return;}if(state.room!=='ward404'){focusQuest=null;focusRoom='ward404';notice='Смена режима доступна только в палате 404. ';toggleMapModal(true);return;}interaction=null;if(dispatch({type:'switch'})){taskMode=state.mode;setPaperDollView(state.mode==='trip'?'combat':'patient');refresh();}}

const priorRoom=window.PalataRoom;window.PalataRoom=Object.freeze({...priorRoom,toggleTrip:()=>newButton.click()});
tasks.addEventListener('click',e=>{if(e.target.dataset.taskMode){taskMode=e.target.dataset.taskMode;renderTasks();}if(e.target.dataset.questTab){tab=e.target.dataset.questTab;renderTasks();}});
document.querySelectorAll('[data-nav-modal="tasks-modal"]').forEach(b=>{b.setAttribute('aria-label','Задания');b.querySelector('span').textContent='Задания';});const taskLabel=document.querySelector('.hud-task span');if(taskLabel)taskLabel.textContent='Задания';

resumeRaid(raw?.raid);locationView=state.room!=='ward404'&&!state.battle;save();refresh();window.PalataQuestPrototype=Object.freeze({snapshot:()=>JSON.parse(JSON.stringify(state))});
})();
