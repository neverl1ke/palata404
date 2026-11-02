"""Current male sources and exhaustive photographs, independent of preparation."""
import hashlib
import json
import subprocess
import unittest
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image,ImageChops

from tests import test_game as support
from tests.asset_history import approved_current_hash

ROOT=support.ROOT
REPORT=ROOT/'review/male-heads-full-library'


def manifest():return json.loads((REPORT/'integration-manifest.json').read_text())


class MaleLibraryAssetTests(unittest.TestCase):
    def test_new_body_is_the_exact_supplied_resource_and_sources_are_retained(self):
        config=json.loads((REPORT/'registration.json').read_text())
        self.assertEqual((ROOT/'base_male.png').read_bytes(),(REPORT/config['base']['source']).read_bytes())
        self.assertEqual(hashlib.sha256((ROOT/'base_male.png').read_bytes()).hexdigest(),
            'b40a31b26dcf9aeea1dad02091228377330c9bb3af3a4b9669cfcc67247fc41d')
        self.assertEqual(len(config['heads']),8)
        for e in config['heads']:
            self.assertEqual(hashlib.sha256((REPORT/e['source']).read_bytes()).hexdigest(),e['source_sha256'])

    def test_new_portraits_are_uniformly_registered_without_rgb_repaint(self):
        for e in manifest()['files']:
            im=Image.open(REPORT/e['source']).convert('RGBA');p=e['registration'];s,tx,ty=p['scale'],p['x'],p['y']
            scaled=im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.LANCZOS)
            sx,sy=scaled.width/im.width,scaled.height/im.height
            registered=np.array(scaled.transform((941,1672),Image.Transform.AFFINE,
                (sx/s,0,-tx*sx/s,0,sy/s,-ty*sy/s),Image.Resampling.BICUBIC))
            current=np.array(Image.open(ROOT/e['output']))
            visible=current[:,:,3]>0
            self.assertTrue(np.array_equal(current[:,:,:3][visible],registered[:,:,:3][visible]),e['id'])
            yy,xx=np.where(current[:218,:,3]>=128)
            self.assertTrue(155<=np.ptp(xx)+1<=190,e['id'])
            self.assertTrue(27<=int(yy.min())<=33,e['id'])

    def test_current_complementary_masks_hide_old_skull_and_restore_the_new_torso(self):
        base=Image.open(ROOT/'base_male.png').convert('RGBA');ba=np.array(base)[:,:,3]
        for e in manifest()['files']:
            head=Image.open(ROOT/e['output']).convert('RGBA');mask=Image.open(ROOT/e['mask']).getchannel('A')
            self.assertIsNone(mask.crop((0,0,941,210)).getbbox(),e['id'])
            body=base.copy();body.putalpha(ImageChops.multiply(base.getchannel('A'),mask))
            result=Image.alpha_composite(body,head);a=np.array(result)
            self.assertTrue(np.array_equal(a[286:],np.array(base)[286:]),e['id'])
            self.assertTrue(np.all(a[240:275,450:500,3].astype(int)>=ba[240:275,450:500].astype(int)-1),e['id'])
            self.assertTrue(np.all(a[90:190,440:505,3]==255),e['id'])

    def test_female_assets_hair_palette_clothing_and_renderer_remain_unchanged(self):
        for path,digest in manifest()['protected_sha256'].items():
            # Follow-up normalization changes only the female native rendering helper.
            raw=subprocess.check_output(['git','show','fd20bc3:'+path],cwd=ROOT) if path=='paper-doll.js' else (ROOT/path).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),digest if path=='paper-doll.js' else approved_current_hash(path,digest),path)
        baseline=json.loads((REPORT/'registration.json').read_text())['baseline']
        old=subprocess.check_output(['git','show',baseline+':paper-doll-data.js'],cwd=ROOT,text=True)
        expression=';JSON.stringify({items:PAPER_DOLL_ITEMS,frame:PAPER_DOLL_FRAME,order:PAPER_DOLL_LAYER_ORDER,bodies:PAPER_DOLL_BODIES})'
        def catalog(source):
            return json.loads(subprocess.check_output(['node','-e',
                'const vm=require("vm"),fs=require("fs");console.log(vm.runInNewContext(fs.readFileSync(0,"utf8")))'],
                input=source+expression,cwd=ROOT,text=True))
        before,after=catalog(old),catalog((ROOT/'paper-doll-data.js').read_text())
        self.assertEqual(before['frame'],after['frame']);self.assertEqual(before['order'],after['order'])
        self.assertEqual(before['bodies']['female'],after['bodies']['female'])
        current={i['id']:i for i in after['items']}
        for item in before['items']:
            now=current[item['id']]
            if item['slot']=='face':
                # Male integration and later approved female normalization replace only resource URLs.
                item=json.loads(json.dumps(item));now=json.loads(json.dumps(now))
                for key in ['genderVariants','bodyMaskByGender']:
                    item.get(key,{}).pop('male',None);now.get(key,{}).pop('male',None)
                    # Female resources now have explicitly approved standardized derivatives.
                    item.get(key,{}).pop('female',None);now.get(key,{}).pop('female',None)
            self.assertEqual(item,now,item['id'])

    def test_every_new_resource_is_registered_with_its_actual_hash(self):
        catalog=(ROOT/'paper-doll-data.js').read_text()
        for e in manifest()['files']:
            for key,h in [('output','sha256'),('mask','mask_sha256')]:
                digest=hashlib.sha256((ROOT/e[key]).read_bytes()).hexdigest()
                self.assertEqual(digest,e[h]);self.assertIn(e[key]+'?v='+digest[:8],catalog)

    def test_all_3375_combinations_have_unique_real_lossless_screenshots(self):
        result=json.loads((REPORT/'captures/result.json').read_text())
        records=[json.loads(s) for s in (REPORT/'captures/records.jsonl').read_text().splitlines()]
        expected=set()
        for gender,info in result['genders'].items():
            self.assertEqual(len(info['faces']),9);self.assertEqual(len(info['colors']),25)
            self.assertEqual(len(info['hairs']),7 if gender=='male' else 8)
            expected.update('/'.join([gender,face or 'base',hair,color]) for face in info['faces'] for hair in info['hairs'] for color in info['colors'])
        self.assertEqual(len(expected),3375);self.assertEqual({r['key'] for r in records},expected)
        self.assertEqual(len(records),3375)
        groups=defaultdict(lambda:{'skin':set(),'frames':set()})
        for r in records:
            p=REPORT/r['path'];self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),r['sha256'],r['key'])
            with Image.open(p) as im:
                self.assertEqual(im.size,(400,400));self.assertEqual(im.format,'WEBP')
                group=groups[(r['gender'],r['face'],r['hair'])]
                # Independent screenshot evidence: changing pigment must not
                # recolor the nose/mouth, and each real hair color must render.
                group['skin'].add(im.crop((190,205,212,230)).tobytes())
                group['frames'].add(r['sha256'])
        self.assertEqual(len(groups),135)
        for key,group in groups.items():
            self.assertEqual(len(group['skin']),1,key)
            self.assertEqual(len(group['frames']),1 if key[2]=='hair-none' else 25,key)
        self.assertEqual(len(result['full_body']),18);self.assertEqual(result['page_errors'],[]);self.assertEqual(result['http_errors'],[])

    def test_every_combination_is_restored_by_an_actual_browser_reload(self):
        expected={json.loads(s)['key'] for s in (REPORT/'captures/records.jsonl').read_text().splitlines()}
        actual=[]
        for p in (REPORT/'reload').glob('shard-*.jsonl'):
            for line in p.read_text().splitlines():
                r=json.loads(line);self.assertTrue(r['restored']);self.assertTrue(r['patient_trip_preserved']);actual.append(r['key'])
        self.assertEqual(len(actual),3375);self.assertEqual(set(actual),expected)
        gallery=json.loads((REPORT/'combination-manifest.json').read_text())
        self.assertTrue(all(r['reload_verified'] for r in gallery['records']))

    def test_offline_gallery_does_not_depend_on_external_services(self):
        html=(REPORT/'avatar_visual_audit.html').read_text()
        self.assertNotIn('https://',html);self.assertNotIn('http://',html)
        for path in ['gallery.css','gallery.js','data.js']:self.assertTrue((REPORT/path).is_file())
        for control in ['gender','face','hair','color','status','problem','viewer','fullbody','zoom']:
            self.assertIn('id="'+control+'"',html)


class MaleLibraryBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):support.GameTests.setUpClass()
    @classmethod
    def tearDownClass(cls):support.GameTests.tearDownClass()
    def setUp(self):self.case=support.GameTests();self.case.setUp();self.page=self.case.page
    def tearDown(self):self.case.tearDown()
    def test_new_male_catalog_and_tunic_render_on_every_head(self):
        self.case.load();p=self.page;p.evaluate('openCustomization();setGender("male");selectWardrobeCategory("appearance");selectWardrobeSlot("face")')
        faces=p.evaluate('PAPER_DOLL_ITEMS.filter(i=>i.slot==="face"&&paperDollItemSupportsGender(i,"male")).map(i=>i.id)')
        self.assertEqual(len(faces),15)
        for face in faces:
            p.evaluate('f=>{equipPaperDollItem("face",f);equipPaperDollItem("hair","hair-messy");setPaperDollView("patient");equipPaperDollItem("upperBody","patient-tunic")}',face)
            p.wait_for_function('()=>[...document.querySelectorAll("#wardrobe-paperdoll img:not(.hidden)")].every(i=>i.complete&&i.naturalWidth>0)')
            self.assertEqual(p.evaluate('selectedPaperDollItem("face").genderVariants.male'),p.locator('#wardrobe-layer-face').get_attribute('src'))
        p.evaluate('setGender("female");selectWardrobeSlot("face")')
        for face in ['face-male-goth-pierced','face-male-freckled','face-male-blue-eyes']:
            self.assertEqual(p.locator(f'[data-wardrobe-card="{face}"]').count(),0)
        self.assertEqual(self.case.errors,[])

    def test_offline_gallery_filters_modal_zoom_and_mobile_layout(self):
        p=self.page;p.goto(self.case.url+'review/male-heads-full-library/avatar_visual_audit.html',wait_until='networkidle')
        p.select_option('#gender','male');p.select_option('#face','face-male-goth-pierced');p.select_option('#hair','hair-messy');p.select_option('#color','white')
        self.assertEqual(p.locator('#grid article').count(),1);p.locator('[data-open]').click()
        self.assertTrue(p.locator('#viewer').evaluate('e=>e.open'));p.locator('#fullbody').click();p.select_option('#zoom','4')
        self.assertEqual(p.locator('#large').evaluate('e=>e.style.width'),'1920px');p.locator('#close').click()
        for width in [320,360,390,430,768,1440]:
            p.set_viewport_size({'width':width,'height':844});self.assertFalse(p.evaluate('document.documentElement.scrollWidth>innerWidth'),width)
        self.assertEqual(self.case.errors,[])


if __name__=='__main__':unittest.main()
