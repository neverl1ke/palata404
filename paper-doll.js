const PAPER_DOLL_STORAGE_KEY = 'palata404_paper_doll';
const failedPaperDollImages = new Set();
let paperDollSaveFailed = false;

function emptyPaperDollLoadout() {
    return Object.fromEntries(PAPER_DOLL_LAYER_ORDER.filter(slot => slot !== 'baseBody').map(slot => [slot, null]));
}

function normalizePaperDollState(value, legacy = {}) {
    const valid = value && typeof value === 'object' && !Array.isArray(value) && value.schemaVersion === 1;
    const state = { schemaVersion: 1,
        selectedGender: (valid ? value.selectedGender : legacy.gender) === 'female' ? 'female' : 'male',
        activeViewMode: valid && value.activeViewMode === 'combat' ? 'combat' : 'patient',
        patientLoadout: emptyPaperDollLoadout(), combatLoadout: emptyPaperDollLoadout() };
    for (const key of ['patientLoadout', 'combatLoadout']) {
        const source = valid && value[key] && typeof value[key] === 'object' ? value[key] : {};
        for (const slot of Object.keys(state[key])) {
            if (PAPER_DOLL_ITEMS.some(item => item.id === source[slot] && item.slot === slot)) state[key][slot] = source[slot];
        }
    }
    if (!valid && PAPER_DOLL_ITEMS.some(item => item.id === legacy.face && item.slot === 'face')) state.patientLoadout.face = legacy.face;
    return state;
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
    currentFace = activePaperDollLoadout().face || '';
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
    if (itemId !== null && !PAPER_DOLL_ITEMS.some(item => item.id === itemId && item.slot === slot)) return false;
    activePaperDollLoadout()[slot] = itemId;
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

function renderPaperDoll() {
    const host = document.getElementById('character-paperdoll');
    if (!host) return;
    const selectedGender = paperDollState.selectedGender;
    host.setAttribute('aria-label', `${selectedGender === 'female' ? 'Жінка' : 'Чоловік'} · ${paperDollState.activeViewMode === 'combat' ? 'Спогад' : 'Пацієнт'}`);
    PAPER_DOLL_LAYER_ORDER.forEach((slot, index) => {
        const definition = PAPER_DOLL_SLOTS[slot];
        if (!definition) return;
        let image = document.getElementById(definition.elementId);
        if (!image) {
            image = document.createElement('img'); image.id = definition.elementId; image.className = 'char-layer hidden';
            image.setAttribute('alt', ''); image.setAttribute('aria-hidden', 'true'); host.appendChild(image);
        }
        const item = slot === 'baseBody' ? { image: PAPER_DOLL_BODIES[selectedGender] }
            : PAPER_DOLL_ITEMS.find(entry => entry.id === activePaperDollLoadout()[slot] && entry.slot === slot);
        const candidates = paperDollImageCandidates(item, selectedGender);
        positionPaperDollLayer(image, item?.placement, index);
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
}

function renderPaperDollControls(renderSlots = true) {
    document.getElementById('paper-doll-save-note')?.classList.toggle('hidden', !paperDollSaveFailed);
    document.querySelectorAll('[data-paper-gender]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.paperGender === paperDollState.selectedGender)));
    document.querySelectorAll('[data-paper-view]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.paperView === paperDollState.activeViewMode)));
    const label = document.getElementById('paper-doll-view-label');
    if (label) label.textContent = `Комплект: ${paperDollState.activeViewMode === 'combat' ? 'Спогад' : 'Пацієнт'}`;
    document.querySelectorAll('[data-paper-image-status]').forEach(note => {
        const item = PAPER_DOLL_ITEMS.find(entry => entry.id === activePaperDollLoadout()[note.dataset.paperImageStatus]);
        const missing = item && !paperDollImageCandidates(item, paperDollState.selectedGender).some(path => !failedPaperDollImages.has(path));
        note.classList.toggle('hidden', !missing);
    });
    if (!renderSlots) return;
    const container = document.getElementById('paper-doll-slots');
    if (!container) return;
    container.innerHTML = PAPER_DOLL_LAYER_ORDER.filter(slot => slot !== 'baseBody').map(slot => {
        const definition = PAPER_DOLL_SLOTS[slot];
        const available = PAPER_DOLL_ITEMS.filter(item => item.slot === slot);
        const selected = activePaperDollLoadout()[slot];
        const item = available.find(entry => entry.id === selected);
        const missingImage = item && !paperDollImageCandidates(item, paperDollState.selectedGender).some(path => !failedPaperDollImages.has(path));
        return `<div class="paper-doll-slot"><label for="paper-slot-${slot}">${iconHTML(definition.icon)}${escapeHTML(definition.label)}</label>
            <select id="paper-slot-${slot}" data-paper-slot="${slot}"${available.length ? '' : ' disabled'}><option value="">${available.length ? 'Порожній слот' : 'Немає предметів'}</option>${available.map(entry => `<option value="${escapeHTML(entry.id)}"${entry.id === selected ? ' selected' : ''}>${escapeHTML(entry.name)}</option>`).join('')}</select>
            <button type="button" class="btn-outfit" data-paper-remove="${slot}" aria-label="Зняти: ${escapeHTML(definition.label)}"${selected ? '' : ' disabled'}>Зняти</button>
            <p class="paper-doll-slot-note${missingImage ? '' : ' hidden'}" data-paper-image-status="${slot}">Зображення предмета поки недоступне.</p></div>`;
    }).join('');
    container.querySelectorAll('[data-paper-slot]').forEach(select => select.addEventListener('change', () => equipPaperDollItem(select.dataset.paperSlot, select.value || null)));
    container.querySelectorAll('[data-paper-remove]').forEach(button => button.addEventListener('click', () => equipPaperDollItem(button.dataset.paperRemove, null)));
}
