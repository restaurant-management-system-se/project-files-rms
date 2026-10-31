'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');
const { Server } = require('socket.io');
const { connect, subscribe, nextStatus } = require('../test-client');
async function fixture(t) {
  const server = http.createServer();
  const io = new Server(server);
  // Deliberately synthetic server: it validates the harness, not RMS authorization.
  io.use((socket, next) => next(socket.handshake.headers['x-harness-fixture'] === 'allowed' ? undefined : new Error('fixture denied')));
  io.on('connection', socket => socket.on('subscribe_order', (request, ack) => {
    ack({ order_id: request.order_id });
    socket.emit('order_status_changed', { order_id: request.order_id, status: 'Preparing', version: 2 });
  }));
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  t.after(() => new Promise(resolve => io.close(resolve)));
  return `http://127.0.0.1:${server.address().port}`;
}
test('H_NODE_01 client receives a fixture event after subscription', async t => {
  const url = await fixture(t);
  const socket = await connect(url, { headers: { 'x-harness-fixture': 'allowed' } });
  t.after(() => socket.disconnect());
  const event = nextStatus(socket);
  assert.deepEqual(await subscribe(socket, 'fixture-order'), { order_id: 'fixture-order' });
  assert.deepEqual(await event, { order_id: 'fixture-order', status: 'Preparing', version: 2 });
});
test('H_NODE_02 rejected fixture handshake remains a failure', async t => {
  const url = await fixture(t);
  await assert.rejects(connect(url), /fixture denied/);
});
test('H_NODE_03 missing fixture event expires instead of passing', async t => {
  const url = await fixture(t);
  const socket = await connect(url, { headers: { 'x-harness-fixture': 'allowed' } });
  t.after(() => socket.disconnect());
  await assert.rejects(nextStatus(socket, 30), /Status deadline exceeded/);
  assert.equal(socket.listeners('order_status_changed').length, 0);
});
