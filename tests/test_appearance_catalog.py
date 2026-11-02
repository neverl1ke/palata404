"""Accepted appearance transfer: replay the preserved review recipes in the real UI."""
import json,hashlib,unittest,io
from pathlib import Path
from PIL import Image
from tests import test_game as game_tests
ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'review/appearance-catalog-20261102'

class AppearanceCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): game_tests.GameTests.setUpClass.__func__(cls)
    @classmethod
    def tearDownClass(cls): game_tests.GameTests.tearDownClass.__func__(cls)
    setUp=game_tests.GameTests.setUp
    tearDown=game_tests.GameTests.tearDown
    load=game_tests.GameTests.load

    def wait_hair(self):
        self.page.wait_for_function('''async()=>{
            const item=selectedPaperDollItem('hair'),g=paperDollState.selectedGender;
            if(item.id==='hair-none')return !document.getElementById('layer-hair').getAttribute('src');
            const part=paperDollItemLayers(item,g).find(p=>p.id==='front')||item;
            const source=part.genderVariants[g],color=paperDollState.appearance.hairColor;
            const fit=femaleHairFitFor(g,selectedPaperDollItem('face')?.id,item.id,part.placementByGender?.[g]??part.placement);
            const expected=fit?await fittedFemaleHairSource(source,color,part.colorReference,fit):await coloredHairSource(source,color,part.colorReference);
            return ['layer-hair','wardrobe-layer-hair'].every(id=>{const i=document.getElementById(id);return i.getAttribute('src')===expected&&i.complete&&i.naturalWidth>0&&!i.classList.contains('hidden')});
        }''')

    def test_catalog_assets_counts_and_approved_sources(self):
        self.load()
        counts=self.page.evaluate('Object.fromEntries(["male","female"].map(g=>[g,{heads:1+PAPER_DOLL_ITEMS.filter(i=>i.slot==="face"&&paperDollItemSupportsGender(i,g)).length,hair:PAPER_DOLL_ITEMS.filter(i=>i.slot==="hair"&&i.id!=="hair-none"&&paperDollItemSupportsGender(i,g)).length}]))')
        self.assertEqual(counts,{'male':{'heads':16,'hair':12},'female':{'heads':16,'hair':10}})
        manifest=json.loads((REVIEW/'manifest.json').read_text())
        for record in manifest['sources']+manifest['female_heads']:
            self.assertEqual(hashlib.sha256((ROOT/record['path']).read_bytes()).hexdigest(),record['sha256'])
        for path,digest in manifest['unchanged_bodies'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest)
        for item_id in manifest['excluded_ids']:
            self.assertFalse(self.page.evaluate('id=>PAPER_DOLL_ITEMS.some(i=>i.id===id)',item_id))
        paths=self.page.evaluate('PAPER_DOLL_ITEMS.flatMap(i=>[i,...(i.layers||[])]).flatMap(i=>Object.values(i.genderVariants||{}).concat(Object.values(i.bodyMaskByGender||{}),Object.values(i.thumbnailByGender||{})))')
        for path in paths:self.assertTrue((ROOT/path.split('?')[0]).is_file(),path)
        for folder in ['faces/male-approved-seven','hair/male-six']:
            for path in (ROOT/'assets/wardrobe'/folder).rglob('*.png'):
                with Image.open(path) as image:self.assertEqual(image.size,(256,256) if 'thumbnails' in path.parts else (941,1672))

    def test_approved_temple_fills_match_preview_and_follow_hair_color(self):
        import numpy as np
        approved=ROOT/'review/male-temple-gaps-approved-20261102'
        record=json.loads((approved/'integration.json').read_text())
        for entry in record['runtime_files']:
            self.assertEqual(hashlib.sha256((ROOT/entry['path']).read_bytes()).hexdigest(),entry['sha256'])
        for relative,digest in record['protected'].items():
            if relative not in ['paper-doll-data.js','index.html','assets/wardrobe/hair/male-six/mullet-rear.png']:
                self.assertEqual(hashlib.sha256((ROOT/relative).read_bytes()).hexdigest(),digest)
        self.load();self.page.set_viewport_size({'width':1200,'height':900})
        self.page.evaluate('openCustomization();setGender("male");setPaperDollView("combat");equipPaperDollItem("face","face-male-new-neutral");equipPaperDollItem("upperBody",null);setHairColor("original")')
        for column,hair in [(1,'hair-m6-mullet'),(3,'hair-m6-curly-crop')]:
            self.page.evaluate('''hair=>{equipPaperDollItem('hair',hair);document.getElementById('approved-board')?.remove();const c=document.createElement('div');c.id='approved-board';Object.assign(c.style,{position:'fixed',left:0,top:0,width:'250px',height:'310px',overflow:'hidden',background:'#97938d',zIndex:2147483647});const h=document.createElement('div');h.className='character-paperdoll';Object.assign(h.style,{position:'absolute',width:'941px',height:'1672px',left:'-348px',top:0});c.append(h);document.body.append(c);renderPaperDollAt(h,'approval-')}''',hair)
            self.page.wait_for_function('''()=>['approval-layer-body','approval-layer-face','approval-layer-hair','approval-layer-hair-rear'].every(id=>{const i=document.getElementById(id);return i&&i.complete&&i.naturalWidth===941&&!i.classList.contains('hidden')})''')
            actual=Image.open(io.BytesIO(self.page.locator('#approved-board').screenshot())).convert('RGB')
            expected=Image.open(approved/'approved-before-after.png').crop((column*250,38,column*250+250,348)).convert('RGB')
            self.assertTrue(np.array_equal(np.array(actual),np.array(expected)),hair+' differs from approved preview')
        self.page.evaluate('document.getElementById("approved-board").remove()')
        faces=self.page.evaluate('[null,...PAPER_DOLL_ITEMS.filter(i=>i.slot==="face"&&paperDollItemSupportsGender(i,"male")).map(i=>i.id)]')
        for face in faces:
            for hair in ['hair-m6-mullet','hair-m6-curly-crop']:
                for color in ['original','black','white']:
                    self.page.evaluate('([f,h,c])=>{equipPaperDollItem("face",f);equipPaperDollItem("hair",h);setHairColor(c)}',[face,hair,color]);self.wait_hair()
                    self.page.wait_for_function('''async()=>{const part=selectedPaperDollItem('hair').layers.find(p=>p.id==='rear');const expected=await coloredHairSource(part.genderVariants.male,paperDollState.appearance.hairColor,part.colorReference);return ['layer-hair-rear','wardrobe-layer-hair-rear'].every(id=>{const i=document.getElementById(id);return i&&i.getAttribute('src')===expected&&i.complete&&i.naturalWidth===941&&!i.classList.contains('hidden')})}''')
        self.page.set_viewport_size({'width':390,'height':844})
        for mode in ['patient','combat']:
            for hair in ['hair-m6-mullet','hair-m6-curly-crop']:
                self.page.evaluate('([m,h])=>{setPaperDollView(m);equipPaperDollItem("face","face-male-new-neutral");equipPaperDollItem("hair",h);setHairColor("original");selectWardrobeCategory("appearance");selectWardrobeSlot("hair")}',[mode,hair]);self.wait_hair()
                self.page.wait_for_function('()=>["layer-hair-rear","wardrobe-layer-hair-rear"].every(id=>{const i=document.getElementById(id);return i&&i.complete&&i.naturalWidth===941&&!i.classList.contains("hidden")})')
                self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
                self.page.screenshot(path=str(ROOT/'test-results'/f'approved-temple-{hair}-{mode}-mobile.png'))
        self.page.reload(wait_until='networkidle');self.page.evaluate('openCustomization()');self.wait_hair()
        self.assertEqual(self.page.evaluate('paperDollState.appearance.hair'),'hair-m6-curly-crop')
        for hair in ['hair-m6-mullet','hair-m6-curly-crop']:
            self.page.evaluate('h=>{equipPaperDollItem("hair",h);equipPaperDollItem("hair","hair-none")}',hair)
            self.assertEqual(self.page.locator('[data-paper-extra]').count(),0)
            self.page.evaluate('h=>{equipPaperDollItem("hair",h);setGender("female")}',hair)
            self.assertEqual(self.page.locator('[data-paper-extra]').count(),0)
            self.page.evaluate('setGender("male")')

    def test_female_pixels_match_saved_review_in_each_selected_color(self):
        self.load();self.page.evaluate('openCustomization();setGender("female");equipPaperDollItem("upperBody",null)')
        self.page.add_script_tag(content=(REVIEW/'approved-repair-reference.js').read_text())
        maps=json.loads((REVIEW/'approved-repair-maps.json').read_text())['faces']
        total=0
        for path in sorted((REVIEW/'female-settings').glob('F??-saved-settings.json')):
            accepted=json.loads(path.read_text());face=accepted['face_id']
            self.page.evaluate('id=>equipPaperDollItem("face",id)',face)
            for hair,setting in accepted['settings'].items():
                if setting.get('excluded') or hair in ['hair-none','hair-f5-long-waves','hair-f5-high-ponytail','hair-trial-braided-curls']:continue
                record=maps.get(accepted['face_code']+'-'+setting['hair_code'])
                colors=['black','ginger','white'] if record else ['black']
                for color in colors:
                    self.page.evaluate('([id,color])=>{equipPaperDollItem("hair",id);setHairColor(color)}',[hair,color]);self.wait_hair()
                    result=self.page.evaluate('''async v=>{
                        const item=selectedPaperDollItem('hair'),part=paperDollItemLayers(item,'female').find(p=>p.id==='front')||item;
                        const image=new Image();image.src=await coloredHairSource(part.genderVariants.female,v.color,part.colorReference);await image.decode();
                        const b=part.placementByGender?.female??part.placement??{x:0,y:0,width:941,height:1672},s=v.setting;
                        const l=v.record?.registration??{left:b.x,top:b.y,width:b.width,height:b.height,sx:s.horizontalScale,dx:(s.horizontalScale-1)*(b.x-s.anchorX)+s.shiftX,dy:s.downPixels};
                        const canvas=document.createElement('canvas');canvas.width=941;canvas.height=1672;const c=canvas.getContext('2d');
                        c.setTransform(l.sx,0,0,1,l.left+l.dx,l.top+l.dy);c.drawImage(image,0,0,l.width,l.height);c.resetTransform();
                        const expected=v.record?applyRegisteredHairRepair(canvas,v.record.mapping):canvas;
                        const url=expected.toDataURL('image/png');return ['layer-hair','wardrobe-layer-hair'].every(id=>document.getElementById(id).getAttribute('src')===url);
                    }''',{'setting':setting,'record':record,'color':color})
                    self.assertTrue(result,f"{accepted['face_code']} {hair} {color}");total+=1
            print(accepted['face_code'],'saved review replay passed',flush=True)
        self.assertEqual(total,224)
        self.assertLessEqual(self.page.evaluate('femaleHairFitCache.size'),24)

    def test_new_male_layers_and_female_races_reload_mobile(self):
        self.load();self.page.evaluate('openCustomization();setGender("male");setPaperDollView("combat")')
        faces=self.page.evaluate('PAPER_DOLL_ITEMS.filter(i=>i.id.startsWith("face-male-new-")).map(i=>i.id)')
        hairs=self.page.evaluate('PAPER_DOLL_ITEMS.filter(i=>i.id.startsWith("hair-m6-")).map(i=>({id:i.id,rear:i.layers?.length>1}))')
        for face in faces:
            for hair in hairs:
                self.page.evaluate('([f,h])=>{equipPaperDollItem("face",f);equipPaperDollItem("hair",h);setHairColor("original")}',[face,hair['id']]);self.wait_hair()
                self.assertEqual(self.page.locator('#layer-hair').evaluate('i=>i.paperHairFitKey'),'')
                if hair['rear']:
                    self.page.wait_for_function('()=>["layer-hair-rear","wardrobe-layer-hair-rear"].every(id=>{const i=document.getElementById(id);return i&&i.complete&&i.naturalWidth===941})')
                    for prefix in ['', 'wardrobe-']:self.assertEqual(self.page.locator('#'+prefix+'layer-hair-rear').evaluate('i=>getComputedStyle(i).zIndex'),'-1')
        self.page.evaluate('setGender("female");equipPaperDollItem("face","face-goth-black-lips");equipPaperDollItem("hair","hair-textured-short");setHairColor("black");equipPaperDollItem("face","face-goth-septum");setHairColor("white");setGender("male");equipPaperDollItem("hair","hair-m6-asymmetric-fringe");setGender("female");equipPaperDollItem("face","face-female-new-almond-eyes");equipPaperDollItem("hair","hair-textured-short");setHairColor("ginger")');self.wait_hair()
        self.assertEqual(self.page.locator('#layer-hair').evaluate('i=>i.paperHairFitKey'),'F17/hair-textured-short')
        self.assertEqual(self.page.locator('[data-paper-extra]').count(),0)
        self.page.reload(wait_until='networkidle');self.page.evaluate('openCustomization()');self.wait_hair()
        self.assertEqual(self.page.evaluate('paperDollState.appearance.face'),'face-female-new-almond-eyes')
        self.assertEqual(self.page.evaluate('paperDollState.appearance.hairColor'),'ginger')
        for gender in ['female','male']:
            self.page.evaluate('g=>{setGender(g);selectWardrobeCategory("appearance");selectWardrobeSlot("hair")}',gender)
            if gender=='male':self.page.evaluate('equipPaperDollItem("face","face-male-new-neutral");equipPaperDollItem("hair","hair-m6-asymmetric-fringe")')
            else:self.page.evaluate('equipPaperDollItem("face","face-female-new-light-eyes");equipPaperDollItem("hair","hair-f5-braided-updo")')
            self.wait_hair()
            for width,height in [(390,844),(1440,1000)]:
                self.page.set_viewport_size({'width':width,'height':height})
                for mode in ['patient','combat']:
                    self.page.evaluate('m=>setPaperDollView(m)',mode);self.wait_hair()
                    self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
                    output=ROOT/'test-results';output.mkdir(exist_ok=True);self.page.screenshot(path=str(output/f'appearance-main-{gender}-{width}-{mode}.png'))
        self.page.evaluate('equipPaperDollItem("hair","hair-none")');self.wait_hair();self.assertEqual(self.page.locator('[data-paper-extra]').count(),0)

if __name__=='__main__':unittest.main()
