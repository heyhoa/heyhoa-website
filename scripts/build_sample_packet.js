// Prints /sample-packet to app/static/docs/hey-sample-financial-packet.pdf.
// Usage: start the app (flask --app run run), then: node scripts/build_sample_packet.js [baseUrl]
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const base = process.argv[2] || 'http://127.0.0.1:5000';
  const out = path.resolve(__dirname, '..', 'app', 'static', 'docs', 'hey-sample-financial-packet.pdf');
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto(base + '/sample-packet', { waitUntil: 'networkidle' });
  await p.emulateMedia({ media: 'print' });
  await p.pdf({ path: out, format: 'Letter', printBackground: true, preferCSSPageSize: true });
  await b.close();
  console.log('wrote', out);
})().catch((e) => { console.error(e); process.exit(1); });
