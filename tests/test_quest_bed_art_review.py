"""Native browser rendering of isolated, explicitly unapproved K2 artwork.

These tests call the real shared renderer, rather than claiming a screenshot
montage is gameplay. Quest operations/save progression are covered separately.
"""
from pathlib import Path
from io import BytesIO
import hashlib
import json
import unittest

import numpy as np
from PIL import Image, ImageFilter
from tests import test_game as support

ROOT=Path(__file__).resolve().parents[1]
OUT=Path('/dev/shm/quest-bed-mask-review/browser')


class QuestBedArtReviewBrowserTests(unittest.TestCase):
    setUpClass=classmethod(support.GameTests.setUpClass.__func__)
    tearDownClass=classmethod(support.GameTests.tearDownClass.__func__)
    setUp=support.GameTests.setUp
    tearDown=support.GameTests.tearDown
    load=support.GameTests.load

    def ready(self):
        self.page.evaluate('''async()=>{
            await Promise.all([...document.querySelectorAll('#bed-render-probe image,#bed-render-probe img')].map(element=>{
                const image=new Image();image.src=element.getAttribute('href')||element.src;return image.decode();
            }));
            await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
        }''')

    def render(self,name,options=None,room_layer=False,plain=False,mask=None):
        self.page.evaluate('''({options,roomLayer,plain,mask})=>{
            document.getElementById('bed-render-probe')?.remove();
            const host=document.createElement('div');host.id='bed-render-probe';
            host.style.cssText='position:fixed;left:0;top:0;width:1536px;height:1024px;overflow:hidden;z-index:2147483647;isolation:isolate;background:#000;';
            const source='assets/quest-world/ward406-patient.webp';
            if(plain||roomLayer){const image=document.createElement('img');image.src=source;image.style.cssText='position:absolute;inset:0;width:1536px;height:1024px;max-width:none;object-fit:contain;filter:none;';host.append(image);}
            if(mask){
                const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');
                svg.setAttribute('viewBox','0 0 1536 1024');svg.setAttribute('width','1536');svg.setAttribute('height','1024');
                const defs=document.createElementNS(ns,'defs'),clip=document.createElementNS(ns,'clipPath'),path=document.createElementNS(ns,'path');
                clip.id='bed-probe-mask';clip.setAttribute('clipPathUnits','userSpaceOnUse');path.setAttribute('d',PalataQuestBedGeometry.masks[mask]);path.setAttribute('fill-rule','evenodd');path.setAttribute('clip-rule','evenodd');clip.append(path);defs.append(clip);svg.append(defs);
                const rect=document.createElementNS(ns,'rect');rect.setAttribute('width','1536');rect.setAttribute('height','1024');rect.setAttribute('fill','white');rect.setAttribute('clip-path','url(#bed-probe-mask)');svg.append(rect);host.append(svg);
            }else if(!plain){
                const svg=roomLayer?PalataQuestBedView.createRoomLayer(options):PalataQuestBedView.create(options);
                if(svg){svg.style.width='1536px';svg.style.height='1024px';host.append(svg);}
            }
            document.body.append(host);
        }''',{'options':options or {},'roomLayer':room_layer,'plain':plain,'mask':mask})
        self.ready()
        image=Image.open(BytesIO(self.page.locator('#bed-render-probe').screenshot())).convert('RGB')
        OUT.mkdir(parents=True,exist_ok=True);image.save(OUT/(name+'.png'))
        self.assertEqual(image.size,(1536,1024),'Native source coordinates were rescaled')
        return np.asarray(image)

    def test_unapproved_art_is_disabled_by_default_and_never_changes_trip(self):
        self.load()
        self.assertEqual(self.page.evaluate('''()=>({enabled:PalataQuestBedView.reviewEnabled(),
            closeup:PalataQuestBedView.create({preparationStarted:true,placed:[]}),
            layer:PalataQuestBedView.createRoomLayer({preparationStarted:true,placed:[]}),
            piece:PalataQuestBedView.createPiece('sheet','clean')})'''),
            {'enabled':False,'closeup':None,'layer':None,'piece':None})
        self.assertEqual(self.page.locator('[data-bed-art-review=true]').count(),0)
        self.load(query='?bed-art-review=1')
        self.assertTrue(self.page.evaluate('PalataQuestBedView.reviewEnabled()'))
        self.assertEqual(self.page.evaluate('''()=>({
            closeup:PalataQuestBedView.create({mode:'trip',preparationStarted:true,placed:[]}),
            layer:PalataQuestBedView.createRoomLayer({mode:'trip',preparationStarted:true,placed:[]})})'''),
            {'closeup':None,'layer':None})

    def test_native_shared_renderer_changes_only_cloth_and_restores_canonical_pixels(self):
        self.page.set_viewport_size({'width':1536,'height':1024});self.load(query='?bed-art-review=1')
        geometry=json.loads((ROOT/'assets/quest-bed/geometry.json').read_text())
        source=ROOT/geometry['source']['runtime'];source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
        self.assertEqual(source_hash,geometry['source']['sha256'])
        for name in ['assets/quest-world/ward406-patient.webp','assets/quest-bed-review/bare-mattress.webp']:
            with Image.open(ROOT/name) as native:
                self.assertEqual(native.size,(1536,1024),name+' was resized before rendering')
        canonical=self.render('00-canonical',plain=True)
        before=self.render('01-before-start',{'mode':'patient','preparationStarted':False,'placed':[],'prepared':True})
        final=self.render('02-both-placed',{'mode':'patient','preparationStarted':True,'placed':['sheet','pillowcase']})
        self.assertTrue(np.array_equal(before,canonical),'Starting a new order visually dirtied the earlier prepared bed')
        self.assertTrue(np.array_equal(final,canonical),'Finishing both placements did not restore exact canonical pixels')
        raw_masks={part:self.render('mask-'+part,mask=part) for part in ['sheet','pillowcase']}
        allowed={part:np.asarray(Image.fromarray((raw_masks[part].max(axis=2)>0).astype('uint8')*255).filter(ImageFilter.MaxFilter(3)))>0 for part in raw_masks}
        options=[('03-started',[],['sheet','pillowcase']),('04-sheet-placed',['sheet'],['pillowcase']),('05-pillowcase-placed',['pillowcase'],['sheet'])]
        results=[]
        for name,placed,unplaced in options:
            config={'mode':'patient','preparationStarted':True,'placed':placed}
            rendered=self.render(name,config)
            changed=np.any(rendered!=canonical,axis=2)
            permitted=np.logical_or.reduce([allowed[part] for part in unplaced])
            self.assertEqual(int(np.count_nonzero(changed&~permitted)),0,(name,'Artwork changed pixels outside source-native cloth masks + 1px AA'))
            self.assertGreater(int(np.count_nonzero(changed)),1000,(name,'Expected cloth transition is absent'))
            for part in placed:
                # Cloth masks have distinct ownership; completing one piece must
                # remove every change to that piece, not only hide its label.
                owner=allowed[part]&~np.logical_or.reduce([allowed[p] for p in unplaced])
                self.assertEqual(int(np.count_nonzero(changed&owner)),0,(name,part))
            room=self.render(name+'-room-layer',config,room_layer=True)
            self.assertTrue(np.array_equal(room,rendered),(name,'Room and close-up use different registration or masks'))
            # Independent source landmarks inside the authored blanket, table,
            # posts and vertical tubes must remain exact; these boxes are not
            # derived from the implementation's mask path.
            protected={'blanket':(650,715,820,780),'nightstand':(40,680,180,850),
                'front-post':(883,794,895,855),'tube-1':(927,784,931,820),
                'tube-2':(959,747,964,795),'top-rail':(972,673,978,678),
                'window':(920,220,1100,430)}
            for label,(x1,y1,x2,y2) in protected.items():
                self.assertFalse(changed[y1:y2,x1:x2].any(),(name,label,'Protected artwork was recoloured'))
            results.append({'state':name,'placed':placed,'changedPixels':int(changed.sum()),'outsideMaskChanges':int(np.count_nonzero(changed&~permitted))})
        self.assertIsNone(self.page.evaluate('PalataQuestBedView.createRoomLayer({mode:"patient",preparationStarted:false,placed:[]})'))
        self.assertIsNone(self.page.evaluate('PalataQuestBedView.createRoomLayer({mode:"patient",preparationStarted:true,placed:["sheet","pillowcase"]})'))
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),source_hash)
        OUT.joinpath('pixel-evidence.json').write_text(json.dumps({'viewport':[1536,1024],'sourceHash':source_hash,
            'method':'Actual shared renderer rendered by Chromium at native coordinates; no manual RGB painting. One native pixel is allowed around antialiased vector mask edges.',
            'beforeStartCanonicalPixelsEqual':bool(np.array_equal(before,canonical)),
            'bothPlacedCanonicalPixelsEqual':bool(np.array_equal(final,canonical)),'states':results},ensure_ascii=False,indent=2)+'\n')

    def test_closeup_crop_does_not_paint_over_surrounding_interface(self):
        self.page.set_viewport_size({'width':1000,'height':600});self.load(query='?bed-art-review=1')
        geometry=json.loads((ROOT/'assets/quest-bed/geometry.json').read_text())
        self.page.evaluate('''()=>{
            const host=document.createElement('div');host.id='bed-crop-canary';
            host.style='position:fixed;left:0;top:0;width:980px;height:570px;overflow:visible;z-index:2147483647;background:rgb(13,47,71);';
            const svg=PalataQuestBedView.create({mode:'patient',preparationStarted:true,placed:[],crop:true});
            svg.style.position='absolute';svg.style.left='20px';svg.style.top='20px';svg.style.width='940px';svg.style.height='530px';
            host.append(svg);document.body.append(host);
        }''')
        self.ready()
        svg=self.page.locator('#bed-crop-canary>svg')
        self.assertEqual(svg.get_attribute('viewBox'),' '.join(str(geometry['crop'][key]) for key in ['x','y','width','height']))
        image=Image.open(BytesIO(self.page.locator('#bed-crop-canary').screenshot())).convert('RGB')
        pixels=np.asarray(image);canary=np.array([13,47,71],dtype='uint8')
        # The host deliberately does not clip: only the real crop SVG can keep
        # a full-room image from leaking into these simulated UI margins.
        for edge in [pixels[:19],pixels[-19:],pixels[:,:19],pixels[:,-19:]]:
            self.assertTrue(np.all(edge==canary),'Full-room artwork overflowed its crop into the interface')
        OUT.mkdir(parents=True,exist_ok=True);image.save(OUT/'cropped-canary.png')
