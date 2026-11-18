/* Floor 10 adapter for the current game profile. Does not import sandbox saves. */
(function(){
'use strict';

const E=PalataQuestEngine,key='palata404_floor10_progress:'+encodeURIComponent(raidArchiveOwnerId),byId=id=>document.getElementById(id);
const navigation=window.PalataQuestNavigation,modelReady=typeof pendingBossCounters==='function'&&typeof restoreBossCounter==='function'&&typeof queueBossCounter==='function'&&typeof E.cargoName==='function'&&typeof E.bedPresentation==='function'&&E.initial().version===11&&typeof PalataQuestJobModel==='object'&&!!PalataQuestJobModel&&['make','restore','board','operate','supportsRevision','captureObservation'].every(name=>typeof PalataQuestJobModel[name]==='function')&&PalataQuestJobModel.supportsRevision('k3',3)&&PalataQuestJobModel.supportsRevision('k2',5)&&PalataQuestJobModel.supportsRevision('d1',5)&&PalataQuestJobModel.supportsRevision('d2',4)&&PalataQuestJobModel.supportsRevision('d3',4);
const guideFor=id=>navigation?navigation.guide(E,state,id):E.guide(state,id);
let raw,protectedSave=false;const stored=safeStorageGet(key);try{raw=JSON.parse(stored);protectedSave=!modelReady||(!!raw&&!E.supportsSave?.(raw));}catch(_){protectedSave=stored!==null;}let state=E.restore(raw);if(!stored)state.mode=stats.madness>=100?'trip':'patient';let tab='story',taskMode=null,focusQuest=null,focusRoom=null,notice='',workNotice='',locationView=false,interaction=null,travelling=false,saveFailed=false;
// Keep the existing collector and the approved first-test side-job payouts.
const collectorPayout=Object.freeze({silver:15,pills:1}),rewardKey='palata404_floor10_reward:'+encodeURIComponent(raidArchiveOwnerId);
const questKeyNotes=Object.freeze({'Ключ від блоку боса':'Служебный ключ Клары. К замку перехода B/C не подходит.','Ключ від ізолятора':'Ключ из кабинета врача. Лестничный выход требует отдельной проверки маршрута и замка.'});
let pendingQuestReward=null,rewardRecoveryError=false;
try{
 const journalText=safeStorageGet(rewardKey);
 if(journalText){const journal=JSON.parse(journalText);
  const collector=journal.receipt?.kind==='collector'&&Number.isSafeInteger(journal.progress?.collectorCount)&&journal.progress.collectorCount>0&&journal.receipt.id==='collector:'+journal.progress.collectorCount;
  const quest=journal.receipt?.kind==='quest'&&Number.isSafeInteger(journal.progress?.transaction)&&journal.progress.transaction>0&&journal.receipt.id==='transaction:'+journal.progress.transaction;
  const validInventory=Array.isArray(journal.inventory)&&journal.inventory.every(x=>x&&typeof x.name==='string'&&Number.isSafeInteger(x.count)&&x.count>0);
  if(!protectedSave&&[1,2].includes(journal.version)&&journal.owner===raidArchiveOwnerId&&(collector||journal.version===2&&quest)&&[3,4,5,6,7,8,9,10,11].includes(journal.progress?.version)&&modelReady&&!!E.supportsSave?.(journal.progress)&&journal.stats&&['silver','pills','exp','level'].every(k=>Number.isSafeInteger(journal.stats[k])&&journal.stats[k]>=0)&&(journal.version===1||validInventory)){
   raw=journal.progress;state=E.restore(raw);Object.assign(stats,normalizeStats(journal.stats));if(journal.version===2)inventory=normalizeInventory(journal.inventory);pendingQuestReward=journal.receipt;
  }else rewardRecoveryError=true;
 }
}catch(_){rewardRecoveryError=true;}
function syncCargo(){
 for(const item of inventory)if(item.category==='quest'&&questKeyNotes[item.name])item.desc=questKeyNotes[item.name];
 inventory=inventory.filter(x=>!x.questCargo);
 for(const id of state.cargo)inventory.push({...E.cargoCatalog[id],name:E.cargoName?.(state,id)||E.cargoCatalog[id].name,desc:E.cargoDescription?.(state,id)||E.cargoCatalog[id].desc,category:'quest',count:1,questCargo:id});
}
if(!protectedSave&&!rewardRecoveryError)syncCargo();
const originalSaveProgress=saveGameProgress;
saveGameProgress=function(){
 if(restoringRaid||!modelReady)return false;
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
for(const boss of Object.values(bossesDatabase))if(boss.questItem&&questKeyNotes[boss.questItem.name])boss.questItem.desc=questKeyNotes[boss.questItem.name];
const originalUpdate=updateUI,originalFight=startBossFight,originalVictory=handleVictory,originalUnrewarded=recordUnrewardedRaid;
const tasks=byId('tasks-modal').querySelector('.modal-content');tasks.classList.remove('tasks-placeholder');tasks.classList.add('quest-sheet');
tasks.innerHTML='<div class="modal-header"><h3 id="tasks-title">Задания · 10-й этаж</h3><button onclick="closeTasks()" aria-label="Закрыть задания">✕</button></div><p class="quest-note">Награда выдаётся после сдачи.<span class="quest-mobile-scroll-cue"> Лист прокручивается ↓</span></p><div class="quest-filter-row"><nav class="quest-tabs" aria-label="Категории заданий"><button data-quest-tab="story">Сюжет</button><button data-quest-tab="nurse">Клара</button><button data-quest-tab="doctor">Врач</button></nav><nav class="quest-tabs"><button data-task-mode="patient">Пациент</button><button data-task-mode="trip">Трип</button></nav></div><div id="quest-list"></div><p id="quest-save" role="status"></p><button onclick="toggleMapModal(true)">К действиям на этаже</button>';
const journalParts=[...tasks.children],dossier=document.createElement('section');dossier.className='quest-dossier hidden';tasks.append(dossier);let dossierId=null,dossierSelected=null,journalReturn=null;
const map=byId('map-floors-view');map.classList.add('quest-floor');byId('map-modal').querySelector('.map-clipboard-body').classList.add('quest-map-sheet');
const mapHome=byId('map-modal').querySelector('.map-clipboard-body');const locationScreen=document.createElement('main');locationScreen.id='quest-location-screen';locationScreen.classList.add('hidden');locationScreen.setAttribute('aria-label','Локация');document.body.append(locationScreen);
const officialHeader=document.createElement('div');officialHeader.className='quest-official-header';officialHeader.innerHTML='<document-header variant="left" department="ПЛАН ДЕСЯТОГО ЭТАЖА" scale="compact"></document-header><document-stamp type="service" rotate="-5"></document-stamp><document-stamp type="seal" rotate="8"></document-stamp>';byId('map-modal').querySelector('.map-clipboard-header').append(officialHeader);byId('map-modal').setAttribute('aria-label','Карта этажей');byId('map-modal').querySelector('.btn-close-map').setAttribute('aria-label','Закрыть окно');
// A single quest checkpoint holds position and the live raid together. Production
// payouts remain exclusively owned by handleVictory's durable reward journal.
let restoringRaid=false,collectorWake=null;
function checkpoint(){
 if(!state.battle||!currentBattleSession)return null;
 return {version:1,owner:raidArchiveOwnerId,boss:currentBossKey,hp:bossCurrentHp,maxHp:bossMaxHp,playerHp:stats.hp,
  endsAt:raidEndsAt,cooldown:attackCooldownEndsAt,ammo:battleWeaponAmmo,reloadAt:weaponReloadEndsAt,
  weapons:typeof battleWeaponSnapshot==='function'?battleWeaponSnapshot():null,
  profile:{...getBattleAttackProfile()},session:{...currentBattleSession,events:[...currentBattleSession.events]},
  members:JSON.parse(JSON.stringify(raidMembers)),inventory:JSON.parse(JSON.stringify(inventory)),
  counters:pendingBossCounters()};
}
// Checkpoint inventories bypass the normal profile loader. Reject the whole
// malformed checkpoint instead of replacing a valid profile with partial data.
function raidInventorySnapshot(items){
 if(!Array.isArray(items))return null;
 const result=[];
 for(const item of items){
  if(!item||typeof item!=='object'||Array.isArray(item)||typeof item.name!=='string'||!item.name.trim())return null;
  const count=item.count===undefined?1:(typeof item.count==='number'||typeof item.count==='string'?Number(item.count):NaN);
  if(!Number.isSafeInteger(count)||count<=0)return null;
  result.push({...item,count});
 }
 return result;
}
function resumeRaid(r){
 if(!state.battle)return;
 if(!modelReady){notice='Не удалось загрузить актуальные файлы боя. Обновите страницу; сохранение не заменено.';return;}
 const completed=r?.session?.id&&(lastBattleResult?.battleId===r.session.id?lastBattleResult:readRaidArchive().find(x=>x.battleId===r.session.id));
 if(completed){if(completed.outcome==='victory'&&state.battle==='doctor')state.flags.doctorWon=true;if(completed.outcome!=='victory')state.room='ward404';state.battle=null;return;}
 const finite=n=>Number.isFinite(n)&&n>=0;
 const savedInventory=raidInventorySnapshot(r?.inventory);
 if(!r||r.version!==1||r.owner!==raidArchiveOwnerId||r.boss!==state.battle||r.session?.bossKey!==r.boss||typeof r.session?.id!=='string'||r.session.finished||!Array.isArray(r.session.events)||!Array.isArray(r.members)||!savedInventory||![r.hp,r.maxHp,r.playerHp,r.endsAt,r.cooldown,r.ammo,r.reloadAt].every(finite)||!r.profile||!finite(r.profile.cooldown)||!finite(r.profile.capacity)||!Number.isSafeInteger(r.session.serial)||r.session.serial<0||!r.session.events.every(x=>typeof x==='string'&&x.startsWith(r.session.id+':'))||!Array.isArray(r.counters)||!r.counters.every(x=>Array.isArray(x)&&x.length===2&&typeof x[0]==='string'&&x[0].startsWith(r.session.id+':')&&finite(x[1]))||!r.members.every(x=>x&&raidMembers.some(m=>m.id===x.id)&&finite(x.damage)&&x.metrics&&['damageTaken','healing','turns','madnessStart'].every(k=>x.metrics[k]===null||finite(x.metrics[k])))||r.hp>r.maxHp||r.maxHp<=0||!['damage','reload','critical','miss','criticalMultiplier'].every(k=>finite(r.profile[k]))){
  // Keep the original bytes available before migrating a legacy/incomplete battle.
  if(stored&&!safeStorageSet(key+':recovery',stored)){protectedSave=true;saveFailed=true;}
  state.battle=null;state.room='ward404';notice='Старый рейд не содержит контрольной точки. Копия сохранения оставлена для восстановления.';return;
 }
 // Starting restores only arena UI and timers; overwrite its new metrics before input.
 restoringRaid=true;originalFight(r.boss);stopBattleTimers();isBattleActive=true;
 currentBossKey=r.boss;bossCurrentHp=r.hp;bossMaxHp=r.maxHp;stats.hp=Math.min(stats.maxHp,r.playerHp);
 inventory=savedInventory;currentBattleSession={...r.session,events:new Set(r.session.events)};
 for(const member of raidMembers){const prior=r.members.find(x=>x.id===member.id);if(prior)Object.assign(member,prior);}
 battleWeaponProfile=r.profile;battleWeaponAmmo=r.ammo;raidEndsAt=r.endsAt;attackCooldownEndsAt=r.cooldown;
 playerAttackCooldown=Date.now()<r.cooldown;
 weaponReloadEndsAt=r.reloadAt;
 if(typeof restoreBattleWeapons==='function')restoreBattleWeapons(r.weapons,r);
 else if(r.reloadAt){const generation=battleGeneration;const finish=()=>{if(!isBattleActive||generation!==battleGeneration)return;battleWeaponAmmo=r.profile.capacity;weaponReloadEndsAt=0;renderWeaponBattleState();save();};if(r.reloadAt<=Date.now())finish();else weaponReloadTimer=setTimeout(finish,r.reloadAt-Date.now());}
 for(const [id,at] of r.counters||[]){if(typeof id!=='string'||!finite(at)||currentBattleSession.events.has(id+':counter'))continue;restoreBossCounter(id,at);}
 raidTimerInterval=setInterval(updateRaidTimerTick,1000);friendAttackInterval=setInterval(friendsAutoAttackTick,3500);
 restoringRaid=false;updateRaidTimerTick();if(isBattleActive){updateBattleUI();updateRaidListUI();reopenNurseBattle();}
}
const attack=performPlayerAttack;performPlayerAttack=function(){const result=attack.apply(this,arguments);save();return result;};
const helpers=friendsAutoAttackTick;friendsAutoAttackTick=function(){const r=helpers.apply(this,arguments);save();return r;};
const reload=startWeaponReload;startWeaponReload=function(){const r=reload.apply(this,arguments);save();return r;};
window.addEventListener('pagehide',save);
window.addEventListener('raid-weapon-state',save);
window.addEventListener('raid-counter-state',save);
function save(){if(restoringRaid)return false;if(protectedSave||!modelReady){saveFailed=true;return false;}state.raid=checkpoint();saveFailed=rewardRecoveryError||(pendingQuestReward?!saveGameProgress():!safeStorageSet(key,JSON.stringify(state)));return !saveFailed;}
function sync(){stats.madness=state.mode==='trip'?100:0;if(!wardrobeSession)paperDollState.activeViewMode=state.mode==='trip'?'combat':'patient';currentRoom={id:state.room==='ward404'?'room_404':state.room,name:E.rooms[state.room][1],desc:'10-й этаж · секция '+E.rooms[state.room][0]};}
function renderTasks(){
 const list=byId('quest-list'),mode=taskMode||state.mode,openNotes=new Set([...list.querySelectorAll('details[data-quest-notes][open]')].map(note=>note.dataset.questNotes));list.replaceChildren();
 const rows=tab==='story'?(navigation?navigation.story(E,state):E.story(state)).filter(r=>r.mode===mode):Object.entries(E.jobs).filter(([,j])=>j.giver===tab).filter(([id])=>mode==='patient'||id==='d3').map(([id,j])=>{
  const p=state.jobs[id],tripStep=mode==='trip';
  let detail;
  if(tripStep){
   if(!p?.active)detail=p?.count?'Предыдущая карточка сдана. Новое поручение можно получить у врача в Пациенте.':'Сначала получите поручение у врача.';
   else if(p.done.difference)detail='Наблюдение записано. Передайте карточку врачу в Пациенте.';
   else if(p.revision===4){
    const stage=E.jobStage(state,id);
    const place=E.rooms[stage?.room]?.[1];
    detail=(place?place+'. ':'')+(stage?.text||'Проверьте доступное действие для выбранного предмета.');
   }else if([2,3].includes(p.revision)&&!p.work.baselineCaptured){
    detail='Сначала запишите первичные показания коридора A в Пациенте.';
   }else detail='Сравните карточку с новым наблюдением в коридоре A.';
  }else{
   const hasBaseline=id==='d3'&&[2,3,4].includes(p?.revision);
   const progress=hasBaseline?Number(!!p.work.baselineCaptured)+Number(!!p.done.difference):j.steps.filter(x=>p?.done[x]).length;
   const total=hasBaseline?2:j.steps.length;
   const callStage=id==='d1'&&p?.active&&[4,5].includes(p.revision)?E.jobStage(state,id):null;
   const active=E.ready(state,id)?'Готово к сдаче':callStage?'Этап: '+callStage.text:'Активно: '+progress+'/'+total;
   const status=p?.active?active:!j.repeat&&p?.count?'Поручение выполнено':'Взять у '+(tab==='nurse'?'Клары (B)':'врача (C)');
   detail=`${j.repeat?'Повторяемое':'Разовое'} · ${status} · Сдано: ${p?.count||0}. Награда: ${E.rewardText(id)}.`;
  }
  return {id,title:j.title+(id==='d3'?(tripStep?' · наблюдение':' · карточка и сдача'):''),done:!!p?.count&&!p.active,detail,repeat:j.repeat};
 });
 for(const r of rows){
  const a=document.createElement('article');a.className='quest-card';a.dataset.questId=r.id;
  const h=document.createElement('h4');h.textContent=(r.pending?'Продолжение · ':r.done?'✓ ':'○ ')+r.id+' '+r.title;
  const p=document.createElement('p');p.textContent=r.detail;a.append(h,p);
  const brief=E.jobBrief?.(r.id,state.jobs[r.id]?.revision);if(brief){const purpose=document.createElement('p');purpose.className='quest-order-purpose';purpose.textContent=brief.giver+': '+brief.purpose;const proof=document.createElement('p');proof.className='quest-order-deliverable';proof.textContent='Подтверждение для сдачи: '+brief.deliverable;a.append(purpose,proof);}
  if(r.pending){const pending=document.createElement('p');pending.textContent='Продолжение пока недоступно. Текущие поручения можно завершить на десятом этаже.';a.append(pending);}
  else if(!r.done||r.repeat){
   const g=guideFor(r.id),hint=document.createElement('p');hint.textContent='Следующая точка: '+(E.rooms[g.room]?.[1]||'продолжение маршрута')+'. '+g.text;
   a.append(hint);
   switchHint(a,g);
   if(g.room)a.append(button('Показать на карте',()=>showQuestTarget(r.id)));
   if(g.hint){const detail=document.createElement('details'),summary=document.createElement('summary'),text=document.createElement('p');summary.textContent='Дополнительная подсказка';text.textContent=g.hint;detail.append(summary,text);a.append(detail);}
  }else{const done=document.createElement('p');done.textContent='Завершено. Повторять эти действия не нужно.';a.append(done);}
  if(r.id==='d1')appendCallPlan(a);
  if(!r.pending)appendCollectedNotes(a,r.id,openNotes.has(r.id),r.done);
  list.append(a);
 }
 tasks.querySelectorAll('[data-quest-tab]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.questTab===tab)));
 tasks.querySelectorAll('[data-task-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.taskMode===mode)));
 if(!list.children.length)list.textContent='В этом режиме нет поручений этой категории. Просмотр другого режима не переключает игру.';
 byId('quest-save').textContent=!modelReady?'Не удалось загрузить рабочие листы. Обновите страницу.':saveFailed?'Сохранение недоступно или формат новее этой версии. Исходные данные не заменяются.':'';
 if(dossierId)renderDossier();
}

function appendCollectedNotes(host,id,open,complete){
 const projection=window.PalataQuestNotes;
 if(!projection)return;
 const records=projection.forQuest(E,window.PalataQuestJobModel,state,id);
 const launch=button('Дело поручения · '+records.length,()=>openDossier(id));launch.dataset.openDossier=id;launch.className='quest-dossier-launch';host.append(launch);
 const detail=document.createElement('details'),summary=document.createElement('summary');
 detail.dataset.questNotes=id;detail.open=open;
 summary.textContent='Собранные записи · '+records.length;detail.append(summary);
 const scope=document.createElement('p');scope.textContent='Копии сохранённых осмотров и актов. Текущая или последняя заявка.';detail.append(scope);
 if(!records.length){const empty=document.createElement('p');empty.textContent=complete?'Подробные источники в этом сохранении не зафиксированы. Отметка о выполнении остаётся в журнале.':id==='k3'&&state.jobs.k3?.active?'Здесь сохраняются отмеченные поля и итог сверки. Исходные записи находятся в процедурной.':'Записи появятся после осмотра предмета или работы с документом.';detail.append(empty);}
 for(const record of records){
  const entry=document.createElement('section');entry.dataset.questNote=record.id;
  const title=document.createElement('h4');title.textContent=record.title;
  const origin=document.createElement('p');origin.textContent=record.source+' · '+({draft:'Черновик',recorded:'Записано',confirmed:'Подтверждено'}[record.status]||'Записано');
  entry.append(title,origin);
  if(record.text){const text=document.createElement('p');text.textContent=record.text;entry.append(text);}
  for(const field of record.fields){const line=document.createElement('p'),label=document.createElement('strong');label.textContent=field.label+': ';line.append(label,document.createTextNode(field.value));entry.append(line);}
  detail.append(entry);
 }
 host.append(detail);
}

function appendCallPlan(host){
 const plan=E.jobStage?.(state,'d1')?.plan;
 if(!Array.isArray(plan)||!plan.length)return;
 const detail=document.createElement('details');detail.dataset.callPlan='d1';
 const summary=document.createElement('summary');summary.textContent='План проверки · '+plan.length;
 const steps=document.createElement('ol');
 const labels={diagnosis:'Первичная проверка',service:'Обслуживание',retest:'Контрольный вызов'};
 for(const step of plan){
  const row=document.createElement('li');row.dataset.callStop=step.action;
  const place=document.createElement('strong');place.textContent=(labels[step.phase]||'Проверка')+' · '+E.rooms[step.room][1];
  row.append(place,document.createElement('br'),document.createTextNode(step.text));steps.append(row);
 }
 const note=document.createElement('p');note.textContent='После обслуживания соответствующего узла в плане появится контрольный вызов. Проверки выполняются в палатах.';
 detail.append(summary,steps,note);host.append(detail);
}

function showQuestTarget(id){
 focusQuest=id;focusRoom=null;notice='Точка задания подсвечена. ';toggleMapModal(true);
 requestAnimationFrame(()=>{if(!byId('map-modal').classList.contains('hidden'))map.querySelector('.quest-map-pin.is-target')?.scrollIntoView({block:'center',inline:'center',behavior:'instant'});});
}
function openDossier(id){
 journalReturn={top:tasks.scrollTop,id};dossierId=id;dossierSelected=null;
 tasks.classList.add('has-dossier');journalParts.forEach(part=>part.classList.add('quest-journal-hidden'));
 dossier.classList.remove('hidden');tasks.scrollTop=0;
 byId('tasks-modal').setAttribute('aria-labelledby','quest-dossier-title');
 renderDossier();dossier.querySelector('[data-dossier-heading]')?.focus({preventScroll:true});
}
function closeDossier(restoreFocus=true){
 dossierId=null;dossierSelected=null;dossier.classList.add('hidden');tasks.classList.remove('has-dossier');
 journalParts.forEach(part=>part.classList.remove('quest-journal-hidden'));
 byId('tasks-modal').setAttribute('aria-labelledby','tasks-title');
 if(journalReturn){
  const view=journalReturn;tasks.scrollTop=view.top;
  if(restoreFocus)requestAnimationFrame(()=>{
   if(dossierId||byId('tasks-modal').classList.contains('hidden'))return;
   [...tasks.querySelectorAll('[data-open-dossier]')].find(control=>control.dataset.openDossier===view.id)?.focus({preventScroll:true});tasks.scrollTop=view.top;
   requestAnimationFrame(()=>{if(!dossierId&&!byId('tasks-modal').classList.contains('hidden'))tasks.scrollTop=view.top;});
  });
 }
}
function renderDossier(){
 const id=dossierId;if(!id)return;
 const records=window.PalataQuestNotes?.forQuest(E,window.PalataQuestJobModel,state,id)||[],previous=dossier.querySelector('.quest-dossier-body'),top=previous?.scrollTop||0;
 const oldFocus=dossier.contains(document.activeElement)?document.activeElement?.dataset.dossierRecord:null;
 const selected=records.find(record=>record.id===dossierSelected)||records[0];dossierSelected=selected?.id||null;
 dossier.replaceChildren();dossier.dataset.questDossier=id;
 const toolbar=document.createElement('nav');toolbar.className='quest-dossier-toolbar';toolbar.setAttribute('aria-label','Навигация по делу');
 const back=button('← К журналу',()=>closeDossier());back.dataset.dossierBack='true';
 const label=document.createElement('span');label.textContent='Дело '+id+' · 10-й этаж · '+(state.mode==='trip'?'Трип':'Пациент');
 const cue=document.createElement('small');cue.className='quest-dossier-scroll-cue';cue.textContent='Лист прокручивается ↓';label.append(cue);
 const close=button('✕',()=>{closeDossier(false);closeTasks();});close.setAttribute('aria-label','Закрыть задания');close.dataset.dossierClose='true';toolbar.append(back,label,close);
 const body=document.createElement('div');body.className='quest-dossier-body';
 const masthead=document.createElement('div');masthead.className='quest-dossier-masthead';
 const header=document.createElement('document-header');header.setAttribute('variant','left');header.setAttribute('department','МАТЕРИАЛЫ ПОРУЧЕНИЯ');header.setAttribute('scale','compact');
 const g=guideFor(id),job=state.jobs[id],complete=job&&!job.active&&job.count>0||g.complete;
 const status=document.createElement('span');status.className='quest-dossier-status';status.textContent=complete?'ПОРУЧЕНИЕ СДАНО':job&&E.ready(state,id)?'ГОТОВО К СДАЧЕ':'В РАБОТЕ';masthead.append(header,status);
 const heading=document.createElement('h3');heading.id='quest-dossier-title';heading.dataset.dossierHeading='true';heading.tabIndex=-1;
 heading.textContent=E.jobs[id]?.title||((navigation?navigation.story(E,state):E.story(state)).find(row=>row.id===id)?.title)||'Сохранённые осмотры';
 const scope=document.createElement('p');scope.className='quest-dossier-scope';scope.textContent='Копии полученных источников и оформленных актов · текущая или последняя заявка';
 body.append(masthead,heading,scope);
 const columns=document.createElement('div');columns.className='quest-dossier-columns';
 const sources=document.createElement('nav');sources.className='quest-dossier-sources';sources.setAttribute('aria-label','Материалы дела');
 const sourceTitle=document.createElement('h4');sourceTitle.textContent='МАТЕРИАЛЫ ДЕЛА';sources.append(sourceTitle);
 for(const record of records){
  const control=button(record.title,()=>{dossierSelected=record.id;renderDossier();const content=dossier.querySelector('.quest-dossier-document');content?.focus({preventScroll:true});if(matchMedia('(pointer:coarse)').matches)content?.scrollIntoView({block:'start'});});
  control.dataset.dossierRecord=record.id;control.setAttribute('aria-pressed',String(record.id===selected?.id));
  const provenance=document.createElement('small');provenance.textContent=record.status==='draft'?'Черновик · не подтверждён':record.status==='confirmed'?'Подтверждённый акт':'Сохранённый источник';control.append(provenance);sources.append(control);
 }
 if(id==='d1')appendCallPlan(sources);
 const documentCopy=document.createElement('article');documentCopy.className='quest-dossier-document';documentCopy.tabIndex=-1;documentCopy.setAttribute('aria-label','Копия выбранного материала');
 if(selected){
  documentCopy.dataset.dossierNote=selected.id;
  const title=document.createElement('h4');title.textContent=selected.title;
  const provenance=document.createElement('p');provenance.className='quest-dossier-origin';provenance.textContent=selected.source+' · '+({draft:'Черновик',recorded:'Записано',confirmed:'Подтверждено'}[selected.status]||'Записано');documentCopy.append(title,provenance);
  if(selected.text){const text=document.createElement('p');text.textContent=selected.text;documentCopy.append(text);}
  const facts=document.createElement('dl');for(const field of selected.fields){const label=document.createElement('dt'),value=document.createElement('dd');label.textContent=field.label;value.textContent=field.value;facts.append(label,value);}documentCopy.append(facts);
  const note=document.createElement('p');note.className='quest-dossier-copy-note';note.textContent=selected.status==='draft'?'Это сохранённый выбор, а не подтверждённый результат. Проверка выполняется в рабочем листе.':'Это копия уже полученных сведений. Осмотр и проверку выполняют у предмета.';documentCopy.append(note);
 }else{
  const title=document.createElement('h4');title.textContent='Сохранённых материалов пока нет';const text=document.createElement('p');
  text.textContent=complete?'В этом сохранении подробные источники не фиксировались. Отметка о выполнении остаётся в журнале.':id==='k3'&&job?.revision!==3?'В старом листе здесь сохраняются пометки и итог. Исходные записи находятся в процедурной.':'Материалы появятся после осмотра предмета или получения документа.';documentCopy.append(title,text);
 }
 columns.append(sources,documentCopy);body.append(columns);
 const footer=document.createElement('footer');footer.className='quest-dossier-footer';
 const next=document.createElement('p');const nextTitle=document.createElement('strong');nextTitle.textContent=g.complete?'Поручение завершено':'Следующий шаг · '+(E.rooms[g.room]?.[1]||'Журнал')+(g.mode?' · '+(g.mode==='trip'?'Трип':'Пациент'):'');next.append(nextTitle,document.createElement('br'),document.createTextNode(g.text));footer.append(next);
 if(g.room&&!g.complete){const target=button('Показать на карте →',()=>showQuestTarget(id));target.dataset.dossierMap='true';footer.append(target);}
 dossier.append(toolbar,body,footer);body.scrollTop=top;
 if(oldFocus)[...sources.querySelectorAll('[data-dossier-record]')].find(control=>control.dataset.dossierRecord===oldFocus)?.focus({preventScroll:true});
}
tasks.addEventListener('keydown',event=>{if(event.key==='Escape'&&dossierId){event.preventDefault();event.stopPropagation();closeDossier();}});

function switchHint(host,g){
 if(!g?.needsModeChange)return;
 const text=document.createElement('p');text.className='quest-mode-requirement';text.textContent='Следующий шаг доступен в состоянии «'+(g.mode==='trip'?'Трип':'Пациент')+'». ';
 const control=button('К переключателю состояния',()=>{if(closeOtherModals([])===false)return;locationView=false;interaction=null;locationScreen.classList.add('hidden');mapHome.append(map);byId('map-modal').classList.add('hidden');requestAnimationFrame(()=>{const target=document.querySelector('.room-trip-switch');if(target?.getClientRects().length&&!document.body.classList.contains('modal-open'))target.focus({preventScroll:true});});});host.append(text,control);
}

function button(label,fn,disabled=false){const b=document.createElement('button');b.type='button';b.textContent=label;b.disabled=disabled;b.addEventListener('click',fn);return b;}
const roomDescriptions={
 ward404:'Палата пациента: кровать, шкаф и переключатель режимов.',ward405:'Соседняя палата с кроватью, стулом и документом.',collector:'Ординаторская: шкаф с хозяйственным резервом и припасами.',gym:'Зал реабилитации со скакалкой, турником, скамьёй для жима и матом.',toilet:'Уборная с умывальником и шкафчиком.',A:'Коридор секции A. Здесь находится механизм прохода в секцию B.',B:'Коридор секции B с проходом и замком в секцию C.',C:'Коридор секции C у кабинета врача и лестницы.',nurse:'Медпункт Клары: лоток, документы и медицинский шкаф.',procedure:'Процедурная с кроватью, лотком и документами.',technical:'Техническое помещение с оборудованием и служебной дверью.',linen:'Бельевая: шкафы и комплекты больничного белья.',ward406:'Палата 406 с местом для передачи белья.',ward407:'Палата 407 с кнопкой вызова у кровати.',ward408:'Палата 408 с кнопкой вызова и документом.',doctor:'Кабинет врача с документами, шкафом и креслом.',stairs:'Лестничная площадка с замком на выходе.'
};
const doorIcon='<svg viewBox="0 0 24 30" aria-hidden="true"><path d="M3 28V2h18v26M1 28h22" fill="none" stroke="currentColor" stroke-width="2"/><path d="M6 27V5l12-2v24Z" fill="currentColor" fill-opacity=".25" stroke="currentColor" stroke-width="1.5"/><circle cx="15" cy="16" r="1.3" fill="currentColor"/></svg>';
let selectedRoom=null,roomClickTimer=0,roomInfoCollapsed=state.room==='gym',planScrollLeft=0,planScrollTop=0,lastDoorTap=null,paperPlacement={key:null,side:'right'};
function cancelRoomClick(){clearTimeout(roomClickTimer);roomClickTimer=0;}
function cancelRoomGesture(){cancelRoomClick();lastDoorTap=null;}
byId('map-modal').addEventListener('palata:map-orient',cancelRoomGesture);
// Generic dialog controls (Escape/backdrop) can hide this modal directly.
new MutationObserver(()=>{if(byId('map-modal').classList.contains('hidden'))cancelRoomGesture();})
 .observe(byId('map-modal'),{attributes:true,attributeFilter:['class']});
for(const type of ['wheel','touchmove'])byId('map-modal').addEventListener(type,cancelRoomGesture,{capture:true,passive:true});
// A touch can be timestamped before the preview deadline but delivered after
// the browser has painted the description. Preserve that real double-tap's
// original door intent; do not route it to a newly exposed document control.
byId('map-modal').addEventListener('click',event=>{
 const tap=lastDoorTap;
 if(byId('map-modal').classList.contains('hidden')||document.documentElement.dataset.touchUi!=='true'||!tap||event.detail<2||
    byId('map-modal').dataset.compactView!=='details'||selectedRoom!==tap.id||
    event.target.closest?.('.quest-map-pin'))return;
 const elapsed=event.timeStamp-tap.at;
 const tolerance=12*(parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--touch-ui-scale'))||1);
 if(elapsed<0||elapsed>280||Math.hypot(event.clientX-tap.x,event.clientY-tap.y)>tolerance)return;
 event.preventDefault();event.stopImmediatePropagation();openRoom(tap.id);
},true);
function showRoomPreview(id){
 cancelRoomClick();if(!E.rooms[id])return;selectedRoom=id;
 const sidebar=map.querySelector('.quest-map-sidebar');if(!sidebar)return;
 sidebar.querySelector('.quest-room-preview')?.remove();
 const card=document.createElement('section');card.className='quest-room-preview';card.setAttribute('aria-live','polite');
 const title=document.createElement('h4');title.textContent=E.rooms[id][1];
 const description=document.createElement('p');description.textContent=roomDescriptions[id];
 const gate=navigation?.blocked(E,state,E.rooms[id][0]);const locked=gate?!gate.accessible:!E.accessible(state,E.rooms[id][0]),heading=document.createElement('h5');heading.textContent='Доступные задания и действия';
 const list=document.createElement('ul');
 for(const action of locked?[]:E.actions({...state,room:id})){const row=document.createElement('li');row.textContent=action.label;list.append(row);}
 if(!list.childNodes.length){const row=document.createElement('li');row.textContent=locked?(gate?.text||'Проход пока закрыт.'):'Сейчас нет новых поручений. Комнату можно осмотреть.';list.append(row);}
 const enter=button(locked?'Дверь пока закрыта':'Открыть дверь',()=>openRoom(id),locked);enter.dataset.enterRoom=id;
 card.append(title,description);const outcomes=window.PalataQuestStateView?.forRoom(E,state,id)||[];if(outcomes.length){const section=document.createElement('section');section.className='quest-room-outcomes';section.setAttribute('aria-label','Подтверждённые изменения');for(const outcome of outcomes){const row=document.createElement('p');row.dataset.roomOutcome=outcome.id;row.dataset.outcomeStatus=outcome.status;const label=document.createElement('strong');label.textContent=outcome.label;const detail=document.createElement('span');detail.textContent=outcome.text;row.append(label,detail);section.append(row);}card.append(section);}card.append(heading,list,enter);if(locked&&gate)switchHint(card,gate);sidebar.prepend(card);sidebar.scrollTop=0;
 map.querySelectorAll('.quest-map-pin').forEach(pin=>pin.setAttribute('aria-expanded',String(pin.dataset.room===id)));
 window.PalataCompactUI?.previewOpened();
}
function openRoom(id){
 cancelRoomGesture();if(travelling)return;
 if(isBattleActive){reopenNurseBattle();return;}
 if(!E.accessible(state,E.rooms[id][0])){showRoomPreview(id);if(matchMedia('(max-width:900px)').matches)map.querySelector('.quest-room-preview')?.scrollIntoView({block:'nearest'});return;}
 selectedRoom=null;roomInfoCollapsed=id==='gym';interaction=null;
 if(id===state.room){locationView=true;renderMap();}else travel(id);
}
function selectRoomDoor(id,event){
 cancelRoomClick();lastDoorTap=event.detail>0?{id,at:event.timeStamp,x:event.clientX,y:event.clientY}:null;
 if(event.detail===0){showRoomPreview(id);map.querySelector('[data-enter-room]')?.focus();return;}
 roomClickTimer=setTimeout(()=>{showRoomPreview(id);if(matchMedia('(max-width:900px)').matches)map.querySelector('.quest-room-preview')?.scrollIntoView({block:'nearest'});},280);
}

function talkToStaff(action){
 const [verb,id]=action.split(':');
 const job=E.jobs[id];
 if(!job||!E.actions(state).some(candidate=>candidate.id===action))return;
 if(!window.PalataQuestDialogues?.open){showCustomToast('Разговор не загрузился. Обновите страницу и повторите.');return;}
 const phase=verb==='accept'?'offer':verb==='claim'?'ready':'active';
 const stage=()=>E.jobStage(state,id)||guideFor(id);
 const outcome=()=>{
  const order=state.jobs[id];
  return {method:order?.work?.draftScene?.method||order?.work?.draftMethod,
          result:verb==='claim'&&order?.active===false?state.lastReceipt:'',
          reward:E.rewardText(id)};
 };
 const selector='[data-scene-action="'+action+'"],[data-action="'+action+'"]';
 window.PalataQuestDialogues?.open({
  id,phase,revision:state.jobs[id]?.revision||PalataQuestJobModel.make(id,state.jobs[id]?.count||0,state.world.callEquipment,state).revision,
  stage:stage(),getStage:stage,outcome:outcome(),getOutcome:outcome,
  anchor:document.activeElement,
  restoreFocus:()=>Array.from(locationScreen.querySelectorAll(selector)).find(el=>el.getClientRects().length)||
    locationScreen.querySelector('.quest-room-tools button'),
  onConfirm:()=>{
   const previous=focusQuest;
   focusQuest=verb==='accept'?id:focusQuest===id?null:focusQuest;
   const ok=dispatch({type:'action',id:action});
   if(!ok)focusQuest=previous;
   return ok?{ok:true}:{ok:false,message:'Действие не подтверждено. Проверьте сообщение о сохранении и повторите.'};
  }
 });
}
function beginAction(id){
 if(/^(accept:|claim:|talk:)/.test(id))return talkToStaff(id);
 workNotice='';if(E.workbench?.(state,id)){
 const owner=PalataQuestJobModel.owner?.[id.slice(4)];
 if(owner)focusQuest=owner;
 interaction=id;locationView=true;renderMap();const opened=E.workbench(state,id);if(opened?.kind==='caseCompare'&&!opened.sourcesRead&&locationScreen.querySelector('[data-work-kind=caseCompare]'))dispatch({type:'work',id,op:'readSources'});locationScreen.querySelector('[data-work-heading]')?.focus({preventScroll:true});return;}if(!E.interactions[id])return dispatch({type:'action',id});if(id==='unlockB'&&(!state.flags.doorKnown||!state.flags.reserveKnown||!state.flags.tripHandle)){focusQuest='lockB';notice='Нужны знание исправного механизма и аварийная рукоять из ординаторской A. ';locationView=false;renderMap();return;}if(id==='unlockC'&&(!state.flags.cKeyKnown||!state.flags.cLockKnown)){focusQuest='lockC';notice='Нужны опись хранения ключа в процедурной и памятка о замке у врача. ';locationView=false;renderMap();return;}interaction=id;locationView=true;renderMap();}
function renderInteraction(host){const board=E.workbench?.(state,interaction);if(board){const note=document.createElement('p');note.textContent=board.title||'Рабочий лист';host.append(note);return;}const spec=E.interactions[interaction];if(!spec){interaction=null;return;}const index=state.interactions[interaction]||0,step=spec.steps[index];if(!step){interaction=null;return;}const h=document.createElement('h4');h.textContent=spec.title+' · шаг '+(index+1)+'/'+spec.steps.length;const p=document.createElement('p');p.textContent=step.text;host.append(h,p);if(step.hint&&state.interactions.inspectDoor>=E.interactions.inspectDoor.steps.length){const hint=document.createElement('details'),summary=document.createElement('summary'),text=document.createElement('p');hint.dataset.interactionHint=interaction;summary.textContent='Вспомнить запись осмотра';text.textContent=step.hint;hint.append(summary,text);host.append(hint);}for(const [choice,label] of step.choices){const b=button(label,()=>{const id=interaction;const ok=dispatch({type:'interact',id,choice});if(ok){if((state.interactions[id]||0)===spec.steps.length||id==='exercise'&&state.interactions.exercise===0)interaction=null;renderMap();}else b.setAttribute('aria-invalid','true');});b.dataset.choice=choice;if(window.PalataQuestScenes)PalataQuestScenes.decorateChoice(b,choice);host.append(b);}const feedback=document.createElement('p');feedback.className='interaction-feedback';feedback.setAttribute('role','status');host.append(feedback,button('Отложить осмотр',()=>{interaction=null;renderMap();}));}

// Keep the requested handoff ahead of unrelated offers; preserve its real handler.
function prioritizeRoomTask(info){
 if(interaction)return;
 const actions=E.actions(state),requested=focusQuest&&actions.find(a=>a.id==='accept:'+focusQuest||a.id==='claim:'+focusQuest);
 const priority=(requested||actions.find(a=>a.id.startsWith('claim:')))?.id;
 const control=id=>info.querySelector('[data-action="'+id+'"],[data-scene-action="'+id+'"]');
 const raise=(target,container)=>{
  const previous=target.closest('.scene-document-actions');
  container.append(target);
  if(previous&&!previous.querySelector('button'))previous.remove();
 };
 if(document.documentElement.dataset.touchUi==='true'){
  const start=info.querySelector(':scope > p');
  if(state.room==='doctor'){
   const observation=actions.find(({id})=>['accept:d3','job:baseline','claim:d3'].includes(id));
   if(observation){
    const chosenWork=focusQuest&&actions.find(({id})=>id.startsWith('job:')&&PalataQuestJobModel.owner?.[id.slice(4)]===focusQuest);
    const other=focusQuest==='d3'?null:requested?.id||chosenWork?.id||priority;
    const shortcuts=document.createElement('section');
    shortcuts.className='scene-document-actions';shortcuts.dataset.doctorPriority='true';
    shortcuts.setAttribute('aria-label','Поручения врача');
    for(const id of new Set([other,observation.id])){
     const target=id&&control(id);
     if(target)raise(target,shortcuts);
    }
    if(shortcuts.childElementCount){start.after(shortcuts);return;}
   }
  }else if(state.jobs.d3?.revision===4&&['ward406','ward407'].includes(state.room)){
   const observation=actions.find(({id})=>id==='job:baseline'||id==='job:difference');
   const target=observation&&control(observation.id);
   if(target){
    const previous=target.closest('.scene-document-actions');
    start.after(target);
    if(previous&&!previous.querySelector('button'))previous.remove();
   }
  }
 }
 if(!priority)return;
 const target=control(priority);
 if(!target)return;
 const group=target.closest('.scene-document-actions');
 if(group){const heading=group.querySelector('h4');if(heading)heading.after(target);}
 const block=group||target,first=info.querySelector('.scene-instruction,.scene-document-actions');
 if(first&&first!==block)info.insertBefore(block,first);
}
function renderGiverBriefs(info,scene){
 if(interaction||state.mode!=='patient')return;
 const seen=new Set();
 for(const action of info.querySelectorAll('[data-scene-action^="accept:"],[data-action^="accept:"]')){
  const id=(action.dataset.sceneAction||action.dataset.action).slice(7),brief=E.jobBrief?.(id);
  if(!brief||seen.has(id))continue;seen.add(id);
  const note=document.createElement('p');note.className='quest-order-preview';note.id='quest-offer-'+id;
  const purpose=document.createElement('span');purpose.textContent=brief.purpose;
  const proof=document.createElement('small');proof.textContent='Передать: '+brief.deliverable;
  note.append(purpose,proof);
  const shortcuts=action.closest('[data-doctor-priority]');
  if(shortcuts)shortcuts.append(note);else action.after(note);
  action.setAttribute('aria-describedby',note.id);scene.querySelector('[data-action="accept:'+id+'"]')?.setAttribute('aria-describedby',note.id);
 }
}

function renderRoomContinuation(host){
 const next=navigation?.continuation?.(E,state,focusQuest);
 if(!next||next.room===state.room&&!next.needsModeChange)return false;
 const section=document.createElement('section');section.className='quest-room-next';section.dataset.roomNext=next.questId;
 const title=document.createElement('h4');title.textContent='Следующий шаг';
 const text=document.createElement('p');text.textContent=(E.rooms[next.room]?.[1]||'Следующая точка')+'. '+next.text;
 const control=button('Показать следующую точку',()=>showQuestTarget(next.questId));control.dataset.roomNextTarget=next.questId;
 control.className='scene-paper-action';
 section.append(title,text,control);switchHint(section,next);host.append(section);return true;
}
function roomActions(host){if(interaction){renderInteraction(host);return;}for(const a of E.actions(state)){const b=button(a.label,()=>beginAction(a.id));b.dataset.action=a.id;if(window.PalataQuestScenes)PalataQuestScenes.decorate(b,a.id);host.append(b);}if(state.room==='ward404')host.append(button(state.mode==='trip'?'Выйти из Трипа':'Войти в Трип',switchMode));if(state.mode==='patient'&&state.room==='procedure'){const shop=button('Медицинский шкаф · купить препараты',openProcedureRoom);shop.className='scene-paper-action';shop.dataset.medicalShop='true';host.append(shop);}if(state.room==='collector'){const p=document.createElement('p');p.textContent='Сборщик: 15 серебра и 1 таблетка в ваш профиль. Следующая выдача через '+Math.max(0,Math.ceil((state.collectorAt+60000-Date.now())/1000))+' с. Частота выдачи пока тестовая; запас за время отсутствия не накапливается.';host.append(p);}const continued=renderRoomContinuation(host);if(!host.children.length&&!continued)host.textContent='Сейчас тут нет новых действий. Открытые записи и поручения доступны в журнале.';}
// Choose the less obstructive side using actual rendered hit regions. The
// remembered side belongs to this room/interaction only and never enters saves.
function positionRoomPaper(scene,info){
 const action=interaction,key=state.room+':'+state.mode+':'+action;
 if(!action){info.dataset.paperPosition='room';return;}
 info.dataset.paperPosition='pending';
 requestAnimationFrame(()=>{
  if(action!==interaction||!scene.isConnected||!info.isConnected||info.inert||info.classList.contains('is-collapsed')){info.dataset.paperPosition='inactive';return;}
  const targets=[...scene.querySelectorAll('.painted-target.choice-object,.scene-key-object.choice-object')]
   .filter(target=>!target.hidden&&target.getClientRects().length).map(target=>target.getBoundingClientRect());
  if(!targets.length){info.dataset.paperPosition='no-targets';return;}
  const score=box=>targets.reduce((sum,target)=>{
   const width=Math.max(0,Math.min(box.right,target.right)-Math.max(box.left,target.left));
   const height=Math.max(0,Math.min(box.bottom,target.bottom)-Math.max(box.top,target.top));
   const x=(target.left+target.right)/2,y=(target.top+target.bottom)/2;
   return sum+width*height/Math.max(1,target.width*target.height)+(x>=box.left&&x<=box.right&&y>=box.top&&y<=box.bottom?2:0);
  },0);
  const current=paperPlacement.key===key?paperPlacement.side:'right',paper=info.getBoundingClientRect(),area=scene.getBoundingClientRect();
  // Both candidates share size/top. Construct their horizontal bounds directly;
  // changing an attribute and immediately measuring it can reuse stale style.
  const touch=document.documentElement.dataset.touchUi==='true';
  const scale=paper.width/(parseFloat(getComputedStyle(info).width)||paper.width);
  const margin=touch?8*scale:16;
  const left=area.left+margin,right=area.right-margin;
  const scores={left:score({left,right:left+paper.width,top:paper.top,bottom:paper.bottom}),
   right:score({left:right-paper.width,right,top:paper.top,bottom:paper.bottom})};
  const other=current==='right'?'left':'right';
  const side=scores[other]+.01<scores[current]?other:current;
  info.dataset.paperSide=side;info.dataset.paperPosition='ready';info.dataset.paperScores=JSON.stringify(scores);paperPlacement={key,side};
  const closeup=scene.querySelector('.scene-key-detail');
  if(closeup){
   const edge=side==='left'?left+paper.width:right-paper.width;
   const freeLeft=side==='left'?edge+margin:area.left+margin;
   const freeRight=side==='left'?area.right-margin:edge-margin;
   const width=Math.max(1,Math.min(area.width*.52,freeRight-freeLeft));
   closeup.style.boxSizing='border-box';closeup.style.width=width+'px';
   closeup.style.left=(freeLeft-area.left+(freeRight-freeLeft-width)/2)+'px';
   closeup.dataset.paperDocked=side==='left'?'right':'left';
  }

 });
}

function renderLocation(){if(interaction&&!E.actions(state).some(a=>a.id===interaction))interaction=null;locationScreen.classList.remove('hidden');locationScreen.append(map);byId('map-modal').classList.add('hidden');map.replaceChildren();map.classList.add('quest-location');const info=document.createElement('section');info.className='scene-paper document-paper';info.dataset.paperInteraction=String(!!interaction);info.dataset.paperSide=paperPlacement.key===state.room+':'+state.mode+':'+interaction?paperPlacement.side:'right';info.addEventListener('scroll',()=>info.style.setProperty('--scene-paper-scroll',info.scrollTop+'px'),{passive:true});const header=document.createElement('document-header');header.setAttribute('variant','left');header.setAttribute('department','КАРТОЧКА ЛОКАЦИИ');header.setAttribute('scale','compact');const title=document.createElement('h3');title.textContent=E.rooms[state.room][1];const mode=document.createElement('p');mode.textContent=(state.mode==='trip'?'Трип':'Пациент')+' · секция '+E.rooms[state.room][0];const message=document.createElement('p');message.className='quest-note';message.setAttribute('role','status');message.textContent=matchMedia('(pointer:coarse)').matches?'Коснитесь предмета. Действия — ниже, лист прокручивается ↓':'Выберите предмет. Enter или пробел активируют выбранную цель. Прогресс сохраняется после каждого шага.';const seal=document.createElement('document-stamp');seal.setAttribute('type','seal');seal.setAttribute('rotate','-8');info.append(header,title,mode,message,seal,button('Вернуться к карте',()=>{interaction=null;locationView=false;renderMap();}),button('Открыть задания',openTasks));const bag=document.createElement('section');bag.className='quest-cargo-panel';bag.setAttribute('aria-label','Предметы поручений');const bagTitle=document.createElement('h4');bagTitle.textContent='При себе · инвентарь';bag.append(bagTitle);for(const item of inventory.filter(x=>x.questCargo)){const row=document.createElement('p');row.dataset.cargo=item.questCargo;row.textContent=item.name+' ×'+item.count;bag.append(row);}if(!inventory.some(x=>x.questCargo)){const empty=document.createElement('p');empty.textContent='Предметов поручений пока нет.';bag.append(empty);}const receipt=document.createElement('p');receipt.className='quest-receipt';receipt.setAttribute('role','status');receipt.textContent=state.lastReceipt||'Собирайте предметы в комнатах и используйте их по поручению.';bag.append(receipt,button('Открыть инвентарь',openInventory));const balance=document.createElement('p');balance.textContent='Уровень '+stats.level+' · EXP '+stats.exp+'/'+stats.nextLvlExp+' · Серебро '+stats.silver;bag.append(balance);info.append(bag);window.PalataFloorArt.renderPortrait(info,state.room,state.mode);const scene=document.createElement('section');if(window.PalataQuestScenes)PalataQuestScenes.render(scene,state.room,state.mode,text=>{message.textContent=text;});const acts=document.createElement('div');acts.className='quest-actions scene-actions';roomActions(acts);scene.append(acts);if(window.PalataQuestScenes?.renderCargo)PalataQuestScenes.renderCargo(scene,state,interaction);if(window.PalataQuestScenes?.finish)PalataQuestScenes.finish(scene,info,interaction,state.interactions[interaction]||0);prioritizeRoomTask(info);renderGiverBriefs(info,scene);window.PalataQuestWorldView?.render(scene,info,state);if(state.room==='gym'&&window.PalataRehabUI)PalataRehabUI.render(info,{mode:state.mode,reveal:()=>{roomInfoCollapsed=false;renderMap();},allowed:()=>!protectedSave&&!rewardRecoveryError&&state.room==='gym'&&locationView&&!locationScreen.classList.contains('hidden')&&!interaction&&!isBattleActive&&!travelling&&!wardrobeSession,refresh:()=>renderMap()});const tools=document.createElement('nav');tools.className='quest-room-tools';tools.setAttribute('aria-label','Управление комнатой');
const back=button('К карте',()=>{interaction=null;locationView=false;renderMap();});
// Required answers must not remain hidden after an interaction advances.
if(interaction && info.querySelector('[data-choice],.scene-document-actions'))roomInfoCollapsed=false;
info.classList.toggle('is-collapsed',roomInfoCollapsed);
const toggle=button(roomInfoCollapsed?'Описание и задания':'Свернуть описание',()=>{const collapsed=info.classList.toggle('is-collapsed');roomInfoCollapsed=collapsed;toggle.textContent=collapsed?'Описание и задания':'Свернуть описание';toggle.setAttribute('aria-expanded',String(!collapsed));if(!collapsed)positionRoomPaper(scene,info);});toggle.setAttribute('aria-expanded',String(!roomInfoCollapsed));toggle.dataset.roomInfoToggle='true';
tools.append(back,toggle);map.append(scene,info,tools);mountWorkbench(scene,info);positionRoomPaper(scene,info);}


function workbenchKeyboardContinuation(current,kind,{op,value},previousFocus){
 if(!current||!previousFocus)return null;
 if(kind==='diagnostic'&&op==='inspect')return current.querySelector('[data-work-focus="test"]:not(:disabled)');
 if((kind==='diagnostic'||kind==='callRetest')&&op==='test')return current.querySelector('[data-work-focus="call-observation"]');
 if(kind==='callService'&&op==='inspectEvidence')return current.querySelector('[data-work-focus="service-evidence"]');
 if(kind!=='timeline'||current.dataset.timelineMap!=='true')return null;
 if(op==='place'){
  const peerSelector=previousFocus.startsWith('route:')?'.workbench-route-point':'.workbench-place-slip';
  const peers=[...current.querySelectorAll(peerSelector)];
  const position=peers.findIndex(control=>control.dataset.workFocus===previousFocus);
  return peers.slice(position+1).find(control=>!control.disabled)||peers.find(control=>!control.disabled)||
   current.querySelector('.workbench-read-reverse:not(:disabled), [data-work-focus="route-order"]');
 }
 if(op==='move')return [...current.querySelectorAll('[data-ordered-slip]')].find(row=>row.dataset.orderedSlip===value?.id);
 if(op==='remove')return [...current.querySelectorAll('.workbench-place-slip:not(:disabled)')].find(control=>control.dataset.workValue===value);
 return null;
}

function mountWorkbench(scene,info){
 const id=interaction,board=id&&E.workbench?.(state,id);
 if(!board||!window.PalataQuestWorkbench)return;
 if(board.kind==='bedmaking'||board.subjectId==='bed406')board.referenceImage=window.PalataFloorArt.resolve('ward406',state.mode).background;
 const host=document.createElement('div');host.className='quest-workbench-host';map.append(host);scene.inert=true;info.inert=true;const tools=map.querySelector('.quest-room-tools');if(tools)tools.inert=true;
 PalataQuestWorkbench.render(host,{board,feedback:workNotice,act:payload=>{
  const active=document.activeElement,focus=active?.dataset.workFocus;
  const keyboard=active?.matches(':focus-visible');
  const ok=dispatch({type:'work',id,op:payload.op,value:payload.value});
  if(ok&&!E.workbench(state,id)){interaction=null;roomInfoCollapsed=false;renderMap();const effectId=id==='job:callReview'?'doctorReview':/^job:callRetest40[78]$/.test(id)?'call:ward'+id.slice(-3):id==='job:deliver'?'linen406':null;const outcome=(effectId&&locationScreen.querySelector('[data-world-effect="'+effectId+'"]'))||locationScreen.querySelector('.quest-receipt');if(outcome&&outcome.getClientRects().length){outcome.tabIndex=-1;outcome.focus({preventScroll:true});outcome.scrollIntoView({block:'nearest'});}else locationScreen.querySelector('[data-room-info-toggle]')?.focus({preventScroll:true});}
  else{
   if(!ok)renderMap();
   const current=locationScreen.querySelector('.quest-workbench');
   const restored=[...(current?.querySelectorAll('[data-work-focus]')||[])].find(e=>e.dataset.workFocus===focus&&!e.disabled);
   const continuation=ok&&keyboard&&!restored&&workbenchKeyboardContinuation(current,board.kind,payload,focus);
   if(continuation){
    // The replacement sheet restores its previous scroll first.
    queueMicrotask(()=>{if(continuation.isConnected)continuation.focus();});
   }else (restored||current?.querySelector('[data-work-heading]'))?.focus({preventScroll:true});
  }
  return ok;
 },close:()=>{workNotice='';interaction=null;renderMap();const candidates=['[data-scene-action="'+id+'"]','[data-action="'+id+'"]','[data-room-info-toggle]'].flatMap(selector=>[...locationScreen.querySelectorAll(selector)]);candidates.find(e=>e.getClientRects().length&&!e.closest('[inert]'))?.focus({preventScroll:true});}});
}

async function travel(id){if(travelling||isBattleActive)return;const points=E.routePoints(state,id);if(!points.length)return;travelling=true;const figure=map.querySelector('.quest-blueprint'),marker=document.createElement('span');marker.className='quest-traveller';marker.textContent='●';marker.setAttribute('aria-label','Движение персонажа');figure.append(marker);map.setAttribute('aria-busy','true');const keyframes=points.map(p=>({left:((p[0]-70)/1610*100)+'%',top:((p[1]-280)/850*100)+'%'}));try{if(marker.animate&&!matchMedia('(prefers-reduced-motion: reduce)').matches){await marker.animate(keyframes,{duration:Math.max(700,Math.min(2400,points.length*230)),fill:'forwards',easing:'linear'}).finished;}}catch(_){}finally{travelling=false;map.setAttribute('aria-busy','false');}interaction=null;roomInfoCollapsed=id==='gym';locationView=true;dispatch({type:'move',room:id});}

function renderWorkLocation(){
 const previous=locationScreen.querySelector('.quest-workbench'),id=previous?.dataset.workAction;
 const scroller=previous?.querySelector('.workbench-scroll'),active=previous?.contains(document.activeElement)?document.activeElement:null;
 const view=id&&id===interaction?{top:scroller?.scrollTop||0,briefOpen:previous.querySelector('.workbench-brief')?.open,focus:active?.dataset.workFocus,heading:active?.hasAttribute('data-work-heading'),summary:active?.matches('summary'),scrollFocused:active===scroller}:null;
 renderLocation();
 const current=locationScreen.querySelector('.quest-workbench');if(!view||current?.dataset.workAction!==id)return;
 const brief=current.querySelector('.workbench-brief');if(brief&&view.briefOpen!==undefined)brief.open=view.briefOpen;
 const target=view.focus?[...current.querySelectorAll('[data-work-focus]')].find(e=>e.dataset.workFocus===view.focus&&!e.disabled):view.heading?current.querySelector('[data-work-heading]'):view.summary?current.querySelector('.workbench-brief-summary'):view.scrollFocused?current.querySelector('.workbench-scroll'):null;
 target?.focus({preventScroll:true});const nextScroll=current.querySelector('.workbench-scroll');if(nextScroll)nextScroll.scrollTop=view.top;
}

function renderMap(){if(travelling)return;if(locationView){renderWorkLocation();return;}const previousPlan=map.querySelector('.quest-blueprint-viewport'),planFocused=document.activeElement===previousPlan,mapTop=map.scrollTop;if(previousPlan?.getClientRects().length){planScrollLeft=previousPlan.scrollLeft;planScrollTop=previousPlan.scrollTop;}const planLeft=planScrollLeft,planTop=planScrollTop;if(!locationScreen.classList.contains('hidden')){mapHome.append(map);locationScreen.classList.add('hidden');byId('map-modal').classList.remove('hidden');window.PalataCompactUI?.setMapView('plan');}map.classList.remove('quest-location');byId('map-title-text').textContent='10-Й ЭТАЖ';byId('map-floors-view').classList.remove('hidden');byId('map-single-floor-view').classList.add('hidden');map.replaceChildren();const status=document.createElement('h3');status.textContent=`${state.mode==='trip'?'Трип':'Пациент'} · ${E.rooms[state.room][1]}`;map.append(status);const note=document.createElement('p');note.textContent=(state.allSectionsUnlocked?'Все секции открыты отдельной кнопкой. ':'')+(state.mode==='patient'?'Пациент: штриховки нет, все секции доступны. ':'Трип: B '+(E.accessible(state,'B')?'открыта':'закрыта: требуется осмотреть переход A/B')+'; C '+(E.accessible(state,'C')?'открыта':'закрыта: требуется проверить замок B/C')+'. ')+'Пациент: A–B–C, без спуска. Трип: '+['A','B','C'].filter(x=>E.accessible({...state,mode:'trip'},x)).join('–')+'. Режим меняется красным переключателем. Серебро: '+stats.silver+' · Таблетки: '+stats.pills+(state.materials?' · Архив старых тестовых материалов: '+state.materials:'')+'.';map.append(note);const figure=document.createElement('figure');figure.className='quest-blueprint';figure.setAttribute('aria-label','План десятого этажа редакции 04 с интерактивными точками');
const img=document.createElement('img');img.src='quest-plan.svg';img.alt='Общий план Пациента и Трипа: секции A, B, C; палаты 404–408, медпункт, процедурная, кабинет врача и лестница.';img.className='quest-blueprint-image';figure.append(img);
for(const [id,spec] of Object.entries(E.mapLabels)){const [l,t,r,b]=spec.box;const label=document.createElement('span');label.className='quest-plan-label';label.dataset.labelRoom=id;label.lang='ru';label.textContent=spec.text;label.title=spec.full;label.setAttribute('aria-label',spec.full);label.style.left=((l-70)/1610*100)+'%';label.style.top=((t-280)/850*100)+'%';label.style.width=((r-l)/1610*100)+'%';label.style.height=((b-t)/850*100)+'%';figure.append(label);}const origin=document.createElement('span');origin.className='quest-plan-origin-mask';origin.setAttribute('aria-hidden','true');figure.append(origin);
for(const sec of ['B','C'])if(!E.accessible(state,sec)){const shade=document.createElement('div');shade.className='quest-locked-zone';shade.dataset.section=sec;shade.style.clipPath='polygon('+E.sectionPolygons[sec].map(p=>((p[0]-70)/1610*100)+'% '+((p[1]-280)/850*100)+'%').join(',')+')';shade.setAttribute('aria-label','Секция '+sec+' закрыта');figure.append(shade);}
const reachable=E.destinations(state),guidance=focusQuest?guideFor(focusQuest):null,target=guidance?.room||focusRoom;

for(const [id,point] of Object.entries(E.pins)){
 const current=id===state.room,locked=!E.accessible(state,E.rooms[id][0]),available=reachable.includes(id);
 const label=locked?'×':id==='A'||id==='B'||id==='C'?id:id.startsWith('ward')?id.slice(4):id==='stairs'?'↓':'•';
 const pin=button('',event=>selectRoomDoor(id,event),false);pin.innerHTML=doorIcon;pin.dataset.room=id;pin.addEventListener('dblclick',event=>{event.preventDefault();openRoom(id);});pin.setAttribute('aria-expanded',String(selectedRoom===id));
 pin.className='quest-map-pin'+(current?' is-current':locked?' is-locked':available?' is-reachable':' is-distant');
 if(id===target)pin.classList.add('is-target');pin.style.left=((point[0]-70)/1610*100)+'%';pin.style.top=((point[1]-280)/850*100)+'%';
 pin.title=E.rooms[id][1]+(current?' · вы тут':locked?' · секция закрыта в Трипе':available?' · перейти':' · сначала перейдите в коридор');
 const outcomes=window.PalataQuestStateView?.forRoom(E,state,id)||[];if(outcomes.length){const outcome=outcomes[0],mark=document.createElement('span');mark.className='quest-map-outcome';mark.dataset.roomOutcome=outcome.id;mark.dataset.outcomeStatus=outcome.status;mark.setAttribute('aria-hidden','true');mark.textContent=outcome.mark;pin.append(mark);pin.title+=' · '+outcomes.map(item=>item.label).join('; ');}
 pin.setAttribute('aria-label',pin.title);if(current)pin.setAttribute('aria-current','location');figure.append(pin);
}
for(const [sec,x] of [['A',16],['B',49],['C',81]]){const label=document.createElement('span');label.className='plan-section-caption';label.textContent='СЕКЦИЯ '+sec;label.style.left=x+'%';figure.append(label);}const planViewport=document.createElement('div');planViewport.className='quest-blueprint-viewport';planViewport.setAttribute('role','region');planViewport.setAttribute('aria-label','План этажа · прокрутка по горизонтали и вертикали');planViewport.tabIndex=0;planViewport.addEventListener('pointerdown',cancelRoomClick,{passive:true});planViewport.addEventListener('touchstart',cancelRoomClick,{passive:true});planViewport.addEventListener('scroll',()=>{if(planViewport.getClientRects().length){planScrollLeft=planViewport.scrollLeft;planScrollTop=planViewport.scrollTop;}},{passive:true});planViewport.append(figure);map.append(planViewport);planViewport.scrollLeft=planLeft;planViewport.scrollTop=planTop;if(planFocused)planViewport.focus({preventScroll:true});const legend=document.createElement('p');legend.className='quest-map-legend';legend.textContent='УСЛОВНЫЕ ОБОЗНАЧЕНИЯ\nДверь с синей меткой — вы здесь\nЗелёная дверь — проход доступен\nОдно нажатие — описание, два — вход\n× Штриховка — закрыто в Трипе\n◎ Золотой контур — цель задания\nМетка у двери — подтверждённое состояние; подробности в описании.';const sidebar=document.createElement('aside');sidebar.className='quest-map-sidebar';sidebar.setAttribute('aria-label','Действия и подсказка карты');sidebar.tabIndex=0;const names=document.createElement('p');names.className='quest-room-key';names.textContent='КОМНАТЫ\n'+Object.values(E.mapLabels).map(x=>x.text+' — '+x.full).join('\n');sidebar.append(legend);map.append(sidebar);
const heading=document.createElement('h4');heading.textContent='Действия в этой комнате';sidebar.append(heading);const acts=document.createElement('div');acts.className='quest-actions';for(const a of E.actions(state)){const b=button(a.label,()=>beginAction(a.id));b.dataset.action=a.id;acts.append(b);}acts.append(button('Войти в текущую комнату',()=>{locationView=true;renderMap();}));if(state.room==='collector'){const p=document.createElement('p');const seconds=Math.max(0,Math.ceil((state.collectorAt+60000-Date.now())/1000));p.textContent='Сборщик: 15 серебра и 1 таблетка за выдачу. '+(seconds?'До следующего сбора: '+seconds+' с. Обновите карту.':'Нажмите «Получить припасы сборщика».')+' Частота — тестовая: раз в минуту, без накопления.';acts.append(p);}if(!acts.children.length)acts.textContent=state.room==='ward404'?'Закройте карту и нажмите красный переключатель в палате 404.':'Нет новых действий. Журнал подскажет следующий шаг.';sidebar.append(acts,button('Открыть задания',openTasks));const history=document.createElement('p');history.className='quest-note';history.setAttribute('role','status');history.textContent=notice+(guidance?guidance.text+' '+E.directions(state,guidance.room):focusRoom?E.directions(state,focusRoom):(navigation?navigation.mapHint(E,state):E.mapHint(state)));sidebar.append(history,names);if(guidance)switchHint(sidebar,guidance);if(selectedRoom)showRoomPreview(selectedRoom);map.scrollTop=mapTop;window.PalataCompactUI?.mapRendered();window.PalataMapNavigation?.render(map);}
function scheduleCollector(){clearTimeout(collectorWake);const remaining=state.collectorAt+60000-Date.now();if(remaining>0)collectorWake=setTimeout(()=>{if(state.room==='collector'&&!interaction&&!travelling&&!isBattleActive)renderMap();},remaining);}
function refresh(){sync();originalUpdate();save();byId('current-location-name').textContent=E.rooms[state.room][1];byId('current-location-desc').textContent=(state.mode==='trip'?'Трип':'Пациент')+' · секция '+E.rooms[state.room][0];const b=document.querySelector('.room-trip-switch');b.disabled=false;b.setAttribute('aria-pressed',String(state.mode==='trip'));b.setAttribute('aria-label',state.mode==='trip'?'Выйти из Трипа':'Войти в Трип');b.querySelector('.room-action-label').textContent=state.mode==='trip'?'Выйти из Трипа':'Войти в Трип';b.title='Переключить режим';b.dataset.mode=state.mode;document.querySelector('.hospital-hud').dataset.roomMode=state.mode;renderTasks();renderMap();scheduleCollector();}
function dispatch(event){
 const workHasSurface=()=>event.type==='work'&&!!locationScreen.querySelector('.quest-workbench');
 const deny=message=>{if(event.type==='work')workNotice=message;if(!workHasSurface())showCustomToast(message);return false;};
 if(typeof profileWritesAllowed==='function'&&!profileWritesAllowed())return deny('Загрузите актуальную игровую сессию; сохранение не изменено.');
 if(travelling)return deny('Дождитесь прибытия.');
 if(!modelReady&&event.type==='action'&&event.id?.startsWith('boss:'))return deny('Не удалось загрузить актуальные файлы боя. Обновите страницу.');
 if(isBattleActive&&event.type!=='battleEnd')return deny('Завершите рейд.');
 const economic=(event.type==='action'||event.type==='interact'||event.type==='work')&&(event.id==='collect'||/^(accept:|claim:|job:)/.test(event.id));
 if(economic&&(protectedSave||rewardRecoveryError||pendingQuestReward&&!saveGameProgress()))return deny('Действие приостановлено: сначала восстановите сохранение предметов и награды.');
 // Consumers require the actual inventory item as well as quest progress.
 const needed=event.id==='job:deliver'?['linen']:event.id==='job:difference'?['baseline']:event.id?.startsWith('claim:')?E.requiredCargo[event.id.slice(6)]:[];
 if(economic&&needed?.some(id=>!inventory.some(x=>x.questCargo===id&&x.count>0)))return deny('Нужного предмета нет в инвентаре. Получите его в указанной комнате.');
 const before=economic?{state:JSON.parse(JSON.stringify(state)),stats:JSON.parse(JSON.stringify(stats)),inventory:JSON.parse(JSON.stringify(inventory))}:null;
 let reachedLevels=[];
 const result=E.apply(state,event);
 if(event.type==='work')workNotice=result.message||'';
 if(result.ok){
  if(economic){
   syncCargo();
   if(result.reward?.kind==='collector')for(const [currency,amount] of Object.entries(collectorPayout))stats[currency]+=amount;
   if(result.reward?.kind==='job'){
    stats.silver+=result.reward.silver;reachedLevels=addExperience(result.reward.exp,false);
    if(result.reward.medical){const item=MEDICAL_ITEMS[result.reward.medical],existing=inventory.find(x=>x.name===item.name&&x.category==='meds');if(existing)existing.count++;else inventory.push({...item,count:1});}
   }
   state.transaction++;if(event.type!=='work'||result.completed)state.lastReceipt=result.message;
   const receipt=result.reward?.kind==='collector'?result.reward:{kind:'quest',id:'transaction:'+state.transaction};
   // Write the complete result before any profile/progress write. Recovery applies
   // the snapshot, never repeats addExperience or adds the items a second time.
   if(!safeStorageSet(rewardKey,JSON.stringify({version:2,owner:raidArchiveOwnerId,receipt,stats,inventory,progress:state}))){
    state=before.state;Object.assign(stats,before.stats);inventory=before.inventory;return deny('Не удалось сохранить: предметы и награда не изменены. Повторите действие.');
   }
   pendingQuestReward=receipt;
  }
  save();refresh();
  reachedLevels.forEach(showLevelNotice);
  if(event.type==='action'&&event.id.startsWith('boss:')){originalFight(state.battle);save();if(!isBattleActive){state.battle=null;save();refresh();}}
 }
 if(event.type!=='work'||!locationView){const accepted=result.ok&&event.type==='action'&&event.id?.startsWith('accept:');showCustomToast(accepted?'Поручение принято: '+E.jobs[event.id.slice(7)].title+'. Подробности — в журнале и рабочем листе.':result.message);}return result.ok;
}

updateUI=refresh;
openTasks=function(){if(travelling)return false;if(closeOtherModals(['tasks-modal'])===false)return false;if(dossierId)closeDossier(false);taskMode=state.mode;renderTasks();byId('tasks-modal').classList.remove('hidden');return true;};
toggleMapModal=function(show){cancelRoomGesture();if(travelling){showCustomToast('Дождитесь прибытия.');return;}if(show){interaction=null;locationView=false;if(isBattleActive){reopenNurseBattle();return;}if(closeOtherModals(['map-modal'])===false)return;renderMap();window.PalataCompactUI?.setMapView('plan');}byId('map-modal').classList.toggle('hidden',!show);};
showFloorsList=renderMap;openFloorMap=()=>toggleMapModal(true);handleLocationClick=()=>toggleMapModal(true);openMedicalHub=()=>toggleMapModal(true);handleNodeClick=()=>toggleMapModal(true);
// Legacy medical navigation cannot teleport the prototype's authoritative position.
selectRoom=()=>toggleMapModal(true);
openProcedureRoom=function(){
 if(state.mode!=='patient'||state.room!=='procedure'||isBattleActive||travelling)return toggleMapModal(true);
 if(closeOtherModals(['procedure-room-modal'])===false)return false;
 // Reuse the existing medicine shop in the actual room, without legacy teleport.
 locationView=true;renderMap();
 const modal=byId('procedure-room-modal');
 // This adapter owns mode changes, so its legacy madness medicine is unusable.
 // Keep saved pills intact and explain the disabled purchase instead of selling it.
 const modePills=modal.querySelector('[onclick^="buyMedicalItem(\'madness_pills\'"]');
 if(modePills){const description=modePills.previousElementSibling?.lastElementChild;modePills.disabled=true;if(description){description.id='procedure-mode-note';description.setAttribute('role','status');description.textContent='У цій версії режим змінюється червоним перемикачем.';modePills.setAttribute('aria-describedby',description.id);}}
 modal.style.setProperty('z-index','850','important');modal.classList.remove('hidden');return true;
};
startBossFight=function(boss){if(isBattleActive){reopenNurseBattle();return;}dispatch({type:'action',id:'boss:'+boss});};
openBossDossier=function(boss){if(!E.actions(state).some(a=>a.id==='boss:'+boss)){showCustomToast('Рейд доступен в комнате босса в Трипе после открытия секции.');return;}startBossFight(boss);};
handleVictory=function(){const active=isBattleActive,battle=currentBattleSession?.id;originalVictory();if(active&&lastBattleResult?.battleId===battle&&state.battle)dispatch({type:'battleEnd',victory:true});};
recordUnrewardedRaid=function(){const result=originalUnrewarded.apply(this,arguments);if(state.battle){E.apply(state,{type:'battleEnd',victory:false});save();sync();}return result;};
const consume=consumeMedicalItem;consumeMedicalItem=function(item){if(item?.effectType==='madness'){showCustomToast('Используйте красный переключатель режима.');return false;}return consume(item);};devSetMadness=()=>showCustomToast('Используйте красный переключатель режима.');
// Replace only this page's listener so the shared room-scene code stays untouched.
const unlockAllButton=document.createElement('button');unlockAllButton.type='button';unlockAllButton.id='quest-unlock-all';unlockAllButton.className='quest-unlock-all';unlockAllButton.textContent='Открыть все секции';
document.querySelector('.hospital-hud').append(unlockAllButton);
function updateUnlockAll(){unlockAllButton.textContent=state.allSectionsUnlocked?'Вернуть доступ по прогрессу':'Открыть все секции';unlockAllButton.setAttribute('aria-pressed',String(state.allSectionsUnlocked===true));}
unlockAllButton.addEventListener('click',()=>{if(isBattleActive||travelling||wardrobeSession){showCustomToast('Завершите бой, переход или примерку.');return;}if(dispatch({type:'unlockAll'}))updateUnlockAll();});
updateUnlockAll();
const oldButton=document.querySelector('.room-trip-switch'),newButton=oldButton.cloneNode(true);oldButton.replaceWith(newButton);newButton.addEventListener('click',()=>switchMode(true));
function switchMode(fromRoom=false){
 if(isBattleActive){showCustomToast('Сначала завершите рейд.');return;}
 if(travelling){showCustomToast('Дождитесь прибытия.');return;}
 if(wardrobeSession){showCustomToast('Сначала примените или отмените примерку.');return;}
 if(fromRoom===true){
  if(closeOtherModals([])===false)return;
  // The wall switch changes mode directly; refreshing a saved location must
  // not reopen its location screen or the map as a side effect.
  locationView=false;locationScreen.classList.add('hidden');mapHome.append(map);
 }
 interaction=null;
 if(dispatch({type:'switch'})){taskMode=state.mode;setPaperDollView(state.mode==='trip'?'combat':'patient');refresh();}
}

const priorRoom=window.PalataRoom;window.PalataRoom=Object.freeze({...priorRoom,toggleTrip:()=>newButton.click()});
tasks.addEventListener('click',e=>{if(e.target.dataset.taskMode){taskMode=e.target.dataset.taskMode;renderTasks();}if(e.target.dataset.questTab){tab=e.target.dataset.questTab;renderTasks();}});
document.querySelectorAll('[data-nav-modal="tasks-modal"]').forEach(b=>{b.setAttribute('aria-label','Задания');b.querySelector('span').textContent='Задания';});const taskLabel=document.querySelector('.hud-task span');if(taskLabel)taskLabel.textContent='Задания';

// Restore durable progress, not a transient room or arena overlay. The saved
// location still belongs to the quest; a live raid continues minimized.
resumeRaid(raw?.raid);if(isBattleActive)minimizeNurseBattle();save();refresh();window.PalataQuestPrototype=Object.freeze({snapshot:()=>JSON.parse(JSON.stringify(state))});
})();
