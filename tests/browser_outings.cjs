/* Focused Outings browser smoke. Run against the local Atlas server.
 * ATLAS_URL, CHROMIUM_PATH and NODE_PATH may be set for local installations.
 * Outing responses are synthetic; this checks UI behavior, not transit service.
 */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');

(async () => {
  const browser = await chromium.launch({
    headless: true,
    ...(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {}),
  });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    const errors = [];
    let phase = 'unknown';
    let lastHomeBy;
    page.on('pageerror', error => errors.push(error.message));
    await page.route('**/api/v1/outings?*', route => {
      const params = new URL(route.request().url()).searchParams;
      lastHomeBy = Number(params.get('home_by'));
      const base = { coverage: [], scheduled: true };
      let body;
      if (params.has('to')) {
        body = { ...base, status: 'unknown', destination: { id: 'hartford:9', name: 'SPRINGFIELD' },
          reason: { message: 'Fixture cannot certify the return.' } };
      } else if (phase === 'unknown') {
        body = { ...base, status: 'unknown', candidates: [], search: { complete: false, evaluated: 0, unevaluated_count: 0 },
          reason: { message: 'Fixture source is outside its service period.' } };
      } else {
        body = { ...base, status: 'scheduled', counts: { verified: 1, ruled_out: 0, unknown: 0 },
          home_by: lastHomeBy, minimum_stay: 7200, outbound_budget: 3600,
          search: { complete: true, evaluated: 1, unevaluated_count: 0 },
          candidates: [{ status: 'verified', destination: { id: 'hartford:9', name: 'SPRINGFIELD' },
            outbound: { arrival: 36000 }, home_arrival: 60000 }] };
      }
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });
    });
    await page.goto(process.env.ATLAS_URL || 'http://127.0.0.1:8000');
    await page.locator('#loading').waitFor({ state: 'hidden' });
    await page.click('#outingTab');
    await page.fill('#outingFrom', 'hartford:6');
    await page.click('#browseOutings');
    await page.getByRole('heading', { name: 'Outing search cannot be determined' }).waitFor();
    assert.match(await page.locator('#results').innerText(), /outside its service period/);
    assert.equal(await page.locator('#errorNotice').isVisible(), false);

    phase = 'scheduled';
    await page.check('#outingNextDay');
    await page.click('#browseOutings');
    await page.getByRole('heading', { name: '1 verified outing stops' }).waitFor();
    assert.equal(lastHomeBy, 165600);
    assert.match(await page.locator('.outingCandidate').innerText(), /Verified round trip/);
    const pin = page.locator('.outingMapIcon.verified').first();
    assert.match(await pin.getAttribute('aria-label'), /SPRINGFIELD: Verified round trip/);
    await pin.focus();
    await pin.press('Enter');
    await page.getByRole('heading', { name: 'SPRINGFIELD' }).waitFor();
    assert.match(await page.locator('#results').innerText(), /Fixture cannot certify the return/);
    assert.match(await page.locator('#outingTo').inputValue(), /SPRINGFIELD/);
    assert.deepEqual(errors, []);
    console.log('Outings browser smoke test passed.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
