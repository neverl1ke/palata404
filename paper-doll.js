const PAPER_DOLL_STORAGE_KEY = 'palata404_paper_doll';
const failedPaperDollImages = new Set();
let paperDollSaveFailed = false;

function emptyPaperDollLoadout() {
    return Object.fromEntries(PAPER_DOLL_LAYER_ORDER.filter(slot => slot !== 'baseBody').map(slot => [slot, null]));
}

function normalizePaperDollState(value, legacy = {}) {
    const valid = value && typeof value === 'object' && !Array.isArray(value) && [1,2].includes(value.schemaVersion);
    const state = { schemaVersion: 2,
        selectedGender: (valid ? value.selectedGender : legacy.gender) === 'female' ? 'female' : 'male',
        activeViewMode: valid && value.activeViewMode === 'combat' ? 'combat' : 'patient',
        appearance: { face: null, hair: valid && value.schemaVersion === 2 && typeof value.appearance?.hair === 'string' ? value.appearance.hair : legacy.hair || '' },
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
        state.legacyFaces = Object.fromEntries(['patient','combat'].map(key => [key, PAPER_DOLL_ITEMS.some(item => item.id === oldFaces[key] && item.slot === 'face') ? oldFaces[key] : null]));
    }
    if (!valid) {
        for (const item of PAPER_DOLL_ITEMS.filter(entry => entry.inventoryName && isPaperDollItemOwned(entry))) {
            if (equippedGear[item.inventoryCategory] === item.inventoryName) state.combatLoadout[item.slot] = item.id;
        }
    }
    return state;
}

function isPaperDollItemOwned(item) {
    return item?.availableByDefault === true || Boolean(item?.inventoryName && inventory.some(entry =>
        entry.name === item.inventoryName && entry.category === item.inventoryCategory && entry.count > 0));
}

function selectedPaperDollItem(slot) {
    const id = slot === 'face' ? paperDollState.appearance.face : activePaperDollLoadout()[slot];
    return PAPER_DOLL_ITEMS.find(item => item.id === id && item.slot === slot && isPaperDollItemOwned(item));
}

function loadPaperDollState(legacy) {
    let value = null;
    try { value = JSON.parse(safeStorageGet(PAPER_DOLL_STORAGE_KEY) || 'null'); } catch { /* Keep old cosmetic choices. */ }
    return normalizePaperDollState(value, legacy);
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
    if (slot === 'baseBody' || !Object.hasOwn(activePaperDollLoadout(), slot)) return false;
    if (itemId !== null && !PAPER_DOLL_ITEMS.some(item => item.id === itemId && item.slot === slot && isPaperDollItemOwned(item))) return false;
    if (slot === 'face') paperDollState.appearance.face = itemId;
    else activePaperDollLoadout()[slot] = itemId;
    commitPaperDollSelection();
    return true;
}

function paperDollImageCandidates(item, selectedGender) {
    const variants = item?.genderVariants || {};
    return [...new Set([variants[selectedGender], item?.image, variants[selectedGender === 'female' ? 'male' : 'female']])]
        .filter(path => typeof path === 'string' && /^(?:[a-zA-Z0-9_-]+\/)*[a-zA-Z0-9_.-]+\.png$/.test(path)
            && !path.split('/').includes('..'));
}

function positionPaperDollLayer(image, placement, index) {
    const frame = PAPER_DOLL_FRAME;
    const valid = placement && ['x','y','width','height'].every(key => Number.isFinite(placement[key])) && placement.width > 0 && placement.height > 0;
    image.style.left = `${valid ? placement.x / frame.width * 100 : 0}%`;
    image.style.top = `${valid ? placement.y / frame.height * 100 : 0}%`;
    image.style.width = `${valid ? placement.width / frame.width * 100 : 100}%`;
    image.style.height = `${valid ? placement.height / frame.height * 100 : 100}%`;
    image.style.zIndex = String(index);
}

function renderPaperDollAt(host, prefix = '') {
    if (!host) return;
    const selectedGender = paperDollState.selectedGender;
    host.setAttribute('aria-label', `${selectedGender === 'female' ? 'Жінка' : 'Чоловік'} · ${paperDollState.activeViewMode === 'combat' ? 'Спогад' : 'Пацієнт'}`);
    const extraLayers = new Set();
    PAPER_DOLL_LAYER_ORDER.forEach((slot, index) => {
        const definition = PAPER_DOLL_SLOTS[slot];
        if (!definition) return;
        const item = slot === 'baseBody' ? { image: PAPER_DOLL_BODIES[selectedGender] } : selectedPaperDollItem(slot);
        const layered = Array.isArray(item?.layers) && item.layers.length > 0;
        const parts = layered ? item.layers.filter(part => part && typeof part.id === 'string' && /^[a-zA-Z0-9_-]+$/.test(part.id)) : [item || {}];
        if (layered) {
            const base = document.getElementById(prefix + definition.elementId);
            if (base) { base.onload = null; base.onerror = null; base.classList.add('hidden'); base.removeAttribute('src'); }
        }
        parts.forEach(part => {
        const id = prefix + definition.elementId + (layered ? `-${part.id}` : '');
        if (layered) extraLayers.add(id);
        let image = document.getElementById(id);
        if (!image) {
            image = document.createElement('img'); image.id = id; image.className = 'char-layer hidden';
            image.setAttribute('alt', ''); image.setAttribute('aria-hidden', 'true'); host.appendChild(image);
        }
        if (layered) image.setAttribute('data-paper-extra', 'true');
        const layer = layered ? { ...part, placement: part.placement ?? item.placement, renderOrder: part.renderOrder ?? item.renderOrder } : part;
        const candidates = paperDollImageCandidates(layer, selectedGender);
        const order = Number.isFinite(layer.renderOrder) ? Math.max(-100, Math.min(100, layer.renderOrder)) : index;
        positionPaperDollLayer(image, layer.placement, order);
        const source = candidates.find(path => !failedPaperDollImages.has(path));
        if (!source) {
            image.onload = null; image.onerror = null;
            image.classList.add('hidden'); image.removeAttribute('src'); return;
        }
        if (image.getAttribute('src') !== source) image.classList.add('hidden');
        image.onload = () => { if (image.getAttribute('src') === source && image.naturalWidth > 0) image.classList.remove('hidden'); };
        image.onerror = () => {
            if (image.getAttribute('src') !== source) return;
            failedPaperDollImages.add(source); renderPaperDoll(); renderPaperDollControls(false);
        };
        if (image.getAttribute('src') !== source) image.setAttribute('src', source);
        if (image.complete && image.naturalWidth > 0) image.classList.remove('hidden');
        });
    });
    host.querySelectorAll('[data-paper-extra]').forEach(image => {
        if (!extraLayers.has(image.id)) { image.onload = null; image.onerror = null; image.remove(); }
    });
}

function renderPaperDoll() {
    renderPaperDollAt(document.getElementById('character-paperdoll'));
    renderPaperDollAt(document.getElementById('wardrobe-paperdoll'), 'wardrobe-');
}

function renderPaperDollControls(renderSlots = true) {
    document.getElementById('paper-doll-save-note')?.classList.toggle('hidden', !paperDollSaveFailed);
    document.querySelectorAll('[data-paper-view]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.paperView === paperDollState.activeViewMode)));
    const label = document.getElementById('paper-doll-view-label');
    if (label) label.textContent = `Комплект: ${paperDollState.activeViewMode === 'combat' ? 'Спогад' : 'Пацієнт'}`;
    document.querySelectorAll('[data-paper-image-item]').forEach(note => {
        const item = PAPER_DOLL_ITEMS.find(entry => entry.id === note.dataset.paperImageItem);
        const layers = item?.layers?.length ? item.layers : [item];
        const missing = item && !layers.some(layer => paperDollImageCandidates(layer, paperDollState.selectedGender).some(path => !failedPaperDollImages.has(path)));
        note.classList.toggle('hidden', !missing);
    });
}
