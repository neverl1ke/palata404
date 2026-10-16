let wardrobeCategory = 'appearance';
let wardrobeSlot = 'baseBody';
// Inspection is transient UI state; only the existing equip operation saves.
let wardrobeSelectedItemId = null;
let wardrobeHairColorGroup = 'natural';

function renderWardrobeRegistration() {
    document.getElementById('custom-modal')?.setAttribute('data-wardrobe-theme', paperDollState.activeViewMode === 'combat' ? 'trip' : 'patient');
    const panel = document.getElementById('wardrobe-registration');
    if (!panel) return;
    panel.setAttribute('data-view', paperDollState.activeViewMode);
    const name = document.getElementById('wardrobe-patient-name');
    const caseId = document.getElementById('wardrobe-patient-case');
    if (name) name.textContent = playerName;
    if (caseId) caseId.textContent = getPlayerUniqueId().id;
}

function wardrobeVisibleItems() {
    return PAPER_DOLL_ITEMS.filter(item => item.slot === wardrobeSlot && !PAPER_DOLL_RETIRED_FACES.has(item.id));
}

function selectWardrobeCategory(category) {
    // Preserve existing callers while hair now belongs to Appearance.
    if (category === 'hair') { selectWardrobeCategory('appearance'); selectWardrobeSlot('hair'); return; }
    if (!Object.hasOwn(WARDROBE_CATEGORIES, category)) return;
    wardrobeCategory = category;
    wardrobeSlot = WARDROBE_CATEGORIES[category].slots[0];
    wardrobeSelectedItemId = null;
    const grid = document.getElementById('wardrobe-container');
    if (grid) grid.scrollTop = 0;
    renderWardrobe();
}

function selectWardrobeSlot(slot) {
    if (!WARDROBE_CATEGORIES[wardrobeCategory].slots.includes(slot)) return;
    wardrobeSlot = slot;
    if (slot === 'hair') wardrobeHairColorGroup = HAIR_COLORS.find(color => color.id === paperDollState.appearance.hairColor)?.group === 'alternative' ? 'alternative' : 'natural';
    wardrobeSelectedItemId = null;
    const grid = document.getElementById('wardrobe-container');
    if (grid) grid.scrollTop = 0;
    renderWardrobe();
}

function selectWardrobeItem(id) {
    if (!wardrobeVisibleItems().some(item => item.id === id)) return false;
    wardrobeSelectedItemId = id;
    renderWardrobe();
    return true;
}

function applyWardrobeItemAction() {
    const item = wardrobeVisibleItems().find(entry => entry.id === wardrobeSelectedItemId);
    if (!item) return false;
    return equipPaperDollItem(wardrobeSlot, wardrobeSlot !== 'hair' && selectedPaperDollItem(wardrobeSlot)?.id === item.id ? null : item.id);
}

function wardrobeItemImage(item) {
    const parts = paperDollItemLayers(item, paperDollState.selectedGender);
    return parts.flatMap(part => paperDollImageCandidates(part, paperDollState.selectedGender)).find(path => !failedPaperDollImages.has(path));
}

function wardrobeItemStatus(item) {
    return selectedPaperDollItem(item.slot)?.id === item.id ? item.slot === 'hair' ? 'ВИБРАНО' : 'ЕКІПІРОВАНО' : isPaperDollItemOwned(item) ? 'Доступно' : 'Недоступно';
}

// Presentation only: missing graphics never change ownership or the saved outfit.
function wardrobeImageStatus(item, detailed = false) {
    if (item?.noImageRequired) return { state: 'ready', text: '' };
    const layers = paperDollItemLayers(item, paperDollState.selectedGender);
    const ready = layers.filter(layer => paperDollImageCandidates(layer, paperDollState.selectedGender).some(path => !failedPaperDollImages.has(path))).length;
    const state = layers.length && ready === layers.length ? 'ready' : ready ? 'partial' : 'missing';
    const equipped = item && selectedPaperDollItem(item.slot)?.id === item.id;
    if (state === 'ready') return { state, text: '' };
    if (state === 'partial') return { state, text: detailed
        ? `${equipped ? 'Предмет екіпіровано. ' : ''}Частина PNG-шарів відсутня або не завантажилася. На персонажі ${equipped ? 'видно' : 'буде видно'} лише доступні частини.`
        : 'PNG неповний · лише частина шарів' };
    return { state, text: detailed
        ? `${equipped ? 'Предмет екіпіровано в цьому комплекті, але на персонажі він не відображається. ' : ''}PNG-накладку ще не підготовлено або не вдалося завантажити.`
        : equipped ? 'PNG відсутній · на моделі не видно' : 'Зображення не підготовлено' };
}

function renderWardrobeImageNotes() {
    document.querySelectorAll('[data-paper-image-item]').forEach(note => {
        const item = PAPER_DOLL_ITEMS.find(entry => entry.id === note.dataset.paperImageItem);
        const status = wardrobeImageStatus(item, note.hasAttribute('data-paper-image-detail'));
        note.classList.toggle('hidden', !item || status.state === 'ready');
        note.setAttribute('data-paper-graphics', status.state);
        note.textContent = status.text;
    });
}

function wardrobeEmptyState(hasCatalog = false) {
    const hospitalClothes = paperDollState.activeViewMode === 'patient' && wardrobeCategory === 'clothes';
    const title = hasCatalog ? 'Немає доступних предметів' : hospitalClothes ? 'Лікарняний одяг ще не додано' : 'У цьому слоті поки немає предметів';
    const description = hasCatalog
        ? 'Записи нижче можна оглянути. Щоб надягнути річ, спочатку потрібно мати її в інвентарі.'
        : hospitalClothes
            ? `Тут з’явиться доступний лікарняний одяг для слота «${PAPER_DOLL_SLOTS[wardrobeSlot].label}». Поки що зберігається базовий вигляд персонажа.`
            : 'Коли для цього слота будуть доступні речі, їх можна буде обрати тут. Зараз змінювати нічого.';
    return `<div class="wardrobe-empty" data-wardrobe-empty>${iconHTML(PAPER_DOLL_SLOTS[wardrobeSlot].icon,'large')}<h4>${escapeHTML(title)}</h4><p>${escapeHTML(description)}</p><span class="wardrobe-item-state">${hasCatalog ? 'Доступних речей: 0' : 'Слот порожній'}</span></div>`;
}

function wardrobeItemCard(item) {
    const equipped = selectedPaperDollItem(wardrobeSlot)?.id === item.id;
    const inspected = wardrobeSelectedItemId === item.id;
    const source = wardrobeItemImage(item);
    return `<button type="button" class="wardrobe-item-card${equipped ? ' equipped' : ''}${inspected ? ' selected' : ''}" data-wardrobe-card="${escapeHTML(item.id)}" data-wardrobe-item="${escapeHTML(item.id)}" data-equipped="${equipped}" data-available="${isPaperDollItemOwned(item)}" data-wardrobe-focus="item-${escapeHTML(item.id)}" aria-pressed="${inspected}" aria-controls="wardrobe-item-detail">
        <span class="wardrobe-item-image">${iconHTML(item.icon || PAPER_DOLL_SLOTS[item.slot].icon, 'large')}${source ? `<img src="${escapeHTML(source)}" alt="" aria-hidden="true">` : ''}</span>
        <strong class="wardrobe-item-name">${escapeHTML(item.name)}</strong>
        <span class="wardrobe-item-state">${wardrobeItemStatus(item)}</span>
        <span class="wardrobe-image-note${source || item.noImageRequired ? ' hidden' : ''}" data-paper-image-item="${escapeHTML(item.id)}">Зображення не підготовлено</span>
    </button>`;
}

function renderWardrobeItemDetail(item) {
    const panel = document.getElementById('wardrobe-item-detail');
    if (!panel) return;
    panel.classList.toggle('hidden', !item);
    if (!item) { panel.innerHTML = ''; return; }
    const owned = isPaperDollItemOwned(item);
    const equipped = selectedPaperDollItem(wardrobeSlot)?.id === item.id;
    if (item.slot === 'hair') {
        panel.removeAttribute('aria-labelledby');
        panel.setAttribute('aria-label', 'Вибір зачіски');
        // The card already names the style; do not repeat catalog/service text.
        panel.innerHTML = `<button type="button" class="report-button" data-wardrobe-action="${escapeHTML(item.id)}" data-wardrobe-focus="action-${escapeHTML(item.id)}" aria-label="${equipped ? 'Обрано' : 'Обрати'}: ${escapeHTML(item.name)}"${equipped ? ' disabled' : ''}>${equipped ? 'Обрано' : 'Обрати'}</button>`;
        panel.querySelectorAll('[data-wardrobe-action]').forEach(button => button.addEventListener('click', applyWardrobeItemAction));
        return;
    }
    panel.removeAttribute('aria-label');
    panel.setAttribute('aria-labelledby', 'wardrobe-detail-title');
    const reference = inventory.find(entry => entry.name === item.inventoryName && entry.category === item.inventoryCategory)
        || DEFAULT_INVENTORY.find(entry => entry.name === item.inventoryName && entry.category === item.inventoryCategory);
    const description = reference?.desc || item.description || PAPER_DOLL_SLOTS[item.slot].label;
    panel.innerHTML = `<header><span class="wardrobe-record-label">ІНВЕНТАРНИЙ ЗАПИС</span><h4 id="wardrobe-detail-title">${escapeHTML(item.name)}</h4><span class="wardrobe-detail-slot">${escapeHTML(PAPER_DOLL_SLOTS[item.slot].label)}</span></header>
        <p class="wardrobe-detail-description">${escapeHTML(description)}</p>
        <span class="wardrobe-item-state" role="status">${wardrobeItemStatus(item)}</span>
        <p class="wardrobe-image-note${wardrobeItemImage(item) ? ' hidden' : ''}" data-paper-image-item="${escapeHTML(item.id)}" data-paper-image-detail role="status"></p>
        <button type="button" class="report-button" data-wardrobe-action="${escapeHTML(item.id)}" data-wardrobe-focus="action-${escapeHTML(item.id)}"${!owned || item.slot === 'hair' && equipped ? ' disabled' : ''}>${item.slot === 'hair' ? equipped ? 'Обрано' : 'Обрати' : equipped ? 'Зняти' : item.slot === 'face' ? 'Обрати' : 'Надягнути'}</button>`;
    panel.querySelectorAll('[data-wardrobe-action]').forEach(button => button.addEventListener('click', applyWardrobeItemAction));
}

function renderWardrobeUI() {
    const container = document.getElementById('wardrobe-container');
    if (!container) return;
    const focused = document.activeElement?.getAttribute('data-wardrobe-focus');
    const gridScroll = container.scrollTop || 0;
    const categoryList = document.getElementById('wardrobe-categories');
    const categoryScroll = categoryList?.scrollLeft || 0;
    if (categoryList) categoryList.innerHTML = Object.entries(WARDROBE_CATEGORIES).map(([id, category], index) =>
        `<button type="button" class="wardrobe-category" data-wardrobe-category="${id}" data-wardrobe-focus="category-${id}" aria-pressed="${id === wardrobeCategory}">${iconHTML(category.icon)}<span>${escapeHTML(category.label)}</span><small aria-hidden="true">${String(index + 1).padStart(2,'0')}</small></button>`).join('');
    const slots = document.getElementById('wardrobe-slots');
    if (slots) slots.innerHTML = WARDROBE_CATEGORIES[wardrobeCategory].slots.map(slot =>
        `<button type="button" class="wardrobe-slot" data-wardrobe-slot="${slot}" data-wardrobe-focus="slot-${slot}" aria-pressed="${slot === wardrobeSlot}">${iconHTML(PAPER_DOLL_SLOTS[slot].icon)}${escapeHTML(PAPER_DOLL_SLOTS[slot].label)}</button>`).join('');
    const heading = document.getElementById('wardrobe-items-title');
    if (heading) heading.textContent = PAPER_DOLL_SLOTS[wardrobeSlot].label;
    const genderSwitch = document.getElementById('wardrobe-gender-switch');
    genderSwitch?.classList.toggle('hidden', wardrobeCategory !== 'appearance');
    genderSwitch?.querySelectorAll('[data-paper-gender]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.paperGender === paperDollState.selectedGender)));
    const items = wardrobeVisibleItems();
    if (!items.some(item => item.id === wardrobeSelectedItemId)) wardrobeSelectedItemId = items.find(item => item.id === selectedPaperDollItem(wardrobeSlot)?.id)?.id || items[0]?.id || null;
    container.classList.toggle('wardrobe-has-items', items.length > 0);
    container.classList.toggle('wardrobe-hair-grid', wardrobeSlot === 'hair');
    renderHairPalette();
    if (wardrobeSlot === 'baseBody') {
        container.innerHTML = `<div class="wardrobe-appearance-note">${iconHTML('user','large')}<h4>Повноростова модель</h4><p>Обраний персонаж одразу відображається в центрі та у палаті.</p><span class="wardrobe-item-state">${paperDollState.selectedGender === 'female' ? 'Жінка' : 'Чоловік'}</span></div>`;
    } else {
        const nativeFace = wardrobeSlot === 'face' ? `<article class="wardrobe-native-face"><h4>Базове обличчя</h4><p>Обличчя з актуального зображення персонажа.</p><span class="wardrobe-item-state">${selectedPaperDollItem('face') ? 'ДОСТУПНЕ' : 'ВИКОРИСТОВУЄТЬСЯ'}</span>${selectedPaperDollItem('face') ? '<button type="button" class="report-button" data-wardrobe-native-face data-wardrobe-focus="native-face">Зняти накладку</button>' : ''}${items.length ? '' : '<p class="wardrobe-cosmetic-note">Нові затверджені накладки ще не долучено.</p>'}</article>` : '';
        const unavailable = items.length > 0 && !items.some(isPaperDollItemOwned) && wardrobeSlot !== 'face';
        container.innerHTML = nativeFace + (unavailable ? wardrobeEmptyState(true) : '') + (items.length ? items.map(wardrobeItemCard).join('') : wardrobeSlot === 'face' ? '' : wardrobeEmptyState());
    }
    renderWardrobeItemDetail(items.find(item => item.id === wardrobeSelectedItemId));
    categoryList?.querySelectorAll('[data-wardrobe-category]').forEach(button => button.addEventListener('click', () => selectWardrobeCategory(button.dataset.wardrobeCategory)));
    slots?.querySelectorAll('[data-wardrobe-slot]').forEach(button => button.addEventListener('click', () => selectWardrobeSlot(button.dataset.wardrobeSlot)));
    container.querySelectorAll('[data-wardrobe-native-face]').forEach(button => button.addEventListener('click', () => equipPaperDollItem('face', null)));
    container.querySelectorAll('[data-wardrobe-item]').forEach(button => button.addEventListener('click', () => selectWardrobeItem(button.dataset.wardrobeItem)));
    container.querySelectorAll('.wardrobe-item-image img:not(.game-icon)').forEach(thumbnail => {
        thumbnail.onerror = () => { failedPaperDollImages.add(thumbnail.getAttribute('src')); thumbnail.classList.add('hidden'); renderPaperDoll(); renderPaperDollControls(false); };
    });
    container.scrollTop = gridScroll;
    if (categoryList) categoryList.scrollLeft = categoryScroll;
    renderPaperDoll();
    renderPaperDollControls(false);
    if (focused) document.querySelectorAll('[data-wardrobe-focus]').forEach(button => {
        if (button.getAttribute('data-wardrobe-focus') === focused && !button.disabled) button.focus({ preventScroll: true });
    });
}

function renderHairPalette() {
    const panel=document.getElementById('wardrobe-hair-palette');
    if (!panel) return;
    panel.classList.toggle('hidden', wardrobeSlot !== 'hair');
    if (wardrobeSlot !== 'hair') return;
    const selected=HAIR_COLORS.find(color => color.id===normalizeHairColor(paperDollState.appearance.hairColor));
    panel.innerHTML = `<header><strong>Колір волосся</strong><span role="status">${escapeHTML(selected.name)}</span></header>
        <div class="hair-color-controls"><button type="button" class="hair-original" data-hair-color="original" data-wardrobe-focus="color-original" aria-pressed="${selected.id==='original'}">Оригінальний</button>
        <div class="hair-color-groups" role="group" aria-label="Група кольорів">${[['natural','Природні'],['alternative','Альтернативні']].map(([id,name]) => `<button type="button" data-hair-color-group="${id}" data-wardrobe-focus="color-group-${id}" aria-pressed="${wardrobeHairColorGroup===id}">${name}</button>`).join('')}</div></div>
        <div class="hair-color-swatches" role="group" aria-label="Відтінки волосся">${HAIR_COLORS.filter(color => color.group===wardrobeHairColorGroup).map(color => `<button type="button" data-hair-color="${color.id}" data-wardrobe-focus="color-${color.id}" aria-label="${escapeHTML(color.name)}" title="${escapeHTML(color.name)}" aria-pressed="${selected.id===color.id}" style="--hair-color:${color.hex}"><span aria-hidden="true">${selected.id===color.id ? '✓' : ''}</span></button>`).join('')}</div>
        <p id="hair-color-error" class="hidden" role="alert">Колір не вдалося застосувати. Показано оригінал; спробуйте обрати колір знову.</p>`;
    panel.querySelectorAll('[data-hair-color]').forEach(button => button.addEventListener('click', () => setHairColor(button.dataset.hairColor)));
    panel.querySelectorAll('[data-hair-color-group]').forEach(button => button.addEventListener('click', () => {
        wardrobeHairColorGroup=button.dataset.hairColorGroup;
        renderWardrobe();
    }));
}
