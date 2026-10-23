"""Reverse ONLY the enumerated review-integration edits before legacy freezes.
Historical goldens and thresholds stay intact. Every unrelated byte still has
its original Git/hash expectation. New browser tests assert the added behavior.
"""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
GAME_PATHS={'index.html','paper-doll.js','wardrobe.js'}
LOCAL_SPACE_PATHS={'avatar-core/skin.mjs','avatar-core/pose-art.mjs'}
def pre_integration_bytes(path):
 data=(ROOT/path).read_bytes()
 if path not in GAME_PATHS|LOCAL_SPACE_PATHS:return data
 text=data.decode()
 if path=='paper-doll.js':text=text.replace('    window.avatarCoreGamePreview?.refresh();\n','')
 elif path=='wardrobe.js':
  text=text.replace('    const thumbnail = window.avatarCoreWeaponCatalog?.get(item?.id)?.thumbnail;\n    if (thumbnail && !failedPaperDollImages.has(thumbnail)) return thumbnail;\n','')
  text=text.replace("    if (window.avatarCoreWeaponCatalog?.has(item?.id)) return {state:'partial',text:'Оригінальна модель: приховані ділянки рукоятки потребують відновлення. Режим Avatar Core: ?avatarCore=1. Одяг із непідготовленими рукавами зберігає чинний рендер.'};\n",'')
 elif path=='index.html':
  text=text.replace('<script type="module">\nif (new URLSearchParams(location.search).get("avatarCore") === "1") import("./avatar-core/game-preview.mjs");\n</script>\n','')
  for name,version in [('paper-doll.js','female-head-standard-1'),('wardrobe.js','paper-targeted-1')]:text=text.replace(name+'?v=avatar-requested-1',name+'?v='+version)
 else:
  text=text.replace("import { pinnedTorsoPoint } from './torso-space.mjs';\n",'')
  if path.endswith('/skin.mjs'):
   text=text.replace('t = pinnedTorsoPoint(torso, p);','t = point(torso, p);')
   text=text.replace('        // A pinned torso is not affine near its upper/lower partition joins.\n        // Keep these cells in the vertex path instead of the affine batch.\n        if (vs.every((v) => v[2] === 0)) bone = null;',"        if (vs.every((v) => v[2] === 0)) bone = 'torso';")
  else:text=text.replace('t = pinnedTorsoPoint(matrices.torso, p),','t = point(matrices.torso, p),')
 return text.encode()
