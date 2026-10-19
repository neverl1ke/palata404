"""Current approved eight-face release: geometry, identity, assets and real UI."""
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops
from scipy import ndimage as ndi

from tests import test_game as support

ROOT = support.ROOT
REPORT = ROOT/'review/female-faces-integration'
spec = importlib.util.spec_from_file_location('female_prepare', ROOT/'tools/prepare-female-faces.py')
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


def manifest():
    return json.loads((REPORT/'integration-manifest.json').read_text())


class FemaleFacesAssetTests(unittest.TestCase):
    def test_all_sources_and_final_resources_are_exact_and_versioned(self):
        data = manifest()
        self.assertEqual(len(data['files']), 8)
        self.assertEqual(len({e['id'] for e in data['files']}), 8)
        for e in data['files']:
            self.assertEqual(prepare.sha((REPORT/e['source']).read_bytes()), e['source_sha256'])
            for k, h in [('output','sha256'),('mask','mask_sha256')]:
                self.assertEqual(prepare.sha((ROOT/e[k]).read_bytes()), e[h])
                with Image.open(ROOT/e[k]) as im:
                    self.assertEqual(im.mode,'RGBA')
                    self.assertEqual(im.size,(941,1672))
                self.assertIn(e[k]+'?v='+e[h][:8], (ROOT/'paper-doll-data.js').read_text())

    def test_registered_approved_portrait_features_and_piercings_are_preserved(self):
        for e in manifest()['files']:
            # Reproduce registration from the actual supplied image; zero pixel
            # difference inside the portrait rules out a generated replacement.
            im = Image.open(REPORT/e['source']).convert('RGBA')
            p = e['registration'];s,tx,ty = p['scale'],p['x'],p['y']
            if s != 1 or tx != 0 or ty != 0:
                scaled = im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.LANCZOS)
                sx,sy = scaled.width/im.width,scaled.height/im.height
                im = scaled.transform((941,1672),Image.Transform.AFFINE,
                    (sx/s,0,-tx*sx/s,0,sy/s,-ty*sy/s),Image.Resampling.BICUBIC)
            a=np.array(Image.open(ROOT/e['output']))
            expected_core=np.array(im)[80:210,425:525]
            opaque=expected_core[:,:,3]>=230
            self.assertTrue(np.array_equal(a[80:210,425:525,:3][opaque],expected_core[:,:,:3][opaque]),e['kind'])
            # Ears and their ornaments keep all well-covered source pixels;
            # only low-alpha matte may be corrected at the very outside edge.
            expected=np.array(im)[:218]
            ears=np.zeros(expected.shape[:2],bool)
            ears[110:210,375:425]=True;ears[110:210,525:575]=True
            core=ears&(expected[:,:,3]>=230)
            self.assertTrue(np.array_equal(a[:218,:,:3][core],expected[:,:,:3][core]),e['kind'])

    def test_no_remote_alpha_noise_and_complete_head_silhouette(self):
        for e in manifest()['files']:
            a=np.array(Image.open(ROOT/e['output']))[:,:,3]
            roi=a[:215];remote=(roi>0)&(roi<=16)&(ndi.distance_transform_edt(roi<32)>4)
            self.assertEqual(int(remote.sum()),0,e['kind'])
            labels,n=ndi.label(a>0,np.ones((3,3)))
            peaks=ndi.maximum(a,labels,np.arange(1,n+1))
            self.assertFalse(np.any(peaks<=16),e['kind'])
            interior=ndi.distance_transform_edt(a[:218]>=128)>2
            self.assertTrue(np.all(a[:218][interior]==255),e['kind']+' translucent solid skin')
            yy,xx=np.where(a[:218]>=128)
            self.assertTrue(155<=xx.max()-xx.min()+1<=205,e['kind'])
            self.assertTrue(20<=yy.min()<=36,e['kind'])
            self.assertIsNone(Image.fromarray(a).crop((0,286,941,1672)).getbbox(),e['kind'])

    def test_complementary_masks_have_no_old_skull_holes_or_body_changes(self):
        base=Image.open(ROOT/'base_female.png').convert('RGBA')
        ba=np.array(base)[:,:,3]
        for e in manifest()['files']:
            head=Image.open(ROOT/e['output']).convert('RGBA')
            mask=Image.open(ROOT/e['mask']).getchannel('A')
            self.assertIsNone(mask.crop((0,0,941,210)).getbbox(),e['kind'])
            body=base.copy();body.putalpha(ImageChops.multiply(base.getchannel('A'),mask))
            result=Image.alpha_composite(body,head)
            aa=np.array(result)[:,:,3]
            self.assertEqual(ndi.label(aa>=128,np.ones((3,3)))[1],1,e['kind'])
            self.assertTrue(np.all(aa[250:288,445:505]>=ba[250:288,445:505]-1),e['kind'])
            self.assertIsNone(ImageChops.difference(result,base).crop((0,286,941,1672)).getbbox(),e['kind'])

    def test_all_other_approved_art_and_hair_placements_are_unchanged(self):
        data=manifest();authorized={e[k] for e in data['files'] for k in ['output','mask']}
        for rel,digest in data['before_sha256'].items():
            if rel not in authorized:
                self.assertEqual(prepare.sha((ROOT/rel).read_bytes()),digest,rel)
        import subprocess
        code="const fs=require('fs'),vm=require('vm');console.log(vm.runInNewContext(fs.readFileSync('paper-doll-data.js','utf8')+';JSON.stringify(PAPER_DOLL_ITEMS.filter(i=>i.slot===\"hair\"))'))"
        current=subprocess.check_output(['node','-e',code],cwd=ROOT,text=True)
        self.assertEqual(json.loads(current),data['hair_items_before'])


class FemaleFacesBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): support.GameTests.setUpClass()
    @classmethod
    def tearDownClass(cls): support.GameTests.tearDownClass()
    def setUp(self):
        self.case=support.GameTests();self.case.setUp();self.case.load();self.p=self.case.page
        self.http=[];self.p.on('response',lambda r:self.http.append(r.url) if r.status>=400 else None)
    def tearDown(self):
        self.assertEqual(self.http,[]);self.case.tearDown()

    def test_eight_female_choices_and_reload_preserve_each_appearance_and_loadout(self):
        self.p.evaluate('openCustomization();setGender("female");selectWardrobeSlot("face")')
        ids=[e['id'] for e in manifest()['files']]
        self.assertEqual(self.p.locator('[data-wardrobe-card]').count(),8)
        protected=self.p.evaluate('JSON.stringify({stats,inventory,equippedGear,patient:paperDollState.patientLoadout,combat:paperDollState.combatLoadout})')
        for face in ids:
            self.p.locator('[data-wardrobe-card="'+face+'"]').click()
            self.p.locator('[data-wardrobe-action="'+face+'"]').click()
            self.p.evaluate('equipPaperDollItem("hair","hair-bob-bangs");setHairColor("white")')
            self.p.reload(wait_until='networkidle')
            self.assertEqual(self.p.evaluate('paperDollState.appearance.face'),face)
            self.assertEqual(self.p.evaluate('paperDollState.appearance.hair'),'hair-bob-bangs')
            self.assertEqual(self.p.evaluate('paperDollState.appearance.hairColor'),'white')
            self.assertEqual(self.p.evaluate('JSON.stringify({stats,inventory,equippedGear,patient:paperDollState.patientLoadout,combat:paperDollState.combatLoadout})'),protected)
            self.p.evaluate('openCustomization();selectWardrobeSlot("face")')

    def test_female_only_faces_do_not_leak_to_male_or_bad_saved_state(self):
        for kind in ['ginger-soft','goth-septum','goth-black-lips']:
            self.p.evaluate('f=>{setGender("female");equipPaperDollItem("face",f);setGender("male");openCustomization();selectWardrobeSlot("face")}','face-'+kind)
            self.assertIsNone(self.p.evaluate('paperDollState.appearance.face'))
            self.assertEqual(self.p.locator('[data-wardrobe-card]').count(),5)
            self.assertFalse(self.p.evaluate('f=>equipPaperDollItem("face",f)','face-'+kind))
            self.assertTrue(self.p.locator('#layer-face').evaluate('i=>i.classList.contains("hidden")'))

    def test_full_female_face_hair_matrix_has_correct_layers_and_palette(self):
        self.p.evaluate('setGender("female");setPaperDollView("combat");openCustomization();selectWardrobeSlot("hair")')
        protected=self.p.evaluate('JSON.stringify({stats,inventory,equippedGear})')
        hairs=self.p.evaluate('wardrobeVisibleItems().map(i=>i.id)')
        self.assertEqual(len(hairs),8)
        count=0
        for e in manifest()['files']:
            self.p.evaluate('f=>equipPaperDollItem("face",f)',e['id'])
            for hair in hairs:
                count+=1
                for color in ['original','black','white']:
                    self.p.evaluate('([h,c])=>{equipPaperDollItem("hair",h);setHairColor(c)}',[hair,color])
                    self.p.wait_for_function('''async()=>{
                        for(const i of document.querySelectorAll('#wardrobe-paperdoll img:not(.hidden)')){
                            if(!i.complete||!i.naturalWidth)return false;
                            if(i.paperHairRequest){const r=i.paperHairRequest,n=r.lastIndexOf('|');
                                if(i.getAttribute('src')!==await coloredHairSource(r.slice(0,n),r.slice(n+1),i.paperHairColorReference))return false;}
                        }return true;
                    }''')
                    for prefix in ['','wardrobe-']:
                        self.assertEqual(self.p.locator('#'+prefix+'layer-face').evaluate('i=>+getComputedStyle(i).zIndex'),1)
                        self.assertIn(e['output'],self.p.locator('#'+prefix+'layer-face').get_attribute('src'))
                        self.assertIn(e['mask'],self.p.locator('#'+prefix+'layer-body').evaluate('i=>i.style.maskImage'))
                        if hair!='hair-none':self.assertEqual(self.p.locator('#'+prefix+'layer-hair').evaluate('i=>+getComputedStyle(i).zIndex'),9)
        self.assertEqual(count,64)
        self.assertEqual(self.p.evaluate('JSON.stringify({stats,inventory,equippedGear})'),protected)
        self.assertEqual(self.p.evaluate('[...failedPaperDollImages]'),[])

    def test_mobile_last_face_is_selectable_and_patient_trip_outfits_survive(self):
        for w,h in [(320,568),(390,844),(768,1024)]:
            self.p.set_viewport_size({'width':w,'height':h})
            self.p.evaluate('openCustomization();setGender("female");selectWardrobeSlot("face");equipPaperDollItem("face",null)')
            card=self.p.locator('[data-wardrobe-card="face-goth-black-lips"]');card.scroll_into_view_if_needed();card.click()
            button=self.p.locator('[data-wardrobe-action="face-goth-black-lips"]');button.scroll_into_view_if_needed();button.click()
            self.assertEqual(self.p.evaluate('paperDollState.appearance.face'),'face-goth-black-lips')
            self.assertLessEqual(self.p.evaluate('document.documentElement.scrollWidth'),w)
            self.p.evaluate('setPaperDollView("combat");equipPaperDollItem("upperBody",null);setPaperDollView("patient");equipPaperDollItem("upperBody","patient-tunic")')
            self.p.reload(wait_until='networkidle')
            self.assertEqual(self.p.evaluate('paperDollState.patientLoadout.upperBody'),'patient-tunic')
            self.assertIsNone(self.p.evaluate('paperDollState.combatLoadout.upperBody'))
            self.assertEqual(self.p.evaluate('paperDollState.appearance.face'),'face-goth-black-lips')


if __name__=='__main__': unittest.main()
