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

// === Збереження та Завантаження прогресу ===
const DEFAULT_STATS = {
    money: 125,
    pills: 4,
    scrap: 1,
    hp: 100,
    maxHp: 100,
    armor: 0,
    dmg: 10,
    madness: 45,
    energy: 55,
    maxEnergy: 100
};

let stats = loadSaveData('palata404_stats', DEFAULT_STATS);
let currentOutfit = localStorage.getItem('palata404_outfit') || 'default';

let outfits = loadSaveData('palata404_outfits', {
    'default': { name: 'Рвануватий халат', icon: '🩺', cost: 0, bonus: 'Без бонусив', purchased: true, armorBonus: 0, hpBonus: 0 },
    'cozy': { name: 'Смикальна сорочка', icon: '🥋', cost: 50, bonus: '+10 до Броні (пасивно)', purchased: false, armorBonus: 10, hpBonus: 0 },
    'mask': { name: 'Маска Тріщини', icon: '🎭', cost: 120, bonus: '+20 до Броні, +15 Макс. HP', purchased: false, armorBonus: 20, hpBonus: 15 }
});

let inventory = loadSaveData('palata404_inventory', [
    { id: 'pm', name: 'ПМ', type: 'weapon', bonus: '+15 Шкоди' },
    { id: 'helmet', name: 'Тактичний шолом', type: 'helmet', bonus: '+15 Броні' },
    { id: 'vest', name: 'Плитник (Бронежилет)', type: 'armor', bonus: '+35 Броні' },
    { id: 'sight', name: 'Коліматорний приціл', type: 'attachment', bonus: '+5 Шкоди' },
    { id: 'morphine', name: 'Стимулятор \'Морфін\'', type: 'use', bonus: 'Відновлює 50 HP' }
]);

function loadSaveData(key, fallback) {
    const saved = localStorage.getItem(key);
    if (!saved) return fallback;
    try {
        return JSON.parse(saved);
    } catch (e) {
        return fallback;
    }
}

function saveGameProgress() {
    localStorage.setItem('palata404_stats', JSON.stringify(stats));
    localStorage.setItem('palata404_outfit', currentOutfit);
    localStorage.setItem('palata404_outfits', JSON.stringify(outfits));
    localStorage.setItem('palata404_inventory', JSON.stringify(inventory));
}

// === Оновлення Інтерфейсу ===
function updateUI() {
    document.getElementById('money').textContent = stats.money;
    document.getElementById('pills').textContent = stats.pills;
    document.getElementById('scrap').textContent = stats.scrap;

    let outfitArmor = outfits[currentOutfit]?.armorBonus || 0;
    let outfitHp = outfits[currentOutfit]?.hpBonus || 0;

    let totalMaxHp = stats.maxHp + outfitHp;
    let totalArmor = stats.armor + outfitArmor;

    document.getElementById('hp-val').textContent = `${stats.hp} / ${totalMaxHp} HP`;
    document.getElementById('armor-val').textContent = totalArmor;
    document.getElementById('dmg-val').textContent = stats.dmg;
    document.getElementById('madness-val').textContent = `${stats.madness}%`;
    document.getElementById('energy-val').textContent = `${stats.energy}/${stats.maxEnergy}`;

    document.getElementById('hp-bar').style.width = `${Math.min(100, Math.max(0, (stats.hp / totalMaxHp) * 100))}%`;
    document.getElementById('madness-bar').style.width = `${Math.min(100, Math.max(0, stats.madness))}%`;
    document.getElementById('energy-bar').style.width = `${Math.min(100, Math.max(0, stats.energy))}%`;

    document.getElementById('outfit-icon').textContent = outfits[currentOutfit].icon;

    updatePlayerNameDisplay();
    saveGameProgress(); // Автоматичне збереження стану при кожному оновленні UI
}

// === Кліки та Божевілля ===
function tapCharacter() {
    if (stats.energy >= 5) {
        stats.energy -= 5;
        stats.money += Math.floor(Math.random() * 5) + 2;
        
        // Покращений набір божевілля: +3–6% за кожен клік
        const madnessGain = Math.floor(Math.random() * 4) + 3;
        stats.madness = Math.min(100, stats.madness + madnessGain);

        // Побочний ефект високого божевілля
        if (stats.madness >= 80 && Math.random() > 0.5) {
            stats.hp = Math.max(1, stats.hp - 2); // втрачає HP від галюцинацій
        }
    } else {
        alert("Занадто мало енергії! Потрібно поспати.");
    }
    updateUI();
}

function restInBed() {
    stats.energy = Math.min(stats.maxEnergy, stats.energy + 35);
    // Сон зменшує божевілля
    stats.madness = Math.max(0, stats.madness - 15);
    updateUI();
}

// === Модальні вікна ===
function openInventory() {
    renderStash();
    document.getElementById('inventory-modal').classList.remove('hidden');
}

function closeInventory() {
    document.getElementById('inventory-modal').classList.add('hidden');
}

function openCustomization() {
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

        let btnText = item.purchased ? (currentOutfit === key ? 'Надіто ✓' : 'Вдягти') : `Купити ${item.cost}$`;
        let btnClass = item.purchased ? (currentOutfit === key ? 'btn-outfit equipped' : 'btn-outfit') : 'btn-outfit buy';

        card.innerHTML = `
            <div class="outfit-info">
                <div class="outfit-icon-large">${item.icon}</div>
                <div class="outfit-details">
                    <h4>${item.name}</h4>
                    <p>${item.bonus}</p>
                </div>
            </div>
            <button class="${btnClass}" onclick="selectOutfit('${key}')">${btnText}</button>
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

function renderStash() {
    const container = document.getElementById('stash-items');
    container.innerHTML = '';

    inventory.forEach((item, index) => {
        let row = document.createElement('div');
        row.className = 'stash-item';
        row.innerHTML = `
            <span>📦 ${item.name} <small style="color:#aaa">(${item.bonus})</small></span>
            <button onclick="useItem(${index})">Вдягти/Ужити</button>
        `;
        container.appendChild(row);
    });
}

function useItem(index) {
    let item = inventory[index];
    if (item.type === 'use') {
        stats.hp = Math.min(stats.maxHp, stats.hp + 50);
        inventory.splice(index, 1);
    } else {
        alert(`Предмет ${item.name} екіпіровано!`);
    }
    updateUI();
    renderStash();
}

document.addEventListener('DOMContentLoaded', () => {
    updateUI();
});