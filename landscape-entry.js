/* Keep the game document intact inside a fixed landscape viewport. */
(() => {
    const url = new URL(location.href);
    if (window.__PALATA_TEST_DIRECT__) return;
    window.__PALATA_PROFILE_PROTECTED__ = true;
    let departed = false;
    function ownsSession() {
        try { return window.parent !== window && window.parent.PalataProfileSession?.canWrite(window) === true; }
        catch (_) { return false; }
    }
    function fenceRestoredDocument() {
        window.__PALATA_PROFILE_STALE__ = true;
        try { window.parent.PalataProfileSession?.restored(window); } catch (_) { /* Fence remains closed. */ }
    }
    addEventListener('pagehide', () => { departed = true; });
    // BFCache visibility can resume game timers before pageshow. This listener
    // is installed before those timers, while pagehide final saves remain valid.
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden && departed) fenceRestoredDocument();
    });
    addEventListener('pageshow', event => { if (event.persisted) fenceRestoredDocument(); });
    if (url.searchParams.get('canvas') === '1' && ownsSession()) return;
    // A naked canvas URL must not bypass ownership or load profile data.
    window.__PALATA_PROFILE_STALE__ = true;
    window.stop();
    url.pathname = url.pathname.replace(/[^/]*$/, 'play.html');
    location.replace(url.href);
})();
