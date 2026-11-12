// src/components/ScamTipsTab.jsx
import React from 'react';
import { ShieldCheck, AlertCircle, Key, Globe, ArrowDownLeft, MonitorX } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export function ScamTipsTab() {
  const { t } = useLanguage();

  const tips = [
    {
      icon: <Key className="w-6 h-6 text-rose-500" />,
      title: t('tip1Title'),
      desc: t('tip1Desc'),
      highlight: "UPI PIN is ONLY for sending money, NEVER for receiving."
    },
    {
      icon: <Globe className="w-6 h-6 text-amber-500" />,
      title: t('tip2Title'),
      desc: t('tip2Desc'),
      highlight: "Official banks never use free .xyz, .top, or .tk domains."
    },
    {
      icon: <ArrowDownLeft className="w-6 h-6 text-blue-500" />,
      title: t('tip3Title'),
      desc: t('tip3Desc'),
      highlight: "Declining unknown collect requests is completely risk-free."
    },
    {
      icon: <MonitorX className="w-6 h-6 text-purple-500" />,
      title: t('tip4Title'),
      desc: t('tip4Desc'),
      highlight: "Never share 9-digit remote codes with strangers over call."
    }
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center space-x-2">
          <ShieldCheck className="w-5 h-5 text-emerald-500" />
          <span>{t('scamTipsTitle')}</span>
        </h2>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
          Crucial security rules curated for everyday UPI and digital payment users in India.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {tips.map((tip, idx) => (
          <div
            key={idx}
            className="p-6 rounded-2xl bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col justify-between"
          >
            <div>
              <div className="w-12 h-12 rounded-xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-4">
                {tip.icon}
              </div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white mb-2">
                {tip.title}
              </h3>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed mb-4">
                {tip.desc}
              </p>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 text-[11px] font-semibold text-blue-600 dark:text-blue-400">
              💡 {tip.highlight}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

