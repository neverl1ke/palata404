'use strict';

const assert = require('node:assert/strict');
const {test} = require('node:test');
const work = require('../quest-job-model.js');

const roundTrip = value => JSON.parse(JSON.stringify(value));

function accept(state, id, count = 0) {
    state.jobs[id] = {
        active: true,
        count,
        startTrip: 0,
        done: {},
        ...work.make(id, count, state.world?.callEquipment)
    };
    return state.jobs[id];
}

function operation(state, action, op, value) {
    const result = work.operate(state, 'job:' + action, op, value);
    assert.equal(result.ok, true, result.message);
    const job = state.jobs[work.owner[action]];
    job.work = result.work;
    // The engine records a reserve approval in work, not as a cargo step.
    if (result.complete && result.complete !== 'linenReserve') job.done[result.complete] = true;
    assert.equal(work.validRecord(work.owner[action], job), true, JSON.stringify(job));
    return result;
}

function completedPacking(state, method) {
    const job = accept(state, 'k2');
    operation(state, 'linen', 'select', 'linen-0');
    operation(state, 'linen', 'select', 'linen-1');
    operation(state, 'linen', 'submit');
    state.cargo.push('linen');
    assert.equal(work.operate(state, 'job:deliver', 'chooseMethod', method).ok, false);
    operation(state, 'deliver', 'startBedPreparation');
    assert.equal(work.operate(state, 'job:deliver', 'selectPiece', 'sheet').ok, false);
    operation(state, 'deliver', 'chooseMethod', method);
    return job;
}

test('both first K2 methods accept either placement order and keep choice through restore', () => {
    for (const [method, first] of [['assistance', 'pillowcase'], ['window', 'sheet']]) {
        const state = {jobs: {}, cargo: []};
        const job = completedPacking(state, method);
        assert.equal(job.revision, 5);
        assert.equal(job.work.draftScene.windowState, method === 'window' ? 'closed' : 'open');
        assert.deepEqual(work.restore('k2', roundTrip(job)).work, job.work);
        for (const piece of [first, first === 'sheet' ? 'pillowcase' : 'sheet']) {
            operation(state, 'deliver', 'selectPiece', piece);
            if (piece === 'sheet') {
                const before = roundTrip(job);
                assert.equal(work.operate(state, 'job:deliver', 'place', 'sheetZone').ok, false);
                assert.deepEqual(job, before);
                operation(state, 'deliver', 'spreadSheet');
            } else {
                operation(state, 'deliver', 'place', 'pillowZone');
            }
        }
        assert.equal(job.done.deliver, true);
        assert.equal(job.work.draftScene.spread, true);
        job.active = false;
        job.count = 1;
        assert.equal(work.validRecord('k2', job), true);
    }
});

test('reissued K2 retains shortage and reserve flow without repeating the assistance choice', () => {
    const state = {jobs: {},cargo: []};
    const job = accept(state, 'k2', 1);
    assert.equal(job.work.draftScene.required, false);
    operation(state, 'linen', 'select', 'linen-0');
    operation(state, 'linen', 'noteShortage');
    operation(state, 'linenReserve', 'select', 'reserve-same-size');
    operation(state, 'linenReserve', 'submit');
    operation(state, 'linen', 'select', 'linen-1');
    operation(state, 'linen', 'submit');
    state.cargo.push('linen');
    operation(state, 'deliver', 'startBedPreparation');
    assert.equal(work.operate(state, 'job:deliver', 'chooseMethod', 'assistance').ok, false);
    operation(state, 'deliver', 'selectPiece', 'sheet');
    operation(state, 'deliver', 'place', 'sheetZone');
    operation(state, 'deliver', 'selectPiece', 'pillowcase');
    operation(state, 'deliver', 'place', 'pillowZone');
    assert.equal(job.done.deliver, true);
    assert.equal(job.work.draftScene.method, null);
});

test('D1 accepts either ward first and keeps service request evidence, selection and retest local', () => {
    for (const wardOrder of [['ward407', 'ward408'], ['ward408', 'ward407']]) {
        const callEquipment = {
            ward407: {condition:'noResponse', revision:0, verified:false},
            ward408: {condition:'disconnected', revision:0, verified:false}
        };
        const state = {jobs:{},cargo:[],room:'doctor',mode:'patient',world:{callEquipment}};
        const job = accept(state, 'd1');
        assert.equal(job.revision, 5);
        assert.deepEqual(work.route(state, 'd1').plan.map(stop => stop.room), ['ward407', 'ward408']);
        for (const room of wardOrder) {
            state.room = room;
            const number = room.slice(4);
            const diagnostic = 'bell' + number;
            const service = 'callService' + number;
            const retest = 'callRetest' + number;
            assert.equal(work.route(state, 'd1').action, 'job:' + diagnostic);
            operation(state, diagnostic, 'inspect', 'connector');
            operation(state, diagnostic, 'test');
            assert.equal(work.operate(state, 'job:' + diagnostic, 'report', 'working').ok, false);
            operation(state, diagnostic, 'report', callEquipment[room].condition);
            assert.equal(work.route(state, 'd1').action, 'job:' + service);
            const action = 'job:' + service;
            assert.deepEqual(work.board(state, action).options, []);
            operation(state, service, 'inspectEvidence');
            const board = work.board(state, action);
            const agrees = x => x.equipmentId === board.evidence.equipmentId &&
                x.connector === board.evidence.connector && x.postAddress === board.evidence.postAddress;
            const wrong = board.options.find(x => !agrees(x));
            const correct = board.options.find(agrees);
            operation(state, service, 'select', wrong.id);
            assert.equal(work.operate(state, action, 'submit').ok, false);
            operation(state, service, 'select', correct.id);
            const reloaded = {...state,jobs:{d1:{...job,...work.restore('d1',roundTrip(job))}}};
            assert.deepEqual(work.board(reloaded, action).options, board.options);
            assert.deepEqual(work.board(reloaded, action).selected, [correct.id]);
            const serviceResult = operation(state, service, 'submit');
            assert.deepEqual(serviceResult.effect, {kind:'callService', room});
            callEquipment[room] = {condition:'working', revision:1, verified:false};
            assert.equal(work.serviceReady(state), false);
            assert.equal(work.route(state, 'd1').action, 'job:' + retest);
            assert.equal(work.operate(state, 'job:' + retest, 'confirm').ok, false);
            operation(state, retest, 'test');
            operation(state, retest, 'confirm');
            callEquipment[room].verified = true;
        }
        assert.equal(work.route(state, 'd1').action, 'claim:d1');
        assert.equal(work.serviceReady(state), true);
        const repeat = accept(state, 'd1', 1);
        for (const room of wardOrder) {
            state.room = room;
            const step = 'bell' + room.slice(4);
            operation(state, step, 'inspect');
            operation(state, step, 'test');
            operation(state, step, 'report', 'working');
            assert.ok(work.route(state, 'd1').plan.every(stop=>stop.room!==room));
            assert.equal(repeat.work.services[room].authorization, null);
        }
        assert.equal(work.serviceReady(state), true);
    }
});

test('D1 presentation rejects sparse or duplicate records and rotates stable labels only', () => {
    const a = Object.freeze({id:'service-a', label:'Запись 01'});
    const b = Object.freeze({id:'service-b', label:'Запись 02'});
    const c = Object.freeze({id:'service-c', label:'Запись 03'});
    const records = Object.freeze([a,b,c]);
    assert.deepEqual(work.orderServiceRecords([a,,c], 'd1:1', 'ward407'), []);
    assert.deepEqual(work.orderServiceRecords([a,a,c], 'd1:1', 'ward407'), []);
    assert.deepEqual(work.orderServiceRecords(records, 'd1:1', 'ward407'), [a,b,c]);
    assert.deepEqual(work.orderServiceRecords(records, 'd1:1', 'ward408'), [b,c,a]);
    assert.deepEqual(work.orderServiceRecords(records, 'd1:2', 'ward407'), [b,c,a]);
    assert.deepEqual(work.orderServiceRecords(records, 'd1:3', 'ward407'), [c,a,b]);
    assert.deepEqual(records, [a,b,c]);
});

// These two partial version-10 saves were emitted by the separate ac8b7d2
// checkout through its public engine before loading the reconstructed model.
test('loads and finishes actual pre-reconstruction K2 r4 and D1 r4 partial saves', () => {
    const engine = require('../quest-engine.js');
    const olderK2 = require('./fixtures/palata404-ac8b7d2-k2-partial.json');
    const olderD1 = require('./fixtures/palata404-ac8b7d2-d1-partial.json');

    function apply(state, event) {
        const result = engine.apply(state, event, 0);
        assert.equal(result.ok, true, result.message);
        assert.equal(engine.supportsSave(state), true, JSON.stringify(state.jobs));
        return result;
    }

    const move = (s, room) => apply(s, {type:'move', room});
    const perform = (s, id, op, value) => apply(s, {type:'work', id, op, value});

    assert.equal(engine.supportsSave(olderK2), true);
    const k2 = engine.restore(olderK2);
    assert.equal(k2.jobs.k2.revision, 4);
    assert.deepEqual(k2.jobs.k2.work.placed, ['sheet']);
    assert.equal(engine.workbench(k2, 'job:deliver').draftScene, undefined);
    perform(k2, 'job:deliver', 'selectPiece', 'pillowcase');
    perform(k2, 'job:deliver', 'place', 'pillowZone');
    move(k2, 'nurse');
    const linen = apply(k2, {type:'action',id:'claim:k2'});
    assert.deepEqual(linen.reward, {kind:'job', job:'k2', id:'k2:1', exp:15, silver:8, medical:'hp_10'});
    assert.equal(engine.apply(k2, {type:'action',id:'claim:k2'}).ok, false);

    assert.equal(engine.supportsSave(olderD1), true);
    const d1 = engine.restore(olderD1);
    assert.equal(d1.jobs.d1.revision, 4);
    assert.equal(d1.jobs.d1.work.services.ward407.tested, true);
    assert.equal(d1.jobs.d1.work.services.ward407.confirmed, false);
    const history = roundTrip(d1.world.doctorReview);
    perform(d1, 'job:callRetest407', 'confirm');
    move(d1, 'technical');
    perform(d1, 'job:callService408', 'inspectEvidence');
    const board = engine.workbench(d1, 'job:callService408');
    const matching = board.options.find(option =>
        ['equipmentId','connector','postAddress'].every(field => option[field] === board.evidence[field]));
    assert.ok(matching);
    perform(d1, 'job:callService408', 'select', matching.id);
    perform(d1, 'job:callService408', 'submit');
    move(d1, 'ward408');
    perform(d1, 'job:callRetest408', 'test');
    perform(d1, 'job:callRetest408', 'confirm');
    move(d1, 'doctor');
    const calls = apply(d1, {type:'action',id:'claim:d1'});
    assert.deepEqual(calls.reward, {kind:'job', job:'d1', id:'d1:1', exp:20, silver:10});
    assert.deepEqual(d1.world.doctorReview, history);
    assert.equal(engine.apply(d1, {type:'action',id:'claim:d1'}).ok, false);
    assert.equal(engine.supportsSave(engine.restore(roundTrip(d1))), true);
});
