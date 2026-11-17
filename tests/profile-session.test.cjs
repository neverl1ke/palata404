'use strict';
const {test}=require('node:test');
const a=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const Session=require('../profile-session.js');
function locks(){
 let owner=null;const requests=[];
 return {requests,request(name,options,callback){
  requests.push({name,options});const token=owner?null:{};if(token)owner=token;
  return Promise.resolve().then(()=>callback(token?{name}:null)).finally(()=>{if(owner===token)owner=null;});
 }};
}
const turn=()=>new Promise(resolve=>setImmediate(resolve));
function page(manager){const frame={contentWindow:{}},states=[],s=Session.create({locks:manager,onState:x=>states.push(x)});let loads=0;return{frame,s,states,load:()=>loads++,loads:()=>loads};}
test('profile data is not loaded until exclusive ownership is acquired',async()=>{
 const manager=locks(),p=page(manager);p.s.start(p.frame,p.load);
 a.equal(p.loads(),0);a.equal(p.s.canWrite(p.frame.contentWindow),false);
 await p.s.ready;a.equal(p.loads(),1);a.equal(p.s.canWrite(p.frame.contentWindow),true);
 a.deepEqual(manager.requests,[{name:Session.lockName,options:{mode:'exclusive',ifAvailable:true}}]);
 a.equal(p.s.canWrite({}),false,'another frame never inherits write permission');
});
test('a second tab cannot load old data, write, or automatically take over a live session',async()=>{
 const manager=locks(),first=page(manager),second=page(manager);
 await first.s.start(first.frame,first.load);await second.s.start(second.frame,second.load);
 a.equal(second.loads(),0);a.equal(second.s.state().reason,'occupied');a.equal(second.s.canWrite(second.frame.contentWindow),false);
 first.s.restored();await turn();a.equal(second.loads(),0);
 await second.s.start(second.frame,second.load);a.equal(second.loads(),0,'a stale page must reload rather than re-use memory');
 const fresh=page(manager);await fresh.s.start(fresh.frame,fresh.load);a.equal(fresh.loads(),1);a.equal(fresh.s.canWrite(fresh.frame.contentWindow),true);
});
test('history restoration permanently fences the old frame before releasing its lock',async()=>{
 const manager=locks(),p=page(manager);await p.s.start(p.frame,p.load);
 p.s.restored({});a.equal(p.s.canWrite(p.frame.contentWindow),true,'an unrelated caller cannot invalidate the frame');
 p.s.restored(p.frame.contentWindow);a.equal(p.s.canWrite(p.frame.contentWindow),false);a.equal(p.s.state().reason,'restored');
 await turn();const next=page(manager);await next.s.start(next.frame,next.load);a.equal(next.loads(),1);
});
test('unsupported or denied lock access never loads or writes a profile',async()=>{
 for(const manager of [undefined,{request(){throw new Error('unavailable');}},{request(){return Promise.reject(new Error('denied'));}}]){
  const p=page(manager);await p.s.start(p.frame,p.load);await turn();
  a.equal(p.loads(),0);a.equal(p.s.state().status,'blocked');a.equal(p.s.canWrite(p.frame.contentWindow),false);
 }
});
test('frame load errors release ownership and remain blocked',async()=>{
 const manager=locks(),p=page(manager);await p.s.start(p.frame,()=>{throw new Error('load failed');});await turn();
 a.equal(p.s.state().reason,'unavailable');a.equal(p.s.canWrite(p.frame.contentWindow),false);
 const next=page(manager);await next.s.start(next.frame,next.load);a.equal(next.loads(),1);
});
// Execute the actual game helpers, not a second implementation of write guards.
const fixture=fs.readFileSync(path.join(__dirname,'game-logic.test.cjs'),'utf8');
const host={require,__dirname,console,URLSearchParams};vm.runInNewContext(fixture.slice(0,fixture.indexOf('\ntest('))+'\nglobalThis.makeGame=game;',host);
test('a stale real game document cannot replace profile bytes or delete reward journals',()=>{
 const g=host.makeGame();g.run('safeStorageSet("palata404_pending_battle_reward","durable");safeStorageSet("palata404_stats","newer");window.parent={PalataProfileSession:{canWrite:()=>false}}');
 a.equal(g.run('safeStorageSet("palata404_stats","old")'),false);a.equal(g.run('safeStorageRemove("palata404_pending_battle_reward")'),false);
 a.equal(g.run('safeStorageGet("palata404_stats")'),'newer');a.equal(g.run('safeStorageGet("palata404_pending_battle_reward")'),'durable');
 a.equal(g.run('saveGameProgress()'),false);a.equal(g.run('safeStorageGet("palata404_pending_battle_reward")'),'durable');
});
test('transactions cannot mutate gear or currency after session ownership is lost',()=>{
 const g=host.makeGame();g.run('window.parent={PalataProfileSession:{canWrite:()=>false}};var changed=0;var before=JSON.stringify({stats,inventory,equippedGear})');
 a.equal(g.run('weaponTransaction(()=>{changed++;stats.silver=0;return {ok:true}}).ok'),false);
 a.equal(g.run('changed'),0);a.equal(g.run('JSON.stringify({stats,inventory,equippedGear})===before'),true);
});
