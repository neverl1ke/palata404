"""Final local corrections over the accepted4f46b15 prototype; no source edits."""
from pathlib import Path
import json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,str(ROOT/'tools/prepare-avatar-wrist-patches.py')],cwd=ROOT,check=True)
path=ROOT/'avatar-core/rigs/female_rig.json'
rig=json.loads(path.read_text())
rig['skinMeshes']['left']['shoulderArcBlend']={
    'startAngle':.75,'fullAngle':1.0,'fadeStart':80,'fadeEnd':130,'fadeOuterX':[689,725],
    'contourLift':{'centre':[667,405],'radius':[56,70],'pixels':8}}
path.write_text(json.dumps(rig,indent=2)+'\n')
print('Prepared local female raised-shoulder surface correction; stance/joints untouched.')
