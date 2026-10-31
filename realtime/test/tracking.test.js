const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync(require('node:path').join(__dirname, '../../backend/orders/static/orders/tracking.js'), 'utf8');
function harness({live = true} = {}) {
  const elements = {tracking: {dataset: {orderId: '7'}}, status: {}, connection: {}};
  const handlers = {}, requests = [], timers = [], lifecycle = {};
  const socket = {connected: true, on: (name, fn) => { handlers[name] = fn; }, disconnect: () => { socket.connected = false; socket.disconnected = true; }};
  let options;
  const context = {document: {getElementById: id => elements[id]}, fetch: () => new Promise(resolve => requests.push(resolve)),
    setInterval: fn => { timers.push(fn); return 1; }, clearInterval: () => {},
    window: {addEventListener: (name, fn) => { lifecycle[name] = fn; }}};
  if (live) context.io = config => { options = config; return socket; };
  vm.runInNewContext(source, context);
  const reply = (index, data, code = 200) => requests[index]({status: code, ok: code === 200, json: async () => data});
  const flush = () => new Promise(resolve => setImmediate(resolve));
  return {elements, handlers, requests, timers, lifecycle, socket, reply, flush, options};
}
test('reconnect fetches missed state; late REST and duplicate/stale events never regress UI', async () => {
  const h = harness(); assert.equal(h.options.reconnection, true);
  h.reply(0, {id: 7, version: 1, status: 'Received'}); await h.flush();
  h.handlers.disconnect('transport close'); assert.match(h.elements.connection.textContent, /Reconnecting/);
  const connected = h.handlers.connect();
  h.handlers.order_status_changed({order_id: 7, version: 3, status: 'Served'});
  h.reply(2, {id: 7, version: 2, status: 'Preparing'}); await connected;
  h.reply(1, {id: 7, version: 1, status: 'Received'}); await h.flush();
  for (const data of [{order_id: 7, version: 2, status: 'Preparing'}, {order_id: 7, version: 3, status: 'Received'}, {order_id: 8, version: 9, status: 'Received'}]) h.handlers.order_status_changed(data);
  assert.equal(h.elements.status.textContent, 'Served'); assert.equal(h.elements.tracking.dataset.version, '3');
});
test('expired REST session stops reconnection and rejects pending events', async () => {
  const h = harness(); h.reply(0, {}, 401); await h.flush();
  assert.equal(h.socket.disconnected, true); assert.match(h.elements.connection.textContent, /Log in again/);
  h.handlers.order_status_changed({order_id: 7, version: 2, status: 'Preparing'});
  assert.equal(h.elements.status.textContent, undefined); h.timers[0](); assert.equal(h.requests.length, 1);
});
test('Node/client outage still polls authoritative REST and recovers transient HTTP errors', async () => {
  const h = harness({live: false}); h.reply(0, {}, 503); await h.flush();
  h.timers[0](); h.reply(1, {id: 7, version: 3, status: 'Served'}); await h.flush();
  assert.equal(h.elements.status.textContent, 'Served');
  h.lifecycle.pagehide(); h.timers[0](); assert.equal(h.requests.length, 2);
});
test('server authorization revocation stops automatic resubscription', async () => {
  const h = harness(); h.handlers.disconnect('io server disconnect');
  assert.equal(h.socket.disconnected, true); assert.match(h.elements.connection.textContent, /Log in again/);
});
