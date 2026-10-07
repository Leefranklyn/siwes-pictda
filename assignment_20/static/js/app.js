// Toasts: dismiss button and auto-hide.
document.querySelectorAll('[data-toast]').forEach(toast => {
  const dismiss = () => { toast.classList.add('opacity-0', 'transition-opacity'); setTimeout(() => toast.remove(), 150); };
  toast.querySelector('[data-dismiss-toast]').addEventListener('click', dismiss);
  setTimeout(dismiss, 5000);
});

// Theme: MODE [L][D] toggle, persisted, with a themechange event for canvases and charts.
const root = document.documentElement;
const currentTheme = () => root.getAttribute('data-theme') ||
  (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
const syncModeButtons = () => {
  document.querySelectorAll('[data-theme-set]').forEach(button => {
    button.setAttribute('aria-pressed', String(button.dataset.themeSet === currentTheme()));
  });
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.setAttribute('content', currentTheme() === 'dark' ? '#0B0C0C' : '#EEEDE8');
};
document.querySelectorAll('[data-theme-set]').forEach(button => button.addEventListener('click', () => {
  root.setAttribute('data-theme', button.dataset.themeSet);
  try { localStorage.setItem('theme', button.dataset.themeSet); } catch (e) {}
  syncModeButtons();
  document.dispatchEvent(new Event('themechange'));
}));
syncModeButtons();

// Moving lime dot under the active top navigation item.
const topnav = document.getElementById('topnav'), navDot = document.getElementById('nav-dot');
if (topnav && navDot) {
  const placeDot = () => {
    const active = topnav.querySelector('a[aria-current="page"]');
    if (active) navDot.style.transform = `translateX(${active.offsetLeft + active.offsetWidth / 2 - 3}px)`;
  };
  placeDot();
  addEventListener('resize', placeDot);
  document.fonts?.ready.then(placeDot);
}

// Mobile navigation panel below md.
const mobileToggle = document.getElementById('mobile-menu-toggle'), mobileMenu = document.getElementById('mobile-menu');
mobileToggle?.addEventListener('click', () => {
  const open = mobileMenu.classList.toggle('hidden') === false;
  mobileToggle.setAttribute('aria-expanded', String(open));
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && mobileMenu && !mobileMenu.classList.contains('hidden')) {
    mobileMenu.classList.add('hidden');
    mobileToggle.setAttribute('aria-expanded', 'false');
  }
});

// Scroll reveals.
if (!matchMedia('(prefers-reduced-motion: reduce)').matches) {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) { entry.target.classList.add('in-view'); observer.unobserve(entry.target); }
    });
  }, { threshold: 0.15 });
  document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
} else {
  document.querySelectorAll('.reveal').forEach(el => el.classList.add('in-view'));
}

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

// Selects with data-autosubmit submit their form on change.
document.querySelectorAll('[data-autosubmit]').forEach(select => {
  select.addEventListener('change', () => select.form && select.form.submit());
});

// Student list bulk selection: the bar appears when at least one row is checked.
const bulkBar = document.getElementById('bulk-bar');
const updateBulkBar = () => {
  if (!bulkBar) return;
  const checked = document.querySelectorAll('#results input[name="selected"]:checked');
  bulkBar.classList.toggle('hidden', checked.length === 0);
  bulkBar.classList.toggle('flex', checked.length > 0);
  document.getElementById('bulk-count').textContent = `${checked.length} selected`;
  const ids = Array.from(checked).map(box => box.value);
  for (const suffix of ['promote-ids', 'status-ids', 'export-ids']) {
    const field = document.getElementById(`bulk-${suffix}`);
    if (field) field.value = JSON.stringify(ids);
  }
};
document.addEventListener('change', event => {
  if (event.target.name === 'selected' || event.target.id === 'select-all') {
    if (event.target.id === 'select-all') {
      document.querySelectorAll('#results input[name="selected"]').forEach(box => { box.checked = event.target.checked; });
    }
    updateBulkBar();
  }
});
document.getElementById('bulk-clear')?.addEventListener('click', () => {
  document.querySelectorAll('#results input[name="selected"]').forEach(box => { box.checked = false; });
  const all = document.getElementById('select-all');
  if (all) all.checked = false;
  updateBulkBar();
});
const statusDialog = document.getElementById('bulk-status-dialog');
document.getElementById('bulk-status-open')?.addEventListener('click', () => statusDialog?.showModal());

// Account form: generate a temporary password.
document.getElementById('generate-password')?.addEventListener('click', () => {
  const alphabet = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789';
  const bytes = new Uint8Array(12);
  crypto.getRandomValues(bytes);
  document.getElementById('id_password').value = Array.from(bytes, byte => alphabet[byte % alphabet.length]).join('');
});

// One-time credential panel copy button.
document.querySelector('[data-copy-credentials]')?.addEventListener('click', () => {
  const code = document.querySelector('[data-credentials] code');
  navigator.clipboard.writeText(code.textContent).then(() => {
    const button = document.querySelector('[data-copy-credentials]');
    button.textContent = 'Copied';
    setTimeout(() => { button.textContent = 'Copy'; }, 1500);
  });
});

// Grade sheet: live counter and change highlight.
const gradeForm = document.getElementById('grade-form');
if (gradeForm) {
  const counter = document.getElementById('graded-counter');
  const total = gradeForm.querySelectorAll('[data-grade-row]').length;
  const initial = parseInt(gradeForm.dataset.gradedCount || '0', 10);
  let changed = false;
  gradeForm.addEventListener('change', event => {
    if (event.target.type !== 'radio') return;
    changed = true;
    event.target.closest('[data-grade-row]').classList.add('changed-row');
    let gradedRows = 0;
    gradeForm.querySelectorAll('[data-grade-row]').forEach(row => {
      if (!row.querySelector('input[value=""]:checked')) gradedRows += 1;
    });
    counter.textContent = `${gradedRows} of ${total} graded`;
  });
  gradeForm.addEventListener('submit', () => { if (changed) gradeForm.dataset.changed = '1'; });
}

// Global search: arrow keys move through results, Enter opens, Escape closes.
const searchPanel = document.getElementById('global-search-results');
if (searchPanel) {
  const container = document.getElementById('global-search');
  const input = container.querySelector('input');
  let index = -1;
  const options = () => Array.from(searchPanel.querySelectorAll('[role=option]'));
  input.addEventListener('keydown', event => {
    const items = options();
    if (event.key === 'Escape') { searchPanel.innerHTML = ''; input.blur(); return; }
    if (!items.length) return;
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault();
      index = event.key === 'ArrowDown' ? (index + 1) % items.length : (index - 1 + items.length) % items.length;
      items.forEach((item, position) => item.classList.toggle('bg-surface-2', position === index));
    } else if (event.key === 'Enter' && index >= 0) {
      event.preventDefault(); items[index].click();
    }
  });
  document.addEventListener('click', event => { if (!container.contains(event.target)) searchPanel.innerHTML = ''; });
  document.addEventListener('keydown', event => {
    if (event.key === '/' && !event.ctrlKey && !event.metaKey && !event.target.closest('input, textarea, select, [contenteditable]')) {
      event.preventDefault(); input?.focus();
    }
  });
}

// Typing effect for the login title and error page codes.
(() => {
  const target = document.querySelector('[data-typein]');
  if (!target) return;
  const text = target.textContent;
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  target.textContent = '';
  target.style.borderRight = '6px solid var(--accent)';
  let i = 0;
  const timer = setInterval(() => {
    i += 1;
    target.textContent = text.slice(0, i);
    if (i >= text.length) { clearInterval(timer); setTimeout(() => { target.style.borderRight = ''; }, 400); }
  }, 45);
})();

// Vapor: tiny monochrome particle wisps on primary button hover.
const Vapor = (() => {
  const off = () => matchMedia('(prefers-reduced-motion: reduce)').matches || matchMedia('(hover: none)').matches;
  if (off()) return { burst: () => {} };
  const c = document.createElement('canvas');
  c.style.cssText = 'position:fixed;inset:0;width:100%;height:100%;pointer-events:none;z-index:40';
  document.body.appendChild(c);
  const ctx = c.getContext('2d');
  let parts = [], raf = 0;
  const size = () => {
    const d = devicePixelRatio || 1;
    c.width = innerWidth * d; c.height = innerHeight * d;
    ctx.setTransform(d, 0, 0, d, 0, 0);
  };
  addEventListener('resize', size); size();
  const tick = () => {
    ctx.clearRect(0, 0, innerWidth, innerHeight);
    const dark = currentTheme() === 'dark';
    parts = parts.filter(p => p.age < p.life);
    parts.forEach(p => {
      p.age += 16; p.x += p.vx; p.y += p.vy; p.vy *= 0.99; p.r += 0.05;
      const k = 1 - p.age / p.life;
      ctx.globalAlpha = 0.28 * k;
      ctx.fillStyle = dark ? '#cfd1d1' : '#555';
      ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, 6.28); ctx.fill();
    });
    ctx.globalAlpha = 1;
    raf = parts.length ? requestAnimationFrame(tick) : 0;
  };
  const burst = (x, y, n = 9) => {
    if (off() || document.hidden) return;
    for (let i = 0; i < n && parts.length < 60; i++) {
      parts.push({ x: x + (Math.random() - 0.5) * 24, y, vx: (Math.random() - 0.5) * 0.5,
                   vy: -(0.35 + Math.random() * 0.7), r: 2 + Math.random() * 3,
                   age: 0, life: 650 + Math.random() * 300 });
    }
    if (!raf) raf = requestAnimationFrame(tick);
  };
  document.addEventListener('mouseover', e => {
    const el = e.target.closest && e.target.closest('.button-primary,[data-vapor]');
    if (el && !el.contains(e.relatedTarget)) {
      const r = el.getBoundingClientRect();
      burst(r.left + r.width / 2, r.top + 4, 7);
    }
  });
  document.addEventListener('visibilitychange', () => { if (document.hidden) { cancelAnimationFrame(raf); raf = 0; } });
  return { burst };
})();
