const notice = document.querySelector('#message');
for (const time of document.querySelectorAll('time')) {
  time.textContent = new Date(time.dateTime).toLocaleString();
}
for (const button of document.querySelectorAll('[data-cancel]')) {
  button.addEventListener('click', async () => {
    if (!window.confirm('Cancel this booking and release the table?')) return;
    button.disabled = true;
    notice.textContent = '';
    try {
      const response = await fetch(button.dataset.cancel, {
        method: 'POST', headers: {'Content-Type': 'application/json',
          'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value},
        body: '{}'
      });
      const data = await response.json();
      if (!response.ok) {
        notice.textContent = data.message || data.detail || 'Cancellation could not be completed.';
        if (response.status === 401) notice.textContent += ' Sign in again, then reload this page.';
        return;
      }
      button.closest('article').querySelector('[data-status]').textContent = data.status;
      notice.textContent = `${data.booking_id} cancelled. The table is available for booking again.`;
      button.remove();
    } catch {
      notice.textContent = 'Connection interrupted. Retry cancellation safely or reload to check its status.';
    } finally { button.disabled = false; }
  });
}
