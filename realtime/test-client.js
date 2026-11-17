'use strict';
// Shared test client only. No business writes or production server are implemented here.
const { io } = require('socket.io-client');
async function connect(url, { timeout = 2000, headers = {} } = {}) {
  const socket = io(url, { transports: ['websocket'], forceNew: true, reconnection: false,
    autoConnect: false, timeout, withCredentials: true, extraHeaders: headers });
  return new Promise((resolve, reject) => {
    const cleanup = () => { socket.off('connect', success); socket.off('connect_error', failure); };
    const success = () => { cleanup(); resolve(socket); };
    const failure = (error) => { cleanup(); socket.disconnect(); reject(error); };
    socket.once('connect', success);
    socket.once('connect_error', failure);
    socket.connect();
  });
}
function nextStatus(socket, timeout = 2000) {
  return new Promise((resolve, reject) => {
    const onStatus = event => { clearTimeout(timer); resolve(event); };
    const timer = setTimeout(() => { socket.off('order_status_changed', onStatus); reject(new Error('Status deadline exceeded')); }, timeout);
    socket.once('order_status_changed', onStatus);
  });
}
function subscribe(socket, orderId, timeout = 2000) {
  return new Promise((resolve, reject) => {
    socket.timeout(timeout).emit('subscribe_order', { order_id: orderId }, (error, reply) => {
      if (error) reject(error); else resolve(reply);
    });
  });
}
module.exports = { connect, subscribe, nextStatus };
