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
// Hashes of the integrated bodies invalidate previously cached art.
const PAPER_DOLL_BODIES = { male: 'base_male.png?v=08da7a7f', female: 'base_female.png?v=e76e72be' };
// The six retired trial faces stay on disk, but are not catalog entries.
// New approved cosmetics can use the face slot, placement and multipart layers.
const PAPER_DOLL_RETIRED_FACES = new Set(Array.from({ length: 6 }, (_, index) => `face_${index + 1}.png`));
const PAPER_DOLL_TUNIC_IMAGES = Object.freeze({
    male: 'assets/wardrobe/clothing/patient/patient_tunic_male.png?v=b0da3128',
    female: 'assets/wardrobe/clothing/patient/patient_tunic_female.png?v=809fd1e8'
});
const PAPER_DOLL_ITEMS = [
    { id: 'face-asian', slot: 'face', name: 'Азійський тип обличчя', icon: 'user', availableByDefault: true,
        fittedToGender: true, description: 'Варіант голови для обраного базового аватара.',
        // DOM image renderer: above the body (0), below clothing and hair (9).
        renderOrder: 1,
        genderVariants: { male: 'assets/wardrobe/faces/male_asian_head.png?v=1043b5b2', female: 'assets/wardrobe/faces/female_asian_head.png?v=cf29ee83' },
        bodyMaskByGender: { male: 'assets/wardrobe/faces/masks/male_asian_body.png?v=dbaab2c9', female: 'assets/wardrobe/faces/masks/female_asian_body.png?v=4ce39715' },
        placementByGender: {
            male: { x: 0, y: 0, width: 941, height: 1672 },
            female: { x: 0, y: 0, width: 941, height: 1672 }
        } },
    { id: 'face-young', slot: 'face', name: 'Молоде обличчя', icon: 'user', availableByDefault: true,
        fittedToGender: true, description: 'Молодий тип обличчя, 18–20 років.',
        // DOM image renderer: above the body (0), below clothing and hair (9).
        renderOrder: 1,
        genderVariants: { male: 'assets/wardrobe/faces/male_young_head.png?v=02729493', female: 'assets/wardrobe/faces/female_young_head.png?v=8feabbfb' },
        bodyMaskByGender: { male: 'assets/wardrobe/faces/masks/male_young_body.png?v=73bad65e', female: 'assets/wardrobe/faces/masks/female_young_body.png?v=4ce39715' },
        placementByGender: {
            male: { x: 0, y: 0, width: 941, height: 1672 },
            female: { x: 0, y: 0, width: 941, height: 1672 }
        } },
    { id: 'face-exhausted', slot: 'face', name: 'Виснажене обличчя', icon: 'user', availableByDefault: true,
        fittedToGender: true, description: 'Виснажений, тривожний тип обличчя.',
        // DOM image renderer: above the body (0), below clothing and hair (9).
        renderOrder: 1,
        genderVariants: { male: 'assets/wardrobe/faces/male_exhausted_head.png?v=5683706e', female: 'assets/wardrobe/faces/female_exhausted_head.png?v=877804b3' },
        bodyMaskByGender: { male: 'assets/wardrobe/faces/masks/male_exhausted_body.png?v=95e48d48', female: 'assets/wardrobe/faces/masks/female_exhausted_body.png?v=4ce39715' },
        placementByGender: {
            male: { x: 0, y: 0, width: 941, height: 1672 },
            female: { x: 0, y: 0, width: 941, height: 1672 }
        } },
    { id: 'face-elder', slot: 'face', name: 'Старше обличчя', icon: 'user', availableByDefault: true,
        fittedToGender: true, description: 'Старший тип обличчя, 60+ років.',
        // DOM image renderer: above the body (0), below clothing and hair (9).
        renderOrder: 1,
        genderVariants: { male: 'assets/wardrobe/faces/male_elder_head.png?v=f6e3003c', female: 'assets/wardrobe/faces/female_elder_head.png?v=9547a763' },
        bodyMaskByGender: { male: 'assets/wardrobe/faces/masks/male_elder_body.png?v=191ad94a', female: 'assets/wardrobe/faces/masks/female_elder_body.png?v=4ce39715' },
        placementByGender: {
            male: { x: 0, y: 0, width: 941, height: 1672 },
            female: { x: 0, y: 0, width: 941, height: 1672 }
        } },
    { id: 'face-alternative', slot: 'face', name: 'Нове обличчя', icon: 'user', availableByDefault: true,
        fittedToGender: true, description: 'Новий затверджений варіант обличчя для обраної статі.', renderOrder: 1,
        genderVariants: { male: 'assets/wardrobe/faces/male_alternative_head.png?v=2b58bf7a', female: 'assets/wardrobe/faces/female_alternative_head.png?v=ece9a9c4' },
        bodyMaskByGender: { male: 'assets/wardrobe/faces/masks/male_alternative_body.png?v=2778f476', female: 'assets/wardrobe/faces/masks/female_alternative_body.png?v=4ce39715' },
        placementByGender: {
            male: { x: 0, y: 0, width: 941, height: 1672 },
            female: { x: 0, y: 0, width: 941, height: 1672 }
        } },
    { id: 'face-ginger-soft', slot: 'face', name: 'Світле ніжне обличчя', icon: 'user', availableByDefault: true,
        genders: ['female'], fittedToGender: true, description: 'Світлий жіночий портрет із ніжними рисами.', renderOrder: 1,
        genderVariants: { female: 'assets/wardrobe/faces/female_ginger_soft_head.png?v=5bdd230b' },
        bodyMaskByGender: { female: 'assets/wardrobe/faces/masks/female_ginger_soft_body.png?v=e3d160bd' },
        placementByGender: { female: { x: 0, y: 0, width: 941, height: 1672 } } },
    { id: 'face-goth-septum', slot: 'face', name: 'Готичне обличчя із септумом', icon: 'user', availableByDefault: true,
        genders: ['female'], fittedToGender: true, description: 'Жіночий портрет із готичним макіяжем і септумом.', renderOrder: 1,
        genderVariants: { female: 'assets/wardrobe/faces/female_goth_septum_head.png?v=4b9aa067' },
        bodyMaskByGender: { female: 'assets/wardrobe/faces/masks/female_goth_septum_body.png?v=e3d160bd' },
        placementByGender: { female: { x: 0, y: 0, width: 941, height: 1672 } } },
    { id: 'face-goth-black-lips', slot: 'face', name: 'Готичне обличчя з чорними губами', icon: 'user', availableByDefault: true,
        genders: ['female'], fittedToGender: true, description: 'Жіночий портрет із чорними губами та пірсингом.', renderOrder: 1,
        genderVariants: { female: 'assets/wardrobe/faces/female_goth_black_lips_head.png?v=d158e029' },
        bodyMaskByGender: { female: 'assets/wardrobe/faces/masks/female_goth_black_lips_body.png?v=e3d160bd' },
        placementByGender: { female: { x: 0, y: 0, width: 941, height: 1672 } } },
    { id: 'hair-none', slot: 'hair', name: 'Без зачіски', icon: 'user', availableByDefault: true,
        noImageRequired: true, description: 'Початковий вигляд затвердженого аватара без накладки волосся.' },
    { id: 'hair-bob-bangs', slot: 'hair', name: 'Каре з чубчиком', icon: 'user', availableByDefault: true,
        genders: ['female'], fittedToGender: true, description: 'Каштанове жіноче каре з чубчиком.',
        genderVariants: { female: 'assets/wardrobe/hair/unisex_bob_bangs.png?v=0293b69f' },
        placementByGender: {
            female: { x: 365.9, y: -59.9, width: 216.43, height: 384.56 }
        } },
    { id: 'hair-messy', slot: 'hair', name: 'Розкуйовджена зачіска', icon: 'user', availableByDefault: true,
        fittedToGender: true, description: 'Розкуйовджене волосся з першого комплекту зачісок.',
        genderVariants: { male: 'assets/wardrobe/hair/male_messy_hair.png?v=4e890f4b', female: 'assets/wardrobe/hair/female_messy_hair.png?v=fe47846c' },
        placementByGender: {
            male: { x: 364.082398407408, y: -29.293952, width: 209.373552192592, height: 256.9470636, stretchX: true },
            female: { x: 343, y: -5, width: 246.84, height: 308.44 }
        } },
    { id: 'hair-bob', slot: 'hair', name: 'Каре до підборіддя', icon: 'user', availableByDefault: true,
        fittedToGender: true, description: 'Каре до підборіддя з першого комплекту зачісок.',
        genderVariants: { male: 'assets/wardrobe/hair/male_chin_length_bob.png?v=978335df', female: 'assets/wardrobe/hair/female_chin_length_bob.png?v=b8f42959' },
        placementByGender: {
            male: { x: 352.60516025, y: 14.4574795, width: 236.60111475, height: 236.60111475 },
            female: { x: 344.8386675, y: 6.7274324, width: 246.2881707, height: 246.2881707 }
        } },
    { id: 'hair-double-buns', slot: 'hair', name: 'Два бокові пучки з локонами', icon: 'user', availableByDefault: true,
        fittedToGender: true, description: 'Два бокові пучки з локонами з першого комплекту зачісок.',
        genderVariants: { male: 'assets/wardrobe/hair/male_double_buns.png?v=5b2aae59', female: 'assets/wardrobe/hair/female_double_buns.png?v=6290b9c9' },
        placementByGender: {
            male: { x: 317.05, y: 4.5, width: 304.722, height: 304.722 },
            female: { x: 315.058, y: -0.896, width: 306.87888, height: 306.87888 }
        } },
    { id: 'hair-classic-short', slot: 'hair', name: 'Класична коротка стрижка', icon: 'user', availableByDefault: true,
        fittedToGender: true, description: 'Затверджена зачіска з другого комплекту.',
        genderVariants: { male: 'assets/wardrobe/hair/classic_short_unisex_style_A.png?v=1ddab573', female: 'assets/wardrobe/hair/classic_short_unisex_style_A.png?v=1ddab573' },
        placementByGender: {
            male: { x: 370.5, y: 0, width: 200.64, height: 200.64 },
            female: { x: 372.5, y: -5, width: 196.878, height: 196.878 }
        } },
    { id: 'hair-textured-short', slot: 'hair', name: 'Коротка текстурована стрижка', icon: 'user', availableByDefault: true,
        fittedToGender: true, description: 'Затверджена зачіска з другого комплекту.',
        genderVariants: { male: 'assets/wardrobe/hair/classic_short_unisex_style_B.png?v=9ad8b4e1', female: 'assets/wardrobe/hair/classic_short_unisex_style_B.png?v=9ad8b4e1' },
        placementByGender: {
            male: { x: 369.9884556812, y: -7.8760272324, width: 201.8883785688, height: 201.8883785688 },
            female: { x: 372.0210235314683, y: -13.885696649022648, width: 201.45305805472074, height: 201.45305805472074 }
        } },
    { id: 'hair-shoulder-length', slot: 'hair', name: 'Волосся до плечей', icon: 'user', availableByDefault: true,
        fittedToGender: true, description: 'Затверджена зачіска з другого комплекту.',
        genderVariants: { male: 'assets/wardrobe/hair/male_medium_shoulder_length.png?v=aa3b097a', female: 'assets/wardrobe/hair/female_medium_shoulder_length.png?v=79b8f5b8' },
        layers: [
            { id: 'rear', genders: ['male'], renderOrder: -1, fittedToGender: true,
                genderVariants: { male: 'assets/wardrobe/hair/male_medium_shoulder_length_rear.png?v=895e676c' },
                colorReference: 'assets/wardrobe/hair/male_medium_shoulder_length.png?v=aa3b097a',
                placementByGender: { male: { x: 0, y: 0, width: 941, height: 1672 } } },
            { id: 'front', renderOrder: 9, fittedToGender: true,
                genderVariants: { male: 'assets/wardrobe/hair/male_medium_shoulder_length.png?v=aa3b097a', female: 'assets/wardrobe/hair/female_medium_shoulder_length.png?v=79b8f5b8' } }
        ],
        placementByGender: {
            male: { x: 330.705600351, y: 21.61907, width: 277.29702, height: 277.29702 },
            female: { x: 319.19278624, y: 13.02804571232, width: 290.59567314624, height: 290.59567314624 }
        } },
    {
        id: 'patient-tunic', slot: 'upperBody', name: 'Лікарняна туніка', icon: 'shirt',
        description: 'Легка лікарняна туніка вільного крою.',
        availableByDefault: true, starterForPatient: true, fittedToGender: true,
        genderVariants: PAPER_DOLL_TUNIC_IMAGES,
        layers: [
            { id: 'front', genderVariants: PAPER_DOLL_TUNIC_IMAGES },
            { id: 'neckline', genders: ['female'], renderOrder: 2,
                genderVariants: { female: 'assets/wardrobe/clothing/patient/female_neckline_skin_underlay.png?v=8a9076fa' } }
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
    appearance: { label: 'Зовнішність', icon: 'user', slots: ['baseBody', 'face', 'hair'] },
    clothes: { label: 'Одяг', icon: 'shirt', slots: ['upperBody', 'outerwear', 'pants', 'footwear', 'gloves'] },
    gear: { label: 'Броня та спорядження', icon: 'shield', slots: ['headwear', 'armor', 'loadout', 'back'] },
    weapons: { label: 'Зброя', icon: 'swords', slots: ['weapon'] },
    accessories: { label: 'Аксесуари', icon: 'key', slots: ['accessory'] }
};
