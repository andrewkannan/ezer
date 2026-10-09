"""Page behaviour checks. Run via tests/run_tests.ps1."""
import json, sys
import os, pathlib
BASE_URL = os.environ.get("EZER_TEST_URL", "http://localhost:8765/")
OUT_DIR = pathlib.Path(__file__).parent / "output"
OUT_DIR.mkdir(exist_ok=True)
from playwright.sync_api import sync_playwright

URL = BASE_URL + 'index.html'
OUT = str(OUT_DIR)
results = []


def check(name, ok, detail=''):
    results.append(('PASS' if ok else 'FAIL', name, detail))


def scroll_through(page):
    h = page.evaluate('document.body.scrollHeight')
    for y in range(0, h + 800, 500):
        page.evaluate(f'window.scrollTo(0, {y})')
        page.wait_for_timeout(70)
    page.wait_for_timeout(900)
    page.evaluate('window.scrollTo(0, 0)')
    page.wait_for_timeout(400)


with sync_playwright() as p:
    browser = p.chromium.launch(channel='msedge')
    _np = browser.new_page
    def _new_page(**kw):
        pg = _np(**kw)
        pg.add_init_script("document.addEventListener('DOMContentLoaded',()=>{const s=document.createElement('style');s.textContent='html{scroll-behavior:auto!important}';document.head.appendChild(s)})")
        return pg
    browser.new_page = _new_page
    issues = []

    # ------------------------------------------------------------ desktop
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    page.context.route('https://wa.me/**', lambda r: r.fulfill(status=200, content_type='text/html', body='stub'))
    page.on('console', lambda m: issues.append(f'console {m.type}: {m.text}') if m.type in ('error', 'warning') else None)
    page.on('pageerror', lambda e: issues.append(f'pageerror: {e}'))
    page.on('response', lambda r: issues.append(f'HTTP {r.status}: {r.url}') if r.status >= 400 else None)
    page.goto(URL, wait_until='networkidle')

    dupes = page.evaluate("""(() => { const c = {}; document.querySelectorAll('[id]').forEach(e => c[e.id] = (c[e.id]||0)+1); return Object.entries(c).filter(([k,v]) => v > 1); })()""")
    check('no duplicate IDs', not dupes, str(dupes))
    broken = page.evaluate("""[...document.querySelectorAll('a[href^="#"]')].map(a => a.getAttribute('href')).filter(h => h.length > 1 && !document.querySelector(h))""")
    check('all in-page anchors resolve', not broken, str(sorted(set(broken))))
    check('fake social proof removed', page.evaluate("!document.body.innerText.includes('Sarah from') && !document.body.innerText.includes('14,250')"))
    check('logo strip hidden without real logos', page.is_hidden('#logoStrip'))
    check('FAQ visible (showFaq=true)', page.is_visible('#faq'))
    check('no "risk-free" promise anywhere', page.evaluate("!document.documentElement.innerHTML.includes('risk-free')"))
    wa = page.evaluate("[...document.querySelectorAll('a[href*=\"wa.me\"]')].map(a => a.href)")
    check('WhatsApp links use +60 11-6054 7134', bool(wa) and all(h.startswith('https://wa.me/601160547134') for h in wa), str(wa[:3]))
    check('languages listed without Mandarin', 'Tamil' in page.inner_text('body') and 'Mandarin' not in page.inner_text('body'))
    check('video button hidden without URL', page.is_hidden('#founderVideoBtn'))

    scroll_through(page)
    page.screenshot(path=f'{OUT}\\full_desktop.png', full_page=True)

    # floating CTA: hidden on hero, visible mid-page, hidden on pricing
    check('floating CTA hidden on hero', not page.evaluate("document.getElementById('floatingCta').classList.contains('is-visible')"))
    page.evaluate("document.getElementById('what').scrollIntoView({behavior:'instant'})"); page.wait_for_timeout(500)
    check('floating CTA visible mid-page', page.evaluate("document.getElementById('floatingCta').classList.contains('is-visible')"))
    page.evaluate("document.getElementById('packages').scrollIntoView({behavior:'instant'})"); page.wait_for_timeout(500)
    check('desktop: floating WhatsApp shortcut hidden', page.evaluate("getComputedStyle(document.querySelector('.floating-cta__wa')).display") == 'none')
    check('floating CTA hidden over pricing', not page.evaluate("document.getElementById('floatingCta').classList.contains('is-visible')"))

    # industries
    page.evaluate("document.getElementById('problem').scrollIntoView({behavior:'instant'})")
    page.click('text=Renovation & contractors')
    check('industry chip updates example', 'quotation' in page.inner_text('#industryExample').lower())

    # stepper + services tabs + keyboard
    page.click('#step-tab-5')
    check('stepper shows Retain panel', page.is_visible('#step-5') and page.is_hidden('#step-1'))
    page.focus('#svc-tab-1'); page.keyboard.press('ArrowDown')
    check('services tabs keyboard nav', page.is_visible('#svc-2') and page.evaluate("document.activeElement.id") == 'svc-tab-2')

    # ROI -> plan
    page.evaluate("const s=document.getElementById('roiLeads'); s.value=100; s.dispatchEvent(new Event('input'))")
    plan_name = page.inner_text('#roiPlanName')
    check('ROI recommends by volume (100 -> Follow-Up Engine)', plan_name == 'The Follow-Up Engine', plan_name)
    check('ROI numbers', page.inner_text('#roiLost') == 'RM50,000' and page.inner_text('#roiGain') == 'RM15,000', page.inner_text('#roiLost') + ' / ' + page.inner_text('#roiGain'))
    page.click('#roiPlanBtn'); page.wait_for_timeout(900)
    check('ROI button highlights plan card', page.evaluate("document.querySelector('.plan.is-highlighted')?.getAttribute('aria-labelledby')") == 'plan-engine-title')

    # finder
    page.click('#finderToggle')
    page.click('[data-finder="pain"][data-value="followup"]')
    page.click('[data-finder="volume"][data-value="50"]')
    check('plan finder result', page.inner_text('#finderPlan') == 'The Lead Catcher', page.inner_text('#finderPlan'))

    # currency
    page.click('.curr-btn[data-curr="SGD"]')
    check('currency toggle SGD', page.evaluate("document.querySelector('.plan-amount').textContent") == 'S$90')
    page.click('.curr-btn[data-curr="RM"]')

    # form validation + no-config fallback
    page.evaluate("document.getElementById('contact').scrollIntoView({behavior:'instant'})")
    page.click('#leadForm [data-next]')
    check('form blocks empty step 1', page.evaluate("document.querySelector('#fName').closest('.field').classList.contains('has-error')"))
    page.fill('#fName', 'Test Owner'); page.fill('#fEmail', 'not-an-email')
    page.click('#leadForm fieldset:not([hidden]) [data-next]')
    check('form rejects bad email', page.evaluate("document.querySelector('#fEmail').closest('.field').classList.contains('has-error')"))
    page.fill('#fEmail', 'owner@example.com')
    page.click('#leadForm fieldset:not([hidden]) [data-next]')
    page.fill('#fCompany', 'Test Sdn Bhd'); page.fill('#fPhone', '+60 12-345 6789'); page.select_option('#fIndustry', 'Property')
    page.click('#leadForm fieldset:not([hidden]) [data-next]')
    page.click('#leadForm button[type=submit]')
    check('form requires radio answers', page.evaluate("document.querySelectorAll('#leadForm .field[data-radio-required].has-error').length") == 2)
    page.check('input[name=volume][value="50–120"]', force=True)
    page.check('input[name=challenge][value="Customer information is a mess"]', force=True)
    with page.expect_popup() as pop:
        page.click('#leadForm button[type=submit]')
    wa_url = pop.value.url
    page.wait_for_timeout(300)
    check('no-key fallback opens WhatsApp with details', '601160547134' in wa_url and 'Test%20Sdn%20Bhd' in wa_url.replace('+', '%20'), wa_url[:160])
    check('fallback shows success message', page.is_visible('#formSuccess'))
    page.screenshot(path=f'{OUT}\\form_desktop.png')
    page.close()

    # ------------------------------------------------- form with Web3Forms key (mocked)
    page = browser.new_page(viewport={'width': 1280, 'height': 900})
    page.add_init_script("localStorage.setItem('ezer_admin_config', JSON.stringify({web3formsKey:'test-key'}))")
    captured = {}
    def handle(route):
        captured['body'] = route.request.post_data
        route.fulfill(status=200, content_type='application/json', body='{"success":true}')
    page.route('https://api.web3forms.com/submit', handle)
    page.goto(URL, wait_until='networkidle')
    page.evaluate("document.getElementById('contact').scrollIntoView({behavior:'instant'})")
    page.fill('#fName', 'Aina Tan'); page.fill('#fEmail', 'aina@example.com'); page.click('#leadForm fieldset:not([hidden]) [data-next]')
    page.fill('#fCompany', 'Glow Studio'); page.fill('#fPhone', '0123456789'); page.select_option('#fIndustry', 'Salon / beauty'); page.click('#leadForm fieldset:not([hidden]) [data-next]')
    page.check('input[name=volume][value="20–50"]', force=True); page.check('input[name=challenge][value="Forgetting to follow up with warm leads"]', force=True)
    page.click('#leadForm button[type=submit]'); page.wait_for_timeout(600)
    body = json.loads(captured.get('body') or '{}')
    check('Web3Forms receives all fields', body.get('access_key') == 'test-key' and body.get('company') == 'Glow Studio' and body.get('volume') == '20–50', str(body))
    check('success state shown', page.is_visible('#formSuccess'))
    page.screenshot(path=f'{OUT}\\form_success.png')
    page.close()

    # ------------------------------------------------------------ mobile
    page = browser.new_page(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
    page.on('pageerror', lambda e: issues.append(f'mobile pageerror: {e}'))
    page.goto(URL, wait_until='networkidle')
    overflow = page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1")
    check('mobile: no horizontal overflow', not overflow, str(page.evaluate("document.documentElement.scrollWidth")))
    page.tap('#navToggle'); page.wait_for_timeout(400)
    check('mobile: menu opens on single tap', page.evaluate("document.getElementById('navLinks').classList.contains('is-open')") and page.is_visible('#navLinks a[href="#services"]'))
    page.tap('#navLinks a[href="#services"]'); page.wait_for_timeout(900)
    check('mobile: menu closes after link tap', not page.evaluate("document.getElementById('navLinks').classList.contains('is-open')"))
    nav_btn = page.evaluate("getComputedStyle(document.querySelector('.nav__actions .btn--nav')).display")
    check('mobile: squashed nav button hidden', nav_btn == 'none', nav_btn)
    page.evaluate("document.getElementById('what').scrollIntoView({behavior:'instant'})"); page.wait_for_timeout(500)
    wa_btn = page.evaluate("(() => { const b = document.querySelector('.floating-cta__wa'); const r = b.getBoundingClientRect(); return {shown: getComputedStyle(b).display !== 'none', href: b.href, w: Math.round(r.width)}; })()")
    check('mobile: floating WhatsApp shortcut shown with number', wa_btn['shown'] and '601160547134' in wa_btn['href'] and wa_btn['w'] > 80, str(wa_btn))
    gold_lines = page.evaluate("(() => { const b = document.querySelector('.floating-cta .btn--gold'); return Math.round(b.getBoundingClientRect().height); })()")
    check('mobile: floating CTA label fits on one line', gold_lines <= 56, str(gold_lines))
    bar_right = page.evaluate("Math.round(Math.max(...[...document.querySelectorAll('.floating-cta .btn')].map(b => b.getBoundingClientRect().right)))")
    check('mobile: floating buttons stay inside screen margins', bar_right <= 390 - 12, str(bar_right))
    scroll_through(page)
    page.screenshot(path=f'{OUT}\\full_mobile.png', full_page=True)
    page.close()

    # ------------------------------------------------------------ tablet
    page = browser.new_page(viewport={'width': 900, 'height': 1100})
    page.goto(URL, wait_until='networkidle')
    check('tablet: no horizontal overflow', not page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1"))
    scroll_through(page)
    page.screenshot(path=f'{OUT}\\full_tablet.png', full_page=True)
    page.close()

    browser.close()

for r in results:
    print(f'{r[0]}  {r[1]}' + (f'  -> {r[2]}' if r[2] and r[0] == 'FAIL' else ''))
print('\nISSUES:', json.dumps(sorted(set(issues)), indent=1) if issues else 'none')
print(f"\n{sum(r[0]=='PASS' for r in results)}/{len(results)} passed")
sys.exit(0 if all(r[0] == 'PASS' for r in results) else 1)
