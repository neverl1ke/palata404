const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const vm = require('node:vm');

const root = path.join(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'script.js'), 'utf8');
const html = fs.readFileSync(path.join(root, 'quest-test.html'), 'utf8') + '<div id="quest-list"></div><div id="quest-save"></div>';
let fixtureRaidSequence = 0;

// Exercise the actual game script with controlled storage/time. Layout and input
// handling belong to test_game.py; these stubs intentionally don't model them.
function game(saves = {}, deniedStorage = false, failWrites = [], telegramId = null, sharedStorage = null) {
    let now = 1700000000000;
    let sequence = 0;
    const timers = new Map();
    const storage = sharedStorage || new Map(Object.entries(saves));
    const failedKeys = new Set(failWrites);
    const elements = new Map();
    const listeners = new Map();
    function element(id = '') {
        const classes = new Set();
        return {
            id, dataset: {}, style: { setProperty(name, value) { this[name] = value; } }, children: [], textContent: '', innerHTML: '',
            classList: {
                add(...names) { names.forEach(name => classes.add(name)); },
                remove(...names) { names.forEach(name => classes.delete(name)); },
                contains(name) { return classes.has(name); },
                toggle(name, force) {
                    const enabled = force ?? !classes.has(name);
                    enabled ? classes.add(name) : classes.delete(name);
                    return enabled;
                }
            },
            appendChild(child) { this.children.push(child); if (child.id) elements.set(child.id, child); },
            remove() { elements.delete(this.id); },
            handlers: {}, addEventListener(type, fn) { (this.handlers[type] ||= []).push(fn); }, click() { if(!this.disabled) for(const fn of this.handlers.click || [])fn({target:this}); }, append(...nodes) { nodes.forEach(n=>this.appendChild(n)); }, replaceChildren(...nodes) { this.children=[]; this.append(...nodes); }, querySelector(selector) { return element(selector); }, cloneNode() { return element(this.id); }, replaceWith(node) { selectors.set('.room-trip-switch',node); }, querySelectorAll(selector) {
                return selector === '[data-paper-extra]' ? this.children.filter(child => child['data-paper-extra'] && elements.get(child.id) === child) : [];
            },
            setAttribute(name, value) { this[name] = value; },
            getAttribute(name) { return this[name] ?? null; },
            removeAttribute(name) { delete this[name]; },
            focus() {}, scrollTo() {}, getClientRects() { return []; },
            contains() { return false; },
        };
    }
    for (const match of html.matchAll(/\bid="([^"]+)"/g)) elements.set(match[1], element(match[1]));
    const selectors = new Map();
    const document = {
        querySelector(s) { if(!selectors.has(s))selectors.set(s,element(s));return selectors.get(s); },
        getElementById(id) { return elements.get(id) || null; },
        createElement() { return element(); },
        querySelectorAll() { return []; },
        addEventListener(name, callback) {
            if (!listeners.has(name)) listeners.set(name, []);
            listeners.get(name).push(callback);
        },
        body: element('body'), hidden: false,
    };
    const window = {
        document, innerWidth: 390, innerHeight: 844,
        location: { search: '' }, addEventListener() {},
        crypto: { randomUUID: () => `fixture-${++fixtureRaidSequence}` },
    };
    if (telegramId !== null) window.Telegram = { WebApp: {
        initDataUnsafe: { user: { id: telegramId, first_name: `Пацієнт ${telegramId}` } }, ready() {}, expand() {}
    } };
    Object.defineProperty(window, 'localStorage', {
        configurable: true,
        get() {
            if (deniedStorage) throw new Error('storage denied');
            return {
                get length() { return storage.size; },
                key(index) { return [...storage.keys()][index] ?? null; },
                getItem(key) { return storage.get(key) ?? null; },
                setItem(key, value) {
                    if (failedKeys.has(key)) throw new Error('Simulated interrupted write');
                    storage.set(key, String(value));
                },
                removeItem(key) { storage.delete(key); },
            };
        }
    });
    const context = vm.createContext({
        window, document, URLSearchParams, console,
        Date: class extends Date { static now() { return now; } },
        alert() {}, confirm() { return true; }, prompt() { return null; },
        MutationObserver: class { observe() {} },
        setInterval() { return ++sequence; }, clearInterval() {},
        setTimeout(callback, delay) { const id = ++sequence; timers.set(id, { at: now + delay, callback }); return id; },
        clearTimeout(id) { timers.delete(id); },
    });
    vm.runInContext('Math.random=()=>0.5;', context);
    vm.runInContext(fs.readFileSync(path.join(root, 'quest-sandbox.js'),'utf8'), context);
    vm.runInContext(fs.readFileSync(path.join(root, 'icons.js'), 'utf8'), context, { filename: 'icons.js' });
    vm.runInContext(fs.readFileSync(path.join(root, 'staff-archive-data.js'), 'utf8'), context, { filename: 'staff-archive-data.js' });
    vm.runInContext(fs.readFileSync(path.join(root, 'battle-results.js'), 'utf8'), context, { filename: 'battle-results.js' });
    vm.runInContext(fs.readFileSync(path.join(root, 'raid-archive.js'), 'utf8'), context, { filename: 'raid-archive.js' });
    vm.runInContext(fs.readFileSync(path.join(root, 'staff-archive.js'), 'utf8'), context, { filename: 'staff-archive.js' });
    vm.runInContext(fs.readFileSync(path.join(root, 'paper-doll-data.js'), 'utf8'), context, { filename: 'paper-doll-data.js' });
    vm.runInContext(fs.readFileSync(path.join(root, 'hair-color.js'), 'utf8'), context, { filename: 'hair-color.js' });
    vm.runInContext(fs.readFileSync(path.join(root, 'female-hair-fit-data.js'), 'utf8'), context, { filename: 'female-hair-fit-data.js' });
    vm.runInContext(fs.readFileSync(path.join(root, 'female-hair-fit.js'), 'utf8'), context, { filename: 'female-hair-fit.js' });
    vm.runInContext(fs.readFileSync(path.join(root, 'male-hair-fit-data.js'), 'utf8'), context, { filename: 'male-hair-fit-data.js' });
    vm.runInContext(fs.readFileSync(path.join(root, 'male-hair-fit.js'), 'utf8'), context, { filename: 'male-hair-fit.js' });
    // This VM tests state/DOM commands; real pixel fitting is checked in test_appearance_catalog.py.
    vm.runInContext('fittedFemaleHairSource = source => ({ then(resolve) { resolve(source); return { catch() {} }; } });', context);
    vm.runInContext(fs.readFileSync(path.join(root, 'paper-doll.js'), 'utf8'), context, { filename: 'paper-doll.js' });
    vm.runInContext(fs.readFileSync(path.join(root, 'weapon-system.js'), 'utf8'), context, { filename: 'weapon-system.js' });
    vm.runInContext(fs.readFileSync(path.join(root, 'weapon-runtime.js'), 'utf8'), context, { filename: 'weapon-runtime.js' });
    vm.runInContext(fs.readFileSync(path.join(root, 'wardrobe.js'), 'utf8'), context, { filename: 'wardrobe.js' });
    vm.runInContext(source, context, { filename: 'script.js' });
    const run = code => vm.runInContext(code, context);
    for (const callback of listeners.get('DOMContentLoaded') || []) callback();
    window.PalataRoom={refresh(){}};
    vm.runInContext(fs.readFileSync(path.join(root, 'quest-engine.js'),'utf8'), context);
    vm.runInContext(fs.readFileSync(path.join(root, 'quest-prototype.js'),'utf8'), context);
    function walk(node,predicate){if(predicate(node))return node;for(const child of node.children||[]){const r=walk(child,predicate);if(r)return r;}}
    return {
        run, storage, elements, failedKeys,
        click(kind,id){if(kind==='room')run('toggleMapModal(true)');const b=walk(elements.get('map-floors-view'),n=>n.dataset?.[kind]===id);if(!b)throw Error('Missing button '+kind+':'+id);b.click();if(kind==='action'&&run('!!PalataQuestEngine.interactions['+JSON.stringify(id)+']')){run('PalataQuestEngine.interactions['+JSON.stringify(id)+'].steps.slice(window.PalataQuestPrototype.snapshot().interactions['+JSON.stringify(id)+']||0)').forEach(step=>{const c=walk(elements.get('map-floors-view'),n=>n.dataset?.choice===step.answer);if(c)c.click();});}},
        switch(){selectors.get('.room-trip-switch').click();},
        state(){return run('window.PalataQuestPrototype.snapshot()');},
        advance(ms) {
            const target = now + ms;
            while (true) {
                const next = [...timers.entries()].filter(([,t]) => t.at <= target).sort((a,b) => a[1].at-b[1].at)[0];
                if (!next) break;
                now = next[1].at; timers.delete(next[0]); next[1].callback();
            }
            now = target;
        }
    };
}


module.exports={game};
