// Personal historical snapshots. Reading a report never finalizes combat.
const RAID_ARCHIVE_LIMIT = 50;
const RAID_OUTCOMES = Object.freeze({
    victory: "Об'єкт тимчасово стабілізовано",
    defeat: 'Поразка — обстеження не завершено',
    timeout: 'Час рейду вичерпано',
    fled: 'Рейд перервано — вихід із бою'
});
let raidArchiveOwnerId = null;
let raidArchiveLegacyOwnerId = null;
let raidArchiveSaveFailed = false;
let pendingArchiveResults = new Map();
let battleReportSource = 'summary';

function initializeRaidArchive() {
    const identity = getPlayerUniqueId();
    // The game currently has one character per identity, with no character slots.
    raidArchiveOwnerId = `${identity.type}:${identity.id}`;
    raidArchiveLegacyOwnerId = safeStorageGet('palata404_legacy_battle_owner');
    if (!raidArchiveLegacyOwnerId) {
        raidArchiveLegacyOwnerId = raidArchiveOwnerId;
        safeStorageSet('palata404_legacy_battle_owner', raidArchiveLegacyOwnerId);
    }
    window.addEventListener('storage', event => {
        if (event.key?.startsWith(raidArchivePrefix())) {
            pruneRaidArchive();
            renderRaidArchive();
        }
    });
}

function ownsBattleResult(result) {
    return Boolean(result && (result.ownerId === raidArchiveOwnerId
        || (!result.ownerId && raidArchiveLegacyOwnerId === raidArchiveOwnerId)));
}

function raidArchivePrefix() {
    return `palata404_raid_archive:${encodeURIComponent(raidArchiveOwnerId)}:`;
}

function raidArchiveRecordKey(id) {
    return `${raidArchivePrefix()}raid:${encodeURIComponent(id)}`;
}

function raidArchiveStorageKeys() {
    try {
        const storage = window.localStorage;
        if (!storage) return null;
        return Array.from({ length: storage.length }, (_, i) => storage.key(i)).filter(Boolean);
    } catch (error) {
        return null;
    }
}

function readRaidArchiveMeta() {
    try {
        const value = JSON.parse(safeStorageGet(`${raidArchivePrefix()}meta`));
        if (value?.schemaVersion === 1 && value.ownerId === raidArchiveOwnerId
            && Number.isSafeInteger(value.generation) && value.generation >= 0
            && Number.isSafeInteger(value.clearedAt) && value.clearedAt >= 0
            && Array.isArray(value.clearedIds) && value.clearedIds.every(id => typeof id === 'string')) return value;
    } catch (error) { /* Old or malformed archives start empty. */ }
    return { schemaVersion: 1, ownerId: raidArchiveOwnerId, generation: 0, clearedAt: 0, clearedIds: [] };
}

function raidWasCleared(result, meta) {
    return result.endedAt < meta.clearedAt || meta.clearedIds.includes(result.battleId);
}

function collectRaidArchive() {
    const meta = readRaidArchiveMeta();
    const keys = raidArchiveStorageKeys();
    const records = [];
    if (!keys) return { meta, records, keys: null };
    for (const key of keys) {
        if (!key.startsWith(`${raidArchivePrefix()}raid:`)) continue;
        try {
            const entry = JSON.parse(safeStorageGet(key));
            const result = normalizeBattleResult(entry?.result);
            if (entry?.schemaVersion !== 1 || entry.ownerId !== raidArchiveOwnerId
                || entry.generation !== meta.generation || !result || !ownsBattleResult(result)
                || key !== raidArchiveRecordKey(result.battleId) || raidWasCleared(result, meta)) continue;
            records.push({ key, result });
        } catch (error) { /* Ignore a damaged record; do not break the other raids. */ }
    }
    records.sort((a, b) => b.result.endedAt - a.result.endedAt
        || b.result.battleId.localeCompare(a.result.battleId));
    return { meta, records, keys };
}

function readRaidArchive() {
    return collectRaidArchive().records.slice(0, RAID_ARCHIVE_LIMIT).map(entry => entry.result);
}

function pruneRaidArchive() {
    const archive = collectRaidArchive();
    let saved = archive.keys !== null;
    for (const entry of archive.records.slice(RAID_ARCHIVE_LIMIT)) {
        saved = safeStorageRemove(entry.key) && saved;
    }
    return saved;
}

function appendRaidArchive(result) {
    if (!normalizeBattleResult(result) || !ownsBattleResult(result)) return false;
    const archive = collectRaidArchive();
    if (!archive.keys) return false;
    if (raidWasCleared(result, archive.meta)) return true;
    if (archive.records.some(entry => entry.result.battleId === result.battleId)) return pruneRaidArchive();
    // Each ID has its own atomic storage entry: tabs cannot overwrite one another's raids.
    const key = raidArchiveRecordKey(result.battleId);
    const saved = safeStorageSet(key, JSON.stringify({
        schemaVersion: 1, ownerId: raidArchiveOwnerId, generation: archive.meta.generation, result
    }));
    if (!saved) return false;
    const latestMeta = readRaidArchiveMeta();
    if (latestMeta.generation !== archive.meta.generation) {
        safeStorageRemove(key);
        return raidWasCleared(result, latestMeta) ? true : appendRaidArchive(result);
    }
    return pruneRaidArchive();
}

function saveRaidArchiveResult(result) {
    const saved = appendRaidArchive(result);
    if (saved) pendingArchiveResults.delete(result.battleId);
    else pendingArchiveResults.set(result.battleId, JSON.parse(JSON.stringify(result)));
    raidArchiveSaveFailed = pendingArchiveResults.size > 0;
    updateRaidArchiveNotice();
    return saved;
}

function retryRaidArchiveSave() {
    for (const result of [...pendingArchiveResults.values()]) saveRaidArchiveResult(result);
    if (pendingBattleReward) retryBattleResultSave();
    renderRaidArchive();
}

function recordUnrewardedRaid(outcome) {
    if (!isBattleActive || !currentBattleSession || currentBattleSession.finished) return;
    const boss = bossesDatabase[currentBattleSession.bossKey];
    if (!boss) return;
    const result = buildBattleResult(boss, outcome);
    currentBattleSession.finished = true;
    saveRaidArchiveResult(result);
}

function getRaidDossierImage(result) {
    // Legacy snapshots have no image field; reuse the same cardImg as the boss dossier.
    // An explicit null in a new snapshot means no card existed at the time of the raid.
    const source = Object.hasOwn(result.boss, 'dossierImage')
        ? result.boss.dossierImage : bossesDatabase[result.boss.id]?.dossier?.cardImg;
    // Historical files may be edited in browser storage. Only allow local image paths.
    return typeof source === 'string'
        && /^(?:[A-Za-z0-9_-]+\/)*[A-Za-z0-9_-]+\.(?:png|jpe?g|webp)$/i.test(source) ? source : null;
}

function getDossierFrameClass(source) {
    // Presentation only: these PNGs share large fully transparent side margins.
    // CSS hides those margins while preserving every nontransparent card pixel.
    if (source === 'nurse_dossier_card.png') return ' dossier-card-trim';
    if (source === 'doctor_dossier_card.png') return ' dossier-card-trim dossier-card-trim-doctor';
    return '';
}

function renderRaidArchive() {
    const list = document.getElementById('raid-archive-list');
    if (!list) return;
    const records = readRaidArchive();
    document.getElementById('raid-archive-count').textContent = `${records.length} / ${RAID_ARCHIVE_LIMIT}`;
    document.getElementById('raid-archive-empty')?.classList.toggle('hidden', records.length > 0);
    document.getElementById('raid-archive-clear').disabled = records.length === 0;
    list.innerHTML = records.map(result => {
        const mvp = result.participants.find(member => member.id === result.mvpId);
        const items = result.extraRewards.filter(reward => reward.granted);
        const dossierImage = getRaidDossierImage(result);
        const personalStamp = getParticipantReportStamp(result.participants.find(member => member.isPlayer));
        return `<li><button type="button" class="raid-archive-card" data-raid-id="${escapeHTML(result.battleId)}">
            <span class="raid-card-visual${getDossierFrameClass(dossierImage)}">
                ${dossierImage ? `<img class="raid-card-dossier-image" src="${escapeHTML(dossierImage)}" alt="Досьє: ${escapeHTML(result.boss.name)} — №${escapeHTML(result.boss.registrationNumber)}" loading="lazy" decoding="async">` : ''}
                <span class="raid-card-no-dossier${dossierImage ? ' hidden' : ''}">${iconHTML('clipboard', 'large')}<span>Досьє не долучено</span></span>
            </span>
            <span class="raid-card-details">
            <span class="raid-card-heading"><strong>${escapeHTML(result.boss.name)} — №${escapeHTML(result.boss.registrationNumber)}</strong><time datetime="${new Date(result.endedAt).toISOString()}">${escapeHTML(new Date(result.endedAt).toLocaleString('uk-UA'))}</time></span>
            <span class="raid-card-case">Справа ${escapeHTML(result.boss.caseCode)}</span>
            <span class="raid-card-result">${escapeHTML(RAID_OUTCOMES[result.outcome || 'victory'])}</span>
            <span class="raid-card-rewards">+${result.payout.exp} EXP · +${result.payout.silver} срібла${(result.outcome || 'victory') === 'victory' && result.participants.some(member => member.isPlayer && member.isMvp) ? ' · особистий бонус MVP +5%' : ''}</span>
            ${mvp ? `<span class="raid-card-mvp">MVP: ${escapeHTML(mvp.name)}</span>` : ''}
            ${items.length ? `<span class="raid-card-items">Отримано: ${items.map(reward => escapeHTML(reward.name)).join(', ')}</span>` : ''}
            ${personalStamp ? `<span class="report-participant-stamp raid-card-personal-stamp">${personalStamp}</span>` : ''}
            <span class="raid-card-open">Детальний протокол →</span>
            </span>
        </button></li>`;
    }).join('');
    list.querySelectorAll('[data-raid-id]').forEach(button => button.addEventListener('click', () => {
        const result = readRaidArchive().find(record => record.battleId === button.dataset.raidId);
        if (result) openDetailedBattleReport(result, 'archive');
    }));
    list.querySelectorAll('.raid-card-dossier-image').forEach(image => {
        const showMissingDossier = () => {
            image.classList.add('hidden');
            image.nextElementSibling?.classList.remove('hidden');
        };
        image.addEventListener('error', showMissingDossier);
        if (image.complete && !image.naturalWidth) showMissingDossier();
    });
    updateRaidArchiveNotice();
}

function updateRaidArchiveNotice() {
    const failed = raidArchiveSaveFailed || raidArchiveStorageKeys() === null;
    const note = document.getElementById('raid-archive-save-note');
    if (note) {
        note.classList.toggle('hidden', !failed);
        note.textContent = failed ? 'Не вдалося зберегти історію рейдів. Не закривайте сторінку; спробуйте збереження ще раз.' : '';
    }
    document.getElementById('raid-archive-save-retry')?.classList.toggle('hidden', !failed);
}

function openRaidArchive() {
    closeOtherModals(['raid-archive-modal']);
    renderRaidArchive();
    document.getElementById('raid-archive-modal')?.classList.remove('hidden');
}

function closeRaidArchive() {
    document.getElementById('raid-archive-modal')?.classList.add('hidden');
}

function requestRaidArchiveClear() {
    if (!readRaidArchive().length) return;
    document.getElementById('raid-archive-confirm')?.classList.remove('hidden');
}

function cancelRaidArchiveClear() {
    document.getElementById('raid-archive-confirm')?.classList.add('hidden');
}

function clearRaidArchive() {
    const archive = collectRaidArchive();
    if (!archive.keys) return false;
    const clearedAt = Math.max(Date.now(), archive.meta.clearedAt);
    const ids = archive.records.map(entry => entry.result.battleId);
    for (const result of [lastBattleResult, pendingBattleReward?.result, ...pendingArchiveResults.values()]) {
        if (ownsBattleResult(result) && result.endedAt <= clearedAt) ids.push(result.battleId);
    }
    if (archive.meta.clearedAt === clearedAt) ids.push(...archive.meta.clearedIds);
    // The generation is the clear transaction: other tabs immediately see an empty archive.
    if (!safeStorageSet(`${raidArchivePrefix()}meta`, JSON.stringify({
        schemaVersion: 1, ownerId: raidArchiveOwnerId, generation: archive.meta.generation + 1,
        clearedAt, clearedIds: [...new Set(ids)]
    }))) return false;
    archive.keys.filter(key => key.startsWith(`${raidArchivePrefix()}raid:`)).forEach(safeStorageRemove);
    pendingArchiveResults.clear();
    raidArchiveSaveFailed = false;
    return true;
}

function confirmRaidArchiveClear() {
    if (!clearRaidArchive()) {
        showCustomToast('Не вдалося очистити архів: сховище недоступне.');
        return;
    }
    cancelRaidArchiveClear();
    renderRaidArchive();
}
