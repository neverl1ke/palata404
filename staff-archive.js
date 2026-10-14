// Personnel collection progress is independent of the erasable raid history.
let staffArchiveState = null;
let pendingStaffReward = null;
let staffArchiveSaveFailed = false;
let selectedStaffBossId = null;
let selectedStaffDocumentId = null;
let staffArchiveTab = 'identity';

function staffArchiveKey() { return `palata404_staff_archive:${encodeURIComponent(raidArchiveOwnerId)}`; }
function staffRewardJournalKey() { return `${staffArchiveKey()}:reward-pending`; }
function emptyStaffArchive() { return { schemaVersion: 1, ownerId: raidArchiveOwnerId, cases: {}, processedRaids: {}, claims: {} }; }

function normalizeStaffArchive(value) {
    const object = v => v && typeof v === 'object' && !Array.isArray(v);
    const whole = v => Number.isSafeInteger(v) && v >= 0;
    if (!object(value) || value.schemaVersion !== 1 || value.ownerId !== raidArchiveOwnerId
        || !object(value.cases) || !object(value.processedRaids) || !object(value.claims)) return null;
    if (!Object.values(value.cases).every(entry => object(entry) && whole(entry.encounteredAt)
        && object(entry.documents) && Object.values(entry.documents).every(whole)
        && whole(entry.misses) && entry.misses <= 29 && whole(entry.victories))) return null;
    if (!Object.values(value.processedRaids).every(entry => object(entry) && typeof entry.bossId === 'string'
        && (entry.documentId === null || typeof entry.documentId === 'string'))) return null;
    if (!Object.values(value.claims).every(whole)) return null;
    return value;
}

function readPendingStaffReward() {
    try {
        const value = JSON.parse(safeStorageGet(staffRewardJournalKey()));
        const profile = normalizeStaffArchive(value?.state?.staffArchive);
        if (!profile || value.ownerId !== raidArchiveOwnerId || typeof value.claimId !== 'string'
            || !Object.hasOwn(profile.claims, value.claimId) || !value.state.stats
            || typeof value.state.stats !== 'object' || Array.isArray(value.state.stats)
            || !Array.isArray(value.state.inventory)) return null;
        return value;
    } catch (error) { return null; }
}

function initializeStaffArchive() {
    pendingStaffReward = readPendingStaffReward();
    let saved = null;
    try { saved = normalizeStaffArchive(JSON.parse(safeStorageGet(staffArchiveKey()))); } catch (error) { /* New profiles start empty. */ }
    staffArchiveState = normalizeStaffArchive(pendingBattleReward?.staffArchive)
        || pendingStaffReward?.state.staffArchive || saved || emptyStaffArchive();
}

function saveStaffArchiveState() {
    const saved = safeStorageSet(staffArchiveKey(), JSON.stringify(staffArchiveState));
    staffArchiveSaveFailed = !saved;
    updateStaffArchiveSaveNotice();
    return saved;
}

function prepareStaffRewardSave() {
    if (!pendingStaffReward) return true;
    pendingStaffReward.state = { stats, inventory, staffArchive: staffArchiveState };
    return safeStorageSet(staffRewardJournalKey(), JSON.stringify(pendingStaffReward));
}

function finishStaffRewardSave(saved) {
    if (saved && pendingStaffReward && safeStorageRemove(staffRewardJournalKey())) pendingStaffReward = null;
    return saved;
}

function retryStaffArchiveSave() { saveGameProgress(); renderStaffArchive(); }

function staffCaseConfig(bossId) { return bossesDatabase[bossId]?.staffArchive; }
function staffCaseProgress(bossId) {
    const config = staffCaseConfig(bossId);
    const documents = config?.documents || [];
    const entry = staffArchiveState.cases[bossId];
    const opened = documents.filter(doc => Object.hasOwn(entry?.documents || {}, doc.id)).length;
    return { opened, total: documents.length, percent: documents.length ? Math.floor(opened * 100 / documents.length) : 0,
        complete: Boolean(documents.length && opened === documents.length) };
}

function openInitialStaffDocuments(bossId, at = Date.now()) {
    const config = staffCaseConfig(bossId);
    if (!Object.hasOwn(bossesDatabase, bossId)) return false;
    let entry = staffArchiveState.cases[bossId];
    if (entry) return false;
    entry = { encounteredAt: at, documents: {}, misses: 0, victories: 0 };
    for (const document of config?.documents || []) if (document.acquisition === 'initial') entry.documents[document.id] = at;
    staffArchiveState.cases[bossId] = entry;
    return true;
}

function encounterStaffBoss(bossId) {
    if (!isBattleActive || currentBattleSession?.bossKey !== bossId) return;
    openInitialStaffDocuments(bossId);
    unlockStaffAchievements(bossId, Date.now());
    saveStaffArchiveState();
}

function restoreStaffEncountersFromHistory() {
    const history = readRaidArchive();
    if (ownsBattleResult(lastBattleResult)) history.push(lastBattleResult);
    let changed = false;
    const unique = [...new Map(history.map(result => [result.battleId, result])).values()];
    for (const result of unique) {
        if (openInitialStaffDocuments(result.boss.id, result.startedAt)) {
            const entry = staffArchiveState.cases[result.boss.id];
            entry.victories = unique.filter(r => r.boss.id === result.boss.id && (r.outcome || 'victory') === 'victory').length;
            unlockStaffAchievements(result.boss.id, result.endedAt);
            changed = true;
        }
    }
    if (changed) saveStaffArchiveState();
}

function unlockStaffAchievements(bossId, at) {
    const entry = staffArchiveState.cases[bossId];
    for (const document of staffCaseConfig(bossId)?.documents || []) {
        if (document.acquisition === 'achievement' && document.requirement?.kind === 'victories'
            && entry.victories >= document.requirement.count) entry.documents[document.id] ??= at;
        if (document.acquisition === 'quest' && document.requirement?.kind === 'rubbleCleared'
            && gameProgress.rubbleCleared) entry.documents[document.id] ??= at;
    }
}

function grantStaffQuestMilestones() {
    for (const bossId of Object.keys(staffArchiveState.cases)) unlockStaffAchievements(bossId, Date.now());
    saveStaffArchiveState();
}

function processStaffRaid(result) {
    // Only the active local finalization can roll; historical viewing cannot use this hook.
    if (!ownsBattleResult(result) || !isBattleActive || currentBattleSession?.finished
        || currentBattleSession?.id !== result.battleId || result.outcome !== 'victory') return;
    const config = staffCaseConfig(result.boss.id);
    if (!config) return;
    openInitialStaffDocuments(result.boss.id, result.startedAt);
    const duplicate = staffArchiveState.processedRaids[result.battleId];
    if (duplicate) return;
    const entry = staffArchiveState.cases[result.boss.id];
    const available = config.documents.filter(doc => doc.acquisition === 'raid' && !Object.hasOwn(entry.documents, doc.id));
    let obtained = null;
    if (available.length) {
        const guaranteed = entry.misses >= 29;
        if (guaranteed || Math.random() < 0.05) {
            obtained = available[Math.floor(Math.random() * available.length)];
            entry.documents[obtained.id] = result.endedAt;
            entry.misses = 0;
            result.extraRewards.push({ type: 'document', id: obtained.id, name: obtained.title, icon: 'clipboard', granted: true });
        } else entry.misses += 1;
    } else entry.misses = 0;
    // Do not retain a pity counter after the last eligible document was collected.
    if (config.documents.filter(doc => doc.acquisition === 'raid').every(doc => Object.hasOwn(entry.documents, doc.id))) entry.misses = 0;
    entry.victories += 1;
    unlockStaffAchievements(result.boss.id, result.endedAt);
    staffArchiveState.processedRaids[result.battleId] = { bossId: result.boss.id, documentId: obtained?.id || null };
}

function staffCollectionProgress(collection) {
    let opened = 0, total = 0;
    for (const [bossId, ids] of Object.entries(collection.required)) {
        total += ids.length;
        opened += ids.filter(id => Object.hasOwn(staffArchiveState.cases[bossId]?.documents || {}, id)).length;
    }
    return { opened, total, complete: total > 0 && opened === total };
}

function getStaffRewardClaim(id) {
    for (const [bossId, boss] of Object.entries(bossesDatabase)) {
        if (boss.staffArchive?.rewardId === id) return { reward: boss.staffArchive.reward, complete: staffCaseProgress(bossId).complete };
    }
    const collection = STAFF_ARCHIVE_COLLECTIONS.find(item => item.id === id);
    return collection ? { reward: collection.reward, complete: staffCollectionProgress(collection).complete } : null;
}

function claimStaffReward(id) {
    const claim = getStaffRewardClaim(id);
    if (!claim?.complete || !claim.reward || Object.hasOwn(staffArchiveState.claims, id)) return false;
    const { silver = 0, exp = 0 } = claim.reward;
    if (![silver, exp].every(value => Number.isSafeInteger(value) && value >= 0) || silver + exp === 0) return false;
    if (isBattleActive || pendingBattleReward || pendingStaffReward) {
        showCustomToast('Завершіть бій і збережіть попередній результат перед отриманням винагороди.');
        return false;
    }
    const before = JSON.parse(JSON.stringify({ stats, inventory, staffArchive: staffArchiveState }));
    stats.silver += silver;
    const levels = addExperience(exp, false);
    staffArchiveState.claims[id] = Date.now();
    pendingStaffReward = { schemaVersion: 1, ownerId: raidArchiveOwnerId, claimId: id,
        state: JSON.parse(JSON.stringify({ stats, inventory, staffArchive: staffArchiveState })) };
    if (!prepareStaffRewardSave()) {
        stats = before.stats; inventory = before.inventory; staffArchiveState = before.staffArchive;
        pendingStaffReward = null; staffArchiveSaveFailed = true;
        updateStaffArchiveSaveNotice();
        return false;
    }
    updateUI();
    renderStaffArchive();
    levels.forEach(level => alert(`Вітаємо! Ви досягли ${level} рівня!`));
    return true;
}

function staffRewardMarkup(id, reward, complete) {
    if (!reward) return '<p class="report-caption">Винагороду ще не затверджено.</p>';
    const claimed = Object.hasOwn(staffArchiveState.claims, id);
    const label = `${reward.temporary ? 'Тимчасова винагорода' : 'Винагорода'}: +${reward.silver || 0} срібла${reward.exp ? ` / +${reward.exp} EXP` : ''}`;
    return `<p>${escapeHTML(label)}</p>${claimed ? '<span class="report-stamp">ВИНАГОРОДУ ОТРИМАНО</span>'
        : complete ? `<button class="report-button staff-claim-button" type="button" data-claim-id="${escapeHTML(id)}">Отримати винагороду</button>`
            : '<p class="report-caption">Доступна після завершення матеріалів справи.</p>'}`;
}

function renderStaffDocuments(bossId, observationsOnly = false) {
    const config = staffCaseConfig(bossId);
    const entry = staffArchiveState.cases[bossId];
    const documents = (config?.documents || []).filter(doc => !observationsOnly || doc.acquisition !== 'initial');
    if (!documents.length) return '<p class="report-caption">Матеріали цього розділу ще не долучені.</p>';
    const randomPool = (config?.documents || []).filter(doc => doc.acquisition === 'raid');
    const remaining = randomPool.filter(doc => !Object.hasOwn(entry.documents, doc.id)).length;
    const dropNote = randomPool.length ? `<p class="report-caption">${remaining
        ? `Випадкова знахідка: 5% після перемоги. Без нової знахідки: ${entry.misses}/30; на 30-му рейді — гарантія.`
        : 'Усі доступні випадкові матеріали зібрано.'}</p>` : '';
    const selected = documents.find(doc => doc.id === selectedStaffDocumentId && Object.hasOwn(entry.documents, doc.id));
    return `${dropNote}<ul class="staff-document-list">${documents.map((doc, index) => {
        const unlocked = Object.hasOwn(entry.documents, doc.id);
        const title = unlocked || !doc.secret ? doc.title : `ДОКУМЕНТ №${doc.id} — ЗАСЕКРЕЧЕНО`;
        return `<li class="staff-document-item"><strong>${escapeHTML(title)}</strong>${unlocked
            ? `<button class="report-detail-link" type="button" data-document-index="${index}">Читати документ</button>`
            : `<span class="report-caption">${escapeHTML(doc.hint || 'Матеріал може бути знайдений після успішного обстеження.')}</span>`}</li>`;
    }).join('')}</ul>${selected ? `<section class="staff-document-reading"><h3>${escapeHTML(selected.title)}</h3><p>${escapeHTML(selected.content)}</p></section>` : '<p class="report-caption">Оберіть відкритий документ для читання.</p>'}`;
}

function renderStaffArchive() {
    const list = document.getElementById('staff-case-list');
    const sheet = document.getElementById('staff-case-sheet');
    if (!list || !sheet) return;
    const filter = document.getElementById('staff-department-filter')?.value || '';
    const all = Object.keys(bossesDatabase);
    const ids = all.filter(id => !filter || staffCaseConfig(id)?.department === filter);
    if (!ids.includes(selectedStaffBossId)) selectedStaffBossId = ids[0] || null;
    list.innerHTML = ids.map((id, index) => {
        const boss = bossesDatabase[id];
        const known = Boolean(staffArchiveState.cases[id]);
        const progress = staffCaseProgress(id);
        const image = known ? getRaidDossierImage({ boss: { id } }) : null;
        return `<li><button class="staff-case-button${id === selectedStaffBossId ? ' selected' : ''}" type="button" data-case-index="${index}" aria-pressed="${id === selectedStaffBossId}">
            ${image ? `<img src="${escapeHTML(image)}" alt="Досьє ${escapeHTML(boss.name)}" loading="lazy">` : `<span class="staff-silhouette" aria-label="Засекречений силует">${iconHTML('user')}</span>`}
            <span><small>СПРАВА №${escapeHTML(boss.dossier?.code || String(all.indexOf(id)+1))}</small><strong>${known ? escapeHTML(boss.name) : 'ОСОБУ НЕ ВСТАНОВЛЕНО'}</strong><small>${progress.opened}/${progress.total} (${progress.percent}%)</small>${progress.complete ? '<span class="report-stamp">СПРАВУ ЗАВЕРШЕНО</span>' : ''}</span>
        </button></li>`;
    }).join('');
    list.querySelectorAll('[data-case-index]').forEach(button => button.addEventListener('click', () => {
        selectedStaffBossId = ids[Number(button.dataset.caseIndex)]; selectedStaffDocumentId = null; renderStaffArchive();
    }));
    const boss = bossesDatabase[selectedStaffBossId];
    const entry = staffArchiveState.cases[selectedStaffBossId];
    const config = staffCaseConfig(selectedStaffBossId);
    const progress = staffCaseProgress(selectedStaffBossId);
    if (!boss) sheet.innerHTML = '<p>У цьому відділенні справ не зареєстровано.</p>';
    else if (!entry) sheet.innerHTML = `<span class="staff-silhouette staff-silhouette-large" aria-label="Засекречений силует">${iconHTML('user')}</span><h3>ОСОБУ НЕ ВСТАНОВЛЕНО</h3><p>Особова справа №${escapeHTML(boss.dossier?.code || '')} · 0%</p><span class="report-stamp">ДОСТУП ОБМЕЖЕНО</span><p class="report-caption">Початкові відомості відкриються після фактичного початку бою з об’єктом.</p>`;
    else {
        let content = '';
        if (staffArchiveTab === 'identity') {
            const image = getRaidDossierImage({ boss: { id: selectedStaffBossId } });
            content = `<div class="staff-identity">${image ? `<img class="staff-dossier-image" src="${escapeHTML(image)}" alt="Досьє ${escapeHTML(boss.name)}">` : ''}<div><h3>${escapeHTML(boss.name)}</h3><p>№${escapeHTML(boss.dossier?.code || '')} · ${escapeHTML(boss.victoryReport?.caseCode || '')}</p><p>${escapeHTML(boss.dossier?.role || '')}</p><p>${escapeHTML(config?.introduction || 'Контакт з об’єктом зафіксовано; службові матеріали ще не долучені.')}</p></div></div>`;
        } else if (staffArchiveTab === 'documents' || staffArchiveTab === 'observations') content = renderStaffDocuments(selectedStaffBossId, staffArchiveTab === 'observations');
        else {
            content = `<h3>Особова справа: ${progress.opened}/${progress.total} (${progress.percent}%)</h3>${staffRewardMarkup(config?.rewardId, config?.reward, progress.complete)}`;
            for (const collection of STAFF_ARCHIVE_COLLECTIONS.filter(item => Object.hasOwn(item.required, selectedStaffBossId))) {
                const collected = staffCollectionProgress(collection);
                content += `<section class="staff-collection"><h3>${escapeHTML(collection.name)}</h3><p>${collected.opened}/${collected.total} документів</p>${staffRewardMarkup(collection.id, collection.reward, collected.complete)}</section>`;
            }
        }
        sheet.innerHTML = `<p class="staff-case-progress">Справа №${escapeHTML(boss.dossier?.code || '')} — ${progress.opened}/${progress.total} (${progress.percent}%)</p>${content}`;
        const documents = (config?.documents || []).filter(doc => staffArchiveTab !== 'observations' || doc.acquisition !== 'initial');
        sheet.querySelectorAll('[data-document-index]').forEach(button => button.addEventListener('click', () => {
            selectedStaffDocumentId = documents[Number(button.dataset.documentIndex)]?.id || null; renderStaffArchive();
            document.getElementById('staff-case-sheet')?.focus({ preventScroll: true });
        }));
        sheet.querySelectorAll('[data-claim-id]').forEach(button => button.addEventListener('click', () => claimStaffReward(button.dataset.claimId)));
    }
    document.querySelectorAll('[data-staff-tab]').forEach(button => {
        button.setAttribute('aria-pressed', String(button.dataset.staffTab === staffArchiveTab));
    });
    updateStaffArchiveSaveNotice();
}

function changeStaffArchiveTab(tab) {
    if (!['identity','observations','documents','rewards'].includes(tab)) return;
    staffArchiveTab = tab; selectedStaffDocumentId = null; renderStaffArchive();
}

function updateStaffArchiveSaveNotice() {
    const failed = staffArchiveSaveFailed || Boolean(pendingStaffReward);
    const note = document.getElementById('staff-save-note');
    if (note) {
        note.classList.toggle('hidden', !failed);
        note.textContent = failed ? 'Прогрес або винагороду архіву ще не вдалося повністю зберегти. Не закривайте сторінку; повторіть збереження.' : '';
    }
    document.getElementById('staff-save-retry')?.classList.toggle('hidden', !failed);
}

function openStaffArchive(bossId = null) {
    if (bossId && Object.hasOwn(bossesDatabase, bossId)) selectedStaffBossId = bossId;
    staffArchiveTab = 'identity'; selectedStaffDocumentId = null;
    const filter = document.getElementById('staff-department-filter');
    if (filter) {
        filter.innerHTML = '<option value="">Усі відділення</option>' + [...new Set(Object.values(bossesDatabase).map(boss => boss.staffArchive?.department).filter(Boolean))]
            .map(name => `<option value="${escapeHTML(name)}">${escapeHTML(name)}</option>`).join('');
        filter.value = '';
    }
    closeOtherModals(['staff-archive-modal']); renderStaffArchive();
    document.getElementById('staff-archive-modal')?.classList.remove('hidden');
}

function closeStaffArchive() { document.getElementById('staff-archive-modal')?.classList.add('hidden'); }
