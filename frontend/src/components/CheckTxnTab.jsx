// src/components/CheckTxnTab.jsx
import React, { useState } from 'react';
import { 
  CreditCard, 
  Sparkles, 
  Loader2, 
  AlertCircle, 
  User, 
  DollarSign, 
  Clock, 
  Tag 
} from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import { useAnalyze } from '../hooks/useAnalyze';
import { analyzeTransaction } from '../api/client';
import { ResultCard } from './ResultCard';

const SAMPLE_TXNS = [
  {
    label: 'High Anomaly: ₹49,999 Night Refund Alert',
    data: {
      user_id: 'u101',
      amount: 49999,
      receiver: 'unknown@ybl',
      timestamp: '2026-11-12T02:14:00',
      channel: 'upi',
      note: 'urgent refund'
    }
  },
  {
    label: 'Safe: Typical Grocery ₹450 Daytime',
    data: {
      user_id: 'u101',
      amount: 450,
      receiver: 'groceries@okhdfcbank',
      timestamp: '2026-11-12T14:30:00',
      channel: 'upi',
      note: 'dinner veggies'
    }
  },
  {
    label: 'Suspicious: ₹28,000 KYC Lottery',
    data: {
      user_id: 'u101',
      amount: 28000,
      receiver: 'claimprize@paytm',
      timestamp: '2026-11-12T03:45:00',
      channel: 'upi',
      note: 'winner KYC charge'
    }
  }
];

export function CheckTxnTab({ onHighRiskDetected }) {
  const { t } = useLanguage();
  const [formData, setFormData] = useState({
    user_id: 'u101',
    amount: '49999',
    receiver: 'unknown@ybl',
    timestamp: new Date().toISOString().slice(0, 16),
    channel: 'upi',
    note: 'urgent refund',
  });
  const [validationErrors, setValidationErrors] = useState({});

  const { loading, error, result, execute } = useAnalyze(analyzeTransaction);

  const validate = () => {
    const errors = {};
    const amt = parseFloat(formData.amount);
    if (isNaN(amt) || amt <= 0) {
      errors.amount = 'Amount must be greater than 0';
    }
    if (!formData.receiver.trim()) {
      errors.receiver = 'Receiver VPA is required';
    } else if (!formData.receiver.includes('@')) {
      errors.receiver = 'Receiver must be a valid UPI VPA (e.g., name@bank)';
    }
    if (!formData.user_id.trim()) {
      errors.user_id = 'User ID is required';
    }
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e && e.preventDefault();
    if (!validate()) return;

    try {
      const payload = {
        user_id: formData.user_id.trim(),
        amount: parseFloat(formData.amount),
        receiver: formData.receiver.trim(),
        timestamp: new Date(formData.timestamp).toISOString(),
        channel: formData.channel,
        note: formData.note.trim(),
      };
      const res = await execute(payload);
      if (res && res.risk_level === 'HIGH') {
        onHighRiskDetected && onHighRiskDetected(res);
      }
    } catch (err) {}
  };

  const handleApplySample = (sample) => {
    setFormData({
      user_id: sample.user_id,
      amount: sample.amount.toString(),
      receiver: sample.receiver,
      timestamp: sample.timestamp.slice(0, 16),
      channel: sample.channel,
      note: sample.note,
    });
    setValidationErrors({});
  };

  return (
    <div className="space-y-6">
      {/* Intro */}
      <div>
        <h2 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center space-x-2">
          <CreditCard className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          <span>{t('checkTxnTitle')}</span>
        </h2>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
          {t('checkTxnDesc')}
        </p>
      </div>

      {/* Main Form */}
      <form onSubmit={handleSubmit} className="p-6 rounded-2xl bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 shadow-sm">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* User ID */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5">
              {t('userIdLabel')}
            </label>
            <input
              type="text"
              data-testid="txn-user-id"
              value={formData.user_id}
              onChange={(e) => setFormData({ ...formData, user_id: e.target.value })}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500/20 focus:outline-none"
              placeholder="e.g. u101"
            />
            {validationErrors.user_id && (
              <p className="mt-1 text-xs text-rose-500">{validationErrors.user_id}</p>
            )}
          </div>

          {/* Amount */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5">
              {t('amountLabel')}
            </label>
            <div className="relative">
              <span className="absolute left-3.5 top-2.5 text-slate-400 text-sm font-semibold">₹</span>
              <input
                type="number"
                step="any"
                data-testid="txn-amount"
                value={formData.amount}
                onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                className="w-full pl-8 pr-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500/20 focus:outline-none"
                placeholder="49999"
              />
            </div>
            {validationErrors.amount && (
              <p className="mt-1 text-xs text-rose-500">{validationErrors.amount}</p>
            )}
          </div>

          {/* Receiver VPA */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5">
              {t('receiverLabel')}
            </label>
            <input
              type="text"
              data-testid="txn-receiver"
              value={formData.receiver}
              onChange={(e) => setFormData({ ...formData, receiver: e.target.value })}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-white text-sm font-mono focus:ring-2 focus:ring-blue-500/20 focus:outline-none"
              placeholder="recipient@okaxis"
            />
            {validationErrors.receiver && (
              <p className="mt-1 text-xs text-rose-500">{validationErrors.receiver}</p>
            )}
          </div>

          {/* Timestamp */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5">
              {t('timestampLabel')}
            </label>
            <input
              type="datetime-local"
              data-testid="txn-timestamp"
              value={formData.timestamp}
              onChange={(e) => setFormData({ ...formData, timestamp: e.target.value })}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500/20 focus:outline-none"
            />
          </div>

          {/* Channel */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5">
              {t('channelLabel')}
            </label>
            <select
              value={formData.channel}
              onChange={(e) => setFormData({ ...formData, channel: e.target.value })}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500/20 focus:outline-none"
            >
              <option value="upi">UPI (Instant Real-time)</option>
              <option value="imps">IMPS</option>
              <option value="neft">NEFT</option>
              <option value="card">Debit/Credit Card</option>
            </select>
          </div>

          {/* Note */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5">
              {t('noteLabel')}
            </label>
            <input
              type="text"
              data-testid="txn-note"
              value={formData.note}
              onChange={(e) => setFormData({ ...formData, note: e.target.value })}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500/20 focus:outline-none"
              placeholder="e.g. urgent refund, lottery fee"
            />
          </div>
        </div>

        {/* Global Error Banner */}
        {error && (
          <div className="mt-4 p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Quick Samples */}
        <div className="mt-5 pt-4 border-t border-slate-100 dark:border-slate-800/80">
          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 block mb-2 flex items-center space-x-1">
            <Sparkles className="w-3.5 h-3.5 text-blue-500" />
            <span>{t('trySample')}:</span>
          </span>
          <div className="flex flex-wrap gap-2">
            {SAMPLE_TXNS.map((sample, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleApplySample(sample.data)}
                className="text-xs px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800/90 text-slate-700 dark:text-slate-300 hover:bg-blue-50 dark:hover:bg-blue-950/60 hover:text-blue-600 dark:hover:text-blue-400 border border-slate-200 dark:border-slate-700 transition-colors"
              >
                {sample.label}
              </button>
            ))}
          </div>
        </div>

        {/* Submit Button */}
        <div className="mt-6 flex justify-end">
          <button
            type="submit"
            disabled={loading}
            data-testid="analyze-txn-btn"
            className="w-full sm:w-auto px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm shadow-md shadow-blue-500/20 transition-all flex items-center justify-center space-x-2 disabled:opacity-70"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>{t('analyzing')}</span>
              </>
            ) : (
              <span>{t('analyzeTxnBtn')}</span>
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

