// src/components/WarningModal.jsx
import React, { useState, useEffect } from 'react';
import { ShieldAlert, AlertTriangle, X, Check, ArrowRight, Bell } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export function WarningModal({ isOpen, onClose, result, onProceedConfirmed }) {
  const { t } = useLanguage();
  const [confirmedRisk, setConfirmedRisk] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setConfirmedRisk(false);
      // Play audio beep cue if browser allows
      try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(440, audioCtx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(880, audioCtx.currentTime + 0.15);
        gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.2);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.25);
      } catch (e) {
        // AudioContext not allowed or autoplay blocked
      }
    }
  }, [isOpen]);

  if (!isOpen || !result) return null;

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in"
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="warning-modal-title"
      aria-describedby="warning-modal-desc"
    >
      <div 
        data-testid="warning-modal"
        className="relative w-full max-w-xl overflow-hidden rounded-3xl bg-slate-900 border-2 border-rose-500 shadow-2xl shadow-rose-950/80 text-white p-6 sm:p-8"
      >
        {/* Urgent Animated Beacon */}
        <div className="flex items-center space-x-3 mb-6">
          <div className="relative flex items-center justify-center w-14 h-14 rounded-2xl bg-rose-500/20 text-rose-500 border border-rose-500/30">
            <ShieldAlert className="w-8 h-8 animate-pulse" />
            <div className="absolute inset-0 rounded-2xl bg-rose-500/10 pulse-ring-anim" />
          </div>
          <div>
            <span className="px-2.5 py-0.5 rounded text-[11px] font-black tracking-widest bg-rose-500 text-white uppercase">
              CRITICAL FRAUD ALERT
            </span>
            <h2 id="warning-modal-title" className="text-xl sm:text-2xl font-black tracking-tight text-white mt-1">
              {t('warningTitle')}
            </h2>
          </div>
        </div>

        {/* Live ARIA announcement region */}
        <div aria-live="assertive" className="sr-only">
          Warning: PayGuard AI detected a high risk payment fraud attempt. Score is {result.risk_score} out of 100.
        </div>

        {/* Explanatory Warning Message */}
        <p id="warning-modal-desc" className="text-slate-300 text-sm leading-relaxed mb-5">
          {result.explanation || t('warningSubtitle')}
        </p>

        {/* Action Callout */}
        <div className="mb-6 rounded-2xl bg-rose-950/40 border border-rose-800/60 p-4">
          <span className="text-xs font-bold uppercase tracking-wider text-rose-400 block mb-1">
            {t('recommendedAction')}
          </span>
          <p className="text-sm font-semibold text-rose-200">
            {result.recommended_action}
          </p>
        </div>

        {/* Safety Gating Checkbox */}
        <div className="mb-6 p-4 rounded-xl bg-slate-800/70 border border-slate-700">
          <label className="flex items-start space-x-3 cursor-pointer select-none">
            <input
              type="checkbox"
              data-testid="risk-confirm-checkbox"
              checked={confirmedRisk}
              onChange={(e) => setConfirmedRisk(e.target.checked)}
              className="mt-1 w-4 h-4 rounded border-slate-600 text-rose-600 focus:ring-rose-500 bg-slate-900 cursor-pointer"
            />
            <span className="text-xs text-slate-300 leading-snug">
              {t('understandCheckbox')}
            </span>
          </label>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-end gap-3">
          {/* Primary Action: Cancel Payment */}
          <button
            onClick={onClose}
            data-testid="cancel-payment-btn"
            className="w-full sm:w-auto px-6 py-3 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white font-bold text-sm shadow-lg shadow-emerald-950 transition-all transform hover:-translate-y-0.5"
          >
            {t('cancelPayment')}
          </button>

          {/* Secondary Gated Action: Proceed Anyway */}
          <button
            disabled={!confirmedRisk}
            onClick={() => {
              if (confirmedRisk) {
                onProceedConfirmed && onProceedConfirmed();
                onClose();
              }
            }}
            data-testid="proceed-payment-btn"
            className={`w-full sm:w-auto px-4 py-3 rounded-xl text-xs font-semibold border transition-all ${
              confirmedRisk
                ? 'bg-rose-900/60 text-rose-200 border-rose-700 hover:bg-rose-800/80 cursor-pointer'
                : 'bg-slate-800/40 text-slate-500 border-slate-800 cursor-not-allowed opacity-50'
            }`}
          >
            {t('proceedAnyway')}
          </button>
        </div>
      </div>
    </div>
  );
}

