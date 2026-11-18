'use strict';

// Explicit pre-upgrade save fixture. Fresh acceptance in the active build
// uses r5; these tests exercise the contract already issued by v9/v10.
const assert = require('node:assert/strict');
const E = require('../quest-engine.js');
const Work = require('../quest-job-model.js');

function loadIssuedV4(state, id, count = 0) {
    assert.ok(['k2', 'd1'].includes(id));
    const raw = JSON.parse(JSON.stringify(state));
    raw.version = 10;
    raw.room = E.jobs[id].giver;
    const work = id === 'd1' ? {
        order: 'd1:' + (count + 1),
        initial: Object.fromEntries(['ward407', 'ward408'].map(room => [
            room,
            {
                condition: raw.world.callEquipment[room].condition,
                revision: raw.world.callEquipment[room].revision
            }
        ]))
    } : {};
    const issued = {revision: 4, active: true, count, startTrip: raw.trip, variant: count % 3, done: {}, work};
    raw.jobs[id] = {...issued, ...Work.restore(id, issued)};
    assert.equal(E.supportsSave(raw), true, 'the old fixture must be recognized as a supported v10 save');
    const restored = E.restore(raw);
    assert.equal(restored.jobs[id].revision, 4);
    Object.assign(state, restored);
    return state.jobs[id];
}

module.exports = {loadIssuedV4};
