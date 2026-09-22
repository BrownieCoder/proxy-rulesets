// Optional real-browser QA. Requires Playwright; no build or frontend framework.
'use strict';
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const path = require('node:path');
const os = require('node:os');
const {pathToFileURL} = require('node:url');
(async () => {
  const options = {headless: true};
  if (process.env.BROWSER_EXECUTABLE_PATH) options.executablePath = process.env.BROWSER_EXECUTABLE_PATH;
  const browser = await chromium.launch(options);
  try {
    const page = await browser.newPage({viewport: {width:1440, height:1000}});
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    const entry = pathToFileURL(path.resolve(__dirname, '../install/index.html')).href;
    await page.goto(entry + '?service=openai&client=shadowrocket');
    const data = await page.evaluate(() => window.INSTALL_CATALOG);
    assert.equal(await page.locator('.service-card').count(), data.services.length);
    for (const service of data.services) {
      await page.locator(`[data-service="${service.id}"]`).click();
      for (const client of data.clients) {
        await page.locator(`[data-client="${client.id}"]`).click();
        assert.equal(await page.locator('#fallback-steps li').count(), 3);
        if (client.mode === 'module') {
          const ready = Boolean(service.module && service.module.published);
          assert.equal(await page.locator('a[href^="shadowrocket:"]').count(), ready ? 1 : 0);
          if (!ready) assert.equal(await page.locator('#install-actions button').count(), 0);
        } else {
          assert.equal(await page.getByRole('button', {name:'复制规则集链接', exact:true}).count(), 1);
          assert.match(await page.locator('#format-warning').textContent(), /不是完整配置或订阅/);
        }
      }
    }
    await page.locator('#service-search').fill('ChatGPT');
    assert.equal(await page.locator('.service-card').count(), 1);
    await page.locator('[data-service="openai"]').click();
    await page.locator('[data-client="clash-verge"]').click();
    await page.evaluate(() => Object.defineProperty(navigator, 'clipboard', {value:undefined, configurable:true}));
    await page.getByRole('button', {name:'复制规则集链接', exact:true}).click();
    assert.equal(await page.locator('#copy-url').inputValue(), data.services.find(s => s.id === 'openai').rawUrl);
    assert.equal(await page.locator('#copy-fallback').isVisible(), true);
    // Browser reads the actual generated guide rather than downloading Markdown.
    const guide = await page.locator('#install-actions a').getAttribute('href');
    const docs = await browser.newPage();
    await docs.goto(guide);
    assert.match(await docs.locator('h1').textContent(), /现有 Clash/);
    await docs.close();
    await page.locator('#service-search').fill('Apple Intelligence');
    assert.equal(await page.locator('.service-card').count(), 1);
    await page.locator('[data-service="siri-ai"]').click();
    await page.locator('#service-search').fill('');
    await page.locator('[data-client="shadowrocket"]').click();
    for (const width of [320,390,760,768,1024,1440]) {
      await page.setViewportSize({width, height:900});
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, `overflow ${width}`);
    }
    await page.screenshot({path:path.join(os.tmpdir(),'proxy-install-desktop.png'),fullPage:true});
    await page.setViewportSize({width:390,height:844});
    await page.screenshot({path:path.join(os.tmpdir(),'proxy-install-mobile.png'),fullPage:true});
    await page.locator('#service-search').fill('not-found-service');
    assert.equal(await page.locator('#empty-state').isVisible(), true);
    await page.locator('#clear-search').click();
    // Simulate publication only in memory; never activate the external scheme.
    await page.evaluate(() => { window.INSTALL_CATALOG.services.find(s => s.module).module.published = true; });
    const moduleService = data.services.find(s => s.module);
    await page.locator(`[data-service="${moduleService.id}"]`).click();
    assert.equal(await page.locator('a[href^="shadowrocket:"]').count(), 1);
    assert.deepEqual(errors, []);
    console.log(`PASS browser: ${data.services.length} services × ${data.clients.length} clients, copy fallback, HTML guide, aliases, publication gates, 6 widths, no page errors`);
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
