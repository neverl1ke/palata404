// Visual wardrobe only. These entries do not grant inventory or combat bonuses.
const PAPER_DOLL_FRAME = Object.freeze({ width: 736, height: 1417 });
const PAPER_DOLL_LAYER_ORDER = Object.freeze([
    'baseBody', 'pants', 'footwear', 'upperBody', 'outerwear', 'armor', 'loadout',
    'gloves', 'back', 'headwear', 'face', 'weapon', 'accessory'
]);
const PAPER_DOLL_SLOTS = {
    baseBody: { label: 'Базове тіло', elementId: 'layer-body', icon: 'user' },
    headwear: { label: 'Головний убір', elementId: 'layer-headwear', icon: 'helmet' },
    face: { label: 'Обличчя', elementId: 'layer-face', icon: 'eye' },
    upperBody: { label: 'Верхній одяг', elementId: 'layer-upper-body', icon: 'shirt' },
    outerwear: { label: 'Зовнішній одяг', elementId: 'layer-outerwear', icon: 'coat' },
    armor: { label: 'Бронежилет', elementId: 'layer-armor', icon: 'shield' },
    loadout: { label: 'Розвантаження', elementId: 'layer-loadout', icon: 'bag' },
    gloves: { label: 'Рукавички', elementId: 'layer-gloves', icon: 'card' },
    pants: { label: 'Штани', elementId: 'layer-pants', icon: 'coat' },
    footwear: { label: 'Взуття', elementId: 'layer-footwear', icon: 'card' },
    back: { label: 'За спиною', elementId: 'layer-back', icon: 'bag' },
    weapon: { label: 'Зброя', elementId: 'layer-weapon', icon: 'swords' },
    accessory: { label: 'Аксесуар', elementId: 'layer-accessory', icon: 'key' }
};
const PAPER_DOLL_BODIES = { male: 'base_male.png', female: 'base_female.png' };
// Existing face PNGs are head cutouts, not full-frame layers. Their measured
// alpha bounds place each visible face at the same head anchor on the canvas.
const PAPER_DOLL_ITEMS = [
    ...[
        ['face_1.png', 'Обличчя #1 (Голений)', 174, 190, 33, 11, 109, 147],
        ['face_2.png', 'Обличчя #2 (Коротка стрижка)', 144, 185, 19, 6, 106, 153],
        ['face_3.png', 'Обличчя #3 (Середнє волосся)', 168, 183, 29, 4, 117, 151],
        ['face_4.png', 'Обличчя #4 (Довге волосся)', 193, 184, 33, 4, 134, 167],
        ['face_5.png', 'Обличчя #5 (Андеркат)', 142, 171, 17, 0, 106, 158],
        ['face_6.png', 'Обличчя #6 (Лисий суворий)', 163, 197, 26, 13, 106, 147]
    ].map(([id, name, width, height, x, y, alphaWidth, alphaHeight]) => {
        const scale = 177 / alphaHeight;
        return { id, slot: 'face', name, image: id,
            placement: { x: 383 - (x + alphaWidth / 2) * scale, y: 25 - y * scale, width: width * scale, height: height * scale } };
    }),
    { id: 'sample-upper-body', slot: 'upperBody', name: 'Зразок верхнього одягу', image: null },
    { id: 'sample-pants', slot: 'pants', name: 'Зразок штанів', image: null },
    { id: 'sample-footwear', slot: 'footwear', name: 'Зразок взуття', image: null },
    { id: 'sample-headwear', slot: 'headwear', name: 'Побитий шолом санітара — зразок', image: null },
    { id: 'sample-armor', slot: 'armor', name: 'Бронежилет БР-1 — зразок', image: null },
    { id: 'sample-weapon', slot: 'weapon', name: 'ПМ — зразок', image: null }
];
