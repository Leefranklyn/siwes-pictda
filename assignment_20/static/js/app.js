document.querySelectorAll('[data-toast]').forEach(toast => {
  const dismiss = () => { toast.classList.add('opacity-0', 'transition-opacity'); setTimeout(() => toast.remove(), 150); };
  toast.querySelector('[data-dismiss-toast]').addEventListener('click', dismiss);
  setTimeout(dismiss, 5000);
});

const drawer = document.getElementById('sidebar'), toggle = document.getElementById('drawer-toggle'), overlay = document.getElementById('drawer-overlay');
const setDrawer = open => {
  drawer.classList.toggle('hidden', !open); drawer.classList.toggle('flex', open);
  overlay.hidden = !open; toggle.setAttribute('aria-expanded', String(open));
  document.body.style.overflow = open ? 'hidden' : '';
  (open ? document.getElementById('drawer-close') : toggle).focus();
};
toggle?.addEventListener('click', () => setDrawer(true));
overlay?.addEventListener('click', () => setDrawer(false));
document.getElementById('drawer-close')?.addEventListener('click', () => setDrawer(false));
document.addEventListener('keydown', event => { if (event.key === 'Escape' && overlay && !overlay.hidden) setDrawer(false); });

document.addEventListener('keydown', event => {
  if (event.key !== '/' || event.ctrlKey || event.metaKey || event.target.closest('input, textarea, select, [contenteditable]')) return;
  const search = document.querySelector('input[type="search"]');
  if (search) { event.preventDefault(); search.focus(); }
  else if (location.pathname === '/dashboard/') { event.preventDefault(); location.href = '/students/?focus=search'; }
});
if (new URLSearchParams(location.search).get('focus') === 'search') document.querySelector('input[type="search"]')?.focus();

document.getElementById('password-toggle')?.addEventListener('click', event => {
  const input = document.getElementById('id_password'), button = event.currentTarget;
  const showing = input.type === 'password'; input.type = showing ? 'text' : 'password';
  button.setAttribute('aria-label', showing ? 'Hide password' : 'Show password');
  button.setAttribute('title', showing ? 'Hide password' : 'Show password');
  button.setAttribute('aria-pressed', String(showing));
  button.querySelector('i').className = showing ? 'ti ti-eye-off' : 'ti ti-eye';
});

const demoData = document.getElementById('demo-accounts');
if (demoData) document.querySelectorAll('[data-demo-role]').forEach(button => button.addEventListener('click', () => {
  const account = JSON.parse(demoData.textContent).find(item => item.role === button.dataset.demoRole);
  document.getElementById('id_username').value = account.username;
  document.getElementById('id_password').value = account.password;
  document.querySelector('#login-form button[type="submit"]').focus();
}));

document.body.addEventListener('htmx:afterSwap', event => {
  if (event.detail.target.id !== 'results') return;
  const sort = document.querySelector('#results [data-current-sort]')?.dataset.currentSort;
  if (sort) document.querySelector('[name="sort"]').value = sort;
});
document.body.addEventListener('htmx:responseError', () => {
  const error = document.getElementById('search-error'); if (error) error.hidden = false;
});
document.querySelector('[aria-invalid="true"]')?.focus();
