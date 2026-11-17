/* Standalone task preparation. No live world, boss, inventory or reward imports. */
(function(root,factory){'use strict';const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.PalataFloor9TaskPrep=api;})(globalThis,function(){
 'use strict';
 const brand='palata404-floor9-task-prep',clone=x=>JSON.parse(JSON.stringify(x));
 function freeze(x){if(x&&typeof x==='object'){Object.values(x).forEach(freeze);Object.freeze(x);}return x;}
 const blueprint=freeze({status:'PREPARATION_ONLY_NOT_ACTIVE_GAME',frozenRooms:['903','906','912'],integration:{activeFloor9:false,gameWrites:false,bossAccessWrites:false,realRewards:false},tasks:{
  support:{id:'support',title:'Опора: стендовая подготовка',rooms:['909'],goal:'По маркировке и состоянию подобрать совместимую целую пару, проверить крепление на стенде и вернуть опору на своё место.',scopeNote:'Стендовая подготовка 909. Курс 906 не пройден; полное задание Q2 не завершено.'},
  service:{id:'service',title:'Заявка на фактический узел',rooms:['907','913 · внешнее окно','коридор B'],goal:'Сопоставить запись, реальный узел и наблюдаемую неисправность; после обслуживания проверить ту же створку.',scopeNote:'Только местный результат. Доступ B/C, условия прохода и состояние боссов не меняются.'},
  holder:{id:'holder',title:'Пристосование, которое работает',rooms:['910','911'],goal:'Собрать подходящий держатель, проверить посадку пустой учебной чашки, использовать на подносе и оставить на отмеченной полке.',scopeNote:'Локальная работа 910–911. Полка хранит результат; сдачи и награды активной игры не используются.'}
 }});
 const items=freeze({
  support:[{id:'s1',name:'Опора Б',kind:'support',details:{connector:'N2',condition:'intact'}},{id:'s2',name:'Опора А',kind:'support',details:{connector:'N3',condition:'intact'}},{id:'s3',name:'Опора В',kind:'support',details:{connector:'N2',condition:'damaged'}},{id:'t1',name:'Наконечник В',kind:'tip',details:{connector:'N2',condition:'intact'}},{id:'t2',name:'Наконечник А',kind:'tip',details:{connector:'N3',condition:'intact'}},{id:'t3',name:'Наконечник Б',kind:'tip',details:{connector:'N2',condition:'cracked'}}],
  holder:[{id:'b1',name:'Основа В',kind:'base',details:{connector:'R4',condition:'intact'}},{id:'b2',name:'Основа А',kind:'base',details:{connector:'R3',condition:'intact'}},{id:'b3',name:'Основа Б',kind:'base',details:{connector:'R4',condition:'damaged'}},{id:'i1',name:'Вставка А',kind:'insert',details:{connector:'R4',cup:'C2',condition:'intact'}},{id:'i2',name:'Вставка Б',kind:'insert',details:{connector:'R4',cup:'C3',condition:'intact'}},{id:'i3',name:'Вставка В',kind:'insert',details:{connector:'R4',cup:'C2',condition:'cracked'}}]
 });
 const requests=freeze([{id:'r1',name:'Заявка Б',details:{node:'B17',symptom:'stopmark'}},{id:'r2',name:'Заявка А',details:{node:'B71',symptom:'stopmark'}},{id:'r3',name:'Заявка В',details:{node:'B17',symptom:'lamp'}}]);
 const node=freeze({id:'B17',symptom:'stopmark',text:'Створка останавливается у контрольной метки. На узле шильдик B17.'});
 const request=freeze({support:{connector:'N2',rack:'rack-n2'},holder:{mount:'R4',cup:'C2',tray:'T2',shelf:'P2'}});
 const receiptIds=freeze({support:'f9-task-prep:909-bench',service:'f9-task-prep:B-local-check',holder:'f9-task-prep:911-placement'});
 const ok=message=>({ok:true,message}),no=message=>({ok:false,message});
 function initial(){return{brand,version:1,cases:{
  support:{seen:[],selectedSupport:null,selectedTip:null,assembled:false,bench:false,parked:false,done:false},
  service:{recordsRead:false,nodeSeen:false,selected:null,sent:false,ack:null,tested:false,report:null,done:false},
  holder:{cardRead:false,seen:[],base:null,insert:null,assembled:false,fit:false,delivered:false,view:'910',mounted:false,cup:false,shelf:null,verified:false,done:false}
 },receipts:[]};}
 const item=(task,id)=>items[task]?.find(x=>x.id===id);
 function supportPair(c){const a=item('support',c.selectedSupport)?.details,b=item('support',c.selectedTip)?.details;return!!a&&!!b&&a.connector==='N2'&&b.connector===a.connector&&a.condition==='intact'&&b.condition==='intact';}
 function holderPair(c){const a=item('holder',c.base)?.details,b=item('holder',c.insert)?.details;return!!a&&!!b&&a.connector==='R4'&&b.connector===a.connector&&b.cup==='C2'&&a.condition==='intact'&&b.condition==='intact';}
 function matched(c){const r=requests.find(r=>r.id===c.selected)?.details;return!!r&&r.node===node.id&&r.symptom===node.symptom;}
 function finish(s,id,message){s.cases[id].done=true;const receipt=receiptIds[id];if(!s.receipts.includes(receipt))s.receipts.push(receipt);return{...ok(message),receipt};}
 function board(s,id){
  if(typeof id!=='string'||!Object.hasOwn(blueprint.tasks,id)||!s?.cases||!Object.hasOwn(s.cases,id))return null;
  const spec=blueprint.tasks[id],c=s?.cases?.[id];if(!spec||!c)return null;
  const b={...clone(spec),done:c.done,receipt:c.done?receiptIds[id]:null,progress:clone(c)};
  if(items[id])b.items=items[id].map(x=>({id:x.id,name:x.name,kind:x.kind,inspected:c.seen.includes(x.id),details:c.seen.includes(x.id)?clone(x.details):null})).sort((a,b)=>({support:0,tip:1,base:0,insert:1}[a.kind]-{support:0,tip:1,base:0,insert:1}[b.kind])||a.name.localeCompare(b.name,'ru'));
  if(id==='support'){b.request=clone(request.support);b.routeTested=false;b.observation=c.bench?'На стенде стык зафиксирован; расхождение меток не наблюдается. Проба на маршруте не проводилась.':null;}
  if(id==='service'){b.requests=requests.map(r=>({id:r.id,name:r.name,details:c.recordsRead?clone(r.details):null})).sort((a,b)=>a.name.localeCompare(b.name,'ru'));b.node=c.nodeSeen?clone(node):null;b.observation=c.tested?{movement:'free',text:'После обслуживания створка проходит контрольную метку без остановки.'}:null;}
  if(id==='holder'){b.request=c.cardRead?clone(request.holder):null;b.currentScene=c.view;b.objectLocation=c.shelf==='P2'?'shelf-P2':c.delivered?'table-911':'bench-910';b.observation=c.verified?'Пустая учебная чашка стоит в держателе на подносе, поднос находится на полке P2.':c.fit?'Посадка пустой чашки проверена на рабочем столе. Использование в 911 ещё не подтверждено.':null;}
  return freeze(b);
 }
 function inspect(c,task,value){const x=item(task,value);if(!x)return no('Такого предмета нет на этом рабочем месте.');if(!c.seen.includes(value))c.seen.push(value);return ok('Осмотрено: '+x.name+'. Маркировка и состояние добавлены в рабочий лист.');}
 function selectPart(c,task,key,kind,value){
  const x=item(task,value);if(!x||x.kind!==kind)return no('Выберите предмет нужного типа.');
  if(!c.seen.includes(value))return no('Сначала осмотрите маркировку и состояние этого предмета.');
  if(c[key]===value)return ok('Этот предмет уже выбран; выполненные проверки сохранены.');
  c[key]=value;c.assembled=false;
  if(task==='support'){c.bench=false;c.parked=false;}else c.fit=false;
  return ok('Выбор изменён. Зависимые проверки этой сборки нужно выполнить заново.');
 }
 function reduce(s,e){
  const id=e?.task;
  if(typeof id!=='string'||!Object.hasOwn(blueprint.tasks,id)||!Object.hasOwn(s.cases,id))return no('Неизвестная локальная работа.');
  const c=s.cases[id];
  if(id==='holder'&&e.op==='view'){if(!['910','911'].includes(e.value))return no('В этом просмотре доступны только 910 и 911.');c.view=e.value;return ok('Показано рабочее место '+c.view+'. Предметы и результаты не перемещены.');}
  if(e.op==='submit'&&c.done)return{...ok('Локальная запись уже подтверждена; повторной отметки нет.'),receipt:receiptIds[id]};
  if(c.done)return no('Работа уже подтверждена. Сохранённый результат остаётся на месте.');
  if(id==='support'){
   if(e.op==='inspect')return inspect(c,id,e.value);
   if(e.op==='support')return selectPart(c,id,'selectedSupport','support',e.value);
   if(e.op==='tip')return selectPart(c,id,'selectedTip','tip',e.value);
   if(e.op==='assemble'){
    if(c.assembled)return ok('Эта пара уже собрана; выполненная стендовая проверка сохранена.');
    if(!c.selectedSupport||!c.selectedTip)return no('Для сборки нужны осмотренные опора и наконечник.');
    const a=item(id,c.selectedSupport).details,b=item(id,c.selectedTip).details;
    if(a.condition!=='intact'||b.condition!=='intact')return no('При осмотре отмечено повреждение выбранной детали. Эта сборка не подтверждена.');
    if(a.connector!==b.connector||a.connector!==request.support.connector)return no('Маркировки соединения не совпадают между собой или с заданием стенда.');
    c.assembled=true;return ok('Совместимая пара собрана. Её фиксация на стенде ещё не проверена.');
   }
   if(e.op==='bench'){if(!c.assembled)return no('Сначала соберите совместимую целую пару.');c.bench=true;return ok('Стендовая фиксация подтверждена. Это не проба курса 906.');}
   if(e.op==='park'){
    if(!c.bench)return no('Перед возвращением нужна стендовая проверка.');if(e.value!==request.support.rack)return no('Маркировка места хранения не соответствует выбранной опоре.');
    c.parked=true;return finish(s,id,'Опора возвращена на место N2. Стендовая подготовка завершена; курс 906 не пройден.');
   }
   return no('Локальная подготовка ещё не завершена или действие недоступно.');
  }
  if(id==='service'){
   if(e.op==='records'){c.recordsRead=true;return ok('Прочитаны три записи обслуживания из 907.');}
   if(e.op==='node'){c.nodeSeen=true;return ok(node.text);}
   if(e.op==='request'){
    if(c.sent)return no('Заявка уже обслужена. Смена бумаги не отменяет выполненную работу; проверьте ту же створку.');
    if(!c.recordsRead)return no('Сначала прочитайте записи обслуживания.');if(!requests.some(r=>r.id===e.value))return no('Такой записи в листе нет.');c.selected=e.value;return ok('Выбрана запись для сверки. Обслуживание ещё не выполнено.');
   }
   if(e.op==='send'){
    if(c.sent)return ok('Подтверждение обслуживания уже получено; выполненные повторные проверки сохранены.');
    if(!c.recordsRead||!c.nodeSeen||!c.selected)return no('Нужны прочитанная запись, осмотр узла и выбранная заявка.');
    const r=requests.find(r=>r.id===c.selected).details;
    if(r.node!==node.id)return no('Номер заявки не совпадает с осмотренным шильдиком. Подтверждения обслуживания нет.');
    if(r.symptom!==node.symptom)return no('В заявке другое наблюдение: сверяйте фактическую остановку створки, а не чужую неисправность.');
    c.sent=true;c.ack='local:B17:stopmark';return ok('Внешнее окно 913: обслуживание выбранного узла подтверждено. Теперь нужна проверка той же створки со стороны B.');
   }
   if(e.op==='retest'){if(!c.sent)return no('Проверка результата возможна после подтверждённого обслуживания.');c.tested=true;return ok('Наблюдение: створка проходит контрольную метку без остановки. Доступ B/C этим не меняется.');}
   if(e.op==='report'){if(!c.tested)return no('Сначала проверьте фактический ход створки.');if(!['free','blocked'].includes(e.value))return no('Такого наблюдения в листе нет.');c.report=e.value;return ok('Выбран черновик местного результата; подтверждение ещё не выдано.');}
   if(e.op==='submit'){
    if(!c.tested||!c.report)return no('Нужны фактическая повторная проверка и её запись.');
    if(c.report!=='free')return no('Запись противоречит вашей проверке: створка прошла контрольную метку без остановки.');
    return finish(s,id,'Местная проверка B17 записана. Это не завершение Q4 и не открытие B/C; состояние боссов не изменено.');
   }
   return no('Действие отсутствует в этом рабочем листе.');
  }
  if(e.op==='card'){c.cardRead=true;return ok('Задание прочитано: крепление R4, пустая чашка C2, поднос T2, полка P2.');}
  if(e.op==='inspect')return inspect(c,id,e.value);
  if(['base','insert'].includes(e.op)){
   if(c.delivered)return no('Комплект уже перенесён в 911. Просмотр 910 не создаёт вторую сборку.');
   return selectPart(c,id,e.op,e.op,e.value);
  }
  if(e.op==='assemble'){
   if(c.assembled)return ok('Держатель уже собран; посадка и положение комплекта не изменены.');
   if(c.view!=='910'||c.delivered||!c.cardRead||!c.base||!c.insert)return no('Нужны задание и выбранные осмотренные части на столе 910.');
   const a=item(id,c.base).details,b=item(id,c.insert).details;
   if(a.condition!=='intact'||b.condition!=='intact')return no('У выбранной части отмечено повреждение. Сборка не подтверждена.');
   if(a.connector!=='R4'||b.connector!==a.connector||b.cup!=='C2')return no('Стык или посадка чашки не соответствует заданию. Сверьте осмотренные маркировки.');
   c.assembled=true;return ok('Держатель собран. Посадка пустой чашки ещё не проверена.');
  }
  if(e.op==='fit'){if(c.view!=='910'||c.delivered||!c.assembled)return no('Посадка проверяется на собранном предмете в 910 до переноса.');c.fit=true;return ok('Пустая учебная чашка C2 соответствует посадке. Применение в 911 ещё впереди.');}
  if(e.op==='carry'){if(!c.fit||c.delivered)return no('Нужен проверенный комплект, который ещё находится в 910.');c.delivered=true;c.view='911';return ok('Один комплект перенесён в 911. Стол 910 освобождён.');}
  if(c.view!=='911'||!c.delivered)return no('Это действие выполняется с принесённым комплектом в 911.');
  if(e.op==='mount'){if(e.value!=='T2')return no('Маркировка подноса не совпадает с заданием.');if(c.mounted)return ok('Держатель уже закреплён; положение чашки и подноса не изменено.');c.mounted=true;return ok('Держатель закреплён на учебном подносе T2. Чашка пока не размещена.');}
  if(e.op==='cup'){if(!c.mounted)return no('Сначала установите держатель на нужном подносе.');if(c.cup)return ok('Чашка уже установлена; положение подноса не изменено.');c.cup=true;return ok('Пустая чашка установлена в держателе. Поднос ещё на столе.');}
  if(e.op==='shelf'){if(!c.cup)return no('На подносе ещё нет размещённой чашки.');if(e.value!=='P2')return no('Это другое место. Сверьте маркировку полки с заданием.');c.shelf='P2';return ok('Поднос с чашкой оставлен на полке P2. Проверьте итоговое положение.');}
  if(e.op==='verify'){if(c.shelf!=='P2')return no('Пока нет результата на заданной полке.');c.verified=true;return finish(s,id,'На полке P2 стоит поднос с чашкой в держателе. Стол свободен; местный результат подтверждён.');}
  return no('Локальная работа ещё не завершена или действие недоступно.');
 }
 const keys=(x,k)=>x&&typeof x==='object'&&!Array.isArray(x)&&Object.keys(x).length===k.length&&k.every(n=>Object.hasOwn(x,n));
 const seenValid=(task,a)=>Array.isArray(a)&&new Set(a).size===a.length&&a.every(id=>!!item(task,id));
 function valid(s){
  const blank=initial();if(!keys(s,Object.keys(blank))||s.brand!==brand||s.version!==1||!keys(s.cases,Object.keys(blank.cases))||!Array.isArray(s.receipts)||new Set(s.receipts).size!==s.receipts.length)return false;
  for(const id of Object.keys(blank.cases)){
   const c=s.cases[id],base=blank.cases[id];if(!keys(c,Object.keys(base)))return false;
   for(const [k,v]of Object.entries(base))if(typeof v==='boolean'&&typeof c[k]!=='boolean')return false;
  }
  const a=s.cases.support,b=s.cases.service,c=s.cases.holder;
  if(!seenValid('support',a.seen)||!seenValid('holder',c.seen))return false;
  for(const [task,x,fields]of [['support',a,{selectedSupport:'support',selectedTip:'tip'}],['holder',c,{base:'base',insert:'insert'}]])for(const [key,kind]of Object.entries(fields))if(x[key]!==null&&(!item(task,x[key])||item(task,x[key]).kind!==kind||!x.seen.includes(x[key])))return false;
  if(a.assembled&&!supportPair(a)||a.bench&&!a.assembled||a.parked&&!a.bench||a.done!==a.parked)return false;
  if(b.selected!==null&&!requests.some(r=>r.id===b.selected)||b.selected!==null&&!b.recordsRead||b.sent&&(!b.recordsRead||!b.nodeSeen||!matched(b))||b.ack!==(b.sent?'local:B17:stopmark':null)||b.tested&&!b.sent||b.report!==null&&(!b.tested||!['free','blocked'].includes(b.report))||b.done&&(!b.tested||b.report!=='free'))return false;
  if(!['910','911'].includes(c.view)||c.assembled&&(!c.cardRead||!holderPair(c))||c.fit&&!c.assembled||c.delivered&&!c.fit||c.mounted&&!c.delivered||c.cup&&!c.mounted||c.shelf!==null&&(c.shelf!=='P2'||!c.cup)||c.verified&&c.shelf!=='P2'||c.done!==c.verified)return false;
  const expected=Object.keys(blank.cases).filter(id=>s.cases[id].done).map(id=>receiptIds[id]);return s.receipts.length===expected.length&&expected.every(id=>s.receipts.includes(id));
 }
 function apply(s,event){
  try{if(!valid(s))return no('Некорректный снимок локальных работ.');const next=clone(s),result=reduce(next,event);if(result.ok){if(!valid(next))return no('Изменение не прошло проверку локальных работ.');for(const k of Object.keys(s))delete s[k];Object.assign(s,next);}return result;}catch(_){return no('Не удалось выполнить локальное действие; исходное состояние не изменено.');}
 }
 const snapshot=s=>JSON.stringify(s);
 function restore(text){try{const s=JSON.parse(text);if(!valid(s))throw Error();return{ok:true,state:s,message:'Восстановлены только локальные работы. Игра и боссы не изменены.'};}catch(_){return{ok:false,state:null,message:'Это не снимок этого прототипа или в нём нарушена последовательность. Исходные данные сохранены.'};}}
 return freeze({blueprint,initial,board,apply,snapshot,restore});
});
