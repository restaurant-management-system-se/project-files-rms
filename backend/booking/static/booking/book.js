const form = document.querySelector('#search');
const results = document.querySelector('#results');
const message = document.querySelector('#message');
function showError(data) {
  message.textContent = [data.message, ...Object.entries(data.details || {}).map(([k,v]) => `${k}: ${v}`)].join('\n');
}
form.addEventListener('submit', async event => {
  event.preventDefault(); results.replaceChildren(); message.textContent = '';
  const params = new URLSearchParams({start_at: new Date(document.querySelector('#start').value).toISOString(), party_size: document.querySelector('#guests').value});
  try {
    const response = await fetch(`/api/tables/availability?${params}`);
    const data = await response.json();
    if (!response.ok) { showError(data); return; }
    const heading = document.createElement('h2');
    heading.textContent = data.tables.length ? 'Available tables' : 'No tables at that time'; results.append(heading);
    for (const table of data.tables) {
      const row = document.createElement('p'); row.textContent = `Table ${table.table_number} · ${table.capacity} seats`; results.append(row);
    }
    if (data.alternative) {
      const button = document.createElement('button');
      button.textContent = `Try nearest slot: ${new Date(data.alternative.start_at).toLocaleString()} · Table ${data.alternative.table_number}`;
      button.onclick = () => {
        const date = new Date(data.alternative.start_at);
        date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
        document.querySelector('#start').value = date.toISOString().slice(0, 16);
        form.requestSubmit();
      }; results.append(button);
    } else if (!data.tables.length) { results.append(document.createTextNode('No active table has enough seats. Try a smaller party size.')); }
  } catch { message.textContent = 'Could not check availability. Please try again.'; }
});
