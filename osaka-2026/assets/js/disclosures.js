
(() => {
  const disclosures = Array.from(document.querySelectorAll('[data-disclosure]'));

  const setOpen = (box, open) => {
    const btn = box.querySelector('.disclosure-toggle');
    box.classList.toggle('open', open);
    if (btn) btn.setAttribute('aria-expanded', String(open));
  };

  disclosures.forEach(box => {
    const btn = box.querySelector('.disclosure-toggle');
    if (!btn) return;
    btn.addEventListener('click', () => setOpen(box, !box.classList.contains('open')));
  });

  const days = Array.from(document.querySelectorAll('#days [data-disclosure]'));
  const expandBtn = document.querySelector('[data-expand-days]');
  const collapseBtn = document.querySelector('[data-collapse-days]');
  if (expandBtn) expandBtn.addEventListener('click', () => days.forEach(d => setOpen(d, true)));
  if (collapseBtn) collapseBtn.addEventListener('click', () => days.forEach(d => setOpen(d, false)));

  const revealEls = Array.from(document.querySelectorAll('.reveal'));
  if ('IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });
    revealEls.forEach(el => observer.observe(el));
  } else {
    revealEls.forEach(el => el.classList.add('is-visible'));
  }

  // Keep the summary immediately visible.
  const summary = document.querySelector('#summary');
  if (summary) summary.classList.add('is-visible');
})();
