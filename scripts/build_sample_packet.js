// Prints the sample financial packages to PDF (board: 10 sections; homeowner: first 4).
// Usage: start the app (flask --app run run), then: node scripts/build_sample_packet.js [baseUrl]
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const base = process.argv[2] || 'http://127.0.0.1:5000';
  const b = await chromium.launch();
  for (const [audience, file] of [['board', 'hey-sample-financial-packet.pdf'], ['homeowner', 'hey-sample-homeowner-package.pdf']]) {
    const out = path.resolve(__dirname, '..', 'app', 'static', 'docs', file);
    const p = await b.newPage();
    await p.goto(base + '/sample-packet?audience=' + audience, { waitUntil: 'networkidle' });
    await p.emulateMedia({ media: 'print' });
    await p.pdf({ path: out, format: 'Letter', printBackground: true, preferCSSPageSize: true });
    await p.close();
    console.log('wrote', out);
  }
  await b.close();
})().catch((e) => { console.error(e); process.exit(1); });
