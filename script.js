const tg = window.Telegram.WebApp;
tg.expand();

let hp = 100;
let pills = 0;
let scrap = 0; // Брухт / Деталі для крафту
let madness = 20;
let energy = 80;
let currentOutfit = '🩺';

// Структура Military-екіпіровки
let equipment = {
    helmet: null,
    armor: null,
    weapon: "ПМ (Базовий)",
    attachment: null
};

let stash = ["Гільза 9mm", "Аптечка ПМП"];

function saveProgress() {
    const gameState = { hp, pills, scrap, madness, energy, currentOutfit, equipment, stash };
    localStorage.setItem('palata404_save', JSON.stringify(gameState));
    if (tg.CloudStorage) tg.CloudStorage.setItem('palata404_save', JSON.stringify(gameState));
}

function loadProgress() {
    const savedData = localStorage.getItem('palata404_save');
    if (savedData) {
        try {
            const gameState = JSON.parse(savedData);
            hp = gameState.hp ?? 100;
            pills = gameState.pills ?? 0;
            scrap = gameState.scrap ?? 0;
            madness = gameState.madness ?? 20;
            energy = gameState.energy ?? 80;
            currentOutfit = gameState.currentOutfit ?? '🩺';
            equipment = gameState.equipment ?? equipment;
            stash = gameState.stash ?? stash;
        } catch (e) { console.error(e); }
    }
    
    const outfitEl = document.getElementById('outfit-icon');
    if (outfitEl) outfitEl.innerText = currentOutfit;

    if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
        const nameEl = document.getElementById('player-name');
        if (nameEl) nameEl.innerText = tg.initDataUnsafe.user.first_name;
    }
    
    updateUI();
}

function tapCharacter() {
    if (madness >= 100) {
        hp = Math.max(0, hp - 10);
        alert("🌀 Розум повністю затьмарено! Ти втрачаєш здоров'я (-10 HP). Поспи!");
        updateUI();
        saveProgress();
        return;
    }

    if (energy >= 5) {
        energy -= 5;
        madness += 5;
        pills += 1;

        // Шанс знайти деталі під час пошуку
        if (Math.random() > 0.6) {
            scrap += 1;
        }

        if (madness > 100) madness = 100;

        updateUI();
        saveProgress();
    } else {
        alert("Нестача енергії! Скористайся ліжком, щоб поспати.");
    }
}

function restInBed() {
    if (energy < 100 || madness > 0) {
        energy = Math.min(100, energy + 30);
        madness = Math.max(0, madness - 25);
        updateUI();
        saveProgress();
    }
}

/* Інвентар та сховище */
function openInventory() {
    renderStash();
    const modal = document.getElementById('inventory-modal');
    if (modal) modal.classList.remove('hidden');
}

function closeInventory() {
    const modal = document.getElementById('inventory-modal');
    if (modal) modal.classList.add('hidden');
}

function renderStash() {
    document.getElementById('slot-weapon').innerText = equipment.weapon || "Порожньо";
    document.getElementById('slot-helmet').innerText = equipment.helmet || "Порожньо";
    document.getElementById('slot-armor').innerText = equipment.armor || "Порожньо";
    document.getElementById('slot-attachment').innerText = equipment.attachment || "Без обвісу";

    const stashContainer = document.getElementById('stash-items');
    stashContainer.innerHTML = '';

    if (stash.length === 0) {
        stashContainer.innerHTML = '<div class="stash-item">Сховище порожнє</div>';
    } else {
        stash.forEach((item) => {
            const div = document.createElement('div');
            div.className = 'stash-item';
            div.innerHTML = `<span>📦 ${item}</span>`;
            stashContainer.appendChild(div);
        });
    }
}

function openCustomization() {
    const modal = document.getElementById('custom-modal');
    if (modal) modal.classList.remove('hidden');
}

function closeCustomization() {
    const modal = document.getElementById('custom-modal');
    if (modal) modal.classList.add('hidden');
}

function setOutfit(icon, name, price) {
    if (price > pills) {
        alert("Не вистачає пігулок!");
        return;
    }
    
    if (price > 0 && currentOutfit !== icon) {
        pills -= price;
    }
    
    currentOutfit = icon;
    const outfitEl = document.getElementById('outfit-icon');
    if (outfitEl) outfitEl.innerText = currentOutfit;

    updateUI();
    saveProgress();
    closeCustomization();
}

function updateUI() {
    const pillsEl = document.getElementById('pills');
    if (pillsEl) pillsEl.innerText = pills;

    const scrapEl = document.getElementById('scrap');
    if (scrapEl) scrapEl.innerText = scrap;
    
    // HP
    const hpBar = document.getElementById('hp-bar');
    const hpVal = document.getElementById('hp-val');
    if (hpBar) hpBar.style.width = hp + '%';
    if (hpVal) hpVal.innerText = hp + '/100';

    // Madness
    const madnessBar = document.getElementById('madness-bar');
    const madnessVal = document.getElementById('madness-val');
    if (madnessBar) madnessBar.style.width = madness + '%';
    if (madnessVal) madnessVal.innerText = madness + '%';

    if (madness >= 100) {
        document.body.style.filter = "sepia(0.8) hue-rotate(-50deg) contrast(1.5)";
    } else {
        document.body.style.filter = "none";
    }

    // Energy
    const energyBar = document.getElementById('energy-bar');
    const energyVal = document.getElementById('energy-val');
    if (energyBar) energyBar.style.width = energy + '%';
    if (energyVal) energyVal.innerText = energy + '/100';
}

document.addEventListener('DOMContentLoaded', () => {
    loadProgress();
});