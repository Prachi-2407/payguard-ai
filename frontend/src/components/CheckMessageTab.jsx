// src/components/CheckMessageTab.jsx
import React, { useState } from 'react';
import { MessageSquare, Clipboard, Sparkles, Loader2, AlertCircle, Send } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import { useAnalyze } from '../hooks/useAnalyze';
import { analyzeMessage } from '../api/client';
import { ResultCard } from './ResultCard';

const SAMPLE_MESSAGES = [
  {
    label: 'KYC Phishing SMS',
    text: 'Dear user your SBI KYC expires today. Update at http://sbi-kyc-update.top/login or account will be blocked',
    source: 'sms',
  },
  {
    label: 'KBC Lottery WhatsApp',
    text: 'Congratulations! Your mobile number won 25,00,000 INR in KBC Lucky Draw! Contact WhatsApp Manager at +919876543210 to claim prize.',
    source: 'whatsapp',
  },
  {
    label: 'Job Scam WhatsApp',
    text: 'Work from Home part-time job! Earn 5,000 daily by liking YouTube videos and rating hotels. Contact HR on WhatsApp +918765432109',
    source: 'whatsapp',
  },
  {
    label: 'Safe Bank OTP Alert',
    text: '482910 is your OTP for transaction of INR 1,500.00 at Swiggy using HDFC Bank Card ending 1234. OTP is valid for 10 mins. Do not share with anyone.',
    source: 'sms',
  },
];

export function CheckMessageTab({ onHighRiskDetected }) {
  const { t } = useLanguage();
  const [message, setMessage] = useState('');
  const [source, setSource] = useState('sms');
  const [inputError, setInputError] = useState('');
  const { loading, error, result, execute } = useAnalyze(analyzeMessage);

  const handleSubmit = async (e) => {
    e && e.preventDefault();
    setInputError('');
    const trimmed = message.trim();
    if (!trimmed) {
      setInputError('Please enter or paste a message to analyze.');
      return;
    }

    try {
      const res = await execute({ message: trimmed, source });
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
        setMessage(text);
        setInputError('');
      }
    } catch (e) {
      // Permission blocked
    }
  };

  const handleSample = (sample) => {
    setMessage(sample.text);
    setSource(sample.source);
    setInputError('');
  };

  return (
    <div className="space-y-6">
      {/* Tool Introduction */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 sm:p-8 border border-slate-200 dark:border-slate-800 shadow-sm">
        <div className="flex items-center space-x-3 mb-2">
          <div className="p-2.5 rounded-xl bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400">
            <MessageSquare className="w-5 h-5" />
          </div>
          <h2 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
            Scam Message Analyzer
          </h2>
        </div>
        <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed max-w-3xl">
          Inspect suspicious SMS texts, WhatsApp forwards, or urgent emails. The NLP engine detects bank impersonation, lottery fraud, and coercive KYC threats while extracting embedded URLs, phone numbers, and UPI IDs.
        </p>

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Source Channel:
            </span>
            {['sms', 'whatsapp', 'email', 'other'].map((src) => (
              <label
                key={src}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider cursor-pointer border transition-colors ${
                  source === src
                    ? 'bg-blue-600 text-white border-blue-600 shadow-xs'
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:bg-slate-200 dark:hover:bg-slate-700'
                }`}
              >
                <input
                  type="radio"
                  name="source"
                  value={src}
                  checked={source === src}
                  onChange={(e) => setSource(e.target.value)}
                  className="sr-only"
                />
                {src}
              </label>
            ))}
          </div>

          <div className="relative">
            <textarea
              rows="4"
              value={message}
              onChange={(e) => {
                setMessage(e.target.value);
                if (inputError) setInputError('');
              }}
              placeholder="Paste SMS or WhatsApp message here (e.g., 'Dear user your SBI KYC expires today...')"
              className={`w-full px-4 py-3.5 rounded-xl border ${
                inputError
                  ? 'border-rose-500 focus:ring-rose-500/20'
                  : 'border-slate-300 dark:border-slate-700 focus:ring-blue-500/20'
              } bg-slate-50 dark:bg-[#0c121e] text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 text-sm focus:ring-2 focus:outline-none transition-all shadow-inner`}
            />

            <button
              type="button"
              onClick={handlePaste}
              className="absolute right-3 top-3 p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-200/50 dark:hover:bg-slate-800 transition-colors"
              title="Paste from clipboard"
            >
              <Clipboard className="w-4 h-4" />
            </button>
          </div>

          {inputError && (
            <p className="text-xs font-medium text-rose-500 flex items-center space-x-1">
              <AlertCircle className="w-3.5 h-3.5 shrink-0" />
              <span>{inputError}</span>
            </p>
          )}

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2">
            {/* Quick Sample Triggers */}
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 flex items-center space-x-1">
                <Sparkles className="w-3.5 h-3.5 text-blue-500" />
                <span>Try Sample:</span>
              </span>
              {SAMPLE_MESSAGES.map((s, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSample(s)}
                  className="px-2.5 py-1 text-xs font-medium rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700/80 transition-colors"
                >
                  {s.label}
                </button>
              ))}
            </div>

            <button
              type="submit"
              disabled={loading}
              data-testid="analyze-message-btn"
              className="inline-flex items-center justify-center space-x-2 px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:bg-blue-600/60 text-white text-sm font-bold shadow-md shadow-blue-500/20 transition-all cursor-pointer disabled:cursor-not-allowed shrink-0"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Analyzing message...</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>Analyze Message</span>
                </>
              )}
            </button>
          </div>
        </form>

        {error && (
          <div className="mt-4 p-4 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-xs">
            <strong>Error:</strong> {error.message || 'Failed to inspect message.'}
          </div>
        )}
      </div>

      {/* Analysis Result Output */}
      {result && <ResultCard result={result} />}
    </div>
  );
}

