// src/components/ScanQrTab.jsx
import React, { useRef, useState } from 'react';
import { 
  QrCode, 
  Camera, 
  Upload, 
  Sparkles, 
  Loader2, 
  AlertCircle, 
  CheckCircle2, 
  X, 
  DollarSign, 
  User, 
  FileText 
} from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import { useQrScanner } from '../hooks/useQrScanner';
import { useAnalyze } from '../hooks/useAnalyze';
import { analyzeQr } from '../api/client';
import { ResultCard } from './ResultCard';

const SAMPLE_QRS = [
  { 
    label: 'Malicious: Urgent Collect Trap (₹45,000)', 
    payload: 'upi://pay?pa=refund-agent99@fakebank&pn=VIP Support&am=45000&cu=INR&tn=refund-collect' 
  },
  { 
    label: 'Malicious: Embedded Phishing Link', 
    payload: 'http://paytm-cashback-update.xyz/verify?id=555' 
  },
  { 
    label: 'Safe: Merchant Grocery Retail (₹150)', 
    payload: 'upi://pay?pa=shop@okaxis&pn=Ram Store&am=150&cu=INR&tn=groceries' 
  },
];

export function ScanQrTab({ onHighRiskDetected }) {
  const { t } = useLanguage();
  const fileInputRef = useRef(null);
  const [manualText, setManualText] = useState('');

  const {
    isScanning,
    cameraError,
    decodedData,
    parsedPayload,
    videoRef,
    startCamera,
    stopCamera,
    scanImageFile,
    setManualPayload,
    resetScanner,
  } = useQrScanner();

  const { loading, error, result, execute } = useAnalyze(analyzeQr);

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (file) {
      try {
        await scanImageFile(file);
      } catch (err) {
        // Error captured in cameraError
      }
    }
  };

  const handleAnalyzeDecoded = async () => {
    if (!decodedData) return;
    try {
      const res = await execute({ qr_payload: decodedData });
      if (res && res.risk_level === 'HIGH') {
        onHighRiskDetected && onHighRiskDetected(res);
      }
    } catch (e) {}
  };

  const handleApplySample = (payload) => {
    setManualPayload(payload);
    setManualText(payload);
  };

  return (
    <div className="space-y-6">
      {/* Intro */}
      <div>
        <h2 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center space-x-2">
          <QrCode className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          <span>{t('checkQrTitle')}</span>
        </h2>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
          {t('checkQrDesc')}
        </p>
      </div>

      {/* Camera / Upload Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Webcam Scanner Card */}
        <div className="p-6 rounded-2xl bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center space-x-1.5">
                <Camera className="w-4 h-4 text-blue-500" />
                <span>Live Video Scanner</span>
              </span>
              {isScanning && (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold bg-rose-500 text-white animate-pulse">
                  SCANNING
                </span>
              )}
            </div>

            <div className="relative w-full aspect-video rounded-xl overflow-hidden bg-slate-950 flex items-center justify-center border border-slate-800">
              <video
                ref={videoRef}
                className={`w-full h-full object-cover ${!isScanning ? 'hidden' : 'block'}`}
              />

              {/* Scanning visual overlay with laser */}
              {isScanning && (
                <div className="absolute inset-0 border-2 border-blue-500/80 rounded-xl pointer-events-none flex flex-col justify-center">
                  <div className="w-full h-0.5 bg-gradient-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_8px_#38bdf8] animate-pulse" />
                </div>
              )}

              {!isScanning && (
                <div className="text-center p-6 text-slate-500">
                  <Camera className="w-12 h-12 mx-auto mb-2 opacity-30" />
                  <p className="text-xs">Camera is currently idle.</p>
                </div>
              )}
            </div>
          </div>

          <div className="mt-4 flex items-center gap-2">
            {!isScanning ? (
              <button
                type="button"
                onClick={startCamera}
                className="w-full py-2.5 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-all shadow-sm flex items-center justify-center space-x-2"
              >
                <Camera className="w-4 h-4" />
                <span>{t('openCamera')}</span>
              </button>
            ) : (
              <button
                type="button"
                onClick={stopCamera}
                className="w-full py-2.5 px-4 rounded-xl bg-slate-700 hover:bg-slate-600 text-white text-xs font-bold transition-all flex items-center justify-center space-x-2"
              >
                <X className="w-4 h-4" />
                <span>{t('stopCamera')}</span>
              </button>
            )}
          </div>
        </div>

        {/* Upload Image & Samples Card */}
        <div className="p-6 rounded-2xl bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col justify-between">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 block mb-4 flex items-center space-x-1.5">
              <Upload className="w-4 h-4 text-blue-500" />
              <span>{t('uploadQr')}</span>
            </span>

            {/* Hidden file input */}
            <input
              type="file"
              ref={fileInputRef}
              accept="image/*"
              onChange={handleFileUpload}
              className="hidden"
            />

            {/* Dropzone button */}
            <div
              onClick={() => fileInputRef.current?.click()}
              className="w-full aspect-video rounded-xl border-2 border-dashed border-slate-300 dark:border-slate-700 hover:border-blue-500 dark:hover:border-blue-400 bg-slate-50 dark:bg-slate-900/50 flex flex-col items-center justify-center cursor-pointer p-6 text-center transition-colors group"
            >
              <Upload className="w-10 h-10 text-slate-400 group-hover:text-blue-500 mb-2 transition-colors" />
              <p className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Click to browse or drop QR code image
              </p>
              <p className="text-[11px] text-slate-400 mt-1">PNG, JPG, WEBP formats supported</p>
            </div>
          </div>

          {/* Quick Samples */}
          <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800/80">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 block mb-2 flex items-center space-x-1">
              <Sparkles className="w-3.5 h-3.5 text-blue-500" />
              <span>{t('trySample')}:</span>
            </span>
            <div className="flex flex-col gap-1.5">
              {SAMPLE_QRS.map((sample, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleApplySample(sample.payload)}
                  className="text-left text-xs px-2.5 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800/90 text-slate-700 dark:text-slate-300 hover:bg-blue-50 dark:hover:bg-blue-950/60 hover:text-blue-600 dark:hover:text-blue-400 border border-slate-200 dark:border-slate-700 transition-colors truncate"
                >
                  {sample.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Camera / Image Error Display */}
      {cameraError && (
        <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{cameraError}</span>
        </div>
      )}

      {/* Decoded QR Payload Pre-Analysis Viewer */}
      {decodedData && (
        <div className="p-6 rounded-2xl bg-white dark:bg-[#111827] border-2 border-blue-500/40 shadow-lg shadow-blue-500/5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800 mb-4">
            <div className="flex items-center space-x-2 text-blue-600 dark:text-blue-400 font-bold text-sm">
              <CheckCircle2 className="w-4 h-4" />
              <span>{t('decodedPayload')}</span>
            </div>
            <button
              onClick={resetScanner}
              className="text-xs text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
            >
              Clear
            </button>
          </div>

          {/* Parsed visual elements BEFORE analysis */}
          {parsedPayload?.type === 'upi' ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
              <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                <span className="text-[11px] font-bold text-slate-500 dark:text-slate-400 block mb-1">
                  {t('payeeName')}
                </span>
                <span className="text-sm font-semibold text-slate-900 dark:text-white">
                  {parsedPayload.pn || 'Not specified'}
                </span>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                <span className="text-[11px] font-bold text-slate-500 dark:text-slate-400 block mb-1">
                  {t('payeeVpa')}
                </span>
                <span className="text-sm font-mono font-semibold text-blue-600 dark:text-blue-400">
                  {parsedPayload.pa}
                </span>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                <span className="text-[11px] font-bold text-slate-500 dark:text-slate-400 block mb-1">
                  {t('amount')}
                </span>
                <span className="text-sm font-bold text-slate-900 dark:text-white">
                  {parsedPayload.am ? `₹${parsedPayload.am} ${parsedPayload.cu}` : 'Open (Any amount)'}
                </span>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                <span className="text-[11px] font-bold text-slate-500 dark:text-slate-400 block mb-1">
                  {t('transactionNote')}
                </span>
                <span className="text-sm text-slate-700 dark:text-slate-300">
                  {parsedPayload.tn || 'No note'}
                </span>
              </div>
            </div>
          ) : (
            <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 mb-4">
              <span className="text-[11px] font-bold text-slate-500 dark:text-slate-400 block mb-1">
                Embedded Payload Content
              </span>
              <p className="text-xs font-mono break-all text-slate-800 dark:text-slate-200">
                {decodedData}
              </p>
            </div>
          )}

          {/* Trigger Analysis Button */}
          <div className="flex justify-end">
            <button
              onClick={handleAnalyzeDecoded}
              disabled={loading}
              data-testid="analyze-qr-btn"
              className="px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm shadow-md shadow-blue-500/20 transition-all flex items-center space-x-2 disabled:opacity-70"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>{t('analyzing')}</span>
                </>
              ) : (
                <span>{t('analyzeQrBtn')}</span>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Result Card */}
      {result && (
        <div className="animate-fade-in">
          <ResultCard result={result} />
        </div>
      )}
    </div>
  );
}

