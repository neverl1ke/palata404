let wardrobeCategory = 'appearance';
let wardrobeSlot = 'baseBody';

function selectWardrobeCategory(category) {
    if (!Object.hasOwn(WARDROBE_CATEGORIES, category)) return;
    wardrobeCategory = category;
    wardrobeSlot = WARDROBE_CATEGORIES[category].slots[0];
    renderWardrobe();
}

function selectWardrobeSlot(slot) {
    if (!WARDROBE_CATEGORIES[wardrobeCategory].slots.includes(slot)) return;
    wardrobeSlot = slot;
    renderWardrobe();
}

function wardrobeItemImage(item) {
    const parts = Array.isArray(item?.layers) && item.layers.length ? item.layers : [item];
    return parts.flatMap(part => paperDollImageCandidates(part, paperDollState.selectedGender)).find(path => !failedPaperDollImages.has(path));
}

function wardrobeItemCard(item) {
    const selected = selectedPaperDollItem(wardrobeSlot)?.id === item.id;
    const owned = isPaperDollItemOwned(item);
    const source = wardrobeItemImage(item);
    const inventoryItem = inventory.find(entry => entry.name === item.inventoryName && entry.category === item.inventoryCategory);
    return `<article class="wardrobe-item-card${selected ? ' selected' : ''}" data-wardrobe-card="${escapeHTML(item.id)}">
        <span class="wardrobe-item-image">${iconHTML(item.icon || PAPER_DOLL_SLOTS[item.slot].icon, 'large')}${source ? `<img src="${escapeHTML(source)}" alt="" aria-hidden="true">` : ''}</span>
        <div class="wardrobe-item-details"><h4>${escapeHTML(item.name)}</h4><span class="wardrobe-item-state">${selected ? 'НАДЯГНУТО' : owned ? item.slot === 'face' ? 'ЗОВНІШНІСТЬ' : 'В ІНВЕНТАРІ' : 'НЕМАЄ В ІНВЕНТАРІ'}</span>
        ${inventoryItem?.desc || item.description ? `<p>${escapeHTML(inventoryItem?.desc || item.description)}</p>` : ''}
        <p class="wardrobe-image-note${source ? ' hidden' : ''}" data-paper-image-item="${escapeHTML(item.id)}">Зображення не підготовлено</p></div>
        <button type="button" class="report-button" data-wardrobe-item="${escapeHTML(item.id)}" data-wardrobe-focus="item-${escapeHTML(item.id)}" aria-pressed="${selected}"${owned ? '' : ' disabled'}>${selected ? 'Зняти' : item.slot === 'face' ? 'Обрати' : 'Надягнути'}</button>
    </article>`;
}

function renderWardrobeUI() {
    const container = document.getElementById('wardrobe-container');
    if (!container) return;
    const focused = document.activeElement?.getAttribute('data-wardrobe-focus');
    const categoryList = document.getElementById('wardrobe-categories');
    if (categoryList) categoryList.innerHTML = Object.entries(WARDROBE_CATEGORIES).map(([id, category]) =>
        `<button type="button" class="wardrobe-category" data-wardrobe-category="${id}" data-wardrobe-focus="category-${id}" aria-pressed="${id === wardrobeCategory}">${iconHTML(category.icon)}<span>${escapeHTML(category.label)}</span></button>`).join('');
    const slots = document.getElementById('wardrobe-slots');
    if (slots) slots.innerHTML = WARDROBE_CATEGORIES[wardrobeCategory].slots.map(slot =>
        `<button type="button" class="wardrobe-slot" data-wardrobe-slot="${slot}" data-wardrobe-focus="slot-${slot}" aria-pressed="${slot === wardrobeSlot}">${iconHTML(PAPER_DOLL_SLOTS[slot].icon)}${escapeHTML(PAPER_DOLL_SLOTS[slot].label)}</button>`).join('');
    const heading = document.getElementById('wardrobe-items-title');
    if (heading) heading.textContent = PAPER_DOLL_SLOTS[wardrobeSlot].label;
    container.classList.toggle('wardrobe-face-grid', wardrobeSlot === 'face');
    if (wardrobeSlot === 'baseBody') {
        container.innerHTML = ['male','female'].map(value => `<article class="wardrobe-item-card wardrobe-body-card${paperDollState.selectedGender === value ? ' selected' : ''}">
            <img class="wardrobe-body-image" src="${PAPER_DOLL_BODIES[value]}" alt="">
            <h4>${iconHTML(value)}${value === 'female' ? 'Жінка' : 'Чоловік'}</h4><button type="button" class="report-button" data-paper-gender="${value}" data-wardrobe-focus="gender-${value}" aria-pressed="${paperDollState.selectedGender === value}">${value === 'female' ? 'Жінка' : 'Чоловік'}</button></article>`).join('');
    } else {
        const items = PAPER_DOLL_ITEMS.filter(item => item.slot === wardrobeSlot);
        container.innerHTML = items.length ? items.map(wardrobeItemCard).join('') : `<div class="wardrobe-empty">${iconHTML(PAPER_DOLL_SLOTS[wardrobeSlot].icon, 'hero')}<h4>Матеріали не долучено</h4><p>Для цього слота ще немає предметів і підготовлених зображень.</p></div>`;
    }
    categoryList?.querySelectorAll('[data-wardrobe-category]').forEach(button => button.addEventListener('click', () => selectWardrobeCategory(button.dataset.wardrobeCategory)));
    slots?.querySelectorAll('[data-wardrobe-slot]').forEach(button => button.addEventListener('click', () => selectWardrobeSlot(button.dataset.wardrobeSlot)));
    container.querySelectorAll('[data-paper-gender]').forEach(button => button.addEventListener('click', () => setGender(button.dataset.paperGender)));
    container.querySelectorAll('[data-wardrobe-item]').forEach(button => button.addEventListener('click', () => {
        const id = button.dataset.wardrobeItem;
        equipPaperDollItem(wardrobeSlot, selectedPaperDollItem(wardrobeSlot)?.id === id ? null : id);
    }));
    container.querySelectorAll('.wardrobe-item-image img:not(.game-icon)').forEach(thumbnail => {
        thumbnail.onerror = () => {
            failedPaperDollImages.add(thumbnail.getAttribute('src')); thumbnail.classList.add('hidden');
            renderPaperDoll(); renderPaperDollControls(false);
        };
    });
    renderPaperDoll();
    renderPaperDollControls(false);
    if (focused) document.querySelectorAll('[data-wardrobe-focus]').forEach(button => {
        if (button.getAttribute('data-wardrobe-focus') === focused && !button.disabled) button.focus({ preventScroll: true });
    });
}
