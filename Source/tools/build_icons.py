"""Build original local SVG illustrations and the game's safe icon registry.

Run from any directory: python3 tools/build_icons.py. No third-party artwork,
fonts, network requests or image libraries are required.
"""
import json
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Shapes are drawn on a 64px canvas. Shared metal/paper colors match the clinic UI.
SHAPES = {
    'helmet': '<path d="M9 39V31a23 23 0 0 1 46 0v8H9Z"/><path d="M6 39h52v9H6Z"/><path d="M29 9h7v30h-7Z" fill="url(#paper)"/><path d="M15 48v7m34-7v7"/>',
    'bag': '<rect x="13" y="17" width="38" height="40" rx="9"/><path d="M24 17v-5h16v5M13 30h38"/><rect x="20" y="35" width="24" height="15" rx="3" fill="url(#paper)"/><path d="M28 28h8v7h-8Z" fill="#a94a3e"/>',
    'coat': '<path d="m23 9 9 6 9-6 13 10-7 14-5-4 3 27H19l3-27-5 4-7-14Z" fill="url(#paper)"/><path d="m23 9 9 14 9-14M32 23v33M22 40h6m8 0h6"/><path d="M31 29h2m-2 7h2m-2 7h2"/>',
    'map': '<path d="m5 15 18-7 18 7 18-7v41l-18 7-18-7-18 7Z" fill="url(#paper)"/><path d="M23 8v41m18-34v41M11 32l8-8 12 12 11-7 11 5" fill="none"/><circle cx="42" cy="29" r="5" fill="#a94a3e"/>',
    'clipboard': '<rect x="13" y="11" width="38" height="47" rx="4"/><rect x="19" y="18" width="26" height="33" rx="1" fill="url(#paper)"/><rect x="23" y="6" width="18" height="13" rx="3"/><path d="M25 29h15m-15 8h15m-15 8h9"/>',
    'swords': '<path d="M13 6 27 15 47 45 41 49 20 20Z" fill="url(#steel)"/><path d="m51 6-14 9-20 30 6 4 21-29Z" fill="url(#steel)"/><path d="m9 41 17 11m29-11L38 52M16 47l-6 10m36-10 7 10" stroke-width="6"/>',
    'people': '<circle cx="23" cy="20" r="10" fill="url(#paper)"/><path d="M6 54v-8a17 17 0 0 1 34 0v8Z"/><circle cx="45" cy="23" r="8" fill="url(#paper)"/><path d="M43 38a14 14 0 0 1 15 14v2H44"/>',
    'bell': '<path d="M13 45c6-8 5-14 5-21a14 14 0 0 1 28 0c0 7-1 13 5 21Z"/><path d="M9 45h46v6H9ZM27 52a5 5 0 0 0 10 0M29 7h6"/>',
    'mail': '<rect x="6" y="15" width="52" height="36" rx="4" fill="url(#paper)"/><path d="m7 17 25 20 25-20M7 49l17-17m33 17L40 32"/><circle cx="32" cy="37" r="5" fill="#a94a3e"/>',
    'gear': '<path d="m26 6 12 0 2 8 7 4 8-2 6 10-6 6v8l6 6-6 10-8-2-7 4-2 6H26l-2-6-7-4-8 2-6-10 6-6v-8l-6-6 6-10 8 2 7-4Z" transform="translate(1 -4) scale(.96)"/><circle cx="32" cy="31" r="12" fill="#30251d"/><circle cx="32" cy="31" r="6" fill="url(#steel)"/>',
    'brain': '<path d="M31 12c-7-7-17-2-17 7-11 2-11 17-4 20-3 13 15 19 22 10 7 9 25 3 22-10 7-3 7-18-4-20 0-9-10-14-17-7Z" fill="url(#paper)"/><path d="M32 12v37M14 20l9 6-2 9m-9 6 10-1 5 5m23-25-9 6 2 9m9 6-10-1-5 5" fill="none" stroke="#935944"/>',
    'lightning': '<path d="M35 5 13 35h16l-4 24 27-33H35Z" fill="url(#metal)"/><path d="m34 14-11 15h13" fill="none" stroke="#f5e0ac"/>',
    'coin': '<circle cx="32" cy="32" r="25"/><circle cx="32" cy="32" r="19" fill="none" stroke="#eddbb0"/><path d="M39 21c-11-8-23 8-9 12 15 4 3 20-8 12M32 15v34" fill="none" stroke-width="4"/>',
    'pills': '<path d="M12 42 34 13a12 12 0 0 1 19 15L31 57a12 12 0 0 1-19-15Z" fill="url(#paper)"/><path d="m23 28 19 15 11-15a12 12 0 0 0-19-15Z" fill="#a94a3e"/><path d="m38 17 7 5" stroke="#efc5a8"/>',
    'cash': '<rect x="5" y="14" width="54" height="37" rx="3" fill="#6a7959"/><path d="M12 20h40v25H12Z" fill="none" stroke="#d4d5a5"/><ellipse cx="32" cy="33" rx="10" ry="14" fill="url(#paper)"/><path d="M32 23v20m-5-15h9l-9 9h10" fill="none"/><path d="M17 30v5m30-5v5"/>',
    'heart': '<path d="M32 55 9 32C-7 11 22 0 32 19 42 0 71 11 55 32Z" fill="#a94a3e"/><path d="m9 33 11 0 5-12 8 23 5-13h17" fill="none" stroke="#f3ddbe" stroke-width="4"/>',
    'shield': '<path d="M32 5 55 14v20c-2 13-12 21-23 26C21 55 11 47 9 34V14Z"/><path d="M32 13 47 19v15c-2 9-8 14-15 18-7-4-13-9-15-18V19Z" fill="url(#steel)"/><path d="M32 14v38" stroke="#dbc793"/>',
    'bank': '<path d="M6 22 32 6l26 16Z" fill="url(#paper)"/><path d="M9 25h46M9 53h46M6 58h52M15 26v26m17-26v26m17-26v26" stroke-width="6"/><circle cx="32" cy="17" r="3" fill="#a94a3e"/>',
    'user': '<circle cx="32" cy="20" r="12" fill="url(#paper)"/><path d="M10 57v-8a22 22 0 0 1 44 0v8Z"/><path d="m22 36 10 10 10-10" fill="none" stroke="#eddbb0"/>',
    'speaker': '<path d="M6 24h12L33 11v43L18 41H6Z"/><path d="M42 21c10 5 10 18 0 23m6-30c18 10 18 27 0 37" fill="none" stroke="#eddbb0" stroke-width="4"/>',
    'info': '<circle cx="32" cy="32" r="25" fill="url(#paper)"/><path d="M29 29h6v19h-6ZM29 16h6v6h-6Z" fill="#574132"/>',
    'card': '<rect x="6" y="13" width="52" height="39" rx="5"/><path d="M7 24h50v8H7Z" fill="#30251d"/><rect x="13" y="38" width="12" height="7" rx="1" fill="url(#paper)"/><path d="M33 41h16"/>',
    'box': '<path d="m8 17 24-10 24 10v31L32 59 8 48Z"/><path d="m8 17 24 11 24-11M32 28v31" fill="none"/><path d="m21 12 24 11v9l-9 4v-9L12 17Z" fill="url(#paper)"/>',
    'gift': '<rect x="10" y="28" width="44" height="30" rx="2"/><rect x="6" y="20" width="52" height="12" rx="2" fill="url(#paper)"/><path d="M27 20h10v38H27Z" fill="#a94a3e"/><path d="M32 20C4 20 14-5 32 20 50-5 60 20 32 20Z" fill="#a94a3e"/>',
    'pistol': '<path d="M7 16h49v15H35l-5 22H15l4-22H7Z" fill="url(#steel)"/><path d="M8 19h45m-17 13v10H27M17 36l10 2" fill="none"/><path d="m15 52 15 0 3-13-14-3Z" fill="#77533b"/>',
    'puzzle': '<path d="M8 9h18c-4 13 16 13 12 0h17v18c-13-4-13 16 0 12v17H37c4-13-16-13-12 0H8V38c13 4 13-16 0-12Z" fill="url(#steel)"/>',
    'flask': '<path d="M23 7h18v7H23ZM26 14v17L9 51a5 5 0 0 0 4 7h38a5 5 0 0 0 4-7L38 31V14Z" fill="url(#paper)"/><path d="m19 40-8 12h42l-8-12Z" fill="#899b65"/><circle cx="28" cy="44" r="2"/><circle cx="37" cy="49" r="2"/>',
    'scissors': '<circle cx="16" cy="45" r="9" fill="url(#metal)"/><circle cx="45" cy="45" r="9" fill="url(#metal)"/><path d="m23 39 28-32-13 30 13-30M38 39 10 7l13 30" fill="url(#steel)"/><circle cx="31" cy="30" r="4"/>',
    'eye': '<path d="M4 32c16-23 40-23 56 0-16 23-40 23-56 0Z" fill="url(#paper)"/><circle cx="32" cy="32" r="12" fill="#879b82"/><circle cx="32" cy="32" r="6" fill="#30251d"/><circle cx="29" cy="28" r="3" fill="#f2ead4"/>',
    'shirt': '<path d="m20 8 12 7 12-7 16 13-10 15-7-5v26H21V31l-7 5L4 21Z" fill="url(#paper)"/><path d="M25 13c0 10 14 10 14 0M27 36h11" fill="none"/><path d="M31 28v16m-7-8h16" stroke="#a94a3e" stroke-width="5"/>',
    'dumbbell': '<path d="M20 31h24" stroke-width="8"/><rect x="9" y="16" width="12" height="32" rx="3"/><rect x="43" y="16" width="12" height="32" rx="3"/><path d="M5 23v18m54-18v18" stroke-width="6"/>',
    'hospital': '<path d="M8 58V21h16V7h16v14h16v37Z" fill="url(#paper)"/><path d="M27 47h10v11H27" fill="#4a352a"/><path d="M30 13h4v15h-4Zm-5 5h14v4H25Z" fill="#a94a3e" stroke="none"/><path d="M15 31h5m-5 9h5m24-9h5m-5 9h5" stroke-width="4"/>',
    'bed': '<path d="M8 19v39m48-17v17M8 48h48" stroke-width="5"/><path d="M12 34h39a5 5 0 0 1 5 5v9H12Z" fill="url(#paper)"/><rect x="13" y="24" width="13" height="10" rx="3" fill="url(#paper)"/>',
    'rubble': '<path d="m7 47 12-16 14 8-4 18H9Zm25-26 12-7 13 15-11 12-17-7ZM34 42l16-6 11 20H33Z" fill="url(#steel)"/><path d="m18 15 7-7 8 8-5 13-13-3Z" fill="url(#paper)"/>',
    'boss': '<path d="M13 18 6 6l17 9h18l17-9-7 12v18c0 12-10 23-19 23S13 48 13 36Z" fill="url(#paper)"/><path d="m19 28 10 4-6 7-4-11Zm26 0-10 4 6 7 4-11Z" fill="#a94a3e"/><path d="m25 49 7-5 7 5M32 37v5" fill="none"/>',
    'syringe': '<path d="m17 16 10-10m-5 5 6 6m-3-2 21 21-13 13-21-21Z" fill="url(#paper)"/><path d="m12 28 16-16m5 37 7 7m0 0 14 7M22 30l6-6m0 12 6-6m0 12 6-6" fill="none"/><path d="m28 37 7-7 11 6-13 13Z" fill="#a94a3e"/>',
    'door': '<path d="M12 58V7h37v51ZM19 58V15l23 5v38Z"/><path d="M42 20v38H19" fill="url(#paper)"/><circle cx="36" cy="39" r="3" fill="#a94a3e"/><path d="M8 58h48"/>',
    'clock': '<circle cx="32" cy="35" r="22" fill="url(#paper)"/><path d="M26 5h12m-6 0v8m17 5 6-6M32 20v17l10 6" fill="none" stroke-width="4"/><circle cx="32" cy="35" r="3" fill="#a94a3e"/>',
    'megaphone': '<path d="m9 25 42-16v43L9 36Z"/><path d="m17 39 3 16h10l-4-19" fill="url(#paper)"/><path d="M56 23v15M10 25H5v12h5"/>',
    'search': '<circle cx="26" cy="26" r="17" fill="url(#paper)"/><circle cx="26" cy="26" r="12" fill="#7c9b9c"/><path d="m39 39 17 17" stroke-width="9"/><path d="m19 23 9-6" stroke="#e1e4cf" stroke-width="3"/>',
    'check': '<circle cx="32" cy="32" r="25" fill="#697b53"/><path d="m17 32 10 11 21-24" fill="none" stroke="#f0e1bf" stroke-width="6"/>',
    'flame': '<path d="M32 5c5 19 24 23 21 41-4 20-40 19-42-2-2-11 8-17 9-28l10 12Z" fill="#ba6035"/><path d="M31 30c5 9 13 12 10 20-3 9-19 8-20-2-1-6 7-10 10-18Z" fill="url(#metal)"/>',
    'trophy': '<path d="M20 8h24v17c0 16-24 16-24 0ZM20 15H8v9c0 8 7 12 14 12m22-21h12v9c0 8-7 12-14 12M32 37v14M20 57h24v-6H20Z"/>',
    'star': '<path d="m32 5 8 17 19 3-14 14 3 20-16-9-17 9 4-20L5 25l19-3Z" fill="url(#metal)"/>',
    'key': '<circle cx="20" cy="20" r="13"/><circle cx="20" cy="20" r="5" fill="#30251d"/><path d="m30 30 26 26m-15-5 9-9m-3 15 9-9" stroke-width="7"/>',
    'repeat': '<path d="M13 22a22 22 0 0 1 39 0m0 20a22 22 0 0 1-39 0" fill="none" stroke="#d9ba7b" stroke-width="7"/><path d="m44 9 11 15H38Zm-24 46L9 40h17Z"/>',
    'back': '<path d="M55 26H26V12L6 32l20 20V38h29Z"/>',
    'knife': '<path d="m10 56 10-18 9 5-10 17Z" fill="#77533b"/><path d="m20 38 19-28 17-5-6 23-21 15Z" fill="url(#steel)"/><path d="m18 35 14 11" stroke-width="5"/>',
    'rifle': '<path d="M4 24h14l4-5h24v7h14v6H43l-4 5H24l-7 12-11-6 8-12H4Z" fill="url(#steel)"/><path d="M25 35h9l4 18H27Zm16-10h10v7H41Z" fill="#77533b"/><path d="M8 26h13m7 0h9M33 20v-7h10" fill="none"/>',
    'drink': '<path d="M18 12h28v44H18Z" fill="#778d76"/><ellipse cx="32" cy="12" rx="14" ry="6" fill="url(#steel)"/><path d="m33 22-10 15h8l-1 12 12-19h-9Z" fill="url(#metal)"/><path d="M24 10h15"/>',
    'medkit': '<rect x="9" y="19" width="46" height="38" rx="5" fill="url(#paper)"/><path d="M23 19V9h18v10M10 28h44" fill="none"/><path d="M27 32h10v18H27Zm-5 5h20v8H22Z" fill="#a94a3e" stroke="none"/>',
    'surgery': '<rect x="9" y="15" width="46" height="44" rx="5"/><path d="M23 15V7h18v8" fill="none"/><path d="M12 28h40"/><path d="M28 33h8v20h-8Zm-6 6h20v8H22Z" fill="url(#paper)" stroke="none"/>',
    'male': '<circle cx="26" cy="38" r="17" fill="url(#paper)"/><path d="m38 25 17-17m-16 0h16v16" fill="none" stroke-width="5"/>',
    'female': '<circle cx="32" cy="24" r="17" fill="url(#paper)"/><path d="M32 41v19m-11-9h22" fill="none" stroke-width="5"/>',
    'squats': '<circle cx="31" cy="11" r="6" fill="url(#paper)"/><path d="m29 23 10 11-15 10 18 13M29 23 17 33h24m-2 1 10 12 8 0" fill="none" stroke="#d4be93" stroke-width="7"/>',
    'pushups': '<circle cx="14" cy="24" r="6" fill="url(#paper)"/><path d="m23 29 25 7 9 17M24 30l-8 10 9 13M6 57h52" fill="none" stroke="#d4be93" stroke-width="7"/>',
    'plank': '<circle cx="11" cy="30" r="6" fill="url(#paper)"/><path d="m21 34 26 5 10 12M23 35v16H12M6 57h52" fill="none" stroke="#d4be93" stroke-width="7"/>',
    'pullups': '<circle cx="32" cy="20" r="6" fill="url(#paper)"/><path d="M7 7h50M15 9v13l17 11 17-11V9M32 33v11L21 58m11-14 10 14" fill="none" stroke="#d4be93" stroke-width="6"/>',
    'stretch': '<circle cx="34" cy="13" r="6" fill="url(#paper)"/><path d="m32 25-7 15-16 15m16-15 23 14M30 29 12 42m19-15 17 13 9-4" fill="none" stroke="#d4be93" stroke-width="7"/>',
    'boxing': '<path d="M12 39V21c0-10 13-15 24-12 11 3 17 12 14 23l-8 14H16Z" fill="#a94a3e"/><path d="M16 43h26v14H16Z"/><path d="M15 28c9-4 18 0 17 10m1-22 7 3" fill="none" stroke="#d9a186"/>',
    'lock': '<rect x="12" y="28" width="40" height="31" rx="4"/><path d="M20 28V18a12 12 0 0 1 24 0v10" fill="none" stroke="#d4be93" stroke-width="6"/><circle cx="32" cy="41" r="5" fill="#30251d"/><path d="M32 45v7"/>',
    'warning': '<path d="M32 6 60 57H4Z" fill="url(#metal)"/><path d="M29 22h6v18h-6Zm0 23h6v6h-6Z" fill="#5b3528" stroke="none"/>',
    'cross': '<circle cx="32" cy="32" r="25" fill="#a94a3e"/><path d="m22 22 20 20m0-20L22 42" fill="none" stroke="#f1dfbd" stroke-width="6"/>',
    'crown': '<path d="m7 17 11 9 14-17 14 17 11-9-5 32H12Z"/><path d="M12 49h40v9H12Z" fill="url(#paper)"/><circle cx="32" cy="37" r="5" fill="#a94a3e"/>',
    'status': '<circle cx="32" cy="32" r="24" fill="#697b53"/><circle cx="32" cy="32" r="15" fill="none" stroke="#b9c797" stroke-width="3"/>',
}

ALIASES = {
    '🪖':'helmet', '🎒':'bag', '👕':'coat', '🗺️':'map', '📋':'clipboard',
    '⚔️':'swords', '👥':'people', '🔔':'bell', '✉️':'mail', '⚙️':'gear',
    '🧠':'brain', '⚡':'lightning', '🪙':'coin', '💊':'pills', '💵':'cash',
    '❤️':'heart', '🛡️':'shield', '🏦':'bank', '👤':'user', '🔊':'speaker',
    'ℹ️':'info', '💳':'card', '📦':'box', '🔫':'pistol', '🧩':'puzzle',
    '🧪':'flask', '🧍':'user', '💇':'scissors', '👁️':'eye', '👔':'shirt',
    '🏋️':'dumbbell', '🏥':'hospital', '🛏️':'bed', '🧱':'rubble', '👹':'boss',
    '💉':'syringe', '🚪':'door', '⏱️':'clock', '📢':'megaphone', '🔍':'search',
    '✅':'check', '🔥':'flame', '🎉':'trophy', '🏆':'trophy', '✨':'star', '🎁':'gift',
    '🔑':'key', '🗝️':'key', '🔄':'repeat', '⬅':'back', '🔪':'knife',
    '🧃':'drink', '🩹':'medkit', '👨':'male', '👩':'female', '🦵':'squats',
    '💪':'pushups', '🧘':'plank', '🦾':'pullups', '🤸':'stretch', '🥊':'boxing',
    '🔒':'lock', '⚠️':'warning', '❌':'cross', '👑':'crown', '🟢':'status', '💀':'boss', '💨':'door',
}

SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none">
<defs>
 <linearGradient id="metal" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#ead5a5"/><stop offset=".45" stop-color="#b59a65"/><stop offset="1" stop-color="#695039"/></linearGradient>
 <linearGradient id="paper" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#f1e6c9"/><stop offset="1" stop-color="#ae9976"/></linearGradient>
 <linearGradient id="steel" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#c6cbc2"/><stop offset=".5" stop-color="#89968f"/><stop offset="1" stop-color="#485753"/></linearGradient>
</defs>
<g fill="url(#metal)" stroke="#30251d" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">{shapes}</g>
</svg>
'''

HELPERS = '''
function resolveIconKey(value, fallback = 'box') {
    if (typeof value === 'string') {
        if (Object.prototype.hasOwnProperty.call(GAME_ICONS, value)) return value;
        if (Object.prototype.hasOwnProperty.call(LEGACY_ICON_KEYS, value)) return LEGACY_ICON_KEYS[value];
    }
    return Object.prototype.hasOwnProperty.call(GAME_ICONS, fallback) ? fallback : 'box';
}

// Only registry paths are allowed; saved text cannot become an image URL or HTML.
function iconHTML(value, variant = 'inline') {
    const key = resolveIconKey(value);
    const size = ['inline', 'large', 'hero'].includes(variant) ? variant : 'inline';
    return `<img class="game-icon game-icon--${size}" src="${GAME_ICONS[key]}" alt="" aria-hidden="true" draggable="false" width="64" height="64">`;
}
'''


def main():
    directory = ROOT / 'assets' / 'icons'
    directory.mkdir(parents=True, exist_ok=True)
    for key, shapes in SHAPES.items():
        # Open structural strokes need contrast on both dark panels and paper dialogs.
        group = ET.fromstring('<g>' + shapes + '</g>')
        for node in group:
            if node.tag == 'path' and ('Z' not in node.get('d', '').upper() or node.get('fill') == 'none'):
                if 'stroke' not in node.attrib:
                    node.set('stroke', '#d9be89')
        artwork = ''.join(ET.tostring(node, encoding='unicode') for node in group)
        (directory / f'{key}.svg').write_text(SVG.format(shapes=artwork), encoding='utf-8')
    registry = {key: f'assets/icons/{key}.svg' for key in SHAPES}
    content = '// Generated by tools/build_icons.py. Original artwork for Палата 404.\n'
    content += 'const GAME_ICONS = Object.freeze(' + json.dumps(registry, indent=4) + ');\n'
    content += 'const LEGACY_ICON_KEYS = Object.freeze(' + json.dumps(ALIASES, ensure_ascii=False, indent=4) + ');\n'
    (ROOT / 'icons.js').write_text(content + HELPERS, encoding='utf-8')
    print(f'Built {len(SHAPES)} local SVG icons and their registry')


if __name__ == '__main__':
    main()
