const tg = window.Telegram.WebApp;
tg.expand();

let hp = 100;
let pills = 0;
let madness = 20;
let energy = 80;
let currentOutfit = '🩺';

function saveProgress() {
    const gameState = { hp, pills, madness, energy, currentOutfit };
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
            madness = gameState.madness ?? 20;
            energy = gameState.energy ?? 80;
            currentOutfit = gameState.currentOutfit ?? '🩺';
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
    // Якщо божевілля 100% — персонаж втрачає HP замість пошуку!
    if (madness >= 100) {
        hp = Math.max(0, hp - 10);
        alert("🌀 Розум повністю затьмарено! Ти втрачаєш здоров'я (-10 HP). Поспи або прийняти ліки!");
        updateUI();
        saveProgress();
        return;
    }

    if (energy >= 5) {
        energy -= 5;
        madness += 5; // Божевілля росте трохи швидше
        pills += 1;

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
        // Сон заспокоює розум, якщо божевілля критичне
        madness = Math.max(0, madness - 25);
        
        updateUI();
        saveProgress();
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

    // Ефекти критичного божевілля
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