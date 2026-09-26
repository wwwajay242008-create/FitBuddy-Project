document.addEventListener('submit', (event) => {
  const form = event.target;
  if (form.id === 'plan-form') {
    const button = form.querySelector('button');
    button.disabled = true;
    button.textContent = 'Generating…';
  }
});
