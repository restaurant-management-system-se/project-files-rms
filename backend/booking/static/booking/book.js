const form = document.querySelector('#search');
const results = document.querySelector('#results');
const message = document.querySelector('#message');
const progress = document.querySelector('#progress');
const csrf = document.querySelector('[name=csrfmiddlewaretoken]');
let searchVersion = 0;
let retryRequest = null;
let confirming = false;
function clearErrors() {
  message.textContent = '';
  for (const id of ['start', 'guests']) {
    document.querySelector(`#${id}-error`).textContent = '';
    document.querySelector(`#${id}`).removeAttribute('aria-invalid');
  }
}
function fieldError(id, text) {
  document.querySelector(`#${id}`).setAttribute('aria-invalid', 'true');
  document.querySelector(`#${id}-error`).textContent = text;
}
function confirmationBusy(busy) {
  confirming = busy;
  results.setAttribute('aria-busy', String(busy));
  for (const control of document.querySelectorAll('#search input:not([type=hidden]), #search button, #results button')) control.disabled = busy;
}
function showError(data) {
  message.textContent = [data.message || data.detail || "Request could not be completed.", ...Object.entries(data.details || {}).filter(([k]) => !['tables','alternative'].includes(k)).map(([k,v]) => `${k}: ${v}`)].join('\n');
  if (data.details?.start_at) fieldError('start', String(data.details.start_at));
  if (data.details?.party_size) fieldError('guests', String(data.details.party_size));
}
function showTables(data) {
  const heading = document.createElement('h2'); heading.textContent = data.tables.length ? 'Available tables' : 'No tables at that time'; results.append(heading);
  const visit = document.createElement('p');
  visit.textContent = `${new Date(data.start_at).toLocaleString()} – ${new Date(data.end_at).toLocaleTimeString()} · ${data.party_size} guests`;
  results.append(visit);
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
  if (confirming) return;
  clearErrors(); confirmationBusy(true); progress.textContent = 'Confirming your booking…';
  try {
    const identity = JSON.stringify([table.table_id, data.start_at, data.party_size]);
    if (!retryRequest || retryRequest.identity !== identity) {
      retryRequest = {identity, payload: {table_id:table.table_id, start_at:data.start_at, party_size:data.party_size, idempotency_key:crypto.randomUUID()}};
    }
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
    const history = document.createElement('a'); history.href = '/my-bookings/'; history.textContent = 'View or cancel my booking';
    results.append(summary, history); retryRequest = null; results.focus();
  } catch { message.textContent = 'Connection interrupted. Retry this confirmation to recover the same booking safely.'; }
  finally { confirmationBusy(false); progress.textContent = ''; }
}
async function search(exactStart) {
  if (confirming) return;
  const version = ++searchVersion; results.replaceChildren(); clearErrors(); progress.textContent = '';
  let start;
  try { start = exactStart || new Date(document.querySelector('#start').value).toISOString(); }
  catch { fieldError('start', 'Choose a valid date and time.'); document.querySelector('#start').focus(); return; }
  if (new Date(start).getTime() <= Date.now()) {
    fieldError('start', 'Choose a future date and time.'); document.querySelector('#start').focus(); return;
  }
  if (!document.querySelector('#guests').checkValidity()) {
    fieldError('guests', 'Enter a whole number of guests, from 1 to 32767.'); document.querySelector('#guests').focus(); return;
  }
  progress.textContent = 'Checking availability…'; results.setAttribute('aria-busy', 'true');
  const params = new URLSearchParams({start_at:start, party_size:document.querySelector('#guests').value});
  try {
    const response = await fetch(`/api/tables/availability?${params}`);
    const data = await response.json();
    if (version !== searchVersion) return;
    if (!response.ok) { showError(data); return; }
    showTables(data);
  } catch { if (version === searchVersion) message.textContent = 'Could not check availability. Please try again.'; }
  finally { if (version === searchVersion) { progress.textContent = ''; results.setAttribute('aria-busy', 'false'); } }
}
form.addEventListener('submit', event => {event.preventDefault(); search();});
for (const input of form.querySelectorAll('input:not([type=hidden])')) input.addEventListener('input', () => {
  ++searchVersion; results.replaceChildren(); results.setAttribute('aria-busy', 'false');
  progress.textContent = ''; clearErrors();
});
