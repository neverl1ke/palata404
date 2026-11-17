/* Physical-size map and document controls inside the fixed landscape canvas.
   Presentation only: no inventory, route, save or quest state is modified. */
(() => {
    'use strict';
    const root = document.documentElement;
    let launcher;
    let initialPlanCentered = false;
    let suspendedPlan = null;
    let rotationFrame = 0, rotationLayout = '', rotationAttempts = 0;
    const compact = () => root.dataset.touchUi === 'true';
    function scheduleRotationRestore() {
        if (!rotationFrame && suspendedPlan && compact() && rotationAttempts < 120) {
            rotationFrame = requestAnimationFrame(() => {
                rotationFrame = 0; rotationAttempts++;
                restorePlanAfterRotation();
            });
        }
    }
    function restorePlanAfterRotation() {
        if (!suspendedPlan || !compact()) return;
        const view = document.querySelector('.quest-blueprint-viewport');
        if (!view?.getClientRects().length) return;
        const figure = view.querySelector('.quest-blueprint');
        const width = parseFloat(root.style.getPropertyValue('--touch-ui-width'));
        const maxLeft = view.scrollWidth - view.clientWidth, maxTop = view.scrollHeight - view.clientHeight;
        // The desktop layout temporarily has no horizontal scroll range. Wait
        // for the native touch geometry to settle before spending the snapshot.
        if (!figure || figure.offsetWidth !== 1280 || view.clientWidth < 88 || view.clientHeight < 44 ||
            view.clientWidth > width + 1 || maxLeft <= 0) {
            scheduleRotationRestore(); return;
        }
        const layout = [view.clientWidth, view.clientHeight, view.scrollWidth, view.scrollHeight].join(':');
        if (layout !== rotationLayout) {rotationLayout = layout; scheduleRotationRestore(); return;}
        const left = Math.min(suspendedPlan.left, maxLeft), top = Math.min(suspendedPlan.top, maxTop);
        view.scrollTo({left, top, behavior:'instant'});
        if (Math.abs(view.scrollLeft-left)<1 && Math.abs(view.scrollTop-top)<1) {
            suspendedPlan = null; rotationLayout = '';
        } else scheduleRotationRestore();
    }
    function setMapView(view, focusPlan = false) {
        const modal = document.getElementById('map-modal');
        if (!modal) return;
        modal.dataset.compactView = view === 'details' ? 'details' : 'plan';
        modal.querySelectorAll('[data-compact-map-view]').forEach(button => {
            button.setAttribute('aria-pressed', String(button.dataset.compactMapView === modal.dataset.compactView));
        });
        if (focusPlan) {
            const plan = modal.querySelector('.quest-blueprint-viewport');
            plan?.focus({preventScroll: true});
        }
        if (view === 'plan' && suspendedPlan) {rotationAttempts=0; scheduleRotationRestore();}
        if (compact() && view === 'plan' && !initialPlanCentered) {
            requestAnimationFrame(() => {
                if (!modal.getClientRects().length || modal.dataset.compactView !== 'plan') return;
                modal.querySelector('.quest-map-pin.is-current')?.scrollIntoView({block: 'end', inline: 'center'});
                const plan = modal.querySelector('.quest-blueprint-viewport');
                if (plan) plan.scrollTop += 12;
                initialPlanCentered = true;
            });
        }
    }
    function mapRendered() {
        const modal = document.getElementById('map-modal');
        const header = modal?.querySelector('.map-clipboard-header');
        if (!header) return;
        const floor = modal.querySelector('.quest-floor:not(.quest-location)');
        if (floor && !floor.querySelector('.compact-map-help')) {
            const help = document.createElement('p');
            help.className = 'compact-map-help';
            help.textContent = 'Двигайте план пальцем. Два быстрых нажатия — войти.';
            floor.append(help);
        }
        if (header.querySelector('.compact-map-tabs')) return;
        const tabs = document.createElement('nav');
        tabs.className = 'compact-map-tabs';
        tabs.setAttribute('aria-label', 'Представление карты');
        for (const [view, label] of [['plan', 'План 10 этажа'], ['details', 'Описание и действия']]) {
            const button = document.createElement('button');
            button.type = 'button';
            button.dataset.compactMapView = view;
            button.textContent = label;
            button.addEventListener('click', () => setMapView(view, view === 'plan'));
            tabs.append(button);
        }
        header.append(tabs);
        setMapView(modal.dataset.compactView || 'plan');
    }
    function previewOpened() {
        if (!compact()) return;
        setMapView('details');
        const sidebar = document.querySelector('.quest-map-sidebar');
        if (sidebar) sidebar.scrollTop = 0;
    }
    function updateLauncher() {
        if (!launcher) return;
        const scene = document.getElementById('quest-location-screen');
        const dialog = [...document.querySelectorAll('[role="dialog"]')].some(node => node.getClientRects().length);
        const card = document.querySelector('.hud-patient-board');
        const fullCard = card?.dataset.cardMode === 'full' || Boolean(card?.dataset.cardMotion);
        const hidden = !compact() || dialog || fullCard || Boolean(scene?.getClientRects().length);
        if (launcher.hidden !== hidden) launcher.hidden = hidden;
    }
    addEventListener('message', event => {
        if (event.source !== parent || event.origin !== location.origin) return;
        const data = event.data;
        if (data?.type !== 'palata:shell-viewport' || !Number.isFinite(data.scale) || data.scale <= 0 ||
            !Number.isFinite(data.width) || !Number.isFinite(data.height)) return;
        const wasCompact = compact();
        if (wasCompact && !data.compact && !suspendedPlan) {
            const view = document.querySelector('.quest-blueprint-viewport');
            if (view?.getClientRects().length) {
                suspendedPlan = {left:view.scrollLeft, top:view.scrollTop};
                rotationLayout = ''; rotationAttempts = 0;
            }
        }
        if (wasCompact !== Boolean(data.compact)) document.getElementById('map-modal')?.dispatchEvent(new Event('palata:map-orient'));
        if (data.compact) root.dataset.touchUi = 'true';
        else delete root.dataset.touchUi;
        root.style.setProperty('--touch-ui-scale', String(1 / data.scale));
        root.style.setProperty('--touch-ui-width', data.width + 'px');
        root.style.setProperty('--touch-ui-height', data.height + 'px');
        rotationAttempts = 0;
        restorePlanAfterRotation();
        scheduleRotationRestore();
        updateLauncher();
    });
    window.PalataCompactUI = Object.freeze({mapRendered, previewOpened, setMapView});
    function init() {
        launcher = document.createElement('button');
        launcher.type = 'button';
        launcher.className = 'compact-map-launch';
        launcher.textContent = 'Карта';
        launcher.hidden = true;
        launcher.addEventListener('click', () => window.toggleMapModal?.(true));
        document.body.append(launcher);
        let scheduled = false;
        new MutationObserver(() => {
            if (scheduled) return;
            scheduled = true;
            requestAnimationFrame(() => { scheduled = false; updateLauncher(); });
        }).observe(document.body, {subtree: true, childList: true, attributes: true, attributeFilter: ['class', 'hidden', 'aria-hidden', 'data-card-mode', 'data-card-motion']});
        mapRendered();
        updateLauncher();
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, {once: true});
    else init();
})();
