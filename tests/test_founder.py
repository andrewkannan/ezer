"""Automated tests for Founder page (/founder)."""
import sys
import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = 'http://localhost:8765/founder.html'
URL_DIR = 'http://localhost:8765/founder/'

results = []
def check(name, ok, detail=''):
    results.append(('PASS' if ok else 'FAIL', name, detail))

with sync_playwright() as p:
    browser = p.chromium.launch(channel='msedge')
    page = browser.new_page(viewport={'width': 390, 'height': 844})
    res = page.goto(URL, wait_until='networkidle')
    check('founder page returns 200', res.status == 200, str(res.status))
    
    title = page.title()
    check('founder title has Kenisha & EZER', 'Kenisha' in title and 'EZER' in title, title)
    
    og_type = page.get_attribute('meta[property="og:type"]', 'content')
    check('og:type is profile', og_type == 'profile', og_type)
    
    og_img = page.get_attribute('meta[property="og:image"]', 'content')
    check('og:image is set', bool(og_img), og_img)

    check('founder name visible', page.is_visible('.founder-name') and 'Kenisha' in page.inner_text('.founder-name'))
    check('blinking status badge removed', not page.is_visible('.status-pill') and not page.is_visible('.status-dot'))
    check('direct call button present', page.is_visible('a[href^="tel:+601160547134"]'))
    
    wa_href = page.get_attribute('a[href*="wa.me/601160547134"]', 'href')
    check('whatsapp button has phone & greeting', '601160547134' in wa_href and 'scanned' in wa_href.lower(), wa_href)
    
    vcf_href = page.get_attribute('#saveContactBtn', 'href')
    check('vcard download link present', 'kenisha-ezer.vcf' in vcf_href, vcf_href)
    
    vcf_file = ROOT / 'assets' / 'kenisha-ezer.vcf'
    check('vcard file exists on disk', vcf_file.exists() and 'BEGIN:VCARD' in vcf_file.read_text(encoding='utf-8'))
    
    check('growth workflow card present', page.is_visible('.card--featured'))
    
    check('qr modal hidden initially', not page.is_visible('#qrModal.is-active'))
    page.click('#openQrBtn')
    page.wait_for_timeout(300)
    check('qr modal opens on click', page.is_visible('#qrModal.is-active'))
    
    qr_loaded = page.evaluate("() => { const img = document.querySelector('.qr-img'); return img && img.complete && img.naturalWidth > 0; }")
    check('qr code image is rendered', qr_loaded)
    
    page.click('#closeQrBtn')
    page.wait_for_timeout(200)
    check('qr modal closes on close button', not page.is_visible('#qrModal.is-active'))
    
    has_overflow = page.evaluate('document.documentElement.scrollWidth > window.innerWidth')
    check('no horizontal overflow on mobile', not has_overflow)
    
    res_dir = page.goto(URL_DIR, wait_until='networkidle')
    check('directory url /founder/ returns 200', res_dir.status == 200, str(res_dir.status))
    
    page.close()
    browser.close()

print('\n=== test_founder.py ===')
for r in results:
    print(f'{r[0]}  {r[1]}' + (f'  -> {r[2]}' if r[2] and r[0] == 'FAIL' else ''))
print(f'\n{sum(r[0]=="PASS" for r in results)}/{len(results)} passed')
sys.exit(0 if all(r[0] == 'PASS' for r in results) else 1)
