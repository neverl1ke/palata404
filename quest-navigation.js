/* Player-facing directions. Navigation never completes a task or changes a save. */
(function(root,factory){
 'use strict';
 const api=factory();
 if(typeof module==='object'&&module.exports)module.exports=api;
 else root.PalataQuestNavigation=api;
})(globalThis,function(){
 'use strict';

 function target(E,s,room,mode,text,hint,extra){
  const destination=Object.hasOwn(E.rooms,room)?room:'ward404';
  return Object.assign({room:destination,mode,text,needsModeChange:s.mode!==mode},hint?{hint}:{},extra||{});
 }

 function preparationB(E,s){
  const f=s.flags||{};
  if(!f.doorKnown)return target(E,s,'A','patient',
   'Осмотрите механизм перехода A/B, пока створка свободно ходит.',
   'Проверьте, чем удерживается дверь: обычной ручкой или отдельным засовом.');
  return target(E,s,'collector','patient',
   'Найдите запись о хозяйственном резерве для перехода A/B.',
   'Опись хранится в ординаторской секции A. Сравните её с устройством двери.');
 }

 function openingB(E,s){
  const f=s.flags||{};
  if(!f.doorKnown||!f.reserveKnown)return preparationB(E,s);
  if(!f.tripHandle)return target(E,s,'collector','trip',
   'Проверьте резервный отсек, отмеченный в служебной описи.',
   'Ищите уже изученный хозяйственный шкаф, а не случайные вещи в комнате.');
  return target(E,s,'A','trip',
   'Резерв получен. Освободите заевший механизм перехода A/B.',
   'Засов под нагрузкой не сдвинется. Сначала найдите причину перекоса створки.');
 }

 function preparationC(E,s){
  const f=s.flags||{};
  if(!f.cKeyKnown)return target(E,s,'procedure','patient',
   'Найдите служебную запись о резерве перехода B/C.',
   'Осмотрите опись вещей на рабочем столе процедурной.');
  return target(E,s,'doctor','patient',
   'Уточните устройство замка B/C по памятке врача.',
   'Сведения о месте хранения и о самом замке находятся в разных записях.');
 }

 function openingC(E,s){
  const f=s.flags||{};
  if(!f.unlockB)return openingB(E,s);
  if(!f.cKeyKnown||!f.cLockKnown)return preparationC(E,s);
  const step=s.interactions?.unlockC||0;
  const goals=[
   'Найдите резерв для замка B/C по описанию в описи.',
   'Осмотрите содержимое открытой ёмкости.',
   'Сопоставьте найденный предмет с замком перехода.',
   'Проверьте, свободно ли теперь открывается створка.'
  ];
  return target(E,s,'B','trip',goals[Math.min(step,goals.length-1)],
   'Сверьте наблюдаемые предметы с описью и памяткой. Привод A/B здесь не используется.');
 }

 function exitRoute(E,s){
  const f=s.flags||{};
  if(!f.unlockC&&!s.allSectionsUnlocked)return openingC(E,s);
  if(!f.doctorWon)return target(E,s,'doctor','trip',
   'Завершите контакт с врачом, прежде чем проверять лестничный выход.',
   'Запись о первом успешном рейде врача должна быть в журнале.');
  if(!f.route){
   const missing=['A','B','C'].find(section=>!s.visited?.[section]);
   if(missing)return target(E,s,missing,'patient',
    'В маршрутном листе не хватает осмотра секции '+missing+'.',
    'Отметьте доступные коридоры, затем проверьте указатель лестницы.');
   return target(E,s,'stairs','patient',
    'Проверьте указатель и предписание у лестницы секции C.',
    'Одного посещения коридора недостаточно: осмотр лестницы записывается отдельно.');
  }
  return target(E,s,'stairs','trip',
   'Маршрут собран. Проверьте лестничный выход.',
   'Сверьте лестничную дверь с маршрутной записью и осмотрите её замок.');
 }

 function jobGuide(E,s,id){
  const spec=E.jobs[id],job=s.jobs?.[id];
  if(!job?.active){
   const complete=!!job?.count&&!spec.repeat;
   return target(E,s,spec.giver,'patient',
    complete?'Поручение уже сдано; повторять проверку не требуется.':
     'Получите '+(job?.count?'новую заявку':'поручение')+' у '+(spec.giver==='nurse'?'Клары':'врача')+'.',
    null,{complete});
  }
  if(E.ready(s,id))return target(E,s,spec.giver,'patient',
   'Передайте собранные подтверждения '+(spec.giver==='nurse'?'Кларе':'врачу')+'.',
   'Предметы подтверждения находятся в инвентаре; награда выдаётся при сдаче.');
  const stage=E.jobStage?.(s,id);
  if(stage)return target(E,s,stage.room,stage.mode||'patient',stage.text,stage.hint);
  if(id==='d3'){
   if([2,3].includes(job.revision)&&!job.work?.baselineCaptured)return target(E,s,'A','patient',
    'Запишите наблюдаемые детали коридора A в карточку.',
    'Сначала нужна собственная исходная запись; готового вывода в карточке нет.');
   if(job.done?.difference)return target(E,s,'doctor','patient',
    'Проверьте карточку наблюдения и передайте её врачу.');
   if(s.mode==='trip'&&s.trip<=job.startTrip)return target(E,s,'A','patient',
    'Для сравнения нужен новый вход. Вернитесь к переключателю, затем продолжите наблюдение.',
    'Один и тот же вход не считается повторным наблюдением.',{requiresNewTrip:true});
   return target(E,s,'A','trip',
    'Сопоставьте исходную карточку с видимыми деталями коридора A.',
    'Сравните каждую зафиксированную деталь; не приписывайте записям неизвестного автора.');
  }
  if(id==='k3'&&job.revision===3)return target(E,s,'procedure','patient','Сверьте направление, лист процедуры и копию в журнале. Подтвердите вывод по каждому вопросу.','Проверяйте значение поля вместе с его назначением. Нечитаемые сведения остаются неизвестными.');
  const step=spec.steps.find(name=>!job.done?.[name]);
  const goals={
   tag:['procedure','Сверьте заявку с маркировкой и целостностью комплектов.','Сначала осмотрите упаковки и пломбы; затем подтвердите подходящий комплект.'],
   linen:['linen','Соберите чистый комплект по заявке для палаты 406.','Проверьте состав и состояние вещей до упаковки.'],
   deliver:['ward406','Доставьте упакованный комплект в палату 406.','Проверьте номер получателя. Квитанция появится после передачи комплекта.'],
   copies:['procedure','Сопоставьте две записи и отметьте подтверждённые расхождения.','Сверяйте поля по отдельности. Не заполняйте неизвестные сведения предположениями.'],
   bell407:['ward407','Проверьте кнопку вызова в палате 407 и составьте акт наблюдения.','Осмотрите соединение, проверьте индикатор и ответ поста, затем сделайте вывод.'],
   bell408:['ward408','Проверьте кнопку вызова в палате 408 и составьте акт наблюдения.','Осмотрите соединение, проверьте индикатор и ответ поста, затем сделайте вывод.'],
   log:['doctor','Восстановите подтверждённую хронологию в журнале обхода.','Сравнивайте время отдельных записей. Неизвестные поля оставьте пустыми.']
  };
  const g=goals[step];
  if(g){
   if(![2,3].includes(job.revision)&&step==='linen')return target(E,s,'linen','patient',
    'Получите помеченный комплект для палаты 406.',
    'В старой заявке используется уже упакованный комплект. После передачи возьмите квитанцию.');
   if(![2,3].includes(job.revision)&&(step==='bell407'||step==='bell408'))return target(E,s,g[0],'patient',g[1],
    'Нажмите кнопку вызова и зафиксируйте полученный ответ в акте.');
   return target(E,s,g[0],'patient',g[1],g[2]);
  }
  return target(E,s,spec.giver,'patient','Проверьте собранные подтверждения перед сдачей поручения.');
 }

 function guide(E,s,id){
  const f=s.flags||{};
  if(id==='С5')return {room:null,mode:'trip',text:'Продолжение ниже десятого этажа пока недоступно.',needsModeChange:false,pending:true};
  if(Object.hasOwn(E.jobs,id))return jobGuide(E,s,id);
  if(id==='С1')return f.unlockB||f.doorKnown&&f.reserveKnown?
   target(E,s,'A','patient','Осмотр механизма и запись о резерве уже получены.',null,{complete:true}):preparationB(E,s);
  if(id==='П3')return f.unlockC||f.cKeyKnown&&f.cLockKnown?
   target(E,s,'B','patient','Обе служебные записи перехода C уже сверены.',null,{complete:true}):preparationC(E,s);
  if(id==='П4')return target(E,s,'stairs','patient',
   f.stairsSeen||f.exit?'Осмотр лестницы уже внесён в маршрут.':'Осмотрите указатель и предписание у лестницы C.',
   null,{complete:!!(f.stairsSeen||f.exit)});
  if(id==='С2'||id==='lockB')return f.unlockB?
   target(E,s,'B','trip','Проход A/B уже открыт.',null,{complete:true}):openingB(E,s);
  if(id==='С3'||id==='lockC')return f.unlockC?
   target(E,s,'C','trip','Проход B/C уже открыт.',null,{complete:true}):openingC(E,s);
  if(id==='С4')return f.exit?target(E,s,'stairs','trip','Лестничный выход уже проверен.',null,{complete:true}):exitRoute(E,s);
  return target(E,s,Object.hasOwn(E.rooms,id)?id:s.room,s.mode==='trip'?'trip':'patient','Осмотрите выбранную комнату и доступные предметы.');
 }

 function blocked(E,s,section){
  if(!['A','B','C'].includes(section))return {accessible:false,section,text:'Эта секция пока недоступна.',room:null,mode:s.mode,needsModeChange:false,pending:true};
  if(E.accessible(s,section))return {accessible:true,section,room:section,mode:s.mode,needsModeChange:false,text:'Проход в секцию '+section+' открыт.'};
  const prior=section==='C'&&!E.accessible(s,'B');
  const g=section==='B'||prior?openingB(E,s):openingC(E,s);
  return Object.assign({},g,{accessible:false,section,text:(prior?'Сначала требуется проход через секцию B. ':'')+g.text});
 }

 function story(E,s){
  const f=s.flags||{};
  const patches={
   'С1':{detail:'Осмотр механизма A/B и запись о хозяйственном резерве дают сведения о переходе.'},
   'П3':{detail:'Сопоставьте служебную опись перехода B/C с памяткой о его замке.'},
   'П4':{detail:'Осмотрите указатель и предписание у лестницы C. Внесите осмотр в маршрут.'},
   'С2':{title:'Заевший привод A/B',detail:'Переход A/B: '+(f.unlockB?'створка свободна.':'причина заедания ещё не устранена.')},
   'С3':{detail:'Переход B/C: '+(f.unlockC?'замок открыт.':'сверьте найденные сведения с устройством замка.')},
   'С4':{detail:'Первая успешная запись рейда врача: '+(f.doctorWon?'есть':'не получена')+'. Маршрут лестницы: '+(f.route?'собран':'не завершён')+'.'},
   'С5':{title:'Ниже десятого · продолжение',detail:'Следующий этаж пока недоступен. Это продолжение, а не активное поручение.',pending:true,available:false}
  };
  return E.story(s).map(row=>Object.assign({},row,patches[row.id]||{}));
 }

 function mapHint(E,s){
  const f=s.flags||{};
  if(f.exit)return 'Лестничный выход проверен. Открытые комнаты и повторные рейды доступны; дальнейший маршрут пока закрыт.';
  const id=f.unlockC?'С4':f.unlockB?'С3':f.doorKnown&&f.reserveKnown?'С2':'С1';
  const g=guide(E,s,id);
  return g.text+(g.needsModeChange?' Продолжение требует режима «'+(g.mode==='trip'?'Трип':'Пациент')+'». Переключатель находится на главном экране.':'');
 }

 return Object.freeze({guide,blocked,story,mapHint});
});
