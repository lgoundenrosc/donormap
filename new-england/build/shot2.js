const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
const site = process.argv[2], out = process.argv[3];
const head = '<!doctype html><html><head><meta charset=utf8><meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover"><style>:root{color-scheme:light}body{margin:0;font:14px sans-serif}[hidden]:not([hidden=until-found i]){display:none!important}</style></head><body>';
async function serve(p) {
  await p.route('http://page.test/**', r => {
    const n = new URL(r.request().url()).pathname.slice(1) || 'index.html';
    const f = path.join(site, n);
    if (!fs.existsSync(f)) return r.fulfill({ status: 404, body: 'missing' });
    let body = fs.readFileSync(f);
    if (n === 'index.html') body = head + body.toString() + '</body></html>';
    r.fulfill({ status: 200, contentType: n.endsWith('.json') ? 'application/json' : 'text/html', body });
  });
}
(async () => {
  const b = await chromium.launch(); const errs = [];
  const p = await b.newPage({ viewport: { width: 1400, height: 1000 } });
  p.on('pageerror', e => errs.push(String(e))); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await serve(p);
  await p.goto('http://page.test/index.html'); await p.waitForTimeout(1500);
  await p.screenshot({ path: out + '/x-all.png' });
  await p.click('#tab-ne'); await p.waitForTimeout(1500);
  const info = await p.evaluate(() => [location.hash, !!document.getElementById('ne-host').shadowRoot, document.getElementById('panel-all').hidden]);
  await p.screenshot({ path: out + '/x-ne.png' });
  await p.click('.stc[data-st="CT"]'); await p.waitForTimeout(400);
  const tw = await p.$('#side [data-town]'); if (tw) { await tw.click(); await p.waitForTimeout(300); }
  const pp = await p.$('#side [data-id]'); if (pp) { await pp.click(); await p.waitForTimeout(300); }
  await (await p.$('.geo-wrap')).screenshot({ path: out + '/x-ne-person.png' });
  await p.click('#tab-all'); await p.waitForTimeout(400);
  const back = await p.evaluate(() => [location.hash, document.getElementById('panel-ne').hidden]);
  // direct link
  const q = await b.newPage({ viewport: { width: 1400, height: 1000 }, colorScheme: 'dark' });
  q.on('pageerror', e => errs.push('q:' + e)); await serve(q);
  await q.goto('http://page.test/index.html#new-england'); await q.waitForTimeout(1500);
  await q.screenshot({ path: out + '/x-ne-dark.png' });
  const m = await b.newPage({ viewport: { width: 390, height: 844 } });
  m.on('pageerror', e => errs.push('m:' + e)); await serve(m);
  await m.goto('http://page.test/index.html#new-england'); await m.waitForTimeout(1500);
  const sw = await m.evaluate(() => [document.documentElement.scrollWidth, innerWidth]);
  await m.screenshot({ path: out + '/x-ne-m.png' });
  console.log('errors', JSON.stringify(errs), 'after NE click', JSON.stringify(info), 'after All click', JSON.stringify(back), 'mobile', JSON.stringify(sw));
  await b.close();
})();
