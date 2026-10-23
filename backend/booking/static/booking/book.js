const form = document.querySelector('#search');
const results = document.querySelector('#results');
const message = document.querySelector('#message');
const csrf = document.querySelector('[name=csrfmiddlewaretoken]');
let searchVersion = 0;
let retryRequest = null;
function showError(data) {
  message.textContent = [data.message || data.detail || "Request could not be completed.", ...Object.entries(data.details || {}).filter(([k]) => !['tables','alternative'].includes(k)).map(([k,v]) => `${k}: ${v}`)].join('\n');
}
function showTables(data) {
  const heading = document.createElement('h2'); heading.textContent = data.tables.length ? 'Available tables' : 'No tables at that time'; results.append(heading);
  for (const table of data.tables) {
    const button = document.createElement('button'); button.textContent = `Confirm Table ${table.table_number} · ${table.capacity} seats`;
    button.onclick = () => confirm(table, data, button); results.append(button);
  }
  alternatives(data);
  if (!data.tables.length && !data.alternative) results.append(document.createTextNode('No active table has enough seats. Try a smaller party size.'));
}
function alternatives(data) {
  if (!data.alternative) return;
  const button = document.createElement('button');
  button.textContent = `Try nearest slot: ${new Date(data.alternative.start_at).toLocaleString()} · Table ${data.alternative.table_number}`;
  button.onclick = () => search(data.alternative.start_at);
  results.append(button);
}
async function confirm(table, data, button) {
  button.disabled = true; message.textContent = '';
  const identity = JSON.stringify([table.table_id, data.start_at, data.party_size]);
  if (!retryRequest || retryRequest.identity !== identity) {
    retryRequest = {identity, payload: {table_id:table.table_id, start_at:data.start_at, party_size:data.party_size, idempotency_key:crypto.randomUUID()}};
  }
  try {
    const response = await fetch('/api/bookings', {method:'POST', headers:{'Content-Type':'application/json','X-CSRFToken':csrf.value}, body:JSON.stringify(retryRequest.payload)});
    const booking = await response.json();
    if (!response.ok) {
      showError(booking);
      if (response.status === 409) {
        results.replaceChildren(); retryRequest = null;
        const options = booking.details || {};
        if (options.tables) showTables(options);
      }
      if (response.status === 401) message.textContent += '\nSign in with your customer account, then check availability again.';
      return;
    }
    results.replaceChildren();
    const heading = document.createElement('h2'); heading.textContent = 'Booking confirmed'; results.append(heading);
    const summary = document.createElement('p');
    summary.textContent = `${booking.booking_id} · Table ${table.table_number} · ${booking.party_size} guests\n${new Date(booking.start_at).toLocaleString()} – ${new Date(booking.end_at).toLocaleString()}`;
    results.append(summary); retryRequest = null;
  } catch { message.textContent = 'Connection interrupted. Retry this confirmation to recover the same booking safely.'; }
  finally { button.disabled = false; }
}
async function search(exactStart) {
  const version = ++searchVersion; results.replaceChildren(); message.textContent = '';
  let start;
  try { start = exactStart || new Date(document.querySelector('#start').value).toISOString(); }
  catch { message.textContent = 'Choose a valid date and time.'; return; }
  const params = new URLSearchParams({start_at:start, party_size:document.querySelector('#guests').value});
  try {
    const response = await fetch(`/api/tables/availability?${params}`);
    const data = await response.json();
    if (version !== searchVersion) return;
    if (!response.ok) { showError(data); return; }
    showTables(data);
  } catch { message.textContent = 'Could not check availability. Please try again.'; }
}
form.addEventListener('submit', event => {event.preventDefault(); search();});
