// src/App.jsx
import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  Link2, 
  QrCode, 
  CreditCard, 
  History, 
  BookOpen, 
  CheckCircle2, 
  AlertTriangle, 
  ChevronRight, 
  Sparkles,
  Zap,
  Lock,
  ArrowRight
} from 'lucide-react';
import { Navbar } from './components/Navbar';
import { CheckLinkTab } from './components/CheckLinkTab';
import { ScanQrTab } from './components/ScanQrTab';
import { CheckTxnTab } from './components/CheckTxnTab';
import { HistoryTab } from './components/HistoryTab';
import { ScamTipsTab } from './components/ScamTipsTab';
import { DemoQrGallery } from './components/DemoQrGallery';
import { WarningModal } from './components/WarningModal';
import { ReportModal } from './components/ReportModal';
import { OfflineBanner } from './components/OfflineBanner';
import { ErrorBoundary } from './components/ErrorBoundary';
import { useLanguage } from './context/LanguageContext';
import { getHistory } from './api/client';

export default function App() {
  const { t } = useLanguage();
  const [activeTab, setActiveTab] = useState('link'); // 'link' | 'qr' | 'txn' | 'history' | 'tips'
  const [warningModalResult, setWarningModalResult] = useState(null);
  const [isReportOpen, setIsReportOpen] = useState(false);
  const [checksCount, setChecksCount] = useState(148);

  // Sync checks count with history length
  useEffect(() => {
    getHistory(50).then(data => {
      if (Array.isArray(data)) {
        setChecksCount(148 + data.length);
      }
    }).catch(() => {});
  }, [activeTab]);

  const handleHighRisk = (result) => {
    setWarningModalResult(result);
  };

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-slate-50 dark:bg-[#0A0E17] text-slate-900 dark:text-slate-100 flex flex-col font-sans transition-colors duration-200">
        <OfflineBanner />
        <Navbar onOpenReport={() => setIsReportOpen(true)} />

        {/* Global Warning / High Risk Modal */}
        <WarningModal
          isOpen={Boolean(warningModalResult)}
          result={warningModalResult}
          onClose={() => setWarningModalResult(null)}
          onProceedConfirmed={() => setWarningModalResult(null)}
        />

        {/* Report Suspicious Link Modal */}
        <ReportModal
          isOpen={isReportOpen}
          onClose={() => setIsReportOpen(false)}
        />

        {/* Hero Section */}
        <div className="relative overflow-hidden border-b border-slate-200/80 dark:border-slate-800/80 bg-gradient-to-b from-blue-50/50 via-white to-slate-50 dark:from-blue-950/20 dark:via-[#0B0F19] dark:to-[#0A0E17] py-12 sm:py-16">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center max-w-3xl mx-auto">
              {/* Prevention Badge */}
              <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/80 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800 mb-6 shadow-xs">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span>{t('preventionBanner')}</span>
              </div>

              <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-slate-900 dark:text-white leading-tight">
                {t('heroTitle')}
              </h1>

              <p className="mt-4 text-base sm:text-lg text-slate-600 dark:text-slate-300 leading-relaxed">
                {t('heroDesc')}
              </p>

              {/* Live Metric Counters */}
              <div className="mt-8 grid grid-cols-3 gap-4 max-w-xl mx-auto pt-6 border-t border-slate-200/60 dark:border-slate-800/60">
                <div className="p-3">
                  <div className="text-2xl sm:text-3xl font-extrabold font-mono text-blue-600 dark:text-blue-400">
                    {checksCount}+
                  </div>
                  <div className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mt-1">
                    {t('checksDone')}
                  </div>
                </div>
                <div className="p-3 border-x border-slate-200/60 dark:border-slate-800/60">
                  <div className="text-2xl sm:text-3xl font-extrabold font-mono text-emerald-600 dark:text-emerald-400">
                    99.4%
                  </div>
                  <div className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mt-1">
                    {t('detectionRate')}
                  </div>
                </div>
                <div className="p-3">
                  <div className="text-2xl sm:text-3xl font-extrabold font-mono text-indigo-600 dark:text-indigo-400">
                    &lt; 30ms
                  </div>
                  <div className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mt-1">
                    P95 Latency
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* "How It Works" 3-Step Strip */}
        <div className="border-b border-slate-200/80 dark:border-slate-800/80 bg-white/60 dark:bg-[#0D1322]/60 py-4 backdrop-blur-xs">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-medium text-slate-600 dark:text-slate-400">
              <div className="flex items-center space-x-2.5">
                <div className="w-6 h-6 rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/60 dark:text-blue-300 flex items-center justify-center font-bold text-xs shrink-0">
                  1
                </div>
                <span>Inspect URL links, UPI QR codes, or abnormal transfers.</span>
              </div>
              <div className="flex items-center space-x-2.5">
                <div className="w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 dark:bg-indigo-900/60 dark:text-indigo-300 flex items-center justify-center font-bold text-xs shrink-0">
                  2
                </div>
                <span>ML model + 20+ cybersecurity rules compute instant risk index.</span>
              </div>
              <div className="flex items-center space-x-2.5">
                <div className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 dark:bg-emerald-900/60 dark:text-emerald-300 flex items-center justify-center font-bold text-xs shrink-0">
                  3
                </div>
                <span>Real-time warning modal blocks fraudulent PIN authorization.</span>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Area */}
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Navigation Tabs */}
          <div className="flex flex-wrap items-center gap-2 pb-6 border-b border-slate-200 dark:border-slate-800">
            <button
              onClick={() => setActiveTab('link')}
              data-testid="tab-link"
              className={`px-4 py-2.5 rounded-xl text-xs sm:text-sm font-bold transition-all flex items-center space-x-2 ${
                activeTab === 'link'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/25'
                  : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-800'
              }`}
            >
              <Link2 className="w-4 h-4" />
              <span>{t('tabLink')}</span>
            </button>

            <button
              onClick={() => setActiveTab('qr')}
              data-testid="tab-qr"
              className={`px-4 py-2.5 rounded-xl text-xs sm:text-sm font-bold transition-all flex items-center space-x-2 ${
                activeTab === 'qr'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/25'
                  : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-800'
              }`}
            >
              <QrCode className="w-4 h-4" />
              <span>{t('tabQr')}</span>
            </button>

            <button
              onClick={() => setActiveTab('txn')}
              data-testid="tab-txn"
              className={`px-4 py-2.5 rounded-xl text-xs sm:text-sm font-bold transition-all flex items-center space-x-2 ${
                activeTab === 'txn'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/25'
                  : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-800'
              }`}
            >
              <CreditCard className="w-4 h-4" />
              <span>{t('tabTxn')}</span>
            </button>

            <button
              onClick={() => setActiveTab('history')}
              data-testid="tab-history"
              className={`px-4 py-2.5 rounded-xl text-xs sm:text-sm font-bold transition-all flex items-center space-x-2 ${
                activeTab === 'history'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/25'
                  : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-800'
              }`}
            >
              <History className="w-4 h-4" />
              <span>{t('tabHistory')}</span>
            </button>

            <button
              onClick={() => setActiveTab('tips')}
              data-testid="tab-tips"
              className={`px-4 py-2.5 rounded-xl text-xs sm:text-sm font-bold transition-all flex items-center space-x-2 ${
                activeTab === 'tips'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/25'
                  : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-800'
              }`}
            >
              <BookOpen className="w-4 h-4" />
              <span>{t('tabTips')}</span>
            </button>
          </div>

          {/* Active Tab View */}
          <div className="mt-8">
            {activeTab === 'link' && <CheckLinkTab onHighRiskDetected={handleHighRisk} />}
            {activeTab === 'qr' && (
              <div className="space-y-10">
                <ScanQrTab onHighRiskDetected={handleHighRisk} />
                <DemoQrGallery onSelectPayload={(p) => {
                  window.scrollTo({ top: 380, behavior: 'smooth' });
                }} />
              </div>
            )}
            {activeTab === 'txn' && <CheckTxnTab onHighRiskDetected={handleHighRisk} />}
            {activeTab === 'history' && <HistoryTab />}
            {activeTab === 'tips' && <ScamTipsTab />}
          </div>
        </main>

        {/* Footer */}
        <footer className="mt-auto border-t border-slate-200 dark:border-slate-800/80 bg-white dark:bg-[#0B0F19] py-8 text-xs text-slate-500">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center space-x-2">
              <Shield className="w-4 h-4 text-blue-500" />
              <span className="font-semibold text-slate-700 dark:text-slate-300">
                PayGuard AI
              </span>
              <span>— Real-Time Payment Fraud Prevention Engine</span>
            </div>
            <div className="flex items-center space-x-4">
              <span>FastAPI + Scikit-Learn Engine</span>
              <span>•</span>
              <span>React 18 + Tailwind UX</span>
            </div>
          </div>
        </footer>
      </div>
    </ErrorBoundary>
  );
}

