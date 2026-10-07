// === Telegram Web App та Нікнейм ===
const tg = window.Telegram?.WebApp;
if (tg) {
    try {
        tg.ready();
        tg.expand();
    } catch (e) {
        console.log("Telegram WebApp не ініціалізовано");
    }
}

function getInitialUsername() {
    const savedName = localStorage.getItem('palata404_nickname');
    if (savedName) return savedName;

    if (tg && tg.initDataUnsafe && tg.initDataUnsafe.user) {
        const user = tg.initDataUnsafe.user;
        if (user.username) return `@${user.username}`;
        if (user.first_name) return `${user.first_name}${user.last_name ? ' ' + user.last_name : ''}`;
    }

    return "Пацієнт #404";
}

let playerName = getInitialUsername();

function updatePlayerNameDisplay() {
    const nameElement = document.getElementById('player-name');
    if (nameElement) {
        nameElement.textContent = playerName;
    }
}

function changeNickname() {
    const newName = prompt("Введіть ваш новий нікнейм:", playerName);
    if (newName && newName.trim() !== "") {
        playerName = newName.trim().substring(0, 20);
        localStorage.setItem('palata404_nickname', playerName);
        updatePlayerNameDisplay();
    }
}

// === Збереження та Завантаження даних ===
const DEFAULT_STATS = {
    money: 125,
    hp: 100,
    maxHp: 100,
    madness: 20,
    energy: 100,
    maxEnergy: 100,
    level: 1,
    exp: 0,
    nextLvlExp: 100
};

let stats = loadSaveData('palata404_stats', DEFAULT_STATS);
let currentOutfit = localStorage.getItem('palata404_outfit') || 'default';

let outfits = loadSaveData('palata404_outfits', {
    'default': { name: 'Рвануватий халат', avatar: '🥷', cost: 0, purchased: true },
    'cozy': { name: 'Смикальна сорочка', avatar: '🥋', cost: 50, purchased: false },
    'mask': { name: 'Маска Тріщини', avatar: '🎭', cost: 120, purchased: false },
    'armor': { name: 'Важка броня', avatar: '🪖', cost: 250, purchased: false }
});

// Інвентар з категоріями: weapon, helmet, armor, mod, meds
let inventory = loadSaveData('palata404_inventory', [
    { name: 'ПМ', icon: '🔫', count: 1, category: 'weapon' },
    { name: 'Тактичний шолом', icon: '🪖', count: 1, category: 'helmet' },
    { name: 'Бронежилет БР-1', icon: '🛡️', count: 1, category: 'armor' },
    { name: 'Приціл RedDot', icon: '🧩', count: 1, category: 'mod' },
    { name: 'Аптечка', icon: '🧪', count: 3, category: 'meds' }
]);

let currentCategory = 'all';

function loadSaveData(key, fallback) {
    const saved = localStorage.getItem(key);
    if (!saved) return fallback;
    try { return JSON.parse(saved); } catch (e) { return fallback; }
}

function saveGameProgress() {
    localStorage.setItem('palata404_stats', JSON.stringify(stats));
    localStorage.setItem('palata404_outfit', currentOutfit);
    localStorage.setItem('palata404_outfits', JSON.stringify(outfits));
    localStorage.setItem('palata404_inventory', JSON.stringify(inventory));
}

function getPlayerRank(level) {
    if (level >= 20) return "Легенда Руїн";
    if (level >= 15) return "Ветеран";
    if (level >= 10) return "Шукач";
    if (level >= 5) return "Виживальник";
    return "Новачок";
}

function addExperience(amount) {
    stats.exp += amount;
    if (!stats.nextLvlExp) stats.nextLvlExp = stats.level * 100;

    while (stats.exp >= stats.nextLvlExp) {
        stats.exp -= stats.nextLvlExp;
        stats.level += 1;
        stats.nextLvlExp = stats.level * 120;
        stats.maxHp += 5;
        stats.hp = stats.maxHp;
        alert(`🎉 Вітаємо! Ви досягли ${stats.level} рівня!\nВаше звання: ${getPlayerRank(stats.level)}`);
    }
}

// === Оновлення Інтерфейсу ===
function updateUI() {
    document.getElementById('hp-val').textContent = `${stats.hp} / ${stats.maxHp}`;
    document.getElementById('madness-val').textContent = `${stats.madness} / 100`;
    document.getElementById('energy-val').textContent = `${stats.energy} / ${stats.maxEnergy}`;

    document.getElementById('hp-bar').style.width = `${Math.min(100, (stats.hp / stats.maxHp) * 100)}%`;
    document.getElementById('madness-bar').style.width = `${Math.min(100, stats.madness)}%`;
    document.getElementById('energy-bar').style.width = `${Math.min(100, (stats.energy / stats.maxEnergy) * 100)}%`;

    document.getElementById('player-lvl').textContent = stats.level;
    document.getElementById('player-rank').textContent = getPlayerRank(stats.level);
    document.getElementById('exp-val').textContent = `${stats.exp} / ${stats.nextLvlExp} EXP`;
    
    let expPercent = (stats.exp / stats.nextLvlExp) * 100;
    document.getElementById('exp-bar').style.width = `${Math.min(100, expPercent)}%`;

    const heroElem = document.getElementById('character');
    if (heroElem) {
        const activeOutfit = outfits[currentOutfit] || outfits['default'];
        heroElem.textContent = activeOutfit ? activeOutfit.avatar : '🥷';
    }

    updatePlayerNameDisplay();
    saveGameProgress();
}

// === Дії ===
function tapCharacter() {
    if (stats.energy >= 5) {
        stats.energy -= 5;
        stats.money += Math.floor(Math.random() * 5) + 2;
        
        const madnessGain = Math.floor(Math.random() * 4) + 3;
        stats.madness = Math.min(100, stats.madness + madnessGain);

        addExperience(Math.floor(Math.random() * 10) + 15);
    } else {
        alert("Занадто мало витривалості! Потрібно відпочити.");
    }
    updateUI();
}

function restInBed() {
    stats.energy = Math.min(stats.maxEnergy, stats.energy + 35);
    stats.madness = Math.max(0, stats.madness - 15);
    updateUI();
}

// === Інвентар з фільтрацією ===
function openInventory() {
    closeCustomization();
    renderMinecraftStash();
    document.getElementById('inventory-modal').classList.remove('hidden');
}

function closeInventory() {
    document.getElementById('inventory-modal').classList.add('hidden');
}

function setCategoryFilter(category, btnElem) {
    currentCategory = category;
    
    document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
    if (btnElem) btnElem.classList.add('active');

    renderMinecraftStash();
}

function renderMinecraftStash() {
    const container = document.getElementById('stash-items');
    container.innerHTML = '';

    const filteredItems = currentCategory === 'all' 
        ? inventory 
        : inventory.filter(item => item.category === currentCategory);

    const TOTAL_SLOTS = 20;
    for (let i = 0; i < TOTAL_SLOTS; i++) {
        let slot = document.createElement('div');
        slot.className = 'mc-slot';

        if (filteredItems[i]) {
            let item = filteredItems[i];
            slot.innerHTML = `
                <span class="item-icon">${item.icon}</span>
                ${item.count > 1 ? `<span class="item-count">${item.count}</span>` : ''}
            `;
            slot.onclick = () => alert(`Предмет: ${item.name}`);
        }
        container.appendChild(slot);
    }
}

// === Гардероб ===
function openCustomization() {
    closeInventory();
    renderWardrobe();
    document.getElementById('custom-modal').classList.remove('hidden');
}

function closeCustomization() {
    document.getElementById('custom-modal').classList.add('hidden');
}

function renderWardrobe() {
    const container = document.getElementById('wardrobe-container');
    container.innerHTML = '';

    for (let key in outfits) {
        let item = outfits[key];
        let card = document.createElement('div');
        card.className = `outfit-card ${currentOutfit === key ? 'active' : ''}`;

        let btnText = item.purchased ? (currentOutfit === key ? 'Вдягнено' : 'Вдягти') : `Купити ${item.cost}$`;

        card.innerHTML = `
            <div style="display:flex; align-items:center; gap:10px;">
                <span style="font-size:24px;">${item.avatar}</span>
                <div>
                    <h4 style="font-size:12px; color:#fff;">${item.name}</h4>
                </div>
            </div>
            <button class="btn-outfit" onclick="selectOutfit('${key}')">${btnText}</button>
        `;
        container.appendChild(card);
    }
}

function selectOutfit(key) {
    let item = outfits[key];
    if (!item.purchased) {
        if (stats.money >= item.cost) {
            stats.money -= item.cost;
            item.purchased = true;
            currentOutfit = key;
        } else {
            alert("Недостатньо грошей!");
        }
    } else {
        currentOutfit = key;
    }
    updateUI();
    renderWardrobe();
}

document.addEventListener('DOMContentLoaded', () => {
    updateUI();
});