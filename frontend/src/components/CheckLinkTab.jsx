// src/components/CheckLinkTab.jsx
import React, { useState } from 'react';
import { Link2, Clipboard, Sparkles, Loader2, AlertCircle } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import { useAnalyze } from '../hooks/useAnalyze';
import { analyzeUrl } from '../api/client';
import { ResultCard } from './ResultCard';

const SAMPLE_URLS = [
  { label: 'Phishing: Paytm Login Spoof', url: 'http://paytm-secure-login.xyz/verify?id=123' },
  { label: 'Phishing: PhonePe Reward Fake', url: 'http://phonepe-reward-claim.top/collect' },
  { label: 'Safe: Amazon Official India', url: 'https://www.amazon.in/gp/buy/spc/handlers/display.html' },
  { label: 'Safe: NPCI Official Portal', url: 'https://www.npci.org.in/what-we-do/upi/product-overview' },
];

export function CheckLinkTab({ onHighRiskDetected }) {
  const { t } = useLanguage();
  const [url, setUrl] = useState('');
  const [inputError, setInputError] = useState('');
  const { loading, error, result, execute } = useAnalyze(analyzeUrl);

  const handleSubmit = async (e) => {
    e && e.preventDefault();
    setInputError('');
    const trimmed = url.trim();
    if (!trimmed) {
      setInputError('Please enter a URL or payment link to analyze.');
      return;
    }

    try {
      const res = await execute({ url: trimmed });
      if (res && res.risk_level === 'HIGH') {
        onHighRiskDetected && onHighRiskDetected(res);
      }
    } catch (err) {
      // Handled by hook
    }
  };

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        setUrl(text);
        setInputError('');
      }
    } catch (e) {
      // Permission blocked
    }
  };

  const handleSample = (sampleUrl) => {
    setUrl(sampleUrl);
    setInputError('');
  };

  return (
    <div className="space-y-6">
      {/* Tool Introduction */}
      <div>
        <h2 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center space-x-2">
          <Link2 className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          <span>{t('checkLinkTitle')}</span>
        </h2>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
          {t('checkLinkDesc')}
        </p>
      </div>

      {/* Main Input Card */}
      <form onSubmit={handleSubmit} className="p-6 rounded-2xl bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 shadow-sm">
        <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2">
          Payment or Web Link
        </label>
        <div className="relative flex items-center">
          <input
            type="text"
            data-testid="url-input"
            value={url}
            onChange={(e) => {
              setUrl(e.target.value);
              setInputError('');
            }}
            placeholder={t('urlPlaceholder')}
            className={`w-full pl-4 pr-24 py-3.5 rounded-xl border text-sm font-mono bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-600 focus:outline-none focus:ring-2 transition-all ${
              inputError || error
                ? 'border-rose-400 focus:ring-rose-400/40'
                : 'border-slate-300 dark:border-slate-700 focus:border-blue-500 focus:ring-blue-500/20'
            }`}
          />
          <div className="absolute right-2 flex items-center space-x-1">
            <button
              type="button"
              onClick={handlePaste}
              className="px-2.5 py-1.5 text-xs font-semibold rounded-lg bg-slate-200/70 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-slate-700 transition-colors flex items-center space-x-1"
              title="Paste from clipboard"
            >
              <Clipboard className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">{t('pasteBtn')}</span>
            </button>
          </div>
        </div>

        {/* Validation Errors */}
        {(inputError || error) && (
          <div className="mt-3 flex items-center space-x-2 text-xs font-medium text-rose-600 dark:text-rose-400">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{inputError || error}</span>
          </div>
        )}

        {/* Quick Samples */}
        <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800/80">
          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 block mb-2 flex items-center space-x-1">
            <Sparkles className="w-3.5 h-3.5 text-blue-500" />
            <span>{t('trySample')}:</span>
          </span>
          <div className="flex flex-wrap gap-2">
            {SAMPLE_URLS.map((sample, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSample(sample.url)}
                className="text-xs px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800/90 text-slate-700 dark:text-slate-300 hover:bg-blue-50 dark:hover:bg-blue-950/60 hover:text-blue-600 dark:hover:text-blue-400 border border-slate-200 dark:border-slate-700 transition-colors"
              >
                {sample.label}
              </button>
            ))}
          </div>
        </div>

        {/* Action Button */}
        <div className="mt-6 flex justify-end">
          <button
            type="submit"
            disabled={loading}
            data-testid="analyze-url-btn"
            className="w-full sm:w-auto px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm shadow-md shadow-blue-500/20 transition-all flex items-center justify-center space-x-2 disabled:opacity-70 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>{t('analyzing')}</span>
              </>
            ) : (
              <span>{t('analyzeBtn')}</span>
            )}
          </button>
        </div>
      </form>

      {/* Result Card */}
      {result && (
        <div className="animate-fade-in">
          <ResultCard result={result} />
        </div>
      )}
    </div>
  );
}

