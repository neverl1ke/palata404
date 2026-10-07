const tg = window.Telegram.WebApp;
tg.expand();

let money = 100;
let maxHp = 100;
let hp = 100;
let pills = 0;
let scrap = 0;
let madness = 20;
let energy = 80;
let currentOutfit = '🩺';

const OUTFITS = [
    {
        id: "default",
        icon: "🩺",
        name: "Рваха халат",
        price: 0,
        desc: "Базовий лікарняний одяг. Без бонусів.",
        armorBonus: 0,
        hpBonus: 0
    },
    {
        id: "straitjacket",
        icon: "🥼",
        name: "Смикальна сорочка",
        price: 50,
        desc: "+10 до Броні (пасивно)",
        armorBonus: 10,
        hpBonus: 0
    },
    {
        id: "crack_mask",
        icon: "🥷",
        name: "Маска тріщини",
        price: 120,
        desc: "+20 до Броні, +15 Макс. HP",
        armorBonus: 20,
        hpBonus: 15
    }
];

let purchasedOutfits = ["default"];

const ITEM_STATS = {
    "Ніж (Базовий)": { type: "weapon", damage: 10 },
    "ПМ": { type: "weapon", damage: 25 },
    "АК-74": { type: "weapon", damage: 55 },
    "Тактичний шолом": { type: "helmet", armor: 20 },
    "Плитник (Бронежилет)": { type: "armor", armor: 45 },
    "Коліматорний приціл": { type: "attachment", damageBonus: 10 },
    "Глушник": { type: "attachment", damageBonus: 5 },
    "Стимулятор 'Морфін'": { type: "booster", maxHpBonus: 20 },
    "Аптечка ПМП": { type: "heal", hp: 40 }
};

let equipment = {
    helmet: null,
    armor: null,
    weapon: "Ніж (Базовий)",
    attachment: null
};

let stash = ["ПМ", "Тактичний шолом", "Плитник (Бронежилет)", "Коліматорний приціл", "Стимулятор 'Морфін'"];

function calculateStats() {
    let totalDamage = ITEM_STATS[equipment.weapon]?.damage || 10;
    if (equipment.attachment && ITEM_STATS[equipment.attachment]?.damageBonus) {
        totalDamage += ITEM_STATS[equipment.attachment].damageBonus;
    }

    let totalArmor = 0;
    if (equipment.helmet && ITEM_STATS[equipment.helmet]?.armor) {
        totalArmor += ITEM_STATS[equipment.helmet].armor;
    }
    if (equipment.armor && ITEM_STATS[equipment.armor]?.armor) {
        totalArmor += ITEM_STATS[equipment.armor].armor;
    }

    const currentOutfitData = OUTFITS.find(o => o.icon === currentOutfit);
    if (currentOutfitData) {
        totalArmor += currentOutfitData.armorBonus;
    }

    return { totalDamage, totalArmor };
}

function saveProgress() {
    const gameState = { money, maxHp, hp, pills, scrap, madness, energy, currentOutfit, equipment, stash, purchasedOutfits };
    localStorage.setItem('palata404_save_v13', JSON.stringify(gameState));
    if (tg.CloudStorage) tg.CloudStorage.setItem('palata404_save_v13', JSON.stringify(gameState));
}

function loadProgress() {
    const savedData = localStorage.getItem('palata404_save_v13');
    if (savedData) {
        try {
            const gameState = JSON.parse(savedData);
            money = gameState.money ?? 100;
            maxHp = gameState.maxHp ?? 100;
            hp = gameState.hp ?? maxHp;
            pills = gameState.pills ?? 0;
            scrap = gameState.scrap ?? 0;
            madness = gameState.madness ?? 20;
            energy = gameState.energy ?? 80;
            currentOutfit = gameState.currentOutfit ?? '🩺';
            equipment = gameState.equipment ?? equipment;
            stash = gameState.stash ?? stash;
            purchasedOutfits = gameState.purchasedOutfits ?? ["default"];
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
        const { totalArmor } = calculateStats();
        let damageToTake = 15;
        if (totalArmor > 0) {
            damageToTake = Math.max(3, damageToTake - Math.floor(totalArmor / 5));
        }

        hp = Math.max(0, hp - damageToTake);
        alert(`🌀 Розум затьмарено! Отримано ${damageToTake} шкоди HP. Поспи!`);
        updateUI();
        saveProgress();
        return;
    }

    if (energy >= 5) {
        energy -= 5;
        madness += 5;
        
        money += Math.floor(Math.random() * 5) + 2; 
        if (Math.random() > 0.5) pills += 1;

        const rand = Math.random();
        if (rand > 0.7) {
            scrap += 1;
        } else if (rand > 0.9) {
            const rareLoot = ["АК-74", "Глушник", "Стимулятор 'Морфін'"];
            const found = rareLoot[Math.floor(Math.random() * rareLoot.length)];
            stash.push(found);
            alert(`Знайдено предмет у сховище: ${found}!`);
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

/* Сховище та предмети */
function openInventory() {
    renderStash();
    const modal = document.getElementById('inventory-modal');
    if (modal) modal.classList.remove('hidden');
}

function closeInventory() {
    const modal = document.getElementById('inventory-modal');
    if (modal) modal.classList.add('hidden');
}

function equipItem(itemName, index) {
    const itemData = ITEM_STATS[itemName];

    if (!itemData) {
        alert(`Предмет ${itemName} є ресурсом.`);
        return;
    }

    if (itemData.type === "booster") {
        maxHp += itemData.maxHpBonus;
        hp += itemData.maxHpBonus;
        alert(`Прийнято стимулятор! Максимальне здоров'я зросло до ${maxHp} HP!`);
    } else if (itemData.type === "heal") {
        hp = Math.min(maxHp, hp + itemData.hp);
        alert(`Відновлено ${itemData.hp} HP!`);
    } else if (itemData.type === "helmet") {
        if (equipment.helmet) stash.push(equipment.helmet);
        equipment.helmet = itemName;
    } else if (itemData.type === "armor") {
        if (equipment.armor) stash.push(equipment.armor);
        equipment.armor = itemName;
    } else if (itemData.type === "weapon") {
        if (equipment.weapon) stash.push(equipment.weapon);
        equipment.weapon = itemName;
    } else if (itemData.type === "attachment") {
        if (equipment.attachment) stash.push(equipment.attachment);
        equipment.attachment = itemName;
    }

    stash.splice(index, 1);
    renderStash();
    saveProgress();
    updateUI();
}

function unequipSlot(slotType) {
    if (equipment[slotType]) {
        stash.push(equipment[slotType]);
        equipment[slotType] = null;
        renderStash();
        saveProgress();
        updateUI();
    }
}

function renderStash() {
    const { totalDamage, totalArmor } = calculateStats();

    const dmgEl = document.getElementById('modal-dmg');
    const armorEl = document.getElementById('modal-armor');
    const maxHpEl = document.getElementById('modal-max-hp');
    if (dmgEl) dmgEl.innerText = totalDamage;
    if (armorEl) armorEl.innerText = totalArmor;
    if (maxHpEl) maxHpEl.innerText = maxHp + " HP";

    const helmetEl = document.getElementById('slot-helmet');
    const armorSlotEl = document.getElementById('slot-armor');
    const weaponEl = document.getElementById('slot-weapon');
    const attachEl = document.getElementById('slot-attachment');

    if (helmetEl) helmetEl.innerHTML = equipment.helmet ? `${equipment.helmet} <button onclick="unequipSlot('helmet')">❌</button>` : "Порожньо";
    if (armorSlotEl) armorSlotEl.innerHTML = equipment.armor ? `${equipment.armor} <button onclick="unequipSlot('armor')">❌</button>` : "Порожньо";
    if (weaponEl) weaponEl.innerHTML = equipment.weapon ? `${equipment.weapon} <button onclick="unequipSlot('weapon')">❌</button>` : "Порожньо";
    if (attachEl) attachEl.innerHTML = equipment.attachment ? `${equipment.attachment} <button onclick="unequipSlot('attachment')">❌</button>` : "Без обвісу";

    const stashContainer = document.getElementById('stash-items');
    if (!stashContainer) return;
    
    stashContainer.innerHTML = '';

    if (stash.length === 0) {
        stashContainer.innerHTML = '<div class="stash-item">Сховище порожнє</div>';
    } else {
        stash.forEach((item, idx) => {
            const div = document.createElement('div');
            div.className = 'stash-item';
            div.innerHTML = `<span>📦 ${item}</span> <button onclick="equipItem('${item}', ${idx})">Вдягти/Ужити</button>`;
            stashContainer.appendChild(div);
        });
    }
}

/* Кастомізація / Гардероб */
function openCustomization() {
    renderWardrobe();
    const modal = document.getElementById('custom-modal');
    if (modal) modal.classList.remove('hidden');
}

function closeCustomization() {
    const modal = document.getElementById('custom-modal');
    if (modal) modal.classList.add('hidden');
}

function renderWardrobe() {
    const container = document.getElementById('wardrobe-container');
    if (!container) return;

    container.innerHTML = '';

    OUTFITS.forEach(outfit => {
        const isPurchased = purchasedOutfits.includes(outfit.id);
        const isEquipped = currentOutfit === outfit.icon;

        const card = document.createElement('div');
        card.className = `outfit-card ${isEquipped ? 'active' : ''}`;

        let actionBtnHTML = '';
        if (isEquipped) {
            actionBtnHTML = `<button class="btn-outfit equipped">Надіто ✅</button>`;
        } else if (isPurchased) {
            actionBtnHTML = `<button class="btn-outfit" onclick="selectOutfit('${outfit.id}')">Вдягнути</button>`;
        } else {
            actionBtnHTML = `<button class="btn-outfit buy" onclick="buyOutfit('${outfit.id}')">Купити ${outfit.price}$</button>`;
        }

        card.innerHTML = `
            <div class="outfit-info">
                <div class="outfit-icon-large">${outfit.icon}</div>
                <div class="outfit-details">
                    <h4>${outfit.name}</h4>
                    <p>${outfit.desc}</p>
                </div>
            </div>
            <div>${actionBtnHTML}</div>
        `;

        container.appendChild(card);
    });
}

function buyOutfit(outfitId) {
    const outfit = OUTFITS.find(o => o.id === outfitId);
    if (!outfit) return;

    if (money < outfit.price) {
        alert("Невистачає коштів!");
        return;
    }

    money -= outfit.price;
    purchasedOutfits.push(outfit.id);
    currentOutfit = outfit.icon;

    alert(`Вітаємо з покупкою: ${outfit.name}!`);
    saveProgress();
    updateUI();
    renderWardrobe();
}

function selectOutfit(outfitId) {
    const outfit = OUTFITS.find(o => o.id === outfitId);
    if (!outfit) return;

    currentOutfit = outfit.icon;
    saveProgress();
    updateUI();
    renderWardrobe();
}

function updateUI() {
    const { totalDamage, totalArmor } = calculateStats();

    const moneyEl = document.getElementById('money');
    if (moneyEl) moneyEl.innerText = money;

    const pillsEl = document.getElementById('pills');
    if (pillsEl) pillsEl.innerText = pills;

    const scrapEl = document.getElementById('scrap');
    if (scrapEl) scrapEl.innerText = scrap;
    
    // HP
    const hpBar = document.getElementById('hp-bar');
    const hpVal = document.getElementById('hp-val');
    if (hpBar) hpBar.style.width = Math.min(100, (hp / maxHp) * 100) + '%';
    if (hpVal) hpVal.innerText = `${hp} / ${maxHp} HP`;

    // Броня та Шкода
    const armorVal = document.getElementById('armor-val');
    const dmgVal = document.getElementById('dmg-val');
    if (armorVal) armorVal.innerText = totalArmor;
    if (dmgVal) dmgVal.innerText = totalDamage;

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

    const outfitEl = document.getElementById('outfit-icon');
    if (outfitEl) outfitEl.innerText = currentOutfit;
}

document.addEventListener('DOMContentLoaded', () => {
    loadProgress();
});