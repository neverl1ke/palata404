// Replay the approved female fitting after coloring, on the shared native canvas.
const femaleHairFitCache = new Map();

function femaleHairFitFor(gender, faceId, hairId, placement) {
    if (gender !== 'female' || hairId === 'hair-none') return null;
    const face = FEMALE_HAIR_FITS[faceId || '@native'];
    const value = face?.settings[hairId];
    if (!value) return null;
    const repair = FEMALE_HAIR_REPAIR_MAPS[`${face.code}-${value.hair_code}`];
    const base = placement || { x: 0, y: 0, width: 941, height: 1672 };
    const sx = value.horizontalScale;
    return { key: `${face.code}/${hairId}`, mapping: repair?.mapping || [],
        registration: repair?.registration || {
            left: base.x, top: base.y, width: base.width, height: base.height,
            sx, dx: (sx - 1) * (base.x - value.anchorX) + value.shiftX, dy: value.downPixels
        } };
}

function fittedFemaleHairSource(source, color, reference, fit) {
    const key = `${fit.key}|${source}|${color}|${reference || ''}`;
    if (femaleHairFitCache.has(key)) {
        const cached = femaleHairFitCache.get(key);
        femaleHairFitCache.delete(key); femaleHairFitCache.set(key, cached);
        return cached;
    }
    const promise = (async () => {
        const image = new Image();
        image.src = await coloredHairSource(source, color, reference);
        await image.decode();
        const canvas = document.createElement('canvas');
        canvas.width = 941; canvas.height = 1672;
        const context = canvas.getContext('2d', { willReadFrequently: true });
        const p = fit.registration;
        context.setTransform(p.sx, 0, 0, 1, p.left + p.dx, p.top + p.dy);
        context.drawImage(image, 0, 0, p.width, p.height);
        context.resetTransform();
        if (fit.mapping.length) {
            // Every donor comes from the unmodified raster in the selected color.
            const input = context.getImageData(0, 0, 941, 1672);
            const output = new ImageData(new Uint8ClampedArray(input.data), 941, 1672);
            for (const [destination, donor, coverage, alpha] of fit.mapping) {
                const q = destination * 4, k = donor * 4;
                for (let c = 0; c < 3; c++) output.data[q + c] = Math.round(
                    input.data[k + c] * coverage + input.data[q + c] * (1 - coverage));
                output.data[q + 3] = Math.round(alpha * coverage + input.data[q + 3] * (1 - coverage));
            }
            context.putImageData(output, 0, 0);
        }
        return canvas.toDataURL('image/png');
    })();
    femaleHairFitCache.set(key, promise);
    promise.catch(() => { if (femaleHairFitCache.get(key) === promise) femaleHairFitCache.delete(key); });
    while (femaleHairFitCache.size > 24) femaleHairFitCache.delete(femaleHairFitCache.keys().next().value);
    return promise;
}
