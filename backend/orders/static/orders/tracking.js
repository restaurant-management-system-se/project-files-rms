'use strict';
(() => {
  const root = document.getElementById('tracking');
  const orderId = Number(root.dataset.orderId);
  const status = document.getElementById('status');
  const connection = document.getElementById('connection');
  let version = 0, stopped = false, socket;
  const message = text => { connection.textContent = text; };
  function show(data) {
    if ((data.order_id ?? data.id) !== orderId || !Number.isSafeInteger(data.version) ||
        data.version <= version || !['Received', 'Preparing', 'Served'].includes(data.status)) return;
    version = data.version;
    status.textContent = data.status;
    root.dataset.version = String(version);
  }
  function stop(text) {
    stopped = true;
    if (socket) socket.disconnect();
    message(text);
  }
  async function sync() {
    try {
      const response = await fetch('/api/orders/' + orderId, {cache: 'no-store', credentials: 'same-origin'});
      if (response.status === 401) { stop('Session expired. Log in again to resume tracking.'); return false; }
      if ([403, 404].includes(response.status)) { stop('Order access is no longer available.'); return false; }
      if (!response.ok) throw Error('Saved status unavailable');
      const data = await response.json();
      if (stopped) return false;
      show(data);
      return true;
    } catch {
      if (!stopped) message('Reconnecting… Saved status temporarily unavailable. Retrying.');
      return false;
    }
  }
  // Start REST independently: Node downtime must not hide committed state.
  sync();
  if (typeof io === 'function') {
    socket = io({auth: {orderId}, transports: ['websocket'], reconnection: true,
      reconnectionDelay: 1000, reconnectionDelayMax: 5000, randomizationFactor: 0.5});
    socket.on('connect', async () => {
      // Every handshake reauthenticates/subscribes on the server. Fetch missed changes
      // after the subscription, while version checks protect against REST/event races.
      if (stopped) return socket.disconnect();
      message('Reconnecting… Synchronizing saved status.');
      if (await sync() && !stopped && socket.connected) message('Live updates connected');
    });
    socket.on('order_status_changed', data => { if (!stopped) show(data); });
    socket.on('disconnect', reason => {
      if (stopped) return;
      message('Reconnecting… Saved status remains available.');
      sync();
      // Server disconnects are deliberate authorization revocations. Do not bypass
      // them with an automatic reconnect loop; require a fresh login/page load.
      if (reason === 'io server disconnect') stop('Live session ended. Log in again to resume tracking.');
    });
    socket.on('connect_error', () => {
      if (!stopped) { message('Reconnecting… Checking saved status.'); sync(); }
    });
  } else message('Live service unavailable. Checking saved status periodically.');
  // Also works when the Socket.IO client could not load during a Node outage.
  const poll = setInterval(() => { if (!stopped) sync(); }, 5000);
  window.addEventListener('pagehide', () => { stopped = true; clearInterval(poll); if (socket) socket.disconnect(); });
})();
