/* ISOLATED DESIGN PROTOTYPE. Not registered or imported by the live game. */
(function(root,factory){
 'use strict';const api=factory();
 if(typeof module==='object'&&module.exports)module.exports=api;
 else root.PalataFloor9EncounterPlan=api;
})(globalThis,function(){
 'use strict';
 const brand='palata404-floor9-encounter-demo';
 const clone=x=>JSON.parse(JSON.stringify(x));
 function freeze(x){if(x&&typeof x==='object'){Object.values(x).forEach(freeze);Object.freeze(x);}return x;}
 const blueprint=freeze({
  status:'CONCEPT_ONLY_NOT_ACTIVE_GAME',demoUnitsNotApprovedBalance:true,
  bosses:{
   threshold:{id:'threshold',artReference:'F9-B01',name:'Порог',nameStatus:'Рабочее имя',lesson:'Подготовка нажима и восстановление',soloHp:120,duoHp:110,damage:12},
   metronome:{id:'metronome',artReference:'F9-B02',name:'Метроном',nameStatus:'Рабочее имя',lesson:'Сигнал можно прервать атакой',soloHp:100,duoHp:90,damage:10}
  },
  encounters:{
   solo_a:{id:'solo_a',section:'A',room:'903',bosses:['threshold'],title:'Первый отдельный бой'},
   solo_b:{id:'solo_b',section:'B',room:'906',bosses:['metronome'],title:'Второй отдельный бой'},
   duo_c:{id:'duo_c',section:'C',room:'912',bosses:['threshold','metronome'],title:'Эти же двое вместе'}
  },
  proofs:{
   a_plan:{section:'A',room:'902',mode:'patient',requires:[],label:'Прочитан план отделения'},
   a_exam:{section:'A',room:'903',mode:'patient',requires:['a_plan'],label:'Зафиксирован функциональный осмотр'},
   a_return:{section:'A',room:'905',mode:'patient',requires:['a_plan'],label:'Найден ориентир возвращения'},
   a_clear_door:{section:'A',room:'A/B',mode:'trip',requires:['a_plan','a_exam','a_return'],label:'Стул убран из дуги двери A/B'},
   a_test_door:{section:'A',room:'A/B',mode:'trip',requires:['a_clear_door'],label:'Проверен свободный ход A/B'},
   b_record:{section:'B',room:'907',mode:'patient',requires:[],label:'Прочитана запись обслуживания'},
   b_node:{section:'B',room:'B/C',mode:'trip',requires:['b_record'],label:'Осмотрены маркировка и неисправность узла'},
   b_match:{section:'B',room:'913 · внешнее окно',mode:'trip',requires:['b_node'],label:'Заявка сверена с фактическим узлом'},
   b_service:{section:'B',room:'913 · внешнее окно',mode:'trip',requires:['b_match'],label:'Обслуживание подтверждено'},
   b_test_door:{section:'B',room:'B/C',mode:'trip',requires:['b_service'],label:'Проверен свободный ход B/C'}
  },
  gates:{AB:{proofs:['a_plan','a_exam','a_return','a_clear_door','a_test_door'],encounter:'solo_a'},BC:{proofs:['b_record','b_node','b_match','b_service','b_test_door'],encounter:'solo_b'}},
  proposedMechanics:['Выбор отдельной цели','Одна общая последовательность подготовки атак','Прерываемый сигнал поддержки'],
  preserved:['Всего два персонажа и три боя','Открытые проходы и выполненная работа сохраняются','Пациент: все публичные секции, без боёв','Никаких реальных валют или изменений сохранения игры']
 });
 const sections=['A','B','C'],encounterIds=Object.keys(blueprint.encounters),proofIds=Object.keys(blueprint.proofs);
 const success=message=>({ok:true,message}),fail=message=>({ok:false,message});
 const finiteInt=n=>Number.isSafeInteger(n)&&n>=0;
 const exactKeys=(x,keys)=>x&&typeof x==='object'&&!Array.isArray(x)&&Object.keys(x).length===keys.length&&keys.every(k=>Object.hasOwn(x,k));
 function initial(){return{brand,version:1,mode:'patient',section:'A',now:0,proofs:Object.fromEntries(proofIds.map(id=>[id,false])),clears:Object.fromEntries(encounterIds.map(id=>[id,false])),rewards:[],attempt:0,battle:null,lastResult:null};}
 function gates(s){
  const result={};
  for(const [id,g]of Object.entries(blueprint.gates)){
   const missing=g.proofs.filter(p=>!s.proofs[p]);const bossDone=s.clears[g.encounter]===true;
   result[id]={taskDone:missing.length===0,bossDone,open:missing.length===0&&bossDone,missing:[...missing,...(bossDone?[]:[g.encounter])]};
  }
  return freeze(result);
 }
 function accessible(s,section){const g=gates(s);return sections.includes(section)&&(s.mode==='patient'||section==='A'||section==='B'&&g.AB.open||section==='C'&&g.AB.open&&g.BC.open);}
 function availability(s,id){
  const e=blueprint.encounters[id];if(!e)return freeze({available:false,missing:['Неизвестный бой']});
  const missing=[];
  if(s.mode!=='trip')missing.push('Бой доступен только в Трипе');
  if(s.section!==e.section)missing.push('Нужна секция '+e.section);
  if(!accessible(s,e.section))missing.push('Проход в секцию закрыт');
  if(id==='solo_a'&&!s.proofs.a_exam)missing.push('Нужна запись осмотра 903');
  if(id==='solo_b'&&!s.proofs.b_record)missing.push('Нужна запись 907');
  if(id==='duo_c'&&(!s.clears.solo_a||!s.clears.solo_b))missing.push('Нужны обе отдельные победы');
  if(s.battle)missing.push('Сначала завершите текущий бой');
  return freeze({available:missing.length===0,missing});
 }
 function finish(s,outcome){
  const b=s.battle;if(!b)return;
  let receipt=null;
  if(outcome==='victory'&&!s.clears[b.encounter]){
   s.clears[b.encounter]=true;receipt='floor9:first-clear:'+b.encounter;
   if(!s.rewards.includes(receipt))s.rewards.push(receipt);
  }
  s.lastResult={encounter:b.encounter,attempt:b.id,outcome,firstClear:receipt!==null,receipt,enemies:clone(b.enemies),playerHp:b.playerHp};
  s.battle=null;
 }
 function beginCue(s){
  const b=s.battle,alive=b.enemies.filter(e=>e.hp>0),both=alive.length===2;
  if(!finiteInt(b.serial+1))return false;
  const actor=both?alive[b.serial%alive.length]:alive[0];if(!actor)return;
  const kind=actor.id==='threshold'?'pressure':both?'signal':'rhythm';
  b.serial++;b.cue={id:b.id+':cue:'+b.serial,kind,actors:[actor.id],resolveAt:s.now+(kind==='pressure'?1800:2000)};
  b.nextCueAt=0;
  return true;
 }
 function resolveCue(s){
  const b=s.battle,c=b.cue;if(!c)return;
  const actor=b.enemies.find(e=>e.id===c.actors[0]&&e.hp>0);
  b.cue=null;b.nextCueAt=s.now+1000;
  if(!actor)return;
  if(c.kind==='signal'&&b.enemies.some(e=>e.id==='threshold'&&e.hp>0)){
   b.buff=true;return;
  }
  const base=blueprint.bosses[actor.id].damage;
  const damage=c.kind==='pressure'&&b.buff?base+6:base;
  if(c.kind==='pressure')b.buff=false;
  b.playerHp=Math.max(0,b.playerHp-damage);
  if(b.playerHp===0)finish(s,'defeat');
 }
 function advance(s,ms){
  const end=s.now+ms;if(!finiteInt(end)||end>1e12)return fail('Достигнут временной предел прототипа.');
  while(s.battle){
   const b=s.battle,at=b.cue?b.cue.resolveAt:b.nextCueAt;
   if(at>end)break;
   s.now=at;if(b.cue)resolveCue(s);else if(!beginCue(s))return fail('Достигнут предел событий прототипа.');
  }
  s.now=end;return success('Время прототипа продвинуто.');
 }
 function reduce(s,event){
  if(!event||typeof event!=='object')return fail('Неизвестное действие.');
  const b=s.battle;
  if(event.type==='advance')return finiteInt(event.ms)&&event.ms>0&&event.ms<=10000?advance(s,event.ms):fail('Шаг времени должен быть от 1 до 10000 мс.');
  if(event.type==='mode'){
   if(b)return fail('Нельзя менять состояние во время боя.');
   if(!['patient','trip'].includes(event.mode))return fail('Неизвестное состояние.');
   s.mode=event.mode;
   if(!accessible(s,s.section))s.section=gates(s).AB.open?'B':'A';
   return success('Состояние изменено; выполненная работа сохранена.');
  }
  if(event.type==='section'){
   if(b)return fail('Сначала завершите бой.');
   if(!sections.includes(event.section)||!accessible(s,event.section))return fail('Нужны задание на проход и отдельная победа в предыдущей секции.');
   s.section=event.section;return success('Выбрана секция '+s.section+' прототипа.');
  }
  if(event.type==='proof'){
   const p=blueprint.proofs[event.id];
   if(b||!p||p.section!==s.section||p.mode!==s.mode||!accessible(s,p.section))return fail('Это условие проверяется в другой секции или состоянии.');
   if(p.requires.some(id=>!s.proofs[id]))return fail('Сначала нужны предыдущие наблюдения или действия задания.');
   if(s.proofs[event.id])return fail('Это условие уже отмечено.');
   s.proofs[event.id]=true;return success('Демо-условие отмечено: '+p.label+'.');
  }
  if(event.type==='start'){
   const a=availability(s,event.encounter);if(!a.available)return fail(a.missing.join('. '));
   if(!finiteInt(s.attempt+1))return fail('Достигнут предел счётчика попыток прототипа.');
   const e=blueprint.encounters[event.encounter];s.attempt++;
   s.battle={id:'floor9-demo:'+s.attempt,encounter:e.id,enemies:e.bosses.map(id=>({id,hp:e.bosses.length===2?blueprint.bosses[id].duoHp:blueprint.bosses[id].soloHp,maxHp:e.bosses.length===2?blueprint.bosses[id].duoHp:blueprint.bosses[id].soloHp})),target:e.bosses[0],playerHp:100,maxPlayerHp:100,nextAttackAt:s.now,cue:null,nextCueAt:s.now+800,buff:false,serial:0};
   return success('Начат самостоятельный демонстрационный бой. Реальные характеристики не используются.');
  }
  if(event.type==='target'){
   if(!b||!b.enemies.some(e=>e.id===event.boss&&e.hp>0))return fail('Нельзя выбрать отсутствующую или побеждённую цель.');
   b.target=event.boss;return success('Выбрана цель '+blueprint.bosses[event.boss].name+'.');
  }
  if(event.type==='attack'){
   if(!b)return fail('Активного боя нет.');
   if(s.now<b.nextAttackAt)return fail('Общий интервал атаки ещё не завершён.');
   const enemy=b.enemies.find(e=>e.id===b.target&&e.hp>0);if(!enemy)return fail('Выберите живую цель.');
   const guarded=enemy.id==='threshold'&&b.cue?.kind==='pressure';
   enemy.hp=Math.max(0,enemy.hp-(guarded?12:20));b.nextAttackAt=s.now+1000;
   const interrupted=enemy.id==='metronome'&&['signal','rhythm'].includes(b.cue?.kind);
   if(interrupted){b.cue=null;b.nextCueAt=s.now+1200;}
   if(enemy.hp===0){
    b.buff=false;
    // Support cannot turn into an unannounced solo hit when its recipient dies.
    if(b.cue?.actors.includes(enemy.id)||enemy.id==='threshold'&&b.cue?.kind==='signal'){b.cue=null;b.nextCueAt=s.now+1000;}
    const next=b.enemies.find(e=>e.hp>0);if(next)b.target=next.id;else finish(s,'victory');
   }
   return success(interrupted?'Сигнал прерван атакой выбранной цели.':'Атака выполнена; числа — тестовые единицы прототипа.');
  }
  if(event.type==='flee'){
   if(!b)return fail('Активного боя нет.');finish(s,'fled');return success('Бой оставлен. Работа и прежние победы сохранены.');
  }
  return fail('Неизвестное действие.');
 }
 function apply(s,event){
  const next=clone(s),result=reduce(next,event);
  if(result.ok){for(const key of Object.keys(s))delete s[key];Object.assign(s,next);}
  return result;
 }
 function snapshot(s){return JSON.stringify(s);}
 function validEnemies(enemies,e){
  if(!Array.isArray(enemies)||enemies.length!==e.bosses.length)return false;
  return enemies.every((enemy,i)=>{
   const max=e.bosses.length===2?blueprint.bosses[e.bosses[i]].duoHp:blueprint.bosses[e.bosses[i]].soloHp;
   return exactKeys(enemy,['id','hp','maxHp'])&&enemy.id===e.bosses[i]&&enemy.maxHp===max&&finiteInt(enemy.hp)&&enemy.hp<=max;
  });
 }
 function validResult(s,r){
  if(r===null)return true;
  if(!exactKeys(r,['encounter','attempt','outcome','firstClear','receipt','enemies','playerHp']))return false;
  const e=blueprint.encounters[r.encounter],n=Number(String(r.attempt).split(':').pop());
  if(!e||!/^floor9-demo:[1-9][0-9]*$/.test(r.attempt)||!finiteInt(n)||n>s.attempt||!['victory','defeat','fled'].includes(r.outcome)||typeof r.firstClear!=='boolean'||!finiteInt(r.playerHp)||r.playerHp>100||!validEnemies(r.enemies,e))return false;
  const alive=r.enemies.some(x=>x.hp>0);
  if(r.outcome==='victory'?(alive||r.playerHp===0||!s.clears[r.encounter]):(!alive||r.firstClear||r.outcome==='defeat'&&r.playerHp!==0||r.outcome==='fled'&&r.playerHp===0))return false;
  return r.firstClear?r.receipt==='floor9:first-clear:'+r.encounter&&s.rewards.includes(r.receipt):r.receipt===null;
 }
 function restore(text){
  try{
   const s=JSON.parse(text),keys=Object.keys(initial());
   if(!exactKeys(s,keys)||s.brand!==brand||s.version!==1||!['patient','trip'].includes(s.mode)||!sections.includes(s.section)||!finiteInt(s.now)||s.now>1e12||!finiteInt(s.attempt)||!exactKeys(s.proofs,proofIds)||!proofIds.every(id=>typeof s.proofs[id]==='boolean')||!exactKeys(s.clears,encounterIds)||!encounterIds.every(id=>typeof s.clears[id]==='boolean')||!Array.isArray(s.rewards)||new Set(s.rewards).size!==s.rewards.length||!validResult(s,s.lastResult))throw Error();
   for(const id of proofIds)if(s.proofs[id]&&blueprint.proofs[id].requires.some(dep=>!s.proofs[dep]))throw Error();
   const expected=encounterIds.filter(id=>s.clears[id]).map(id=>'floor9:first-clear:'+id);
   if(s.rewards.length!==expected.length||expected.some(id=>!s.rewards.includes(id)))throw Error();
   if(s.clears.solo_a&&!s.proofs.a_exam||s.clears.solo_b&&(!gates(s).AB.open||!s.proofs.b_record)||s.clears.duo_c&&(!gates(s).AB.open||!gates(s).BC.open)||!accessible(s,s.section))throw Error();
   if(s.battle!==null){
    const b=s.battle,e=blueprint.encounters[b.encounter];
    if(!exactKeys(b,['id','encounter','enemies','target','playerHp','maxPlayerHp','nextAttackAt','cue','nextCueAt','buff','serial'])||!e||s.mode!=='trip'||s.section!==e.section||s.attempt<1||b.id!=='floor9-demo:'+s.attempt||s.lastResult?.attempt===b.id||!finiteInt(b.playerHp)||b.playerHp<1||b.playerHp>100||b.maxPlayerHp!==100||!finiteInt(b.nextAttackAt)||b.nextAttackAt>s.now+1000||!finiteInt(b.nextCueAt)||!finiteInt(b.serial)||typeof b.buff!=='boolean'||!validEnemies(b.enemies,e))throw Error();
    if(!b.enemies.some(x=>x.hp>0)||!b.enemies.some(x=>x.id===b.target&&x.hp>0)||b.buff&&b.enemies.filter(x=>x.hp>0).length!==2)throw Error();
    if(b.cue!==null){
     const c=b.cue,alive=b.enemies.filter(x=>x.hp>0).length;if(!exactKeys(c,['id','kind','actors','resolveAt'])||b.serial<1||c.id!==b.id+':cue:'+b.serial||!['pressure','signal','rhythm'].includes(c.kind)||!Array.isArray(c.actors)||c.actors.length!==1||!b.enemies.some(x=>x.id===c.actors[0]&&x.hp>0)||!finiteInt(c.resolveAt)||c.resolveAt<s.now||c.resolveAt>s.now+2000||b.nextCueAt!==0||c.kind==='pressure'&&c.actors[0]!=='threshold'||c.kind!=='pressure'&&c.actors[0]!=='metronome'||c.kind==='signal'&&alive!==2||c.kind==='rhythm'&&alive!==1)throw Error();
    }else if(b.nextCueAt<s.now||b.nextCueAt>s.now+1200)throw Error();
    const copy=clone(s);copy.battle=null;if(!availability(copy,e.id).available)throw Error();
   }
   return{ok:true,state:s,message:'Восстановлен только снимок прототипа; игра не изменена.'};
  }catch(_){return{ok:false,state:null,message:'Это не корректный снимок данного прототипа. Исходные данные не заменены.'};}
 }
 return freeze({blueprint,initial,gates,accessible,availability,apply,snapshot,restore});
});
