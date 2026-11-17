#!/usr/bin/env python3
"""Regenerate source-native Ward 406 cloth masks and renderer geometry.

Authored outlines are traced against the approved 1536x1024 Patient master.
Only single-channel masks and vector geometry are generated; no room, avatar or
artwork RGB is painted, transformed or resized. Geometry remains a review
candidate until its rendered local artwork receives explicit approval.

Run: python tools/prepare-quest-bed-masks.py
Optional diagnostics: --proof-dir /dev/shm/quest-bed-mask-review
"""
from pathlib import Path
import json, hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/quest-bed';S=2;W=1536;H=1024
import argparse,re,math
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--proof-dir',type=Path,help='Optional destination for L-mode mask diagnostics, for example /dev/shm/quest-bed-mask-review')
args=parser.parse_args();REVIEW=args.proof_dir
OUT.mkdir(parents=True,exist_ok=True)
if REVIEW:REVIEW.mkdir(parents=True,exist_ok=True)
pillow='M216 582 C242 574 271 570 299 569 C335 565 375 564 404 570 C433 580 455 599 477 619 C488 630 492 638 501 644 C471 649 421 659 375 666 C344 673 325 678 313 676 C300 674 289 664 276 652 C255 634 240 616 228 600 C222 593 218 587 216 582 Z'
base='M244 663 L501 643 C575 647 674 656 760 662 L1038 711 L1038 775 L901 861 L876 888 C719 865 574 841 430 819 L245 794 Z'
blanket='M556 739 C572 726 603 711 641 698 C686 682 744 669 789 655 C831 654 916 660 965 673 L1043 687 L1040 712 C1005 725 971 746 939 768 L861 828 C802 831 661 818 584 805 C563 803 552 797 553 786 C553 779 558 773 560 769 C554 766 552 757 556 750 C555 745 555 741 556 738 Z'
front='M875 892 L875 791 C874 759 877 732 889 711 C894 702 902 696 909 692 L922 708 C910 716 904 730 902 752 L901 890 Z'
back='M1023 650 C1044 646 1052 669 1055 697 L1058 850 L1039 851 L1035 701 C1033 681 1028 672 1018 672 Z'
def points(d):
 # The authored source paths deliberately use only M/L/C/Z. Keeping this small
 # sampler local makes regeneration depend only on the pinned Pillow/numpy
 # development dependencies, rather than an extra vector library.
 tokens=re.findall(r'[MLCZ]|-?\d+(?:\.\d+)?',d)
 out=[];i=0;current=0j;start=0j
 def pair():
  nonlocal i
  point=complex(float(tokens[i]),float(tokens[i+1]));i+=2;return point
 while i<len(tokens):
  command=tokens[i];i+=1
  if command=='M':
   current=pair();start=current;out.append((current.real*S,current.imag*S))
  elif command=='L':
   end=pair();count=max(2,math.ceil(abs(end-current)*S/2))
   for n in range(1,count+1):
    p=current+(end-current)*n/count;out.append((p.real*S,p.imag*S))
   current=end
  elif command=='C':
   p0=current;p1=pair();p2=pair();p3=pair()
   count=max(2,math.ceil((abs(p1-p0)+abs(p2-p1)+abs(p3-p2))*S/2))
   for n in range(1,count+1):
    t=n/count;p=(1-t)**3*p0+3*(1-t)**2*t*p1+3*(1-t)*t*t*p2+t**3*p3
    out.append((p.real*S,p.imag*S))
   current=p3
  elif command=='Z':
   current=start;out.append((start.real*S,start.imag*S))
  else:raise ValueError('Unsupported authored path command: '+command)
 return out
def polygon(draw,d,fill):draw.polygon(points(d),fill=fill)
def line(draw,d,width):
 pts=points(d);draw.line(pts,fill=0,width=round(width*S),joint='curve')
 r=width*S/2
 # Round discs along every sample prevent subpixel cracks in protective tubes.
 for x,y in pts:draw.ellipse((x-r,y-r,x+r,y+r),fill=0)
def contour_path(image):
 a=np.asarray(image)>127
 top=a & ~np.vstack([np.zeros((1,W*S),bool),a[:-1]])
 bottom=a & ~np.vstack([a[1:],np.zeros((1,W*S),bool)])
 left=a & ~np.column_stack([np.zeros((H*S,1),bool),a[:,:-1]])
 right=a & ~np.column_stack([a[:,1:],np.zeros((H*S,1),bool)])
 edges={}
 def add(start,end):edges.setdefault(start,[]).append(end)
 for y,x in np.argwhere(top):add((int(x),int(y)),(int(x+1),int(y)))
 for y,x in np.argwhere(right):add((int(x+1),int(y)),(int(x+1),int(y+1)))
 for y,x in np.argwhere(bottom):add((int(x+1),int(y+1)),(int(x),int(y+1)))
 for y,x in np.argwhere(left):add((int(x),int(y+1)),(int(x),int(y)))
 loops=[]
 while edges:
  start=next(iter(edges));here=start;loop=[start];previous=(start[0]-1,start[1])
  while True:
   choices=edges[here]
   if len(choices)>1:
    incoming=(here[0]-previous[0],here[1]-previous[1])
    def rank(p):
     outgoing=(p[0]-here[0],p[1]-here[1]);cross=incoming[0]*outgoing[1]-incoming[1]*outgoing[0];dot=incoming[0]*outgoing[0]+incoming[1]*outgoing[1]
     return 3 if cross>0 else 2 if dot>0 else 1 if cross<0 else 0
    nxt=max(choices,key=rank)
   else:nxt=choices[0]
   choices.remove(nxt)
   if not choices:del edges[here]
   previous,here=here,nxt
   if here==start:break
   loop.append(here)
  # Exact collinear simplification keeps every half-pixel contour corner.
  simple=[]
  for i,b in enumerate(loop):
   a0=loop[i-1];c=loop[(i+1)%len(loop)]
   if (b[0]-a0[0])*(c[1]-b[1])!=(b[1]-a0[1])*(c[0]-b[0]):simple.append(b)
  if len(simple)>=3:loops.append(simple)
 return ' '.join('M'+' L'.join(f'{x/S:g} {y/S:g}' for x,y in loop)+' Z' for loop in loops)
mask=Image.new('L',(W*S,H*S),0);draw=ImageDraw.Draw(mask);polygon(draw,base,255)
for d in [pillow,blanket,front,back]:polygon(draw,d,0)
for d,width in [('M902 710 C942 687 990 669 1026 656',27),('M929 695 L929 847',11),('M961 681 L962 827',14),('M990 670 L991 810',12),('M1017 663 L1019 792',12),('M896 869 L1041 778',11)]:line(draw,d,width)
sheet=contour_path(mask)
# A tiny proof image is mask-only; the original RGB is never edited.
if REVIEW:mask.resize((W,H),Image.Resampling.LANCZOS).save(REVIEW/'sheet-mask.png')
if REVIEW:
 pillowMask=Image.new('L',(W*S,H*S),0);polygon(ImageDraw.Draw(pillowMask),pillow,255);pillowMask.resize((W,H),Image.Resampling.LANCZOS).save(REVIEW/'pillow-mask.png')
geo={'version':1,'status':'review-candidate; conservative hand trace, inspect generated overlay boundaries before approval','width':W,'height':H,'crop':{'x':180,'y':450,'width':940,'height':530},'masks':{'sheet':sheet,'pillowcase':pillow},'fillRule':'evenodd','zones':{'sheet':{'x':275,'y':735,'width':260,'height':100},'pillowcase':{'x':235,'y':580,'width':260,'height':90}},'zoneCenters':{'sheet':[405,785],'pillowcase':[365,625]},'pending':{'sheet':{'x':690,'y':688,'width':150,'height':62},'pillowcase':{'x':705,'y':671,'width':125,'height':45}},'source':{'master':str(ROOT.parent/'generated_images/exec-47dfaf67-18e0-4939-9741-f5f037741bbf.png'),'runtime':'assets/quest-world/ward406-patient.webp','sha256':hashlib.sha256((ROOT/'assets/quest-world/ward406-patient.webp').read_bytes()).hexdigest()},'notes':['Mask coordinates are source-native; no avatar or room RGB changes.','Sheet path subtracts pillow, brown folded blanket, nightstand edge and authored footboard posts/bars.','No RGB blur; sheet mask sampled at half-pixel precision for stable vector clipping.','Conservative cloth-edge trace still needs visual review with generated bare mattress; narrow contact-shadow rims may retain original fabric.','Do not use bare overlays until explicit current-order preparationStarted; never dirty a previously prepared bed merely by accepting a repeat order.','Final placement removes overlays to restore the existing canonical base exactly.']}
(OUT/'geometry.json').write_text(json.dumps(geo,ensure_ascii=False,indent=2)+'\n')
(OUT/'geometry.js').write_text('/* Source-native bed geometry; art-review candidate, not automatic artwork approval. */\nwindow.PalataQuestBedGeometry=Object.freeze('+json.dumps(geo,ensure_ascii=False,separators=(',',':'))+');\n')
svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1536 1024"><title>Ward 406 source-native visible-cloth masks; review candidate</title><defs><clipPath id="quest-bed-sheet-visible" clipPathUnits="userSpaceOnUse"><path d="'+sheet+'" fill-rule="evenodd" clip-rule="evenodd"/></clipPath><clipPath id="quest-bed-pillowcase-visible" clipPathUnits="userSpaceOnUse"><path d="'+pillow+'"/></clipPath></defs></svg>\n'
(OUT/'masks.svg').write_text(svg)
print('geometry',len(sheet),'sheet path chars','area native',int((np.asarray(mask)>127).sum()/S/S))
