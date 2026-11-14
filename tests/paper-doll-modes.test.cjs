const {test}=require('node:test');const assert=require('node:assert/strict');const vm=require('node:vm');const fs=require('node:fs');
function context(){const c={window:{},Set,Map,console,inventory:[],equippedGear:{},normalizeHairColor:()=> 'original',PAPER_DOLL_LAYER_ORDER:['baseBody','weapon','armor','headwear','upperBody','hair','beard'],PAPER_DOLL_ITEMS:[{id:'gear-aks',slot:'weapon',availableByDefault:true},{id:'gear-knife',slot:'weapon',availableByDefault:true},{id:'shirt',slot:'upperBody',availableByDefault:true},{id:'hair-none',slot:'hair',availableByDefault:true}],PAPER_DOLL_RETIRED_FACES:new Set(),PAPER_DOLL_LEGACY_ITEMS:{}};vm.createContext(c);vm.runInContext(fs.readFileSync('paper-doll.js','utf8'),c);return c;}
test('mixed old patient equipment moves to combat without replacing an existing combat choice',()=>{
 const c=context();let s=c.normalizePaperDollState({schemaVersion:2,patientLoadout:{weapon:'gear-aks',upperBody:'shirt'},combatLoadout:{},appearance:{}});assert.equal(s.patientLoadout.weapon,null);assert.equal(s.combatLoadout.weapon,'gear-aks');assert.equal(s.patientLoadout.upperBody,'shirt');
 s=c.normalizePaperDollState({schemaVersion:2,patientLoadout:{weapon:'gear-aks'},combatLoadout:{weapon:'gear-knife'},appearance:{}});assert.equal(s.patientLoadout.weapon,null);assert.equal(s.combatLoadout.weapon,'gear-knife');
});
test('patient gear cannot be equipped while ordinary patient clothes remain valid',()=>{
 const c=context();c.paperDollState={activeViewMode:'patient',patientLoadout:{weapon:null}};assert.equal(c.equipPaperDollItem('weapon','gear-aks'),false);assert.equal(c.isCombatPaperDollItem(c.PAPER_DOLL_ITEMS[2]),false);
});
