/* EZER — page behaviour. No dependencies. Loaded with `defer`. */
(() => {
  'use strict';

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const CONFIG = (typeof EZER_CONFIG !== 'undefined') ? EZER_CONFIG : {};
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const PLANS = [
    { key: 'trial',   name: 'The Trial Run',        rm: 300,  cap: 20 },
    { key: 'catcher', name: 'The Lead Catcher',     rm: 600,  cap: 50 },
    { key: 'engine',  name: 'The Follow-Up Engine', rm: 1200, cap: 120 },
    { key: 'team',    name: 'The All-In-One Team',  rm: 2000, cap: 250 }
  ];
  const planForVolume = (enquiries) => PLANS.find(p => enquiries <= p.cap) || PLANS[PLANS.length - 1];
  const fmtRM = (n) => 'RM' + Math.round(n).toLocaleString('en-MY');

  /* ---------------------------------------------------------------- URLs */
  const safeUrl = (value, allowedHosts) => {
    if (!value) return '';
    try {
      const url = new URL(value);
      if (url.protocol !== 'https:') return '';
      return allowedHosts.some(h => url.hostname === h || url.hostname.endsWith('.' + h)) ? url.href : '';
    } catch { return ''; }
  };
  const waNumber = String(CONFIG.whatsappNumber || '').replace(/\D/g, '');
  const waLink = (text) => waNumber ? `https://wa.me/${waNumber}?text=${encodeURIComponent(text || CONFIG.whatsappMessage || '')}` : '';
  const email = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(CONFIG.contactEmail || '') ? CONFIG.contactEmail : '';

  /* ---------------------------------------------------------- Config bind */
  function applyConfig() {
    $$('[data-wa]').forEach(el => {
      const link = waLink();
      if (link) { el.href = link; el.target = '_blank'; el.rel = 'noopener'; el.hidden = false; }
      else el.hidden = true;
    });
    $$('[data-email]').forEach(el => {
      if (email) { el.href = 'mailto:' + email; el.textContent = el.dataset.email === 'text' ? email : el.textContent; el.hidden = false; }
      else el.hidden = true;
    });
    $$('[data-requires-contact]').forEach(el => { el.hidden = !(waNumber || email); });

    const li = safeUrl(CONFIG.linkedinUrl, ['linkedin.com']);
    $$('[data-linkedin]').forEach(el => { if (li) { el.href = li; el.hidden = false; } else el.hidden = true; });

    const video = safeUrl(CONFIG.founderVideoUrl, ['youtube.com', 'youtube-nocookie.com', 'vimeo.com']);
    const videoBtn = $('#founderVideoBtn');
    if (videoBtn) videoBtn.hidden = !video;
    if (video && videoBtn) {
      videoBtn.addEventListener('click', () => {
        $('#videoFrame').src = video;
        openModal($('#videoModal'), videoBtn);
      });
    }

    const logos = (Array.isArray(CONFIG.logos) ? CONFIG.logos : [])
      .filter(u => typeof u === 'string' && /^https:\/\//.test(u) && !/placeholder/i.test(u));
    const strip = $('#logoStrip');
    if (strip && logos.length) {
      const track = $('.logo-strip__track', strip);
      [...logos, ...logos].forEach(src => {
        const img = document.createElement('img');
        img.src = src; img.alt = ''; img.loading = 'lazy';
        track.appendChild(img);
      });
      strip.hidden = false;
    }

    const cases = Array.isArray(CONFIG.caseStudies) ? CONFIG.caseStudies.filter(c => c && c.metric) : [];
    const caseSection = $('#results');
    if (caseSection && cases.length) {
      const grid = $('#casesGrid');
      cases.forEach(c => {
        const card = document.createElement('article');
        card.className = 'card';
        const kicker = document.createElement('p'); kicker.className = 'eyebrow'; kicker.textContent = c.client || '';
        const metric = document.createElement('p'); metric.className = 'stat-big'; metric.style.color = 'var(--gold-ink)'; metric.textContent = c.metric;
        const desc = document.createElement('p'); desc.style.marginTop = '10px'; desc.textContent = c.description || '';
        card.append(kicker, metric, desc);
        grid.appendChild(card);
      });
      caseSection.hidden = false;
    }

    const faq = $('#faq');
    if (faq) {
      faq.hidden = !CONFIG.showFaq;
      $$('[data-faq-link]').forEach(el => { el.hidden = !CONFIG.showFaq; });
    }
  }

  /* ---------------------------------------------------------------- Nav */
  function initNav() {
    const nav = $('#nav');
    const toggle = $('#navToggle');
    const links = $('#navLinks');
    const onScroll = () => nav.classList.toggle('is-scrolled', window.scrollY > 24);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });

    const setOpen = (open) => {
      toggle.setAttribute('aria-expanded', String(open));
      links.classList.toggle('is-open', open);
      if (open) nav.classList.add('is-scrolled'); else onScroll();
    };
    toggle.addEventListener('click', () => setOpen(toggle.getAttribute('aria-expanded') !== 'true'));
    $$('a', links).forEach(a => a.addEventListener('click', () => setOpen(false)));
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && links.classList.contains('is-open')) { setOpen(false); toggle.focus(); } });
  }

  /* ------------------------------------------------------------- Reveal */
  function initReveal() {
    const items = $$('[data-reveal]');
    if (!('IntersectionObserver' in window) || reduceMotion) {
      items.forEach(el => el.classList.add('is-in', 'is-visible'));
      $$('.inbox').forEach(el => el.classList.add('is-playing'));
      return;
    }
    const io = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-in', 'is-visible');
        io.unobserve(entry.target);
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    items.forEach(el => io.observe(el));

    const inbox = $('.inbox');
    if (inbox) {
      const io2 = new IntersectionObserver(([e]) => { if (e.isIntersecting) { inbox.classList.add('is-playing'); io2.disconnect(); } }, { threshold: 0.3 });
      io2.observe(inbox);
    }
  }

  /* -------------------------------------------------------- Industries */
  function initIndustries() {
    const out = $('#industryExample');
    const chips = $$('[data-industry]');
    if (!out || !chips.length) return;
    chips.forEach(chip => chip.addEventListener('click', () => {
      chips.forEach(c => c.setAttribute('aria-pressed', String(c === chip)));
      out.querySelector('span').textContent = chip.dataset.industry;
    }));
  }

  /* ------------------------------------------------------- Day timeline */
  function initDay() {
    const day = $('.day');
    if (!day) return;
    let ticking = false;
    const update = () => {
      const r = day.getBoundingClientRect();
      const vh = window.innerHeight;
      const p = Math.min(1, Math.max(0, (vh * 0.6 - r.top) / r.height));
      day.style.setProperty('--p', p.toFixed(3));
      ticking = false;
    };
    window.addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, { passive: true });
    update();
  }

  /* --------------------------------------------------------- ARIA tabs */
  function initTabs(root) {
    const tabs = $$('[role="tab"]', root);
    const select = (tab, focus) => {
      tabs.forEach(t => {
        const on = t === tab;
        t.setAttribute('aria-selected', String(on));
        t.tabIndex = on ? 0 : -1;
        const panel = document.getElementById(t.getAttribute('aria-controls'));
        if (panel) panel.hidden = !on;
      });
      if (focus) tab.focus();
    };
    tabs.forEach((tab, i) => {
      tab.addEventListener('click', () => select(tab));
      tab.addEventListener('keydown', e => {
        const keys = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 };
        if (e.key in keys) { e.preventDefault(); select(tabs[(i + keys[e.key] + tabs.length) % tabs.length], true); }
        if (e.key === 'Home') { e.preventDefault(); select(tabs[0], true); }
        if (e.key === 'End') { e.preventDefault(); select(tabs[tabs.length - 1], true); }
      });
    });
  }

  /* ------------------------------------------------------ Plan highlight */
  function highlightPlan(key) {
    const card = document.querySelector(`.plan[aria-labelledby="plan-${key}-title"]`);
    if (!card) return;
    card.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'center' });
    $$('.plan.is-highlighted').forEach(c => c.classList.remove('is-highlighted'));
    card.classList.add('is-highlighted');
    setTimeout(() => card.classList.remove('is-highlighted'), 3200);
  }
  document.addEventListener('click', e => {
    const trigger = e.target.closest('[data-plan-link]');
    if (!trigger) return;
    e.preventDefault();
    highlightPlan(trigger.dataset.planLink);
  });

  /* --------------------------------------------------------------- ROI */
  function initROI() {
    const leads = $('#roiLeads'), deal = $('#roiDeal'), rate = $('#roiRate');
    if (!leads) return;
    const paint = (input) => {
      const pct = ((input.value - input.min) / (input.max - input.min)) * 100;
      input.style.setProperty('--fill', pct + '%');
    };
    const calc = () => {
      const l = Number(leads.value), d = Number(deal.value), r = Number(rate.value) / 100;
      $('#roiLeadsOut').textContent = l;
      $('#roiDealOut').textContent = fmtRM(d);
      $('#roiRateOut').textContent = Math.round(r * 100) + '%';
      const lost = l * d;
      const gain = lost * r;
      const plan = planForVolume(l);
      $('#roiLost').textContent = fmtRM(lost);
      $('#roiGain').textContent = fmtRM(gain);
      $('#roiPlanName').textContent = plan.name;
      $('#roiPlanPrice').textContent = fmtRM(plan.rm) + '/month';
      const multiple = gain / plan.rm;
      $('#roiMultiple').textContent = multiple >= 1
        ? `Pays for itself ${multiple >= 10 ? Math.round(multiple) : multiple.toFixed(1)}× over`
        : 'Start small and grow into it';
      $('#roiPlanBtn').dataset.planLink = plan.key;
      [leads, deal, rate].forEach(paint);
    };
    [leads, deal, rate].forEach(i => i.addEventListener('input', calc));
    calc();
  }

  /* -------------------------------------------------------- Currency */
  function initCurrency() {
    const btns = $$('.curr-btn');
    const RATES = { RM: { rate: 1, symbol: 'RM' }, SGD: { rate: 0.3, symbol: 'S$' }, USD: { rate: 0.22, symbol: 'US$' } };
    btns.forEach(btn => btn.addEventListener('click', () => {
      btns.forEach(b => { const on = b === btn; b.classList.toggle('active', on); b.setAttribute('aria-pressed', String(on)); });
      const { rate, symbol } = RATES[btn.dataset.curr] || RATES.RM;
      $$('#packages [data-rm]').forEach(el => { el.textContent = symbol + Math.round(Number(el.dataset.rm) * rate).toLocaleString('en-MY'); });
    }));
  }

  /* ------------------------------------------------------- Plan finder */
  function initFinder() {
    const toggle = $('#finderToggle'), panel = $('#finderPanel');
    if (!toggle) return;
    const state = { pain: null, volume: null };
    toggle.addEventListener('click', () => {
      const open = toggle.getAttribute('aria-expanded') !== 'true';
      toggle.setAttribute('aria-expanded', String(open));
      panel.hidden = !open;
    });
    $$('[data-finder]', panel).forEach(chip => chip.addEventListener('click', () => {
      const group = chip.dataset.finder;
      $$(`[data-finder="${group}"]`, panel).forEach(c => c.setAttribute('aria-pressed', String(c === chip)));
      state[group] = chip.dataset.value;
      if (state.pain && state.volume) {
        let plan = planForVolume(Number(state.volume));
        if (state.pain === 'everything' && plan.cap < 120) plan = PLANS[2];
        $('#finderPlan').textContent = plan.name;
        $('#finderGo').dataset.planLink = plan.key;
        $('#finderResult').hidden = false;
      }
    }));
  }

  /* ------------------------------------------------------------ Modals */
  let lastFocus = null;
  function openModal(modal, opener) {
    if (!modal) return;
    lastFocus = opener || document.activeElement;
    modal.hidden = false;
    document.body.style.overflow = 'hidden';
    const focusable = $('button, a[href], iframe', modal);
    if (focusable) focusable.focus();
  }
  function closeModal(modal) {
    if (!modal || modal.hidden) return;
    modal.hidden = true;
    document.body.style.overflow = '';
    const frame = $('iframe', modal);
    if (frame) frame.src = 'about:blank';
    if (lastFocus) lastFocus.focus();
  }
  function initModals() {
    $$('.modal').forEach(modal => {
      modal.addEventListener('click', e => { if (e.target === modal || e.target.closest('[data-close]')) closeModal(modal); });
    });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') $$('.modal:not([hidden])').forEach(closeModal); });

    // Exit intent: desktop pointer only, once per session.
    const exit = $('#exitModal');
    const fine = window.matchMedia('(pointer: fine) and (min-width: 1024px)').matches;
    if (exit && fine) {
      document.addEventListener('mouseout', e => {
        if (e.relatedTarget || e.clientY > 0) return;
        if (sessionStorage.getItem('ezer_exit_shown')) return;
        if ($('#contact').getBoundingClientRect().top < window.innerHeight) return; // already at the form
        sessionStorage.setItem('ezer_exit_shown', '1');
        openModal(exit);
      });
    }
  }

  /* ------------------------------------------------------ Floating CTA */
  function initFloatingCta() {
    const cta = $('#floatingCta');
    const hero = $('.hero');
    if (!cta || !hero || !('IntersectionObserver' in window)) return;
    const blockers = ['#packages', '#contact', '.footer'].map(s => $(s)).filter(Boolean);
    const visible = new Set();
    let heroVisible = true;
    const update = () => cta.classList.toggle('is-visible', !heroVisible && visible.size === 0);
    new IntersectionObserver(([e]) => { heroVisible = e.isIntersecting; update(); }).observe(hero);
    const io = new IntersectionObserver(entries => {
      entries.forEach(e => e.isIntersecting ? visible.add(e.target) : visible.delete(e.target));
      update();
    }, { threshold: 0.05 });
    blockers.forEach(b => io.observe(b));
  }

  /* -------------------------------------------------------------- Form */
  function initForm() {
    const form = $('#leadForm');
    if (!form) return;
    const steps = $$('.form-step', form);
    const bars = $$('.progress span', form);
    const label = $('#progressLabel');
    const status = $('#formStatus');
    let current = 0;

    const show = (i) => {
      current = i;
      steps.forEach((s, idx) => { s.hidden = idx !== i; });
      bars.forEach((b, idx) => b.classList.toggle('is-done', idx <= i));
      label.textContent = `Step ${i + 1} of ${steps.length}`;
      const first = $('input:not([type=hidden]), select', steps[i]);
      if (first && i > 0) first.focus({ preventScroll: true });
    };

    const setError = (field, msg) => {
      const wrap = field.closest('.field');
      if (!wrap) return;
      wrap.classList.toggle('has-error', Boolean(msg));
      const err = $('.field__error', wrap);
      if (err) err.textContent = msg || '';
      field.setAttribute('aria-invalid', msg ? 'true' : 'false');
    };

    const validateStep = (i) => {
      let ok = true;
      $$('input[required]:not([type=radio]), select[required]', steps[i]).forEach(f => {
        let msg = '';
        const v = f.value.trim();
        if (!v) msg = 'Please fill this in.';
        else if (f.type === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) msg = 'Please enter a valid email address.';
        else if (f.type === 'tel' && v.replace(/\D/g, '').length < 8) msg = 'Please enter a valid phone number.';
        setError(f, msg);
        if (msg && ok) { f.focus(); ok = false; }
      });
      $$('.field[data-radio-required]', steps[i]).forEach(group => {
        const checked = $('input:checked', group);
        group.classList.toggle('has-error', !checked);
        if (!checked && ok) { ok = false; const first = $('input', group); if (first) first.focus(); }
      });
      return ok;
    };

    $$('[data-next]', form).forEach(b => b.addEventListener('click', () => { if (validateStep(current)) show(current + 1); }));
    $$('[data-prev]', form).forEach(b => b.addEventListener('click', () => show(current - 1)));
    $$('input, select', form).forEach(f => f.addEventListener('input', () => { if (f.closest('.has-error')) setError(f, ''); f.closest('.field')?.classList.remove('has-error'); }));

    const summary = (d) =>
      `New EZER enquiry\nName: ${d.name}\nEmail: ${d.email}\nCompany: ${d.company}\nPhone: ${d.phone}\nIndustry: ${d.industry}\nMonthly enquiries: ${d.volume}\nBiggest challenge: ${d.challenge}`;

    const succeed = (msg) => {
      steps.forEach(s => { s.hidden = true; });
      $('.progress', form).hidden = true;
      label.hidden = true;
      const done = $('#formSuccess');
      $('#formSuccessMsg').textContent = msg;
      done.hidden = false;
      const cal = safeUrl(CONFIG.calendlyUrl, ['calendly.com']);
      if (cal) {
        const box = $('#calendarEmbed');
        const frame = document.createElement('iframe');
        frame.src = cal; frame.title = 'Book a consultation'; frame.loading = 'lazy';
        box.appendChild(frame);
        box.hidden = false;
      }
      done.focus();
    };

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!validateStep(current)) return;
      if ($('[name="botcheck"]', form).checked) return; // spam honeypot
      const fd = new FormData(form);
      const data = Object.fromEntries(['name', 'email', 'company', 'phone', 'industry', 'volume', 'challenge'].map(k => [k, String(fd.get(k) || '').trim()]));
      const submit = $('button[type=submit]', form);
      status.hidden = true;

      if (CONFIG.web3formsKey) {
        submit.disabled = true;
        submit.textContent = 'Sending…';
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), 15000);
        try {
          const res = await fetch('https://api.web3forms.com/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
            body: JSON.stringify({ access_key: CONFIG.web3formsKey, subject: `New EZER enquiry: ${data.company || data.name}`, from_name: 'EZER website', ...data }),
            signal: controller.signal
          });
          const json = await res.json().catch(() => ({}));
          if (!res.ok || !json.success) throw new Error(json.message || 'Submission failed');
          succeed(`Thanks, ${data.name.split(' ')[0]}! Your details are with Kenisha and she’ll be in touch to arrange your free workflow check.`);
          return;
        } catch (err) {
          console.error('EZER form error', err);
          status.textContent = waNumber
            ? 'Sorry, we couldn’t send your details just now. Please try again, or message us on WhatsApp.'
            : 'Sorry, we couldn’t send your details just now. Please check your connection and try again.';
          status.hidden = false;
        } finally {
          clearTimeout(timer);
          submit.disabled = false;
          submit.textContent = 'Send & get my free check';
        }
        return;
      }

      // Fallbacks while no form service is connected.
      if (waNumber) {
        window.open(waLink(summary(data)), '_blank', 'noopener');
        succeed('We’ve opened WhatsApp with your details filled in — just press send.');
      } else if (email) {
        window.location.href = `mailto:${email}?subject=${encodeURIComponent('Free workflow check')}&body=${encodeURIComponent(summary(data))}`;
        succeed('Your email app should open with your details — just press send.');
      } else {
        status.textContent = 'Online enquiries are being set up. Please check back shortly.';
        status.hidden = false;
      }
    });

    show(0);
  }

  /* -------------------------------------------------------------- Init */
  function init() {
    applyConfig();
    initNav();
    initReveal();
    initIndustries();
    initDay();
    $$('[data-tabs]').forEach(initTabs);
    initROI();
    initCurrency();
    initFinder();
    initModals();
    initFloatingCta();
    initForm();
    const year = $('#year');
    if (year) year.textContent = new Date().getFullYear();
    initPortrait();
  }

  // Founder photo: only same-repo image paths are accepted. Until a photo is
  // configured, the wrapper keeps .portrait--fallback (gold monogram).
  function initPortrait() {
    const img = $('.portrait img');
    const photo = typeof CONFIG.founderPhoto === 'string' ? CONFIG.founderPhoto.trim() : '';
    if (!img || !/^assets\/[\w.-]+\.(webp|jpe?g|png|avif)$/i.test(photo)) return;
    const wrap = img.parentElement;
    img.addEventListener('load', () => {
      if (img.naturalWidth > 0) { img.hidden = false; wrap.classList.remove('portrait--fallback'); }
    }, { once: true });
    img.addEventListener('error', () => { img.hidden = true; wrap.classList.add('portrait--fallback'); }, { once: true });
    img.src = photo;
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
