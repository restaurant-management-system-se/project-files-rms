const message = document.querySelector('#message');
for (const t of document.querySelectorAll('time')) t.textContent = new Date(t.dateTime).toLocaleString();
async function send(url, payload, button) {
  button.disabled = true;
  message.textContent = '';
  try {
    const response = await fetch(url, {method:'POST',headers:{'Content-Type':'application/json',
      'X-CSRFToken':document.querySelector('[name=csrfmiddlewaretoken]').value},body:JSON.stringify(payload)});
    const data = await response.json();
    if (!response.ok) {
      message.textContent = data.message || data.detail || JSON.stringify(data);
      if (response.status === 409 && data.details?.alternative) {
        message.textContent += ` Nearest slot: ${new Date(data.details.alternative.start_at).toLocaleString()}, table ID ${data.details.alternative.table_id}. Check availability before retrying.`;
      }
      return false;
    }
    window.location.reload();
    return true;
  } catch {
    message.textContent = 'Connection interrupted. Retry the same request safely or reload to inspect booking history.';
    return false;
  } finally { button.disabled = false; }
}
const createForm = document.querySelector('#manual-create');
let attempt = null;
createForm.addEventListener('submit', async event => {
  event.preventDefault();
  const fields = Object.fromEntries(new FormData(createForm));
  let payload;
  try {
    payload = {...fields,customer_id:Number(fields.customer_id),table_id:Number(fields.table_id),
      party_size:Number(fields.party_size),start_at:new Date(fields.start_at).toISOString()};
  } catch { message.textContent = 'Choose a valid date and time.'; return; }
  const identity = JSON.stringify(payload);
  if (!attempt || attempt.identity !== identity) attempt = {identity,key:crypto.randomUUID()};
  payload.idempotency_key = attempt.key;
  if (await send('/api/staff/bookings',payload,createForm.querySelector('button'))) attempt = null;
});
for (const form of document.querySelectorAll('[data-cancel]')) form.addEventListener('submit', event => {
  event.preventDefault();
  if (!window.confirm('Cancel this booking using the recorded staff reason?')) return;
  send(form.dataset.cancel,{reason:new FormData(form).get('reason')},form.querySelector('button'));
});
