import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { chromium } = require(require.resolve('playwright', { paths: process.env.NODE_PATH.split(':') }));

const args = process.argv.slice(2);
const url = args.shift();
if (!url) {
	console.error('Usage: shop-browse <url> [--links <href-substring>] [--json] [--text] [--wait <ms>]');
	process.exit(2);
}
const opt = { links: null, json: false, text: false, wait: 2000 };
while (args.length) {
	const a = args.shift();
	if (a === '--links') opt.links = args.shift() ?? '';
	else if (a === '--json') opt.json = true;
	else if (a === '--text') opt.text = true;
	else if (a === '--wait') opt.wait = Number(args.shift());
	else { console.error(`Unknown option: ${a}`); process.exit(2); }
}

const browser = await chromium.launch();
try {
	const ctx = await browser.newContext({
		locale: 'fi-FI',
		userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36',
	});
	const page = await ctx.newPage();
	const json = [];
	page.on('response', (r) => {
		if (/json/.test(r.headers()['content-type'] || '')) json.push({ status: r.status(), url: r.url() });
	});
	// Some shops never reach network idle (analytics, polling); fall back to what loaded.
	await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
	await page.waitForLoadState('networkidle', { timeout: 20000 }).catch(() => {});
	await page.waitForTimeout(opt.wait);

	const out = { url: page.url(), title: await page.title() };
	if (opt.links !== null) {
		const sub = opt.links;
		const links = await page.$$eval('a[href]', (as) => as.map((a) => ({ text: a.textContent.trim().replace(/\s+/g, ' ').slice(0, 120), href: a.href.split('#')[0] })));
		const seen = new Set();
		out.links = links.filter((l) => l.text && l.href.includes(sub) && !seen.has(l.href) && seen.add(l.href));
	}
	if (opt.json) out.json = json;
	if (opt.text) out.text = await page.evaluate(() => document.body.innerText);
	console.log(JSON.stringify(out));
} finally {
	await browser.close();
}
