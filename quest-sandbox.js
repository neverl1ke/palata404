/* Must run before any game script. Only this document receives this storage facade. */
(function(){
'use strict';
const prefix='palata404_quest_test_v1:';
let storage;try{storage=window.localStorage;}catch(_){storage=null;}
const keys=()=>storage?Array.from({length:storage.length},(_,i)=>storage.key(i)).filter(k=>k?.startsWith(prefix)):[];
const isolated={getItem:k=>storage?.getItem(prefix+k)??null,setItem(k,v){if(!storage)throw Error('Storage unavailable');storage.setItem(prefix+k,String(v));},removeItem:k=>storage?.removeItem(prefix+k),key:i=>keys()[i]?.slice(prefix.length)??null,clear(){keys().forEach(k=>storage.removeItem(k));},get length(){return keys().length;}};
try{Object.defineProperty(window,'localStorage',{value:isolated,configurable:false});window.PalataQuestSandbox=true;}catch(_){document.write('<plaintext>Ізоляція сховища недоступна. Тест не запущено.');window.stop();throw Error('Quest sandbox could not isolate saves');}
})();
