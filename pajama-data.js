// The approved pajama set uses the existing three clothing slots and loadouts.
// Registered garment art is separate from the unchanged avatar bodies and grips.
(() => {
    const poses = (idle, melee = idle, rifle = idle) => ({ idle, melee, rifle });
    const top = {
        male: poses(
            'assets/wardrobe/clothing/patient/pajamas/male/top-idle.png?v=f55d4e5d9f7c',
            'assets/wardrobe/clothing/patient/pajamas/male/top-melee.png?v=906a6ef4956b',
            'assets/wardrobe/clothing/patient/pajamas/male/top-rifle.png?v=7796c09c33d8'
        ),
        female: poses(
            'assets/wardrobe/clothing/patient/pajamas/female/top-idle.png?v=1e087eb02b49',
            'assets/wardrobe/clothing/patient/pajamas/female/top-melee.png?v=c3df05497493',
            'assets/wardrobe/clothing/patient/pajamas/female/top-rifle.png?v=d239135eaedb'
        )
    };
    const pants = {
        male: poses('assets/wardrobe/clothing/patient/pajamas/male/pants.webp?v=80907147fe2f'),
        female: poses('assets/wardrobe/clothing/patient/pajamas/female/pants.webp?v=538ae40a70cb')
    };
    const footwear = {
        male: poses('assets/wardrobe/clothing/patient/pajamas/male/footwear.webp?v=ab51ed65c469'),
        female: poses('assets/wardrobe/clothing/patient/pajamas/female/footwear.webp?v=0ebb4543418d')
    };
    const footwearMask = {
        male: poses('assets/wardrobe/clothing/patient/pajamas/male/mask-footwear.webp?v=d8b038ae1436'),
        female: poses('assets/wardrobe/clothing/patient/pajamas/female/mask-footwear.webp?v=6505d9972bc5')
    };
    const topHands = {
        male: { rifle: 'assets/wardrobe/clothing/patient/pajamas/male/foreground-hands-rifle.webp?v=ce0e3b27047a' },
        female: { rifle: 'assets/wardrobe/clothing/patient/pajamas/female/foreground-hands-rifle.webp?v=803bb04b11cd' }
    };
    const clothing = (id, slot, part, name, description, artwork, thumbnailByGender, eraseMask, foregroundMask) => ({
        id, slot, name, description,
        icon: PAPER_DOLL_SLOTS[slot].icon,
        genders: ['male', 'female'],
        availableByDefault: true,
        fittedToGender: true,
        poseAwareClothing: true,
        poseClothingPart: part,
        poseClothingByGender: artwork,
        ...(eraseMask ? { poseClothingMaskByGender: eraseMask } : {}),
        ...(foregroundMask ? { poseClothingForegroundMaskByGender: foregroundMask } : {}),
        genderVariants: { male: artwork.male.idle, female: artwork.female.idle },
        placement: { x: 0, y: 0, width: 941, height: 1672 },
        // These closed slippers sit under the pajama trouser hems, including
        // the static renderer used when a legacy garment is mixed into the set.
        renderOrder: part === 'footwear' ? 0.5 : PAPER_DOLL_LAYER_ORDER.indexOf(slot),
        thumbnailByGender,
        artApproval: 'pajamas-20261111'
    });
    PAPER_DOLL_ITEMS.push(
        clothing(
            'patient-pajama-top', 'upperBody', 'top', 'Піжамна сорочка',
            'Сіро-блакитна бавовняна сорочка на ґудзиках у тонку смужку.', top,
            {
                male: 'assets/wardrobe/clothing/patient/pajamas/male/thumb-top.webp?v=4d2b143c7ed6',
                female: 'assets/wardrobe/clothing/patient/pajamas/female/thumb-top.webp?v=f172558a481e'
            }, null, topHands
        ),
        clothing(
            'patient-pajama-pants', 'pants', 'pants', 'Піжамні штани',
            'Вільні бавовняні штани в тонку смужку з м’яким поясом.', pants,
            {
                male: 'assets/wardrobe/clothing/patient/pajamas/male/thumb-pants.webp?v=3917f8dbe809',
                female: 'assets/wardrobe/clothing/patient/pajamas/female/thumb-pants.webp?v=9d25abe4ed83'
            }
        ),
        clothing(
            'patient-pajama-slippers', 'footwear', 'footwear', 'Лікарняні капці',
            'Закриті м’які капці з тонкою гумовою підошвою.', footwear,
            {
                male: 'assets/wardrobe/clothing/patient/pajamas/male/thumb-footwear.webp?v=8f1ee160bd80',
                female: 'assets/wardrobe/clothing/patient/pajamas/female/thumb-footwear.webp?v=b3ab212a0b06'
            }, footwearMask
        )
    );
})();

// Approved shirt rear pieces belong only to the equipped shirt and active pose.
PAPER_DOLL_ITEMS.find(item=>item.id==='patient-pajama-top').poseClothingBackByGender={"male":{"idle":"assets/wardrobe/clothing/patient/pajamas/male/back-idle.png?v=af57cfab58fc","melee":"assets/wardrobe/clothing/patient/pajamas/male/back-melee.png?v=56e8919c2d59","rifle":"assets/wardrobe/clothing/patient/pajamas/male/back-rifle.png?v=89adcfa598eb"},"female":{"idle":"assets/wardrobe/clothing/patient/pajamas/female/back-idle.png?v=53a82c63ada5","melee":"assets/wardrobe/clothing/patient/pajamas/female/back-melee.png?v=1b736b925d41","rifle":"assets/wardrobe/clothing/patient/pajamas/female/back-rifle.png?v=6c2f3a664fd4"}};
