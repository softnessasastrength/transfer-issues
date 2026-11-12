/* Optional desktop acceptance test. Requires playwright and a browser install.
 * Run the server first. ATLAS_URL, ATLAS_DATE, CHROMIUM_PATH are optional.
 * Test data below is synthetic. A new isolated browser profile is used.
 */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
(async () => {
  const options = { headless: true };
  if (process.env.CHROMIUM_PATH) options.executablePath = process.env.CHROMIUM_PATH;
  const browser = await chromium.launch(options);
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(process.env.ATLAS_URL || 'http://127.0.0.1:8000');
    await page.locator('#loading').waitFor({ state: 'hidden' });
    await page.fill('#date', process.env.ATLAS_DATE || '2026-11-12');
    await page.locator('#date').dispatchEvent('change');
    await page.click('#browseTab');
    await page.fill('#routeSearch', '905');
    await page.locator('.routeButton').first().click();
    await page.locator('#results select').waitFor();
    await page.locator('#results select').selectOption({ index: 1 });
    await page.locator('#results table').waitFor();
    await page.click('#planTab');
    await page.fill('#from', 'hartford:6');
    await page.fill('#to', 'hartford:9');
    await page.locator('summary').click();
    await page.fill('#radius', '0');
    await page.click('#plan');
    await page.getByRole('heading', { name: 'Return journey' }).waitFor({ timeout: 120000 });
    await page.click('#bookmark');
    await page.getByRole('button', { name: 'My discoveries' }).click();
    await page.fill('#noteTitle', 'Regression note');
    await page.fill('#noteText', '<b>literal text</b>');
    await page.click('#saveNote');
    await page.reload();
    await page.locator('#loading').waitFor({ state: 'hidden' });
    await page.getByRole('button', { name: 'My discoveries' }).click();
    assert.match(await page.locator('#notes').innerText(), /<b>literal text<\/b>/);
    assert.match(await page.locator('#bookmarks').innerText(), /hartford:6/);
    const downloadPromise = page.waitForEvent('download');
    await page.click('#export');
    const download = await downloadPromise;
    await page.setInputFiles('#importFile', await download.path());
    await page.waitForFunction(() => document.querySelectorAll('#notes .note').length === 2);
    await page.getByRole('button', { name: 'Data & sources', exact: true }).click();
    assert.ok(await page.locator('#sourceCards .card').count() >= 5);
    assert.deepEqual(errors, []);
    console.log('Desktop browser smoke test passed.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
