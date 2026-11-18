/* Read-only copies of evidence already recorded by the player. Never read a
   generated observation, hidden equipment cause or uninspected board as proof. */
(function(root,factory){
 'use strict';
 const api=factory();
 if(typeof module==='object'&&module.exports)module.exports=api;
 else root.PalataQuestNotes=api;
})(globalThis,function(){
 'use strict';
 const storySources={
  'С1':['inspectDoor','supplyNote'],
  'С2':['inspectDoor','supplyNote','takeHandle','unlockB'],
  'П3':['record','observation'],
  'С3':['record','observation','unlockC'],
  'П4':['stairsPatient'],
  'С4':['stairsPatient','exit']
 };
 const d3SubjectNames={signA:'Табличка коридора A',bed406:'Край простыни в палате 406',call407:'Вызов палаты 407'};
 const fieldNames={time:'Время',ward:'Палата',signature:'Подпись',lot:'Комплект',route:'Маршрут',mark:'Отметка',hem:'Внутренний подгиб',stitch:'Шов',indicator:'Индикатор',reply:'Ответ поста'};
 const pieceNames={sheet:'Простыня',pillowcase:'Наволочка'};
 function freeze(value){
  if(value&&typeof value==='object'){Object.values(value).forEach(freeze);Object.freeze(value);}
  return value;
 }
 function forQuest(E,Work,state,id){
  const records=[];
  const add=(key,title,source,status,text='',fields=[])=>records.push({
   id:key,title,source,status,text,
   fields:fields.filter(([,value])=>value!==null&&value!==undefined).map(([label,value])=>({label,value:String(value)}))
  });
  if(!state||!E)return freeze(records);
  if(Object.hasOwn(storySources,id)){
   for(const action of storySources[id]){
    const spec=E.interactions?.[action],progress=state.interactions?.[action];
    if(!spec||!Number.isSafeInteger(progress)||progress<1)continue;
    for(let i=0;i<Math.min(progress,spec.steps.length);i++){
     add(action+':'+i,spec.title+' · запись '+(i+1),'Сохранённый осмотр','recorded',spec.steps[i].text);
    }
   }
   return freeze(records);
  }
  const job=state.jobs?.[id];
  if(!job||!Work?.supportsRevision?.(id,job.revision)||!job.work||
     Work.validRecord&&!Work.validRecord(id,job))return freeze(records);
  // A completed order retains its last work. A new order deliberately replaces
  // that work; this is a current/last-order notebook, not an invented archive.
  const copy={...state,jobs:{...state.jobs,[id]:{...job,active:true}}};
  const board=action=>Work.board(copy,'job:'+action);
  const w=job.work,done=job.done||{};
  const receipt=(step,cargo,title)=>{
   if(!done[step])return;
   const text=E.cargoDescription?.(state,cargo);
   if(text)add('result:'+step,title,'Подтверждённый рабочий лист','confirmed',text);
  };
  if(id==='k1'){
   if(w.inspected?.length){
    const b=board('tag');
    if(b){
     add('request','Заявка на комплект','Лист приёмки','recorded','',[
      ['Комплект',b.request.kit],['Партия',b.request.lot]
     ]);
     for(const item of b.items.filter(item=>item.inspected&&item.details)){
      add(item.id,item.name,'Осмотр маркировки и пломбы','recorded','',[
       ['Комплект',item.details.kit],['Партия',item.details.lot],['Пломба',item.details.seal]
      ]);
     }
    }
   }
   receipt('tag','tag','Лист приёмки подтверждён');
  }
  if(id==='k2'){
   if(w.selected?.length){
    const b=board('linen');
    if(b)for(const item of b.items.filter(item=>w.selected.includes(item.id))){
     add(item.id,item.name,'Выбранные вещи · текущая заявка',done.linen?'confirmed':'draft','',[
      ['Маркировка',item.size],['Размер',item.measure],['Состояние упаковки',item.condition]
     ]);
    }
   }
   if(w.shortageNoted)add('shortage','Недостача отмечена','Запись в бельевой','recorded','Недостающая вещь требует уточнения у Клары.');
   if(w.reserveGranted)add('reserve','Замена разрешена','Резолюция Клары','confirmed','Разрешена наволочка М из резерва поста размером 70 × 70 см.');
   if(w.placed?.length)add('bed','Подготовка кровати 406','Действия в палате','recorded',
    'Размещено: '+w.placed.map(piece=>pieceNames[piece]).filter(Boolean).join(', ')+'.');
   if(done.linen)add('result:linen','Комплект собран','Лист комплектации','confirmed',
    'Чистые простыня и наволочка собраны для палаты 406.');
   receipt('deliver','delivery','Подготовка завершена');
  }
  if(id==='k3'){
   if(job.revision===3&&w.sourcesRead){
    const b=board('copies');
    for(const document of b?.documents||[])add(document.id,document.title,'Источники дела №'+b.caseId,'recorded','',
     document.fields.map(field=>[field.label,field.value]));
    if(!done.copies)for(const issue of b?.issues||[]){
     const choice=issue.choices.find(choice=>choice.id===w.conclusions?.[issue.id]);
     if(choice)add('draft:'+issue.id,issue.title,'Черновик сверки','draft',choice.label+'. Вывод ещё не подтверждён.');
    }
   }else if(job.revision!==3&&!done.copies&&w.marked?.length)add('draft','Отмеченные поля','Черновик сверки','draft',
    'Отмечено: '+w.marked.map(key=>fieldNames[key]).filter(Boolean).join(', ')+'. Вывод ещё не подтверждён.');
   receipt('copies','copies','Сверка подтверждена');
  }
  if(id==='d1'){
   for(const room of ['407','408']){
    const diagnostic=w.diagnostics?.['bell'+room];
    if(diagnostic?.inspected){
     const b=board('bell'+room);
     if(b){
      const fields=[['Подключение',b.connector?.text]];
      if(diagnostic.tested)fields.push(['Индикатор',b.indicator==='on'?'Загорелся':'Не загорелся'],['Ответ поста',b.response]);
      add('diagnostic:'+room,'Первичная проверка '+room,diagnostic.tested?'Осмотр и пробный вызов':'Осмотр подключения',done['bell'+room]?'confirmed':'recorded','',fields);
      if(!done['bell'+room]&&diagnostic.selected?.length){
       const report=b.reports.find(item=>item.id===diagnostic.selected[0]);
       if(report)add('report-draft:'+room,'Проект акта '+room,'Черновик','draft',report.label);
      }
     }
    }
    if(job.revision>=4){
     const service=w.services?.['ward'+room];
     if(service?.inspected){
      const b=board('callService'+room),fallback=Work.callEquipment?.('ward'+room),e=b?.evidence||(fallback&&{equipmentId:fallback.id,connector:fallback.connector,postAddress:fallback.postAddress,observedRegistration:''});
      if(e)add('service-source:'+room,'Лист обслуживания '+room,'Прочитанный шильдик и запись персонала','recorded',e.observedRegistration,[
       ['Оборудование',e.equipmentId],['Разъём',e.connector],['Адрес поста',e.postAddress]
      ]);
     }
     if(service?.performed)add('service:'+room,'Обслуживание '+room,'Отметка персонала','confirmed','Обслуживание выполнено. Успешный вызов подтверждается отдельно.');
     if(service?.tested){
      const b=board('callRetest'+room);
      const reply=b?.response||(service.responseAddress?'Пост: «'+room+', вызов принят».':'Ответ нужной палаты не поступил.');
      add('retest:'+room,'Контрольный вызов '+room,'Ответ поста',service.confirmed?'confirmed':'recorded','',[
       ['Индикатор',!b||b.indicator==='on'?'Загорелся':'Не загорелся'],['Ответ',reply]
      ]);
     }
    }
   }
   if(job.revision===4&&w.authorized)add('authorization','Разрешение врача','Первичные акты рассмотрены','confirmed',
    'Обслуживание разрешено для узлов текущей заявки. После обслуживания требуются контрольные вызовы.');
  }
  if(id==='d2'){
   if(w.order?.length||w.reverseRead?.length||done.log){
    const b=board('log');
    if(b)for(const card of b.cards){
     if(!w.order?.includes(card.id)&&!w.reverseRead?.includes(card.id)&&!done.log)continue;
     add(card.id,'Листок обхода · '+card.room,done.log?'Подтверждённый журнал':w.order?.includes(card.id)?'Листок выбран в журнале':'Листок с прочитанным оборотом','recorded',card.note,[
      ['Время',card.time===null?'Не установлено':card.time],['Палата / место',card.room]
     ]);
     if(card.reverseRead&&card.reverseText)add(card.id+':reverse','Оборот листка '+card.room,'Прочитанная запись на обороте','recorded',card.reverseText);
    }
   }
   receipt('log','log','Порядок подтверждён');
  }
  if(id==='d3'){
   // Revision 3 freezes the actual observation. Earlier orders do not retain
   // enough provenance to reconstruct unseen values in a notebook.
   if([3,4].includes(job.revision)){
    const source=job.revision===4?d3SubjectNames[w.subjectId]:'Сохранённые показания коридора A';
    for(const [key,title]of [['baseline','Исходная карточка'],['observed','Повторное наблюдение']]){
     const observed=w[key];
     if(key==='baseline'&&!w.baselineCaptured||!observed)continue;
     add(key,title,source,'recorded','',
      Object.entries(observed).filter(([field])=>Object.hasOwn(fieldNames,field)).map(([field,value])=>[fieldNames[field],value]));
    }
    receipt('difference','difference','Карточка сравнения подтверждена');
   }else if(w.baselineCaptured)add('baseline-recorded','Исходная карточка','Ранее выданное поручение','recorded',
    'Первичная запись сохранена. В старом формате отдельные показания не фиксировались; значения не восстанавливаются предположением.');
  }
  return freeze(records);
 }
 return Object.freeze({forQuest});
});
