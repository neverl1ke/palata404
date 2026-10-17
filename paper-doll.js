const PAPER_DOLL_STORAGE_KEY = 'palata404_paper_doll';
const failedPaperDollImages = new Set();
let paperDollSaveFailed = false;

function emptyPaperDollLoadout() {
    return Object.fromEntries(PAPER_DOLL_LAYER_ORDER.filter(slot => slot !== 'baseBody' && slot !== 'hair').map(slot => [slot, null]));
}

function normalizePaperDollState(value, legacy = {}) {
    const valid = value && typeof value === 'object' && !Array.isArray(value) && [1,2].includes(value.schemaVersion);
    const state = { schemaVersion: 2,
        selectedGender: (valid ? value.selectedGender : legacy.gender) === 'female' ? 'female' : 'male',
        activeViewMode: valid && value.activeViewMode === 'combat' ? 'combat' : 'patient',
        appearance: { face: null, hairColor: normalizeHairColor(valid ? value.appearance?.hairColor : null), hair: (valid && value.schemaVersion === 2 && typeof value.appearance?.hair === 'string' ? value.appearance.hair : legacy.hair) || 'hair-none' },
        patientLoadout: emptyPaperDollLoadout(), combatLoadout: emptyPaperDollLoadout() };
    for (const key of ['patientLoadout', 'combatLoadout']) {
        const source = valid && value[key] && typeof value[key] === 'object' ? value[key] : {};
        for (const slot of Object.keys(state[key])) {
            if (slot === 'face') continue;
            const id = valid && value.schemaVersion === 1 ? PAPER_DOLL_LEGACY_ITEMS[source[slot]] || source[slot] : source[slot];
            if (PAPER_DOLL_ITEMS.some(item => item.id === id && item.slot === slot && isPaperDollItemOwned(item))) state[key][slot] = id;
        }
    }
    const face = valid ? value.schemaVersion === 2 ? value.appearance?.face
        : value[state.activeViewMode === 'combat' ? 'combatLoadout' : 'patientLoadout']?.face : legacy.face;
    if (PAPER_DOLL_ITEMS.some(item => item.id === face && item.slot === 'face' && isPaperDollItemOwned(item))) state.appearance.face = face;
    const oldFaces = valid && value.schemaVersion === 1 ? { patient: value.patientLoadout?.face, combat: value.combatLoadout?.face } : value?.legacyFaces;
    if (oldFaces && oldFaces.patient !== oldFaces.combat) {
        state.legacyFaces = Object.fromEntries(['patient','combat'].map(key => [key, typeof oldFaces[key] === 'string' ? oldFaces[key] : null]));
    }
    if (!valid) {
        for (const item of PAPER_DOLL_ITEMS.filter(entry => entry.inventoryName && isPaperDollItemOwned(entry))) {
            if (equippedGear[item.inventoryCategory] === item.inventoryName) state.combatLoadout[item.slot] = item.id;
        }
    }
    const savedHair = PAPER_DOLL_ITEMS.find(item => item.slot === 'hair' && item.id === state.appearance.hair);
    if (savedHair && !paperDollItemSupportsGender(savedHair, state.selectedGender)) state.appearance.hair = 'hair-none';
    return state;
}

function paperDollItemSupportsGender(item, selectedGender = paperDollState.selectedGender) {
    return Boolean(item && (!item.genders || item.genders.includes(selectedGender)));
}

function isPaperDollItemOwned(item) {
    return Boolean(item && !PAPER_DOLL_RETIRED_FACES.has(item.id) && (item.availableByDefault === true ||
        (item.inventoryName && inventory.some(entry => entry.name === item.inventoryName && entry.category === item.inventoryCategory && entry.count > 0))));
}

function selectedPaperDollItem(slot) {
    if (slot === 'hair') return PAPER_DOLL_ITEMS.find(item => item.slot === 'hair' && item.id === paperDollState.appearance.hair && isPaperDollItemOwned(item) && paperDollItemSupportsGender(item))
        || PAPER_DOLL_ITEMS.find(item => item.id === 'hair-none');
    const id = slot === 'face' ? paperDollState.appearance.face : activePaperDollLoadout()[slot];
    return PAPER_DOLL_ITEMS.find(item => item.id === id && item.slot === slot && isPaperDollItemOwned(item));
}

function loadPaperDollState(legacy) {
    const raw = safeStorageGet(PAPER_DOLL_STORAGE_KEY);
    let value = null;
    try { value = JSON.parse(raw || 'null'); } catch { /* Keep old cosmetic choices. */ }
    const state = normalizePaperDollState(value, legacy);
    // Only a new wardrobe receives the starter. Saved empty slots stay empty.
    if (raw === null) {
        for (const item of PAPER_DOLL_ITEMS) {
            if (item.starterForPatient && Object.hasOwn(state.patientLoadout, item.slot) && isPaperDollItemOwned(item)) {
                state.patientLoadout[item.slot] = item.id;
            }
        }
    }
    return state;
}

function savePaperDollState() {
    paperDollSaveFailed = !safeStorageSet(PAPER_DOLL_STORAGE_KEY, JSON.stringify(paperDollState));
    const note = document.getElementById('paper-doll-save-note');
    if (note) note.classList.toggle('hidden', !paperDollSaveFailed);
    return !paperDollSaveFailed;
}

function activePaperDollLoadout() {
    return paperDollState[paperDollState.activeViewMode === 'combat' ? 'combatLoadout' : 'patientLoadout'];
}

function syncLegacyPaperDollSelection() {
    gender = paperDollState.selectedGender;
    currentFace = paperDollState.appearance.face || '';
    currentHair = paperDollState.appearance.hair || '';
}

function commitPaperDollSelection() {
    syncLegacyPaperDollSelection();
    paperDollSaveFailed = !saveGameProgress();
    updateCharacterLayers();
    renderWardrobe();
}

function retryPaperDollSave() {
    paperDollSaveFailed = !saveGameProgress();
    renderPaperDollControls();
}

function setPaperDollView(mode) {
    if (!['patient', 'combat'].includes(mode)) return false;
    paperDollState.activeViewMode = mode;
    commitPaperDollSelection();
    return true;
}

function equipPaperDollItem(slot, itemId) {
    if (slot === 'baseBody' || (slot !== 'hair' && !Object.hasOwn(activePaperDollLoadout(), slot))) return false;
    if (itemId !== null && !PAPER_DOLL_ITEMS.some(item => item.id === itemId && item.slot === slot && isPaperDollItemOwned(item) && paperDollItemSupportsGender(item))) return false;
    if (slot === 'hair') paperDollState.appearance.hair = itemId || 'hair-none';
    else if (slot === 'face') paperDollState.appearance.face = itemId;
    else activePaperDollLoadout()[slot] = itemId;
    commitPaperDollSelection();
    return true;
}

function paperDollImageCandidates(item, selectedGender) {
    const variants = item?.genderVariants || {};
    const sources = item?.fittedToGender === true ? [variants[selectedGender]]
        : [variants[selectedGender], item?.image, variants[selectedGender === 'female' ? 'male' : 'female']];
    return [...new Set(sources)]
        .filter(path => typeof path === 'string' && /^(?:[a-zA-Z0-9_-]+\/)*[a-zA-Z0-9_.-]+\.png(?:\?v=[a-zA-Z0-9_-]+)?$/.test(path)
            && !path.split('/').includes('..'));
}

function positionPaperDollLayer(image, placement, index) {
    const frame = PAPER_DOLL_FRAME;
    const valid = placement && ['x','y','width','height'].every(key => Number.isFinite(placement[key])) && placement.width > 0 && placement.height > 0;
    image.style.left = `${valid ? placement.x / frame.width * 100 : 0}%`;
    image.style.top = `${valid ? placement.y / frame.height * 100 : 0}%`;
    image.style.width = `${valid ? placement.width / frame.width * 100 : 100}%`;
    image.style.height = `${valid ? placement.height / frame.height * 100 : 100}%`;
    // Opt-in for a registered overlay; clear on every render so it cannot leak to another item/gender.
    image.style.objectFit = valid && placement.stretchX === true ? 'fill' : '';
    image.style.zIndex = String(index);
}

// Resolve the same gender-specific parts for rendering and wardrobe status.
function paperDollItemLayers(item, selectedGender) {
    if (!Array.isArray(item?.layers) || !item.layers.length) return item ? [item] : [];
    return item.layers.filter(part => part && typeof part.id === 'string' && /^[a-zA-Z0-9_-]+$/.test(part.id)
        && (!Array.isArray(part.genders) || part.genders.includes(selectedGender)))
        .map(part => ({ ...part, placement: part.placement ?? item.placement,
            placementByGender: part.placementByGender ?? item.placementByGender,
            fittedToGender: part.fittedToGender ?? item.fittedToGender,
            renderOrder: part.renderOrder ?? item.renderOrder }));
}

// Measured upper envelopes of the approved hair PNGs at their existing placements.
// Hide only the underlying crown; preserve the natural part and every pixel below y=90.
// Both head layers use the same contour so the original scalp cannot reappear below the overlay.
const PAPER_DOLL_CROWN_CONTOURS = {
    "hair-messy": {
        male: [[380,90],[386,90],[390,88],[392,76],[394,74],[396,74],[398,73],[400,49],[402,52],[404,54],[408,56],[410,56],[412,54],[414,38],[418,44],[422,46],[424,45],[430,45],[432,44],[434,44],[436,43],[438,43],[440,39],[444,39],[446,24],[450,32],[452,34],[454,35],[456,35],[458,36],[464,36],[466,34],[478,34],[480,29],[486,32],[488,32],[490,34],[492,35],[494,35],[498,37],[500,33],[502,35],[504,36],[506,38],[508,39],[512,43],[514,46],[516,48],[518,45],[520,45],[524,43],[528,39],[530,50],[532,50],[534,53],[536,53],[538,54],[542,54],[544,55],[546,69],[548,73],[550,75],[552,80],[556,84],[560,86],[562,90],[564,90]]
    },
    "hair-bob": {
        male: [[380,90],[390,90],[392,89],[394,87],[400,78],[402,76],[404,73],[406,71],[408,68],[412,64],[414,63],[416,61],[418,60],[422,56],[424,53],[426,51],[438,45],[440,43],[442,43],[450,39],[452,39],[454,38],[456,38],[458,37],[470,37],[474,39],[476,39],[478,40],[480,40],[482,37],[484,39],[486,38],[490,38],[492,37],[494,38],[498,38],[504,41],[506,41],[512,44],[514,44],[520,50],[522,51],[532,61],[544,79],[548,87],[550,90],[564,90]],
        female: [[380,90],[392,90],[394,87],[398,79],[400,77],[402,70],[404,68],[408,62],[412,58],[414,55],[416,54],[420,50],[422,49],[424,47],[426,46],[428,44],[430,41],[432,40],[434,40],[436,38],[442,35],[444,33],[446,34],[450,32],[454,32],[456,31],[458,31],[460,30],[468,30],[470,29],[472,30],[478,30],[480,31],[482,31],[484,32],[486,34],[488,35],[492,39],[494,40],[496,39],[498,39],[500,38],[504,38],[506,39],[508,39],[518,44],[524,50],[526,51],[528,54],[530,56],[532,59],[534,61],[538,69],[540,72],[542,77],[544,81],[546,86],[548,90],[564,90]]
    },
    "hair-double-buns": {
        male: [[380,30],[384,28],[394,28],[400,31],[402,30],[404,33],[406,35],[408,40],[410,44],[414,44],[416,45],[418,45],[420,50],[422,50],[424,48],[428,46],[430,44],[438,40],[440,40],[442,39],[444,39],[446,38],[448,38],[450,37],[458,37],[460,38],[462,38],[468,41],[470,41],[472,39],[476,37],[480,37],[482,36],[484,36],[486,37],[490,37],[492,38],[494,38],[496,39],[498,39],[512,46],[514,48],[516,49],[518,51],[520,47],[522,48],[524,47],[526,44],[528,43],[532,39],[536,31],[538,31],[540,29],[542,28],[546,28],[548,27],[556,27],[562,30],[564,32]],
        female: [[380,27],[384,27],[386,25],[390,29],[392,30],[396,30],[398,17],[400,20],[402,25],[404,29],[406,30],[408,33],[412,37],[414,34],[416,36],[418,42],[420,45],[438,36],[440,36],[444,34],[446,34],[448,33],[450,33],[452,32],[462,32],[464,33],[466,33],[474,37],[476,36],[478,34],[480,34],[484,32],[496,32],[498,33],[500,33],[502,34],[504,34],[512,38],[514,38],[516,39],[518,39],[520,40],[522,37],[524,35],[526,34],[530,30],[532,26],[534,26],[536,27],[538,27],[542,29],[544,28],[548,24],[550,27],[556,27],[558,26],[564,26]]
    },
    "hair-shoulder-length": {
        male: [[380,90],[392,90],[396,86],[398,83],[402,79],[404,76],[408,72],[410,67],[412,64],[414,63],[424,53],[426,52],[430,48],[438,44],[440,42],[446,39],[448,39],[452,37],[456,37],[458,36],[462,36],[464,35],[478,35],[480,37],[482,38],[484,38],[486,37],[490,39],[496,45],[498,48],[502,46],[504,48],[506,48],[508,46],[514,49],[530,65],[536,74],[538,82],[542,90],[564,90]],
        female: [[380,90],[390,90],[392,86],[394,83],[396,79],[398,77],[402,71],[406,67],[408,62],[410,62],[412,59],[414,55],[416,56],[418,53],[420,52],[422,50],[428,47],[432,43],[442,38],[444,38],[446,36],[448,35],[450,35],[452,34],[454,32],[456,31],[458,31],[460,33],[462,31],[466,31],[468,30],[470,31],[472,30],[474,31],[478,31],[480,32],[482,32],[484,33],[486,32],[488,34],[490,37],[492,39],[494,39],[496,38],[500,38],[502,37],[506,37],[508,36],[510,36],[512,37],[514,41],[516,42],[518,44],[520,45],[522,47],[524,44],[526,47],[528,51],[532,55],[534,59],[536,62],[538,67],[540,70],[542,74],[544,77],[548,85],[550,90],[564,90]]
    }
};

function smoothPaperDollCrown(points) {
    // Sample a quadratic spline in frame coordinates. This rounds measured
    // two-pixel stair corners without changing the clip below the crown.
    if (!points || points.length < 3) return points;
    const result = [points[0]];
    for (let i=1;i<points.length-1;i++) {
        const p=points[i],before=points[i-1],after=points[i+1];
        const a=i===1?before:[(before[0]+p[0])/2,(before[1]+p[1])/2];
        const b=i===points.length-2?after:[(p[0]+after[0])/2,(p[1]+after[1])/2];
        for(let j=1;j<=4;j++) {
            const t=j/4,u=1-t;
            result.push([u*u*a[0]+2*u*t*p[0]+t*t*b[0],Math.min(90,u*u*a[1]+2*u*t*p[1]+t*t*b[1]+.35)]);
        }
    }
    result.push(points[points.length-1]);
    return result;
}

function applyPaperDollCrownMask(image, selectedGender) {
    const hair = selectedPaperDollItem('hair')?.id;
    const overlay = selectedPaperDollItem('face')?.slot === 'face';
    const active = overlay || (selectedGender === 'male' && hair !== 'hair-messy')
        || hair === 'hair-bob';
    let crown = active && PAPER_DOLL_CROWN_CONTOURS[hair]?.[selectedGender];
    // Shoulder-length was enlarged 8% around the crown anchor (474,35).
    // Its occlusion envelope must follow that same transform, not the old fit.
    if (crown && hair === 'hair-shoulder-length' && selectedGender === 'male') crown = crown.map(([x,y]) => [474+(x-474)*1.08, Math.min(90,35+(y-35)*1.08)]);
    // The alternative skull has a slightly fuller cap. Hide its outermost
    // antialias seam under messy strands without moving the approved hair.
    if (crown && hair === 'hair-messy' && selectedGender === 'male' && selectedPaperDollItem('face')?.id === 'face-alternative') crown = crown.map(([x,y]) => [x,Math.min(90,y+1.2)]);
    const outline = crown && [[0,90],[0,1672],[941,1672],[941,90],...smoothPaperDollCrown(crown).slice().reverse()];
    image.style.clipPath = outline ? `polygon(${outline.map(([x,y]) =>
        `${x / PAPER_DOLL_FRAME.width * 100}% ${y / PAPER_DOLL_FRAME.height * 100}%`).join(',')})` : '';
}

function renderPaperDollAt(host, prefix = '') {
    if (!host) return;
    const selectedGender = paperDollState.selectedGender;
    host.style.setProperty('--paper-doll-aspect', `${PAPER_DOLL_FRAME.width} / ${PAPER_DOLL_FRAME.height}`);
    host.style.setProperty('--paper-doll-ratio', String(PAPER_DOLL_FRAME.width / PAPER_DOLL_FRAME.height));
    host.setAttribute('aria-label', `${selectedGender === 'female' ? 'Жінка' : 'Чоловік'} · ${paperDollState.activeViewMode === 'combat' ? 'Трип' : 'Пацієнт'}`);
    const extraLayers = new Set();
    PAPER_DOLL_LAYER_ORDER.forEach((slot, index) => {
        const definition = PAPER_DOLL_SLOTS[slot];
        if (!definition) return;
        const item = slot === 'baseBody' ? { image: PAPER_DOLL_BODIES[selectedGender] } : selectedPaperDollItem(slot);
        const layered = Array.isArray(item?.layers) && item.layers.length > 0;
        const parts = layered ? paperDollItemLayers(item, selectedGender) : [item || {}];
        if (layered) {
            const base = document.getElementById(prefix + definition.elementId);
            if (base) { base.onload = null; base.onerror = null; base.paperHairRequest = null; base.classList.add('hidden'); base.removeAttribute('src'); }
        }
        parts.forEach(part => {
        // Keep the stable hair-front element for saves, tests and integrations;
        // only the optional rear strand part is an extra DOM layer.
        const usesRoot = slot === 'hair' && part.id === 'front';
        const id = prefix + definition.elementId + (layered && !usesRoot ? `-${part.id}` : '');
        if (layered && !usesRoot) extraLayers.add(id);
        let image = document.getElementById(id);
        if (!image) {
            image = document.createElement('img'); image.id = id; image.className = 'char-layer hidden';
            image.setAttribute('alt', ''); image.setAttribute('aria-hidden', 'true'); host.appendChild(image);
        }
        if (layered && !usesRoot) image.setAttribute('data-paper-extra', 'true');
        else image.removeAttribute('data-paper-extra');
        const layer = part;
        const candidates = paperDollImageCandidates(layer, selectedGender);
        const order = Number.isFinite(layer.renderOrder) ? Math.max(-100, Math.min(100, layer.renderOrder)) : index;
        positionPaperDollLayer(image, layer.placementByGender?.[selectedGender] ?? layer.placement, order);
        if (slot === 'baseBody' || slot === 'face') applyPaperDollCrownMask(image, selectedGender);
        // Each replacement head has its own registered under-jaw/neck occlusion.
        // Masks restore the original body only where that head already matches it.
        // The optional neckline skin underlay is base anatomy too, not tunic fabric.
        if (slot === 'baseBody' || (slot === 'upperBody' && part.id === 'neckline')) {
            const face = selectedPaperDollItem('face');
            const faceSource = face?.genderVariants?.[selectedGender];
            const mask = face?.bodyMaskByGender?.[selectedGender];
            const active = mask && faceSource && !failedPaperDollImages.has(faceSource);
            image.style.maskImage = active ? `url("${mask}")` : '';
            image.style.maskSize = active ? '100% 100%' : '';
            image.style.maskRepeat = active ? 'no-repeat' : '';
        }
        const source = candidates.find(path => !failedPaperDollImages.has(path));
        if (!source) {
            image.onload = null; image.onerror = null;
            image.paperHairRequest = null;
            image.classList.add('hidden'); image.removeAttribute('src'); return;
        }
        const color = slot === 'hair' ? normalizeHairColor(paperDollState.appearance.hairColor) : 'original';
        image.paperHairColorReference = layer.colorReference;
        const request = `${source}|${color}`;
        if (image.paperHairRequest !== request) {
            image.paperHairRequest = request;
            if (color === 'original') setPaperDollImage(image, source, source);
            else coloredHairSource(source, color, layer.colorReference).then(colored => {
                if (image.paperHairRequest === request) setPaperDollImage(image, colored, source);
            }).catch(() => {
                if (image.paperHairRequest !== request) return;
                image.paperHairRequest = null;
                setPaperDollImage(image, source, source);
                document.getElementById('hair-color-error')?.classList.remove('hidden');
            });
        }

        });
    });
    host.querySelectorAll('[data-paper-extra]').forEach(image => {
        if (!extraLayers.has(image.id)) { image.onload = null; image.onerror = null; image.remove(); }
    });
}

function renderPaperDoll() {
    document.getElementById('character-container')?.style.setProperty('--paper-doll-aspect', `${PAPER_DOLL_FRAME.width} / ${PAPER_DOLL_FRAME.height}`);
    renderPaperDollAt(document.getElementById('character-paperdoll'));
    renderPaperDollAt(document.getElementById('wardrobe-paperdoll'), 'wardrobe-');
}

function renderPaperDollControls(renderSlots = true) {
    document.getElementById('paper-doll-save-note')?.classList.toggle('hidden', !paperDollSaveFailed);
    document.querySelectorAll('[data-paper-view]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.paperView === paperDollState.activeViewMode)));
    const label = document.getElementById('paper-doll-view-label');
    if (label) label.textContent = `Комплект: ${paperDollState.activeViewMode === 'combat' ? 'Трип' : 'Пацієнт'}`;
    renderWardrobeRegistration();
    renderWardrobeImageNotes();
}

// Source identity stays separate from the runtime color image and its error state.
function setPaperDollImage(image, displaySource, originalSource) {
    if (image.getAttribute('src') !== displaySource) image.classList.add('hidden');
    image.onload = () => { if (image.getAttribute('src') === displaySource && image.naturalWidth > 0) image.classList.remove('hidden'); };
    image.onerror = () => {
        if (image.getAttribute('src') !== displaySource) return;
        if (displaySource !== originalSource) {
            image.paperHairRequest = null;
            setPaperDollImage(image, originalSource, originalSource);
            document.getElementById('hair-color-error')?.classList.remove('hidden');
            return;
        }
        failedPaperDollImages.add(originalSource);
        image.paperHairRequest = null;
        renderPaperDoll(); renderPaperDollControls(false);
    };
    if (image.getAttribute('src') !== displaySource) image.setAttribute('src', displaySource);
    if (image.complete && image.naturalWidth > 0) image.classList.remove('hidden');
}
