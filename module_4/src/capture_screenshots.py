"""Capture actual CLI output and a screenshot of the live Flask page."""
from pathlib import Path
import html
import subprocess
import sys
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent

def capture(base_url='http://127.0.0.1:5000'):
    folder = ROOT / 'screenshots'
    folder.mkdir(exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel='chrome', headless=True)
        page = browser.new_page(viewport={'width': 1400, 'height': 1100}, device_scale_factor=1)
        for name, script in [('raw_sql', 'query_data.py'), ('orm', 'orm_queries.py')]:
            output = subprocess.check_output([sys.executable, str(ROOT / script)], text=True, cwd=ROOT)
            (folder / f'{name}.txt').write_text(output, encoding='utf-8')
            page.set_content('<html><body style="margin:32px;background:#101a23;color:#e6eff5;">'
                             '<h2 style="font:20px monospace">Captured console output: python ' + script + '</h2>'
                             '<pre style="font:15px/1.6 monospace;white-space:pre-wrap">' + html.escape(output) + '</pre></body></html>')
            page.screenshot(path=str(folder / f'{name}.png'), full_page=True)
        page.goto(base_url, wait_until='networkidle')
        assert page.locator('article').count() == 11
        page.get_by_role('button', name='Update Analysis').click()
        page.wait_for_load_state('networkidle')
        assert page.locator('article').count() == 11
        page.screenshot(path=str(folder / 'flask.png'), full_page=True)
        browser.close()
    print('Captured console output and live Flask screenshot; Update Analysis browser check passed.')

if __name__ == '__main__':
    capture()
