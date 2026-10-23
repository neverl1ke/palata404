// Standalone sandbox globals only. script.js, wardrobe.js and save writers are NOT loaded.
let inventory = [];
let paperDollState = {
    selectedGender: 'male',
    activeViewMode: 'patient',
    appearance: { face: null, hair: 'hair-none', hairColor: 'original' },
    patientLoadout: {},
    combatLoadout: {},
};
window.avatarCatalog = {
    faces: (gender) =>
        PAPER_DOLL_ITEMS.filter(
            (i) =>
                i.slot === 'face' &&
                paperDollItemSupportsGender(i, gender) &&
                i.availableByDefault,
        ),
    hairs: (gender) =>
        PAPER_DOLL_ITEMS.filter(
            (i) =>
                i.slot === 'hair' &&
                paperDollItemSupportsGender(i, gender) &&
                i.availableByDefault,
        ),
    colors: HAIR_COLORS,
    async describe(gender, face, hair, color) {
        const allowed = (id, slot) =>
            PAPER_DOLL_ITEMS.find(
                (i) =>
                    i.id === id &&
                    i.slot === slot &&
                    i.availableByDefault &&
                    paperDollItemSupportsGender(i, gender),
            );
        const f =
            face === 'source'
                ? null
                : allowed(face, 'face') || PAPER_DOLL_NATIVE_HEADS[gender];
        const h = allowed(hair, 'hair');
        paperDollState = {
            ...paperDollState,
            selectedGender: gender,
            appearance: {
                face: allowed(face, 'face')?.id || null,
                hair: h?.id || 'hair-none',
                hairColor: normalizeHairColor(color),
            },
        };
        const absolute = (path) => new URL('../' + path, location.href).href;
        let crown = null;
        if (face !== 'source' || hair !== 'hair-none') {
            const im = document.createElement('img');
            applyPaperDollCrownMask(im, gender);
            const p = im.style.clipPath.match(/polygon\((.*)\)/);
            if (p)
                crown = p[1].split(',').map((s) =>
                    s
                        .trim()
                        .split(/\s+/)
                        .map((v, i) => (parseFloat(v) * [941, 1672][i]) / 100),
                );
        }
        const layers = [];
        for (const [slot, item] of [
            ['face', f],
            ['hair', h],
        ]) {
            for (const part of item ? paperDollItemLayers(item, gender) : []) {
                const src = paperDollImageCandidates(part, gender)[0];
                if (!src) continue;
                const source =
                    slot === 'hair'
                        ? await coloredHairSource(
                              absolute(src),
                              normalizeHairColor(color),
                              part.colorReference
                                  ? absolute(part.colorReference)
                                  : null,
                          )
                        : absolute(src);
                layers.push({
                    slot,
                    source,
                    order: part.renderOrder ?? (slot === 'face' ? 1 : 9),
                    placement: part.placementByGender?.[gender] ||
                        part.placement || {
                            x: 0,
                            y: 0,
                            width: 941,
                            height: 1672,
                        },
                    contain:
                        part.placementByGender?.[gender]?.stretchX !== true,
                });
            }
        }
        return {
            layers,
            crown,
            bodyMask: f?.bodyMaskByGender?.[gender]
                ? absolute(f.bodyMaskByGender[gender])
                : null,
        };
    },
    readSave() {
        let s;
        try {
            s = JSON.parse(
                localStorage.getItem('palata404_paper_doll') || 'null',
            );
        } catch {
            return { error: 'Збереження пошкоджене або недоступне' };
        }
        if (!s || !['male', 'female'].includes(s.selectedGender))
            return { error: 'Немає сумісного збереження Paper Doll' };
        const gender = s.selectedGender,
            appearance = s.appearance || {},
            active = s.activeViewMode === 'combat' ? 'combat' : 'patient',
            old =
                s[active === 'combat' ? 'combatLoadout' : 'patientLoadout'] ||
                {};
        const face = appearance.face ?? old.face ?? null,
            hair = appearance.hair ?? old.hair ?? 'hair-none';
        return {
            gender,
            face: this.faces(gender).some((i) => i.id === face)
                ? face
                : 'native',
            hair: this.hairs(gender).some((i) => i.id === hair)
                ? hair
                : 'hair-none',
            color: normalizeHairColor(appearance.hairColor),
            mode: active,
            patientLoadout: structuredClone(s.patientLoadout || {}),
            combatLoadout: structuredClone(s.combatLoadout || {}),
        };
    },
};
