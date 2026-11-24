// Render the page in headless Chromium, serving files from the site folder
// through request interception (no local server needed).
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const site = process.argv[2];
const out = process.argv[3];
const head = '<!doctype html><html><head><meta charset=utf8><meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover">' +
  '<style>:root{color-scheme:light}body{margin:0;font:14px sans-serif}[hidden]{display:none!important}</style></head><body>';

async function serve(page) {
  await page.route('http://page.test/**', route => {
    const name = new URL(route.request().url()).pathname.slice(1) || 'index.html';
    const file = path.join(site, name);
    if (!fs.existsSync(file)) return route.fulfill({ status: 404, body: 'missing' });
    let body = fs.readFileSync(file);
    let type = name.endsWith('.json') ? 'application/json' : 'text/html';
    if (name === 'index.html') body = head + body.toString() + '</body></html>';
    return route.fulfill({ status: 200, contentType: type, body });
  });
}

(async () => {
  const b = await chromium.launch();
  const errs = [];
  const p = await b.newPage({ viewport: { width: 1400, height: 1000 } });
  p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  p.on('pageerror', e => errs.push(String(e)));
  await serve(p);
  await p.goto('http://page.test/index.html');
  await p.waitForTimeout(1200);
  await (await p.$('.geo-wrap')).screenshot({ path: out + '/d1.png' });
  await p.click('.stc[data-st="CT"]'); await p.waitForTimeout(400);
  await p.screenshot({ path: out + '/d2.png' });
  await p.click('#z-ff'); await p.waitForTimeout(400);
  await (await p.$('.geo-wrap')).screenshot({ path: out + '/d3.png' });
  const tw = await p.$('#side [data-town]'); if (tw) { await tw.click(); await p.waitForTimeout(300); }
  const pp = await p.$('#side [data-id]'); if (pp) { await pp.click(); await p.waitForTimeout(300); }
  await (await p.$('.geo-wrap')).screenshot({ path: out + '/d4.png' });
  await p.click('#z-all'); await p.waitForTimeout(200);
  await p.click('#z-bos'); await p.waitForTimeout(300);
  await (await p.$('.geo-wrap')).screenshot({ path: out + '/d5.png' });

  const m = await b.newPage({ viewport: { width: 390, height: 844 } });
  m.on('pageerror', e => errs.push('m:' + e));
  await serve(m);
  await m.goto('http://page.test/index.html'); await m.waitForTimeout(1200);
  const sw = await m.evaluate(() => [document.documentElement.scrollWidth, window.innerWidth]);
  await m.screenshot({ path: out + '/m1.png' });
  await m.emulateMedia({ colorScheme: 'dark' }); await m.waitForTimeout(200);
  await m.evaluate(() => window.scrollTo(0, 760)); await m.waitForTimeout(200);
  await m.screenshot({ path: out + '/m2.png' });
  console.log('errors', JSON.stringify(errs), 'mobile scrollWidth', JSON.stringify(sw));
  await b.close();
})();
