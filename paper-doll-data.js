// Visual wardrobe only. These entries do not grant inventory or combat bonuses.
const PAPER_DOLL_FRAME = Object.freeze({ width: 941, height: 1672 });
const PAPER_DOLL_FACE_ANCHOR = Object.freeze({ x: 474, y: 32, height: 218 });
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
// Hashes of the user's approved uploads invalidate previously cached bodies.
const PAPER_DOLL_BODIES = { male: 'base_male.png?v=0dec17c1', female: 'base_female.png?v=5489c78c' };
// The six retired trial faces stay on disk, but are not catalog entries.
// New approved cosmetics can use the face slot, placement and multipart layers.
const PAPER_DOLL_RETIRED_FACES = new Set(Array.from({ length: 6 }, (_, index) => `face_${index + 1}.png`));
const PAPER_DOLL_TUNIC_IMAGES = Object.freeze({
    male: 'assets/wardrobe/clothing/patient/patient_tunic_male.png?v=28343fe9',
    female: 'assets/wardrobe/clothing/patient/patient_tunic_female.png?v=fa3fac64'
});
const PAPER_DOLL_ITEMS = [
    {
        id: 'patient-tunic', slot: 'upperBody', name: 'Лікарняна туніка', icon: 'shirt',
        description: 'Легка лікарняна туніка вільного крою.',
        availableByDefault: true, starterForPatient: true, fittedToGender: true,
        genderVariants: PAPER_DOLL_TUNIC_IMAGES,
        layers: [
            { id: 'front', genderVariants: PAPER_DOLL_TUNIC_IMAGES },
            { id: 'neckline', genders: ['female'], renderOrder: 2.5,
                genderVariants: { female: 'assets/wardrobe/clothing/patient/female_neckline_skin_underlay.png?v=cc9a05ce' } }
        ]
    },
    { id: 'gear-knife', slot: 'weapon', name: 'Іржавий ніж', inventoryName: 'Іржавий ніж', inventoryCategory: 'weapon', image: null, icon: 'knife' },
    { id: 'gear-pm', slot: 'weapon', name: 'ПМ (Пістолет Макарова)', inventoryName: 'ПМ (Пістолет Макарова)', inventoryCategory: 'weapon', image: null, icon: 'pistol' },
    { id: 'gear-aks', slot: 'weapon', name: 'Штурмовий АКС-74У', inventoryName: 'Штурмовий АКС-74У', inventoryCategory: 'weapon', image: null, icon: 'rifle' },
    { id: 'gear-helmet', slot: 'headwear', name: 'Побитий шолом санітара', inventoryName: 'Побитий шолом санітара', inventoryCategory: 'helmet', image: null, icon: 'helmet' },
    { id: 'gear-br1', slot: 'armor', name: 'Бронежилет БР-1', inventoryName: 'Бронежилет БР-1', inventoryCategory: 'armor', image: null, icon: 'shield' }
];
const PAPER_DOLL_LEGACY_ITEMS = { 'sample-headwear': 'gear-helmet', 'sample-armor': 'gear-br1', 'sample-weapon': 'gear-pm' };
const WARDROBE_CATEGORIES = {
    appearance: { label: 'Зовнішність', icon: 'user', slots: ['baseBody', 'face'] },
    clothes: { label: 'Одяг', icon: 'shirt', slots: ['upperBody', 'outerwear', 'pants', 'footwear', 'gloves'] },
    gear: { label: 'Броня та спорядження', icon: 'shield', slots: ['headwear', 'armor', 'loadout', 'back'] },
    weapons: { label: 'Зброя', icon: 'swords', slots: ['weapon'] },
    accessories: { label: 'Аксесуари', icon: 'key', slots: ['accessory'] }
};
