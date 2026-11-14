// The approved pajama set uses the existing three clothing slots and loadouts.
// Registered garment art is separate from the unchanged avatar bodies and grips.
(() => {
    const poses = (idle, melee = idle, rifle = idle) => ({ idle, melee, rifle });
    const top = {
        male: poses(
            'assets/wardrobe/clothing/patient/pajamas/male/top-idle.png?v=2df763bde43e',
            'assets/wardrobe/clothing/patient/pajamas/male/top-melee.png?v=e0ea02f99757',
            'assets/wardrobe/clothing/patient/pajamas/male/top-rifle.png?v=691ac0ac0ce1'
        ),
        female: poses(
            'assets/wardrobe/clothing/patient/pajamas/female/top-idle.png?v=71f1c22c16f6',
            'assets/wardrobe/clothing/patient/pajamas/female/top-melee.png?v=91e826f3c77d',
            'assets/wardrobe/clothing/patient/pajamas/female/top-rifle.png?v=c67ec0187760'
        )
    };
    const pants = {
        male: poses('assets/wardrobe/clothing/patient/pajamas/male/pants.png?v=92081a7760cf'),
        female: poses('assets/wardrobe/clothing/patient/pajamas/female/pants.png?v=3c8b600aac79')
    };
    const footwear = {
        male: poses('assets/wardrobe/clothing/patient/pajamas/male/footwear.png?v=bdd2cc75318e'),
        female: poses('assets/wardrobe/clothing/patient/pajamas/female/footwear.png?v=856fbe784678')
    };
    const footwearMask = {
        male: poses('assets/wardrobe/clothing/patient/pajamas/male/mask-footwear.png?v=89adcfa598eb'),
        female: poses('assets/wardrobe/clothing/patient/pajamas/female/mask-footwear.png?v=89adcfa598eb')
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
                male: 'assets/wardrobe/clothing/patient/pajamas/male/thumb-top.webp?v=2f1b911ff6ff',
                female: 'assets/wardrobe/clothing/patient/pajamas/female/thumb-top.webp?v=81d68c8064cc'
            }, null, topHands
        ),
        clothing(
            'patient-pajama-pants', 'pants', 'pants', 'Піжамні штани',
            'Вільні бавовняні штани в тонку смужку з м’яким поясом.', pants,
            {
                male: 'assets/wardrobe/clothing/patient/pajamas/male/thumb-pants.webp?v=3fdf3ce8154a',
                female: 'assets/wardrobe/clothing/patient/pajamas/female/thumb-pants.webp?v=35bfd7e5e7e7'
            }
        ),
        clothing(
            'patient-pajama-slippers', 'footwear', 'footwear', 'Лікарняні капці',
            'Закриті м’які капці з тонкою гумовою підошвою.', footwear,
            {
                male: 'assets/wardrobe/clothing/patient/pajamas/male/thumb-footwear.webp?v=cf1195b426c3',
                female: 'assets/wardrobe/clothing/patient/pajamas/female/thumb-footwear.webp?v=39127ef11630'
            }, footwearMask
        )
    );

    const shirt = PAPER_DOLL_ITEMS.find(item => item.id === 'patient-pajama-top');
    const slippers = PAPER_DOLL_ITEMS.find(item => item.id === 'patient-pajama-slippers');
    shirt.poseClothingBackByGender = {"male": {"idle": "assets/wardrobe/clothing/patient/pajamas/male/back-idle.png?v=6cb3845e1419", "melee": "assets/wardrobe/clothing/patient/pajamas/male/back-melee.png?v=128e72f19e3a", "rifle": "assets/wardrobe/clothing/patient/pajamas/male/back-rifle.png?v=89adcfa598eb"}, "female": {"idle": "assets/wardrobe/clothing/patient/pajamas/female/back-idle.png?v=1dc532ecbf94", "melee": "assets/wardrobe/clothing/patient/pajamas/female/back-melee.png?v=ed56f9304478", "rifle": "assets/wardrobe/clothing/patient/pajamas/female/back-rifle.png?v=075ed68f20c0"}};
    slippers.poseClothingBackByGender = {"male": {"idle": "assets/wardrobe/clothing/patient/pajamas/male/back-footwear.png?v=aca460992c31", "melee": "assets/wardrobe/clothing/patient/pajamas/male/back-footwear.png?v=aca460992c31", "rifle": "assets/wardrobe/clothing/patient/pajamas/male/back-footwear.png?v=aca460992c31"}, "female": {"idle": "assets/wardrobe/clothing/patient/pajamas/female/back-footwear.png?v=9b737462ee36", "melee": "assets/wardrobe/clothing/patient/pajamas/female/back-footwear.png?v=9b737462ee36", "rifle": "assets/wardrobe/clothing/patient/pajamas/female/back-footwear.png?v=9b737462ee36"}};
    // Keep masks belong only to this exact artwork pair; pants stay equipped.
    shirt.poseClothingOccludes = [{
        targetItemId: 'patient-pajama-pants', keepMaskByGender: {"male": {"idle": "assets/wardrobe/clothing/patient/pajamas/male/keep-pants-idle.png?v=2ec822b51ca4", "melee": "assets/wardrobe/clothing/patient/pajamas/male/keep-pants-melee.png?v=c30e6839bea1", "rifle": "assets/wardrobe/clothing/patient/pajamas/male/keep-pants-rifle.png?v=b935c91558e4"}, "female": {"idle": "assets/wardrobe/clothing/patient/pajamas/female/keep-pants-idle.png?v=7ff7c8078fa5", "melee": "assets/wardrobe/clothing/patient/pajamas/female/keep-pants-melee.png?v=7ff7c8078fa5", "rifle": "assets/wardrobe/clothing/patient/pajamas/female/keep-pants-rifle.png?v=ec5e8507b3f0"}},
        ownerArtworkByGender: top, targetArtworkByGender: pants
    }];
    // Mixed legacy outfits use the real idle art with the same front/rear order.
    for (const item of [shirt, slippers]) item.layers = [
        {id:'rear', genderVariants:Object.fromEntries(['male','female'].map(g=>[g,item.poseClothingBackByGender[g].idle])), renderOrder:-1},
        {id:'front', genderVariants:item.genderVariants, renderOrder:item.renderOrder}
    ];
})();
