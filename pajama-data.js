// The approved pajama set uses the existing three clothing slots and loadouts.
// Registered garment art is separate from the unchanged avatar bodies and grips.
(() => {
    const poses = (idle, melee = idle, rifle = idle) => ({ idle, melee, rifle });
    const top = {
        male: poses(
            'assets/wardrobe/clothing/patient/pajamas/male/top-idle.webp?v=6b7d8185b1b2',
            'assets/wardrobe/clothing/patient/pajamas/male/top-melee.webp?v=3e0e56f4d292',
            'assets/wardrobe/clothing/patient/pajamas/male/top-rifle.webp?v=14461ff07c72'
        ),
        female: poses(
            'assets/wardrobe/clothing/patient/pajamas/female/top-idle.webp?v=414fd3d32faa',
            'assets/wardrobe/clothing/patient/pajamas/female/top-melee.webp?v=26f666e12a03',
            'assets/wardrobe/clothing/patient/pajamas/female/top-rifle.webp?v=2f3be7e67534'
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
                male: 'assets/wardrobe/clothing/patient/pajamas/male/thumb-top.webp?v=359693fa720e',
                female: 'assets/wardrobe/clothing/patient/pajamas/female/thumb-top.webp?v=4b2e2ec9d0de'
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
