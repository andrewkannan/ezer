"""SEO / social / attribution / consent checks for the EZER site (local server on :8765)."""
import json, sys
import os, pathlib
BASE_URL = os.environ.get("EZER_TEST_URL", "http://localhost:8765/")
OUT_DIR = pathlib.Path(__file__).parent / "output"
OUT_DIR.mkdir(exist_ok=True)
from playwright.sync_api import sync_playwright

BASE = BASE_URL
SITE = 'https://www.ezer-solution.com/'
results = []
def check(name, ok, detail=''):
    results.append(('PASS' if ok else 'FAIL', name, detail))

with sync_playwright() as p:
    b = p.chromium.launch(channel='msedge')
    ctx = b.new_context(viewport={'width': 1280, 'height': 900})
    ctx.add_init_script("document.addEventListener('DOMContentLoaded',()=>{const s=document.createElement('style');s.textContent='html{scroll-behavior:auto!important}';document.head.appendChild(s)})")
    ctx.route('https://wa.me/**', lambda r: r.fulfill(status=200, body='stub'))
    page = ctx.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)

    # ---------- static files
    for path, ctype in (('robots.txt', 'text'), ('sitemap.xml', 'xml'), ('site.webmanifest', ''), ('favicon.svg', 'svg'),
                        ('assets/og-image.jpg', 'image'), ('assets/apple-touch-icon.png', 'image'), ('assets/favicon-32.png', 'image'),
                        ('assets/icon-192.png', 'image'), ('assets/icon-512.png', 'image'), ('404.html', 'html')):
        r = page.request.get(BASE + path)
        check(f'{path} served', r.status == 200 and len(r.body()) > 0, str(r.status))
    check('robots blocks admin + lists sitemap', 'Disallow: /admin.html' in page.request.get(BASE + 'robots.txt').text() and SITE + 'sitemap.xml' in page.request.get(BASE + 'robots.txt').text())
    og_size = len(page.request.get(BASE + 'assets/og-image.jpg').body())
    check('og image under 300 KB (WhatsApp limit)', og_size < 300_000, str(og_size))
    json.loads(page.request.get(BASE + 'site.webmanifest').text())
    check('manifest is valid JSON', True)

    page.goto(BASE + 'index.html', wait_until='networkidle')
    meta = lambda sel: page.evaluate(f"document.querySelector('{sel}')?.getAttribute('content') || document.querySelector('{sel}')?.getAttribute('href') || ''")
    title = page.title()
    desc = meta('meta[name=description]')
    check('title 30-65 chars', 30 <= len(title) <= 65, f'{len(title)}: {title}')
    check('description 70-160 chars', 70 <= len(desc) <= 160, f'{len(desc)}')
    check('canonical is www domain', meta('link[rel=canonical]') == SITE)
    for prop in ('og:title', 'og:description', 'og:url', 'og:site_name', 'og:image', 'og:image:width', 'og:image:height', 'og:image:alt'):
        check(f'{prop} present', bool(meta(f'meta[property="{prop}"]')))
    check('og:image absolute https', meta('meta[property="og:image"]').startswith(SITE))
    check('og description short enough to show fully (<=100)', len(meta('meta[property="og:description"]')) <= 100)
    check('twitter large card', meta('meta[name="twitter:card"]') == 'summary_large_image')
    check('apple-touch-icon + manifest linked', bool(meta('link[rel=apple-touch-icon]')) and bool(meta('link[rel=manifest]')))
    check('exactly one h1', page.evaluate("document.querySelectorAll('h1').length") == 1)
    check('all images have alt', page.evaluate("[...document.images].every(i => i.hasAttribute('alt'))"))

    # og image dimensions
    dims = page.evaluate("""new Promise(r => { const i = new Image(); i.onload = () => r([i.naturalWidth, i.naturalHeight]); i.src = 'assets/og-image.jpg'; })""")
    check('og image is 1200x630', dims == [1200, 630], str(dims))

    # ---------- structured data
    ld = json.loads(page.evaluate("document.querySelector('script[type=\"application/ld+json\"]').textContent"))
    types = [n['@type'] for n in ld['@graph']]
    check('JSON-LD has Organization, ProfessionalService, WebSite, FAQPage', all(t in types for t in ('Organization', 'ProfessionalService', 'WebSite', 'FAQPage')), str(types))
    svc = next(n for n in ld['@graph'] if n['@type'] == 'ProfessionalService')
    prices = sorted(int(o['price']) for o in svc['hasOfferCatalog']['itemListElement'])
    check('offers match plan prices', prices == [300, 600, 1200, 2000], str(prices))
    faq_ld = [q['name'] for q in next(n for n in ld['@graph'] if n['@type'] == 'FAQPage')['mainEntity']]
    faq_dom = page.evaluate("[...document.querySelectorAll('#faq summary')].map(s => s.textContent.trim())")
    check('FAQ schema matches visible FAQ', faq_ld == faq_dom, f'{len(faq_ld)} vs {len(faq_dom)}')

    # ---------- performance guard: featured border only animates on screen
    check('featured border paused off screen', not page.evaluate("document.querySelector('.plan--featured').classList.contains('is-onscreen')"))
    page.evaluate("document.querySelector('.plan--featured').scrollIntoView({behavior:'instant', block:'center'})"); page.wait_for_timeout(300)
    check('featured border runs on screen', page.evaluate("document.querySelector('.plan--featured').classList.contains('is-onscreen')"))
    check('no analytics consent bar without IDs', page.query_selector('.consent') is None)
    page.close()

    # ---------- UTM attribution -> WhatsApp + form payload + chosen plan
    page = ctx.new_page()
    page.add_init_script("localStorage.setItem('ezer_admin_config', JSON.stringify({web3formsKey:'test-key'}))")
    captured = {}
    def handle(route):
        captured['body'] = route.request.post_data
        route.fulfill(status=200, content_type='application/json', body='{"success":true}')
    page.route('https://api.web3forms.com/submit', handle)
    page.goto(BASE + 'index.html?utm_source=instagram&utm_medium=bio&utm_campaign=oct-launch', wait_until='networkidle')
    wa = page.evaluate("document.querySelector('[data-wa]')?.href || ''")
    check('WhatsApp button mentions source', 'instagram' in wa, wa[:140])
    page.evaluate("document.getElementById('plan-engine-title').closest('.plan').querySelector('.plan-cta').click()")
    page.wait_for_timeout(400)
    check('plan click fills hidden plan field', page.input_value('#fPlan') == 'The Follow-Up Engine', page.input_value('#fPlan'))
    # navigate away and back: attribution should persist for the session
    page.goto(BASE + 'index.html', wait_until='networkidle')
    page.evaluate("document.getElementById('plan-engine-title').closest('.plan').querySelector('.plan-cta').click()")
    page.evaluate("document.getElementById('contact').scrollIntoView({behavior:'instant'})")
    page.fill('#fName', 'Aina Tan'); page.fill('#fEmail', 'aina@example.com'); page.click('#leadForm fieldset:not([hidden]) [data-next]')
    page.fill('#fCompany', 'Glow Studio'); page.fill('#fPhone', '0123456789'); page.select_option('#fIndustry', index=1); page.click('#leadForm fieldset:not([hidden]) [data-next]')
    page.locator('#leadForm fieldset:not([hidden]) input[name=volume]').first.check(force=True)
    page.locator('#leadForm fieldset:not([hidden]) input[name=challenge]').first.check(force=True)
    page.click('#leadForm button[type=submit]'); page.wait_for_timeout(600)
    body = json.loads(captured.get('body') or '{}')
    check('lead payload has source (persists across reload)', body.get('source') == 'instagram / bio / oct-launch', str(body.get('source')))
    check('lead payload has chosen plan', body.get('plan') == 'The Follow-Up Engine', str(body.get('plan')))
    page.close()

    # ---------- analytics consent: nothing loads before Accept
    page = ctx.new_page()
    hits = []
    page.route('https://www.googletagmanager.com/**', lambda r: (hits.append(r.request.url), r.fulfill(status=200, body='')))
    page.add_init_script("localStorage.setItem('ezer_admin_config', JSON.stringify({ga4Id:'G-TEST1234'}))")
    page.goto(BASE + 'index.html', wait_until='networkidle')
    check('consent bar shown when GA4 configured', page.is_visible('.consent'))
    check('no GA request before consent', not hits, str(hits))
    page.click('.consent [data-consent="yes"]'); page.wait_for_timeout(500)
    check('GA loads after Accept', any('G-TEST1234' in h for h in hits), str(hits))
    check('consent bar removed', page.query_selector('.consent') is None)
    page.close()

    page = ctx.new_page()
    page.add_init_script("localStorage.setItem('ezer_admin_config', JSON.stringify({ga4Id:'G-TEST1234'})); localStorage.setItem('ezer_analytics_consent','no')")
    hits.clear()
    page.route('https://www.googletagmanager.com/**', lambda r: (hits.append(r.request.url), r.fulfill(status=200, body='')))
    page.goto(BASE + 'index.html', wait_until='networkidle')
    check('declined: no bar, no GA', page.query_selector('.consent') is None and not hits)
    page.close()

    # ---------- 404 page and admin noindex
    page = ctx.new_page()
    page.goto(BASE + '404.html')
    check('404 page has homepage + pricing links', page.is_visible('a[href="/"]') and page.is_visible('a[href="/#packages"]'))
    page.goto(BASE + 'admin.html')
    check('admin is noindex', 'noindex' in (page.evaluate("document.querySelector('meta[name=robots]')?.content") or ''))
    page.close()
    b.close()

check('no console/page errors', not errors, str(errors[:3]))
for r in results:
    print(f'{r[0]}  {r[1]}' + (f'  -> {r[2]}' if r[2] and r[0] == 'FAIL' else ''))
print(f"\n{sum(r[0] == 'PASS' for r in results)}/{len(results)} passed")
sys.exit(0 if all(r[0] == 'PASS' for r in results) else 1)
