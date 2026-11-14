const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
function browser(){
 const state={encodes:0,dataDecodes:0,failEncode:false,failDecode:false,blobURLs:0},manifest={};
 for(let i=0;i<40;i++)manifest[`assets/wardrobe/hair/test-${i}.png`]=true;
 class FakeImage{
  constructor(){this.naturalWidth=2;this.naturalHeight=2;}
  async decode(){if(this.src.startsWith('data:')){state.dataDecodes++;if(state.failDecode){state.failDecode=false;throw Error('decode interrupted');}}}
 }
 const context={window:{PalataOutlineManifest:manifest},URL,Image:FakeImage,Uint8Array,Map,Math,Object,Promise,console:{warn(){}},
  FileReader:class{readAsDataURL(blob){this.result='data:image/png;base64,'+Buffer.from(blob.source).toString('base64');queueMicrotask(()=>this.onload());}},
  document:{baseURI:'https://example.test/',createElement(){let original;return {getContext(){return {drawImage(i){original=i.src},getImageData(){return {width:2,height:2,data:new Uint8ClampedArray([110,120,130,255,110,120,130,255,110,120,130,255,110,120,130,255])}},putImageData(){}}},toBlob(cb){state.encodes++;if(state.deferNextEncode){state.deferNextEncode=false;state.deferredEncode=cb;}else if(state.failEncode){state.failEncode=false;queueMicrotask(()=>cb(null));}else queueMicrotask(()=>cb({source:original}));}};}}};
 vm.createContext(context);vm.runInContext(fs.readFileSync('outline-finish.js','utf8'),context);
 return {api:context.window.PalataOutline,state,original:new FakeImage(),path:i=>`assets/wardrobe/hair/test-${i}.png`};
}
test('an encoder failure falls back for that draw and retries after recovery',async()=>{
 const {api,state,path}=browser();state.failEncode=true;
 assert.equal(await api.source(path(0)),path(0));
 assert.match(await api.source(path(0)),/^data:image\/png;base64,/);assert.equal(state.encodes,2);
});
test('a decoder failure returns the loaded original and does not poison later retries',async()=>{
 const {api,state,path,original}=browser();state.failDecode=true;
 assert.equal(await api.bitmap(original,path(0)),original);
 assert.notEqual(await api.bitmap(original,path(0)),original);assert.equal(state.encodes,1);assert.equal(state.dataDecodes,2);
});
test('source cache retains only32 recently used sources and existing returned URLs stay usable',async()=>{
 const {api,state,path}=browser();const old=await api.source(path(0));
 for(let i=1;i<35;i++)await api.source(path(i));
 assert.equal(state.encodes,35);await api.source(path(34));assert.equal(state.encodes,35);
 assert.equal(await api.source(path(0)),old);assert.equal(state.encodes,36);assert.match(old,/^data:image\/png;base64,/);
});
test('decoded-image cache is bounded independently from the source cache',async()=>{
 const {api,state,path,original}=browser();await api.bitmap(original,path(0));
 for(let i=1;i<35;i++){await api.bitmap(original,path(i));await api.source(path(0));}
 assert.equal(state.encodes,35);assert.equal(state.dataDecodes,35);
 await api.bitmap(original,path(0));assert.equal(state.encodes,35);assert.equal(state.dataDecodes,36);
});

test('an evicted late failure cannot remove a newer successful retry',async()=>{
 const {api,state,path}=browser();state.deferNextEncode=true;
 const old=api.source(path(0));
 while(!state.deferredEncode)await new Promise(resolve=>setImmediate(resolve));
 for(let i=1;i<35;i++)await api.source(path(i));
 const current=await api.source(path(0));const count=state.encodes;
 state.deferredEncode(null);assert.equal(await old,path(0));
 assert.equal(await api.source(path(0)),current);assert.equal(state.encodes,count);
});
