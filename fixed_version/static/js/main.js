// SecureShop – Main JavaScript
// Works for both vulnerable and fixed versions

document.addEventListener('DOMContentLoaded', function () {

  // ── Auto-dismiss flash messages after 5 seconds ──
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      alert.style.opacity = '0';
      alert.style.transform = 'translateX(100%)';
      alert.style.transition = 'all 0.4s ease';
      setTimeout(function () { alert.remove(); }, 400);
    }, 5000);
  });

  // ── Smooth scroll for anchor links ──
  document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
    anchor.addEventListener('click', function (e) {
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // ── Active nav link highlight ──
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(function (link) {
    if (link.getAttribute('href') === currentPath) {
      link.style.color = 'var(--text-primary)';
      link.style.background = 'var(--bg-tertiary)';
    }
  });

  // ── Fade-in animation for cards ──
  const observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('fade-in');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.product-card, .stat-card, .lab-card, .order-card').forEach(function (card) {
    observer.observe(card);
  });

  // ── Confirm delete actions ──
  document.querySelectorAll('form[data-confirm]').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      if (!confirm(this.dataset.confirm)) {
        e.preventDefault();
      }
    });
  });

  // ── Quantity input validation ──
  const qtyInput = document.getElementById('quantity');
  if (qtyInput) {
    qtyInput.addEventListener('change', function () {
      const max = parseInt(this.getAttribute('max'), 10);
      const min = parseInt(this.getAttribute('min'), 10);
      if (parseInt(this.value, 10) > max) this.value = max;
      if (parseInt(this.value, 10) < min) this.value = min;
    });
  }

  // ── Search input focus effect ──
  const searchInput = document.getElementById('search-input');
  if (searchInput) {
    searchInput.addEventListener('focus', function () {
      this.parentElement.style.boxShadow = '0 0 0 3px rgba(37,99,235,0.15)';
      this.parentElement.style.borderRadius = 'var(--radius-sm)';
    });
    searchInput.addEventListener('blur', function () {
      this.parentElement.style.boxShadow = '';
    });
  }

  // ── Highlight active filter chip ──
  const params = new URLSearchParams(window.location.search);
  const cat = params.get('cat');
  if (cat) {
    document.querySelectorAll('.filter-chip').forEach(function (chip) {
      if (chip.href && chip.href.includes('cat=' + cat)) {
        chip.classList.add('active');
      } else {
        chip.classList.remove('active');
      }
    });
  }
});
