import { chromium } from 'playwright-core';
import { mkdirSync } from 'node:fs';

mkdirSync('../output/app_check_images', { recursive: true });
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe' });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 });
await page.goto('http://localhost:5173/products', { waitUntil: 'networkidle' });
await page.locator('input[placeholder="Search the collection…"]').fill('hoodie');
await page.screenshot({ path: '../output/app_check_images/catalogue-filter.png', fullPage: true });

await page.goto('http://localhost:5173/products/basic-hoodie-big-yale', { waitUntil: 'networkidle' });
await page.locator('.chat-toggle').click();
await page.locator('input[placeholder="Type a question…"]').fill('What sizes are in stock for this item?');
await page.locator('.chat-form button').click();
await page.waitForFunction(() => { const items = [...document.querySelectorAll('.chat-message.assistant')]; const last = items.at(-1); return !!last && !last.textContent?.includes('Thinking') && (last.textContent?.length ?? 0) > 10; }, null, { timeout: 90000 });
await page.waitForTimeout(1000);
await page.screenshot({ path: '../output/app_check_images/inventory.png', fullPage: true });

await page.goto('http://localhost:5173/', { waitUntil: 'networkidle' });
await page.locator('.chat-toggle').click();
await page.getByRole('button', { name: 'Show me hoodies' }).click();
await page.locator('.dynamic-results').waitFor({ state: 'visible', timeout: 90000 });
await page.waitForTimeout(1000);
await page.screenshot({ path: '../output/app_check_images/dynamic-search.png', fullPage: true });
await browser.close();
