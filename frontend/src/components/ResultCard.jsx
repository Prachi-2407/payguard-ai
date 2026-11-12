// src/components/ResultCard.jsx
import React, { useState } from 'react';
import { 
  ShieldCheck, 
  AlertTriangle, 
  ShieldAlert, 
  Copy, 
  Check, 
  Share2, 
  Clock, 
  HelpCircle,
  ArrowRight
} from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export function ResultCard({ result }) {
  const { t } = useLanguage();
  const [copied, setCopied] = useState(false);

  if (!result) return null;

  const {
    risk_score = 0,
    risk_level = 'LOW',
    verdict = '',
    signals = [],
    explanation = '',
    recommended_action = '',
    analyzed_at = '',
    type = 'url',
  } = result;

  // Determine colors based on contract risk_level
  const isHigh = risk_level === 'HIGH';
  const isMed = risk_level === 'MEDIUM';
  const isLow = risk_level === 'LOW';

  const colorConfig = isHigh
    ? {
        border: 'border-rose-500/50 dark:border-rose-500/40',
        bg: 'bg-rose-500/5 dark:bg-rose-950/20',
        badge: 'bg-rose-100 text-rose-800 dark:bg-rose-950/80 dark:text-rose-300 border-rose-300 dark:border-rose-800',
        gaugeStroke: '#EF4444',
        glow: 'shadow-rose-500/10 dark:shadow-rose-900/30',
        icon: <ShieldAlert className="w-6 h-6 text-rose-600 dark:text-rose-400" />
      }
    : isMed
    ? {
        border: 'border-amber-500/50 dark:border-amber-500/40',
        bg: 'bg-amber-500/5 dark:bg-amber-950/20',
        badge: 'bg-amber-100 text-amber-800 dark:bg-amber-950/80 dark:text-amber-300 border-amber-300 dark:border-amber-800',
        gaugeStroke: '#F59E0B',
        glow: 'shadow-amber-500/10 dark:shadow-amber-900/30',
        icon: <AlertTriangle className="w-6 h-6 text-amber-600 dark:text-amber-400" />
      }
    : {
        border: 'border-emerald-500/50 dark:border-emerald-500/40',
        bg: 'bg-emerald-500/5 dark:bg-emerald-950/20',
        badge: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/80 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800',
        gaugeStroke: '#10B981',
        glow: 'shadow-emerald-500/10 dark:shadow-emerald-900/30',
        icon: <ShieldCheck className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
      };

  // SVG circular gauge math
  const radius = 42;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (risk_score / 100) * circumference;

  const handleCopy = () => {
    const textToCopy = `[PayGuard AI Security Report]\nType: ${type.toUpperCase()}\nRisk Score: ${risk_score}/100 (${risk_level})\nVerdict: ${verdict}\nAction: ${recommended_action}\nSignals: ${signals.map(s => s.name).join(', ')}`;
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: 'PayGuard AI Threat Report',
        text: `PayGuard AI flagged this ${type} with risk score ${risk_score}/100: ${verdict}. Action: ${recommended_action}`,
      }).catch(() => {});
    } else {
      handleCopy();
    }
  };

  const severityBadge = (sev) => {
    const s = (sev || 'low').toLowerCase();
    if (s === 'high') {
      return 'bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300 border-red-300 dark:border-red-800';
    }
    if (s === 'medium') {
      return 'bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300 border-amber-300 dark:border-amber-800';
    }
    return 'bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300 border-blue-300 dark:border-blue-800';
  };

  return (
    <div 
      data-testid="result-card"
      className={`relative overflow-hidden rounded-2xl border ${colorConfig.border} ${colorConfig.bg} p-6 sm:p-8 shadow-xl ${colorConfig.glow} backdrop-blur-sm transition-all duration-300`}
    >
      {/* Top Header Strip: Verdict & Circular Gauge */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 pb-6 border-b border-slate-200/60 dark:border-slate-800/80">
        <div className="flex items-start space-x-4">
          <div className="p-3 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
            {colorConfig.icon}
          </div>
          <div>
            <div className="flex items-center space-x-2.5">
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border tracking-wider ${colorConfig.badge}`}>
                {risk_level} RISK
              </span>
              <span className="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-widest font-mono">
                {type}
              </span>
            </div>
            <h3 className="mt-1.5 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              {verdict}
            </h3>
            <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400 flex items-center space-x-1">
              <Clock className="w-3.5 h-3.5" />
              <span>{new Date(analyzed_at || Date.now()).toLocaleTimeString()} ({new Date(analyzed_at || Date.now()).toLocaleDateString()})</span>
            </p>
          </div>
        </div>

        {/* Circular Risk Score Gauge */}
        <div className="flex items-center space-x-4 self-center sm:self-auto bg-white/70 dark:bg-slate-900/70 px-5 py-3 rounded-2xl border border-slate-200/60 dark:border-slate-800">
          <div className="relative w-24 h-24 flex items-center justify-center">
            <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
              <circle
                cx="50"
                cy="50"
                r={radius}
                className="stroke-slate-200 dark:stroke-slate-800"
                strokeWidth="8"
                fill="none"
              />
              <circle
                cx="50"
                cy="50"
                r={radius}
                stroke={colorConfig.gaugeStroke}
                strokeWidth="8"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                fill="none"
                style={{ transition: 'stroke-dashoffset 1s ease-out' }}
              />
            </svg>
            <div className="absolute flex flex-col items-center justify-center text-center">
              <span className="text-2xl font-black tracking-tight text-slate-900 dark:text-white">
                {risk_score}
              </span>
              <span className="text-[10px] uppercase font-semibold text-slate-500 dark:text-slate-400">
                / 100
              </span>
            </div>
          </div>
          <div className="text-left">
            <div className="text-xs font-semibold text-slate-500 dark:text-slate-400">Threat Index</div>
            <div className={`text-sm font-bold ${isHigh ? 'text-rose-600 dark:text-rose-400' : isMed ? 'text-amber-600 dark:text-amber-400' : 'text-emerald-600 dark:text-emerald-400'}`}>
              {isHigh ? 'Dangerous' : isMed ? 'Suspicious' : 'Clean'}
            </div>
          </div>
        </div>
      </div>

      {/* Recommended Action Callout */}
      <div className="mt-6 rounded-xl bg-white dark:bg-slate-900 p-4 border border-slate-200 dark:border-slate-800 shadow-sm flex items-start space-x-3">
        <ArrowRight className="w-5 h-5 mt-0.5 text-blue-600 dark:text-blue-400 shrink-0" />
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 block mb-0.5">
            {t('recommendedAction')}
          </span>
          <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">
            {recommended_action}
          </p>
        </div>
      </div>

      {/* Plain-English AI Explainer Panel */}
      <div className="mt-5 rounded-xl bg-slate-100/80 dark:bg-slate-900/80 p-4 border border-slate-200/80 dark:border-slate-800/80">
        <div className="flex items-center space-x-2 mb-2 text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-300">
          <HelpCircle className="w-4 h-4 text-blue-500" />
          <span>{t('whyRisky')}</span>
        </div>
        <p className="text-sm leading-relaxed text-slate-700 dark:text-slate-300">
          {explanation}
        </p>
      </div>

      {/* Signals Detected */}
      {signals && signals.length > 0 && (
        <div className="mt-6">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-3">
            {t('signalsDetected')} ({signals.length})
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {signals.map((sig, idx) => (
              <div 
                key={idx}
                className="p-3.5 rounded-xl bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800/80 shadow-xs"
              >
                <div className="flex items-center justify-between gap-2 mb-1">
                  <span className="font-semibold text-sm text-slate-900 dark:text-slate-100">
                    {sig.name}
                  </span>
                  <span className={`px-2 py-0.5 rounded text-[11px] font-bold uppercase border ${severityBadge(sig.severity)}`}>
                    {sig.severity}
                  </span>
                </div>
                <p className="text-xs text-slate-600 dark:text-slate-400">
                  {sig.detail}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action Bar: Copy / Share */}
      <div className="mt-6 pt-5 border-t border-slate-200/60 dark:border-slate-800 flex items-center justify-end space-x-3">
        <button
          onClick={handleCopy}
          className="inline-flex items-center space-x-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 transition-colors shadow-xs"
        >
          {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
          <span>{copied ? t('copied') : t('copyResult')}</span>
        </button>
        <button
          onClick={handleShare}
          className="inline-flex items-center space-x-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition-colors shadow-sm"
        >
          <Share2 className="w-3.5 h-3.5" />
          <span>{t('shareResult')}</span>
        </button>
      </div>
    </div>
  );
}

