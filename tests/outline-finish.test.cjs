const {test}=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const vm=require('node:vm');
function api(){const context={window:{},URL,document:{baseURI:'https://example.test/'},Uint8Array,Map,Math,Object,Promise};vm.createContext(context);vm.runInContext(fs.readFileSync('outline-finish.js','utf8'),context);return context.window.PalataOutline;}
test('edge processing leaves opaque interior texture and transparent support intact',()=>{
 const data=new Uint8ClampedArray(24*24*4);
 for(let y=0;y<24;y++)for(let x=0;x<24;x++){const i=(y*24+x)*4;data[i]=x%2?220:90;data[i+1]=120;data[i+2]=70;data[i+3]=x>2&&x<21&&y>2&&y<21?255:0;}
 const before=data.slice();api().process({width:24,height:24,data});
 for(let i=0;i<data.length;i+=4)if(!before[i+3])assert.equal(data[i+3],0);
 for(let y=9;y<15;y++)for(let x=9;x<15;x++){const i=(y*24+x)*4;assert.deepEqual(data.slice(i,i+4),before.slice(i,i+4));}
 const edge=(4*24+3)*4;assert.ok(data[edge]<before[edge]);
});
test('face and body sources bypass processing',async()=>{
 const p=api();for(const path of ['base_male.png','base_female.png','assets/wardrobe/faces/test.png'])assert.equal(await p.source(path),path);
});
