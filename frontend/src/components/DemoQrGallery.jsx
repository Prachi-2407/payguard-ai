// src/components/DemoQrGallery.jsx
import React, { useState } from 'react';
import { QrCode, ExternalLink, AlertTriangle, ShieldCheck, Download } from 'lucide-react';
import QRCode from 'qrcode';

const DEMO_QRS = [
  {
    id: 'safe-upi',
    title: 'Safe Retail UPI QR',
    expected: 'LOW',
    amount: '₹150',
    description: 'Legitimate grocery merchant handle with normal retail amount.',
    payload: 'upi://pay?pa=shop@okaxis&pn=Ram Store&am=150&cu=INR&tn=groceries'
  },
  {
    id: 'malicious-collect',
    title: 'Deceptive Collect Fraud QR',
    expected: 'HIGH',
    amount: '₹45,000',
    description: 'Payee name mismatch, excessive amount, and collect-money deception.',
    payload: 'upi://pay?pa=refund-agent99@fakebank&pn=VIP Support&am=45000&cu=INR&tn=refund-collect'
  },
  {
    id: 'phishing-link',
    title: 'Phishing URL in QR Code',
    expected: 'HIGH',
    amount: 'N/A',
    description: 'QR encoding an external deceptive phishing website instead of UPI.',
    payload: 'http://paytm-cashback-update.xyz/verify?id=555'
  }
];

export function DemoQrGallery({ onSelectPayload }) {
  const [qrImages, setQrImages] = useState({});

  React.useEffect(() => {
    DEMO_QRS.forEach(async (item) => {
      try {
        const url = await QRCode.toDataURL(item.payload, {
          width: 200,
          margin: 2,
          color: {
            dark: '#0F172A',
            light: '#FFFFFF',
          },
        });
        setQrImages(prev => ({ ...prev, [item.id]: url }));
      } catch (err) {}
    });
  }, []);

  return (
    <div className="p-6 rounded-3xl bg-slate-100/70 dark:bg-slate-900/40 border border-slate-200 dark:border-slate-800">
      <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2">
        <QrCode className="w-4 h-4 text-blue-500" />
        <span>Demo QR Code Targets (Interactive Scanner Feed)</span>
      </div>
      <p className="text-xs text-slate-600 dark:text-slate-400 mb-5">
        Scan these targets with your mobile phone / webcam, or click 'Send to Scanner' to immediately inspect the payload.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {DEMO_QRS.map((item) => (
          <div
            key={item.id}
            className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col items-center text-center justify-between"
          >
            <div className="w-full">
              <div className="flex items-center justify-between mb-2">
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                  item.expected === 'HIGH' 
                    ? 'bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-300 border-rose-300' 
                    : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300 border-emerald-300'
                }`}>
                  {item.expected} RISK
                </span>
                <span className="text-[11px] font-bold text-slate-500">
                  {item.amount}
                </span>
              </div>
              <h4 className="text-sm font-bold text-slate-900 dark:text-white mb-1">
                {item.title}
              </h4>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 line-clamp-2 mb-3">
                {item.description}
              </p>
            </div>

            {/* QR Image */}
            <div className="p-2 bg-white rounded-xl shadow-xs border border-slate-100 mb-3">
              {qrImages[item.id] ? (
                <img
                  src={qrImages[item.id]}
                  alt={item.title}
                  className="w-36 h-36 object-contain"
                />
              ) : (
                <div className="w-36 h-36 bg-slate-100 animate-pulse rounded" />
              )}
            </div>

            <button
              onClick={() => onSelectPayload && onSelectPayload(item.payload)}
              className="w-full py-2 px-3 rounded-xl bg-blue-50 dark:bg-blue-950/60 hover:bg-blue-100 dark:hover:bg-blue-900/60 text-blue-600 dark:text-blue-400 text-xs font-semibold transition-colors flex items-center justify-center space-x-1"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              <span>Send to Scanner</span>
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

