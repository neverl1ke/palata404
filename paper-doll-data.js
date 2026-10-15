// Visual wardrobe only. These entries do not grant inventory or combat bonuses.
const PAPER_DOLL_FRAME = Object.freeze({ width: 941, height: 1672 });
const PAPER_DOLL_FACE_ANCHOR = Object.freeze({ x: 474, y: 32, height: 218 });
const PAPER_DOLL_LAYER_ORDER = Object.freeze([
    'baseBody', 'pants', 'footwear', 'upperBody', 'outerwear', 'armor', 'loadout',
    'gloves', 'back', 'hair', 'headwear', 'face', 'weapon', 'accessory'
]);
const PAPER_DOLL_SLOTS = {
    baseBody: { label: 'Базове тіло', elementId: 'layer-body', icon: 'user' },
    headwear: { label: 'Головний убір', elementId: 'layer-headwear', icon: 'helmet' },
    face: { label: 'Обличчя', elementId: 'layer-face', icon: 'eye' },
    hair: { label: 'Зачіски', elementId: 'layer-hair', icon: 'user' },
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
    { id: 'hair-none', slot: 'hair', name: 'Без зачіски', icon: 'user', availableByDefault: true,
        noImageRequired: true, description: 'Початковий вигляд затвердженого аватара без накладки волосся.' },
    { id: 'hair-messy', slot: 'hair', name: 'Розкуйовджена зачіска', icon: 'user', availableByDefault: true,
        fittedToGender: true, description: 'Розкуйовджене волосся з першого комплекту зачісок.',
        genderVariants: { male: 'assets/wardrobe/hair/male_messy_hair.png?v=fe4c6349', female: 'assets/wardrobe/hair/female_messy_hair.png?v=e2482312' },
        placementByGender: {
            male: { x: 365.06, y: -30.32, width: 210.936, height: 263.576 },
            female: { x: 343, y: -5, width: 246.84, height: 308.44 }
        } },
    { id: 'hair-bob', slot: 'hair', name: 'Каре до підборіддя', icon: 'user', availableByDefault: true,
        fittedToGender: true, description: 'Каре до підборіддя з першого комплекту зачісок.',
        genderVariants: { male: 'assets/wardrobe/hair/male_chin_length_bob.png?v=260f8f73', female: 'assets/wardrobe/hair/female_chin_length_bob.png?v=52bb5078' },
        placementByGender: {
            male: { x: 350.60516025, y: 17.4574795, width: 236.60111475, height: 236.60111475 },
            female: { x: 348.3386675, y: 6.7274324, width: 246.2881707, height: 246.2881707 }
        } },
    { id: 'hair-double-buns', slot: 'hair', name: 'Два бокові пучки з локонами', icon: 'user', availableByDefault: true,
        fittedToGender: true, description: 'Два бокові пучки з локонами з першого комплекту зачісок.',
        genderVariants: { male: 'assets/wardrobe/hair/male_double_buns.png?v=bd2fdcdc', female: 'assets/wardrobe/hair/female_double_buns.png?v=40d32b64' },
        placementByGender: {
            male: { x: 317.05, y: 4.5, width: 304.722, height: 304.722 },
            female: { x: 315.058, y: -0.896, width: 306.87888, height: 306.87888 }
        } },
    {
        id: 'patient-tunic', slot: 'upperBody', name: 'Лікарняна туніка', icon: 'shirt',
        description: 'Легка лікарняна туніка вільного крою.',
        availableByDefault: true, starterForPatient: true, fittedToGender: true,
        genderVariants: PAPER_DOLL_TUNIC_IMAGES,
        layers: [
            { id: 'front', genderVariants: PAPER_DOLL_TUNIC_IMAGES },
            { id: 'neckline', genders: ['female'], renderOrder: 2,
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
    hair: { label: 'Зачіски', icon: 'user', slots: ['hair'] },
    clothes: { label: 'Одяг', icon: 'shirt', slots: ['upperBody', 'outerwear', 'pants', 'footwear', 'gloves'] },
    gear: { label: 'Броня та спорядження', icon: 'shield', slots: ['headwear', 'armor', 'loadout', 'back'] },
    weapons: { label: 'Зброя', icon: 'swords', slots: ['weapon'] },
    accessories: { label: 'Аксесуари', icon: 'key', slots: ['accessory'] }
};
