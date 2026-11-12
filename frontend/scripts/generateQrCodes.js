// frontend/scripts/generateQrCodes.js
import fs from 'fs';
import path from 'path';
import QRCode from 'qrcode';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Target output directory: /sample_data/qr/
const outDir = path.resolve(__dirname, '../../sample_data/qr');
if (!fs.existsSync(outDir)) {
  fs.mkdirSync(outDir, { recursive: true });
}

const targets = [
  {
    fileName: 'safe_retail_qr.png',
    payload: 'upi://pay?pa=shop@okaxis&pn=Ram Store&am=150&cu=INR&tn=groceries',
    title: 'Safe Retail UPI QR (₹150)'
  },
  {
    fileName: 'malicious_collect_mismatch_qr.png',
    payload: 'upi://pay?pa=refund-agent99@fakebank&pn=VIP Support&am=45000&cu=INR&tn=refund-collect',
    title: 'Malicious High-Amount Collect Mismatch (₹45,000)'
  },
  {
    fileName: 'phishing_link_qr.png',
    payload: 'http://paytm-cashback-update.xyz/verify?id=555',
    title: 'Embedded Phishing Link QR'
  }
];

async function generate() {
  console.log(`Generating QR code images into ${outDir}...`);
  for (const item of targets) {
    const filePath = path.join(outDir, item.fileName);
    await QRCode.toFile(filePath, item.payload, {
      width: 400,
      margin: 2,
      color: {
        dark: '#000000',
        light: '#FFFFFF'
      }
    });
    console.log(`✓ Created: ${item.fileName} (${item.title})`);
  }
  console.log('All sample QR images successfully generated!');
}

generate().catch(err => {
  console.error('QR generation failed:', err);
  process.exit(1);
});

