// Approved male registrations are keyed by face, never by a saved array index.
// Own-head skin-edge repairs remain untinted and disappear with their hairstyle.
function maleHairReviewFor(gender, faceId, hairId) {
    if (gender !== 'male' || hairId === 'hair-none') return null;
    return MALE_HAIR_REVIEW.heads[faceId || '@native'] || null;
}

function maleReviewedHead(face, gender) {
    const source = gender === 'male' && face && MALE_HAIR_REVIEW.headSources[face.id];
    return source ? { ...face, genderVariants: { ...face.genderVariants, male: source } } : face;
}

function maleReviewedHairParts(item, gender, faceId, parts) {
    const fit = maleHairReviewFor(gender, faceId, item?.id);
    if (!fit || item?.slot !== 'hair') return parts;
    const native = { x: 0, y: 0, width: 941, height: 1672 };
    const layers = fit.layers[item.id];
    if (layers) return layers.map(layer => ({ id: layer.id, fittedToGender: true,
        genderVariants: { male: layer.source }, placementByGender: { male: native },
        renderOrder: layer.renderOrder, recolor: layer.recolor }));
    const source = MALE_HAIR_REVIEW.shared[item.id];
    if (source) return [{ id: 'front', fittedToGender: true, renderOrder: 9,
        genderVariants: { male: source }, placementByGender: { male: native } }];
    const delta = fit.placements[item.id];
    if (!delta) return parts;
    return parts.map(part => {
        const p = part.placementByGender?.male || part.placement || native;
        return { ...part, placementByGender: { ...part.placementByGender,
            male: { ...p, x: p.x + delta.dx, y: p.y + delta.dy } } };
    });
}

for (const [id, source] of Object.entries(MALE_HAIR_REVIEW.thumbnails)) {
    const item = PAPER_DOLL_ITEMS.find(item => item.id === id);
    if (item) item.thumbnailByGender = { ...item.thumbnailByGender, male: source };
}
