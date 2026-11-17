'use strict';
const {test}=require('node:test');
const a=require('node:assert/strict');
const E=require('../quest-engine.js');
const Notes=require('../quest-notes.js');
const clone=value=>JSON.parse(JSON.stringify(value));
const route=[
 ['inspectDoor','A','patient'],
 ['supplyNote','collector','patient'],
 ['takeHandle','collector','trip'],
 ['unlockB','A','trip']
];
// These are the existing actions: copy changes must not change their meaning.
const expected={
 inspectDoor:[
  {answer:'door',choices:[['door','Осмотреть ручку и засов'],['bench','Осмотреть скамью']]},
  {answer:'door',choices:[['door','Проверить ход створки и запомнить порядок']]}
 ],
 supplyNote:[
  {answer:'cabinet',choices:[['cabinet','Открыть шкаф'],['clock','Осмотреть часы']]},
  {answer:'cabinet',choices:[['cabinet','Осмотреть отсек с аварийной рукоятью']]}
 ],
 takeHandle:[
  {answer:'cabinet',choices:[['cabinet','Открыть резервный отсек'],['tray','Осмотреть лоток']]},
  {answer:'cabinet',choices:[['cabinet','Взять аварийную рукоять']]}
 ],
 unlockB:[
  {answer:'door',choices:[['door','Прижать створку к коробке'],['pull','Сразу потянуть дверь']]},
  {answer:'handle',choices:[['handle','Вставить и повернуть аварийную рукоять'],['pull','Потянуть дверь до освобождения засова']]},
  {answer:'door',choices:[['door','Потянуть свободную створку']]}
 ]
};
function success(s,event){
 const result=E.apply(s,event,60001);
 a.equal(result.ok,true,result.message);a.equal(result.reward??null,null);
 return result;
}
function choose(s,id,index){return success(s,{type:'interact',id,choice:expected[id][index].answer});}
function at(id,index=0){
 const s=E.initial();
 Object.assign(s,{materials:19,transaction:7,lastReceipt:'Existing receipt',cargo:['tag'],collectorCount:3,collectorAt:42000});
 for(const [current,room,mode] of route){
  if(s.mode!==mode)success(s,{type:'switch'});
  if(s.room!==room)success(s,{type:'move',room});
  const count=current===id?index:expected[current].length;
  for(let i=0;i<count;i++)choose(s,current,i);
  if(current===id)return s;
 }
 throw Error('Unknown interaction '+id);
}
function recorded(s){return ['С1','С2'].map(id=>Notes.forQuest(E,null,s,id));}
function reject(s,id,choice){
 const before=clone(s),sources=JSON.stringify(E.interactions),notes=recorded(s);
 const result=E.apply(s,{type:'interact',id,choice},60001);
 a.equal(result.ok,false);a.equal(result.reward??null,null);
 a.deepEqual(s,before,'a wrong choice must leave all saved state untouched');
 a.deepEqual(recorded(s),notes,'a failed inspection cannot create evidence');
 a.equal(JSON.stringify(E.interactions),sources,'source clues must remain intact');
 return result.message;
}

test('A/B feedback preserves the original step counts, action IDs and choices',()=>{
 for(const [id,steps] of Object.entries(expected)){
  a.deepEqual(E.interactions[id].steps.map(({answer,choices})=>({answer,choices})),steps,id);
 }
});

test('every A/B wrong choice has contextual feedback and no state, reward or evidence changes',()=>{
 const messages=[];
 for(const [id,steps] of Object.entries(expected))for(let index=0;index<steps.length;index++){
  const wrong=steps[index].choices.find(([choice])=>choice!==steps[index].answer)?.[0]||'unrelated-object';
  const message=reject(at(id,index),id,wrong);
  a.equal(message,E.interactions[id].steps[index].failure,id+' step '+index);
  a.ok(message.length>20);
  a.doesNotMatch(message,/Предмет не соответствует|ключ|B\/C|аптеч|EXP|серебр|09:15|Клара/);
  messages.push(message);
 }
 a.equal(new Set(messages).size,messages.length,'feedback describes each current step');
});

test('wrong object feedback stays within the current clue and pulling explains the current latch state',()=>{
 const bench=reject(at('inspectDoor'),'inspectDoor','bench');
 const clock=reject(at('supplyNote'),'supplyNote','clock');
 const tray=reject(at('takeHandle'),'takeHandle','tray');
 const loaded=reject(at('unlockB'),'unlockB','pull');
 const unloaded=reject(at('unlockB',1),'unlockB','pull');
 a.match(bench,/скамья/i);a.doesNotMatch(bench,/рукоят|прижать|повернуть/i);
 a.match(clock,/часах/i);a.doesNotMatch(clock,/рукоят/i);
 a.match(tray,/лоток/i);a.match(tray,/шкафа/i);
 a.match(loaded,/зажат|давит/i);a.match(unloaded,/ещё выдвинут/i);
 a.notEqual(loaded,unloaded);
});

test('the first two latch steps describe observations and offer the recorded Patient plan as an optional hint',()=>{
 for(const step of E.interactions.unlockB.steps.slice(0,2)){
  a.doesNotMatch(step.text,/Прижмите|Вставьте|поверните/i);
  a.match(step.text,/засов/i);a.match(step.hint,/запис/);a.match(step.hint,/Пациент/i);
 }
 // The complete mechanical clue remains in the original Patient inspection.
 a.match(E.interactions.inspectDoor.steps[1].text,/сначала прижать.*затем повернуть.*после щелчка тянуть/i);
});

test('the correct A/B flow still opens B on the last physical action without spending items or currencies',()=>{
 const s=at('unlockB'),before=clone(s);
 a.equal(E.accessible(s,'B'),false);
 for(let index=0;index<expected.unlockB.length;index++){
  choose(s,'unlockB',index);
  a.equal(E.accessible(s,'B'),index===2);
 }
 for(const [id] of route)a.equal(s.interactions[id],expected[id].length);
 for(const flag of ['doorKnown','reserveKnown','tripHandle','unlockB'])a.equal(s.flags[flag],true);
 for(const key of ['cargo','materials','transaction','lastReceipt','collectorCount','collectorAt','world','jobs'])a.deepEqual(s[key],before[key],key);
 a.equal(s.flags.unlockC,undefined);a.equal(s.version,10);
});

test('saved partial latch progress resumes with the same feedback and completion in supported legacy saves',()=>{
 for(const version of [3,4,5,6,7,8,9,10])for(const index of [0,1,2]){
  const raw=clone(at('unlockB',index));raw.version=version;
  const bytes=JSON.stringify(raw),s=E.restore(raw);
  a.equal(JSON.stringify(raw),bytes,'restore cannot modify the saved source');
  a.equal(s.interactions.unlockB,index);a.equal(s.flags.unlockB,false);
  const wrong=expected.unlockB[index].choices.find(([choice])=>choice!==expected.unlockB[index].answer)?.[0]||'unrelated-object';
  a.equal(reject(s,'unlockB',wrong),E.interactions.unlockB.steps[index].failure);
  for(let next=index;next<expected.unlockB.length;next++)choose(s,'unlockB',next);
  a.equal(s.flags.unlockB,true);a.equal(s.interactions.unlockB,3);a.equal(E.accessible(s,'B'),true);
  a.equal(s.transaction,7);a.equal(s.materials,19);
 }
});

test('legacy door knowledge without inspection records still permits the same three actions',()=>{
 const s=E.restore({version:3,room:'A',mode:'trip',flags:{doorKnown:true,reserveKnown:true,tripHandle:true}});
 a.equal(s.interactions.inspectDoor,0);a.deepEqual(recorded(s),[[],[]]);
 for(let index=0;index<expected.unlockB.length;index++)choose(s,'unlockB',index);
 a.equal(s.flags.unlockB,true);a.equal(E.accessible(s,'B'),true);
});
