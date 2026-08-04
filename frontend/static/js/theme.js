function applyActiveButton(mode) {
  document.querySelectorAll('#theme-switch button').forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.themeChoice === mode);
  });
}

function setTheme(mode) {
  if (mode === 'system') {
    localStorage.removeItem('theme');
    document.documentElement.removeAttribute('data-theme');
  } else {
    localStorage.setItem('theme', mode);
    document.documentElement.setAttribute('data-theme', mode);
  }
  applyActiveButton(mode);
}

document.addEventListener('DOMContentLoaded', () => {
  const current = localStorage.getItem('theme') || 'system';
  applyActiveButton(current);

  document.querySelectorAll('#theme-switch button').forEach((btn) => {
    btn.addEventListener('click', () => setTheme(btn.dataset.themeChoice));
  });
});