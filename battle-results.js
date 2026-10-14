// Post-battle accounting and presentation. Combat rules stay in script.js.
let currentBattleSession = null;
let lastBattleResult = null;
let pendingBattleReward = null;
let battleResultPersisted = false;
let battleSessionSequence = 0;

function readPendingBattleReward() {
    try {
        const pending = JSON.parse(safeStorageGet('palata404_pending_battle_reward'));
        const result = normalizeBattleResult(pending?.result);
        const state = pending?.state;
        if (!result || !ownsBattleResult(result) || !state || !state.stats || typeof state.stats !== 'object' || Array.isArray(state.stats)
            || !Array.isArray(state.inventory) || !state.bossKills
            || typeof state.bossKills !== 'object' || Array.isArray(state.bossKills)) return null;
        return { result, state };
    } catch (error) {
        return null;
    }
}

function prepareBattleRewardSave() {
    if (!pendingBattleReward) return true;
    pendingBattleReward.state = { stats, inventory, bossKills: bossKillsCount };
    const saved = safeStorageSet('palata404_pending_battle_reward', JSON.stringify(pendingBattleReward));
    if (!saved) battleResultPersisted = false;
    return saved;
}

function finishBattleRewardSave(saved) {
    if (!pendingBattleReward) return saved;
    if (!saved || !safeStorageSet('palata404_last_battle_result', JSON.stringify(pendingBattleReward.result))) {
        battleResultPersisted = false;
        return false;
    }
    battleResultPersisted = true;
    if (!saveRaidArchiveResult(pendingBattleReward.result)) return false;
    if (safeStorageRemove('palata404_pending_battle_reward')) pendingBattleReward = null;
    return true;
}

function beginBattleMetrics(bossKey) {
    const uniquePart = window.crypto?.randomUUID?.()
        || `${Date.now().toString(36)}-${++battleSessionSequence}-${Math.random().toString(36).slice(2, 10)}`;
    currentBattleSession = {
        id: `raid-${uniquePart}`, bossKey, startedAt: Date.now(), finished: false,
        serial: 0, events: new Set()
    };
    raidMembers.forEach(member => {
        member.metrics = {
            damageTaken: member.isPlayer ? 0 : null,
            healing: member.isPlayer ? 0 : null,
            turns: 0,
            madnessStart: member.isPlayer ? stats.madness : null
        };
    });
}

function nextBattleEventId(type) {
    return currentBattleSession && !currentBattleSession.finished ? `${currentBattleSession.id}:${++currentBattleSession.serial}:${type}` : null;
}

function recordBattleEvent(id, member, delta) {
    const battle = currentBattleSession;
    if (!isBattleActive || !battle || battle.finished || typeof id !== 'string'
        || !id.startsWith(`${battle.id}:`) || !member?.metrics || !raidMembers.includes(member)
        || battle.events.has(id)) return false;
    battle.events.add(id);
    if (Number.isFinite(delta.damage) && delta.damage >= 0) member.damage += delta.damage;
    ['damageTaken', 'healing', 'turns'].forEach(field => {
        if (member.metrics[field] !== null && Number.isFinite(delta[field]) && delta[field] >= 0) {
            member.metrics[field] += delta[field];
        }
    });
    return true;
}

function recordPlayerRecovery(healing, usedMedicine = false) {
    const player = raidMembers.find(member => member.isPlayer);
    recordBattleEvent(nextBattleEventId('recovery'), player, {
        healing: Math.max(0, healing), turns: usedMedicine ? 1 : 0
    });
}

function buildBattleResult(boss, outcome = 'victory') {
    const battle = currentBattleSession;
    const members = raidMembers.filter(member => member.isPlayer || member.called);
    // Stable sorting retains the existing player-first tie rule.
    const sorted = [...members].sort((a, b) => b.damage - a.damage);
    const totalDamage = members.reduce((sum, member) => sum + member.damage, 0);
    const mvpId = sorted[0]?.damage > 0 ? sorted[0].id : null;
    const won = outcome === 'victory';
    const baseExp = won ? boss.expReward : 0;
    const baseSilver = won ? boss.silverReward : 0;
    const playerIsMvp = sorted.find(member => member.id === mvpId)?.isPlayer === true;
    // Saved currencies and experience use whole numbers; round the 5% addition down.
    const bonusExp = playerIsMvp ? Math.floor(baseExp * 5 / 100) : 0;
    const bonusSilver = playerIsMvp ? Math.floor(baseSilver * 5 / 100) : 0;
    const report = boss.victoryReport || {};
    return {
        schemaVersion: 1,
        ownerId: raidArchiveOwnerId,
        outcome,
        battleId: battle.id,
        startedAt: battle.startedAt,
        endedAt: Date.now(),
        boss: {
            id: battle.bossKey, name: boss.name,
            registrationNumber: boss.dossier?.code || report.registrationNumber || battle.bossKey,
            dossierImage: boss.dossier?.cardImg || null,
            caseCode: report.caseCode || 'Не зазначено',
            status: won ? (report.status || 'Тимчасова стабілізація') : RAID_OUTCOMES[outcome],
            conclusion: won ? (report.conclusion || 'Післябойовий стан об’єкта зафіксовано. Медичний висновок потребує уточнення.')
                : `${RAID_OUTCOMES[outcome]}. Тимчасової стабілізації об’єкта не підтверджено. Нагороди не видано.`
        },
        mvpId,
        totalDamage,
        payout: { baseExp, baseSilver, bonusExp, bonusSilver, exp: baseExp + bonusExp, silver: baseSilver + bonusSilver },
        participants: sorted.map(member => ({
            id: member.id, name: member.isPlayer ? playerName : member.name,
            isPlayer: member.isPlayer === true,
            damage: member.damage,
            damageTaken: member.metrics.damageTaken,
            healing: member.metrics.healing,
            turns: member.metrics.turns,
            madnessStart: member.metrics.madnessStart,
            madnessEnd: member.isPlayer ? stats.madness : null,
            madnessDelta: member.isPlayer ? stats.madness - member.metrics.madnessStart : null,
            damageShare: totalDamage > 0 ? member.damage / totalDamage * 100 : 0,
            isMvp: member.id === mvpId,
            activityStatus: member.isPlayer && [member.damage, member.metrics.healing, member.metrics.turns, member.metrics.damageTaken]
                .every(value => Number.isFinite(value) && value >= 0)
                ? ([member.damage, member.metrics.healing, member.metrics.turns, member.metrics.damageTaken].some(value => value > 0) ? 'useful' : 'inactive')
                : null,
            specialStatus: typeof member.status === 'string' ? member.status : null,
            rewards: member.isPlayer ? { exp: baseExp + bonusExp, silver: baseSilver + bonusSilver } : null
        })),
        extraRewards: won && boss.questItem ? [{
            type: 'item', name: boss.questItem.name, icon: resolveIconKey(boss.questItem.icon),
            granted: !inventory.some(item => item.name === boss.questItem.name)
        }] : []
    };
}

function normalizeBattleResult(value) {
    const object = data => data && typeof data === 'object' && !Array.isArray(data);
    const number = data => Number.isSafeInteger(data) && data >= 0;
    const nullableNumber = data => data === null || number(data);
    if (!object(value) || value.schemaVersion !== 1 || typeof value.battleId !== 'string'
        || !object(value.boss) || !object(value.payout) || !Array.isArray(value.participants)
        || !value.participants.length || !Array.isArray(value.extraRewards)
        || !number(value.startedAt) || !number(value.endedAt) || value.endedAt < value.startedAt
        || !number(value.totalDamage)
        || !Number.isFinite(new Date(value.endedAt).getTime())
        || (value.ownerId !== undefined && typeof value.ownerId !== 'string')
        || (value.outcome !== undefined && !Object.hasOwn(RAID_OUTCOMES, value.outcome))) return null;
    if (!['id', 'name', 'registrationNumber', 'caseCode', 'status', 'conclusion']
        .every(field => typeof value.boss[field] === 'string')) return null;
    if (value.boss.dossierImage !== undefined && value.boss.dossierImage !== null
        && typeof value.boss.dossierImage !== 'string') return null;
    if (!['baseExp', 'baseSilver', 'bonusExp', 'bonusSilver', 'exp', 'silver'].every(field => number(value.payout[field]))) return null;
    if (value.payout.exp !== value.payout.baseExp + value.payout.bonusExp
        || value.payout.silver !== value.payout.baseSilver + value.payout.bonusSilver) return null;
    if (!value.participants.every(member => object(member) && typeof member.id === 'string'
        && typeof member.name === 'string' && typeof member.isPlayer === 'boolean'
        && typeof member.isMvp === 'boolean' && number(member.damage) && number(member.turns)
        && (member.activityStatus === undefined || member.activityStatus === null || ['useful', 'inactive'].includes(member.activityStatus))
        && nullableNumber(member.damageTaken) && nullableNumber(member.healing)
        && nullableNumber(member.madnessStart) && nullableNumber(member.madnessEnd)
        && (member.madnessDelta === null || Number.isSafeInteger(member.madnessDelta))
        && Number.isFinite(member.damageShare) && member.damageShare >= 0 && member.damageShare <= 100
        && (member.rewards === null || (object(member.rewards) && number(member.rewards.exp) && number(member.rewards.silver))))) return null;
    if (!value.extraRewards.every(reward => object(reward) && typeof reward.name === 'string'
        && typeof reward.icon === 'string' && typeof reward.granted === 'boolean')) return null;
    return value;
}

function formatReportNumber(value) {
    return value === null ? 'Не застосовується' : String(value);
}

function formatBattleDuration(result) {
    const seconds = Math.floor((result.endedAt - result.startedAt) / 1000);
    return `${Math.floor(seconds / 60)} хв ${seconds % 60} с`;
}

function getParticipantReportStamp(member) {
    if (!member) return '';
    if (member.isMvp) return 'MVP';
    return member.isPlayer && member.activityStatus === 'inactive'
        && member.damage === 0 && member.healing === 0 && member.turns === 0 && member.damageTaken === 0
        ? 'УХИЛЯВСЯ ВІД ПРОЦЕДУРИ' : '';
}

function renderBattleSummary(result) {
    const setText = (id, value) => {
        const element = document.getElementById(id);
        if (element) element.textContent = value;
    };
    setText('victory-summary-boss', result.boss.name);
    setText('victory-summary-number', `№${result.boss.registrationNumber}`);
    setText('victory-summary-case', result.boss.caseCode);
    setText('victory-summary-exp', `+${result.payout.exp}`);
    setText('victory-summary-silver', `+${result.payout.silver}`);
    const player = result.participants.find(member => member.isPlayer);
    const mvp = result.participants.find(member => member.id === result.mvpId);
    const mvpNote = document.getElementById('victory-summary-mvp');
    if (mvpNote) {
        mvpNote.classList.toggle('hidden', !mvp);
    }
    setText('victory-summary-mvp-name', mvp ? `MVP: ${mvp.name}` : '');
    document.getElementById('victory-summary-mvp-bonus')?.classList.toggle('hidden', !player?.isMvp);
    setText('victory-summary-damage', formatReportNumber(player?.damage ?? null));
    setText('victory-summary-taken', formatReportNumber(player?.damageTaken ?? null));
    setText('victory-summary-time', formatBattleDuration(result));
    const items = document.getElementById('victory-summary-items');
    if (items) items.innerHTML = result.extraRewards.length ? result.extraRewards.map(reward =>
        `<li>${iconHTML(reward.icon)} ${reward.granted ? 'Отримано:' : 'Вже в інвентарі:'} <strong>${escapeHTML(reward.name)}</strong></li>`
    ).join('') : '<li>Нових предметів немає.</li>';
    document.getElementById('victory-summary-content')?.scrollTo(0, 0);
    updateBattleResultSaveNotice();
}

// Render a supplied snapshot without completing a fight or changing rewards/saves.
// This document can also be used for stored raid records in a future archive.
function renderBattleResult(result) {
    const setText = (id, value) => {
        const element = document.getElementById(id);
        if (element) element.textContent = value;
    };
    setText('victory-boss-id', result.boss.id);
    setText('victory-boss-number', `№${result.boss.registrationNumber}`);
    setText('victory-boss-name', result.boss.name);
    setText('victory-case-code', result.boss.caseCode);
    setText('victory-status', result.boss.status);
    setText('victory-conclusion', result.boss.conclusion);
    setText('victory-report-id', result.battleId);
    setText('victory-report-date', new Date(result.endedAt).toLocaleString('uk-UA'));
    setText('victory-duration', formatBattleDuration(result));
    const mvp = result.participants.find(member => member.id === result.mvpId);
    setText('victory-mvp-name', mvp ? mvp.name : 'Не визначено');
    setText('victory-base-exp', result.payout.baseExp);
    setText('victory-base-silver', result.payout.baseSilver);
    setText('victory-bonus-exp', result.payout.bonusExp);
    setText('victory-bonus-silver', result.payout.bonusSilver);
    setText('victory-total-exp', result.payout.exp);
    setText('victory-total-silver', result.payout.silver);
    const playerIsMvp = result.participants.some(member => member.isPlayer && member.isMvp);
    setText('victory-bonus-note', playerIsMvp
        ? 'Бонус MVP: 5% від основної нагороди, округлено вниз до цілого.'
        : 'Бонус MVP до вашої нагороди не застосовується.');
    const rows = result.participants.map(member => {
        const madness = member.madnessStart === null ? 'Не застосовується'
            : `${member.madnessStart} → ${member.madnessEnd} (${member.madnessDelta > 0 ? '+' : ''}${member.madnessDelta})`;
        // The personal payout is printed once, in the shared reward section.
        const reward = member.rewards ? '<a href="#victory-rewards">Див. підсумок нагород</a>' : 'Не застосовується';
        const status = [member.specialStatus || '', !member.isPlayer ? 'Локальний помічник' : '']
            .filter(Boolean).map(escapeHTML).join(' · ');
        const stampText = getParticipantReportStamp(member);
        const stamp = stampText ? `<span class="report-participant-stamp">${stampText}</span>` : '';
        return `<tr class="${member.isMvp ? 'report-mvp-row' : ''}">
            <th scope="row">${escapeHTML(member.name)}${stamp}${status ? `<small>${status}</small>` : ''}</th>
            <td>${member.damage}</td><td>${formatReportNumber(member.damageTaken)}</td>
            <td>${formatReportNumber(member.healing)}</td><td>${member.turns}</td>
            <td>${madness}</td><td>${member.damageShare.toFixed(1)}%</td><td>${reward}</td>
        </tr>`;
    }).join('');
    const table = document.getElementById('victory-statistics-body');
    if (table) table.innerHTML = rows;
    const additional = document.getElementById('victory-extra-rewards');
    if (additional) additional.innerHTML = result.extraRewards.length ? result.extraRewards.map(reward =>
        `<li>${iconHTML(reward.icon)} <strong>${escapeHTML(reward.name)}</strong> — ${reward.granted ? 'отримано' : 'вже є в інвентарі'}</li>`
    ).join('') : '<li>Додаткових предметів не видано.</li>';
    updateBattleResultSaveNotice();
}

function updateBattleResultSaveNotice() {
    for (const prefix of ['victory', 'victory-detail']) {
        const note = document.getElementById(`${prefix}-save-note`);
        if (!note) continue;
        const failed = !battleResultPersisted || raidArchiveSaveFailed;
        const historical = prefix === 'victory-detail' && battleReportSource === 'archive';
        note.classList.toggle('hidden', !failed || historical);
        note.textContent = battleResultPersisted
            ? (raidArchiveSaveFailed ? 'Нагороди збережено, але запис архіву ще не збережений. Спробуйте ще раз.' : '')
            : 'Протокол і нагороди поки не вдалося зберегти. Не закривайте сторінку; спробуйте зберегти ще раз.';
        document.getElementById(`${prefix}-save-retry`)?.classList.toggle('hidden', !failed || historical);
    }
}

function openLastBattleResult() {
    if (!lastBattleResult) {
        showCustomToast('Збереженого протоколу бою ще немає.');
        return;
    }
    closeOtherModals(['nurse-victory-modal']);
    renderBattleSummary(lastBattleResult);
    document.getElementById('nurse-victory-modal')?.classList.remove('hidden');
}

function openDetailedBattleReport(result = lastBattleResult, source = 'summary') {
    if (!normalizeBattleResult(result) || !ownsBattleResult(result)) return;
    battleReportSource = source;
    closeOtherModals(['battle-detail-modal']);
    renderBattleResult(result);
    document.getElementById('victory-detail-back').textContent = source === 'archive' ? 'Повернутися до архіву' : 'Повернутися до підсумку';
    document.getElementById('victory-detail-document')?.scrollTo(0, 0);
    document.getElementById('battle-detail-modal')?.classList.remove('hidden');
}

function closeDetailedBattleReport() {
    document.getElementById('battle-detail-modal')?.classList.add('hidden');
    if (battleReportSource === 'archive') openRaidArchive();
    else openLastBattleResult();
}

function retryBattleResultSave() {
    saveGameProgress();
    for (const result of [...pendingArchiveResults.values()]) saveRaidArchiveResult(result);
    updateBattleResultSaveNotice();
}

function closeLastBattleResult() {
    document.getElementById('nurse-victory-modal')?.classList.add('hidden');
}
