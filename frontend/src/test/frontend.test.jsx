// src/test/frontend.test.jsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ResultCard } from '../components/ResultCard';
import { WarningModal } from '../components/WarningModal';
import { CheckLinkTab } from '../components/CheckLinkTab';
import * as mockApi from '../api/mockApi';
import { LanguageProvider } from '../context/LanguageContext';

const renderWithContext = (ui) => {
  return render(
    <LanguageProvider>
      {ui}
    </LanguageProvider>
  );
};

describe('1. Mock Client Shape Validation against API Contract', () => {
  it('mockAnalyzeUrl returns exact contract shape', async () => {
    const res = await mockApi.mockAnalyzeUrl({ url: 'http://paytm-secure-login.xyz/verify?id=123' });
    expect(res).toHaveProperty('risk_score');
    expect(typeof res.risk_score).toBe('number');
    expect(res.risk_score).toBeGreaterThanOrEqual(0);
    expect(res.risk_score).toBeLessThanOrEqual(100);

    expect(['LOW', 'MEDIUM', 'HIGH']).toContain(res.risk_level);
    expect(typeof res.verdict).toBe('string');
    expect(Array.isArray(res.signals)).toBe(true);
    res.signals.forEach(sig => {
      expect(sig).toHaveProperty('name');
      expect(['low', 'medium', 'high']).toContain(sig.severity);
      expect(sig).toHaveProperty('detail');
    });

    expect(typeof res.explanation).toBe('string');
    expect(typeof res.recommended_action).toBe('string');
    expect(typeof res.analyzed_at).toBe('string');
    expect(res.type).toBe('url');
  });

  it('mockAnalyzeQr returns exact contract shape', async () => {
    const res = await mockApi.mockAnalyzeQr({ qr_payload: 'upi://pay?pa=shop@okaxis&pn=Ram Store&am=5000&cu=INR' });
    expect(res).toHaveProperty('risk_score');
    expect(['LOW', 'MEDIUM', 'HIGH']).toContain(res.risk_level);
    expect(res.type).toBe('qr');
    expect(Array.isArray(res.signals)).toBe(true);
  });

  it('mockAnalyzeTransaction returns exact contract shape', async () => {
    const res = await mockApi.mockAnalyzeTransaction({
      user_id: 'u101',
      amount: 49999,
      receiver: 'unknown@ybl',
      timestamp: '2026-11-12T02:14:00',
      channel: 'upi',
      note: 'urgent refund'
    });
    expect(res).toHaveProperty('risk_score');
    expect(['LOW', 'MEDIUM', 'HIGH']).toContain(res.risk_level);
    expect(res.type).toBe('transaction');
    expect(Array.isArray(res.signals)).toBe(true);
  });
});

describe('2. Result Card Component (All 3 Risk Levels)', () => {
  it('renders LOW risk card correctly with clean state', () => {
    const lowResult = {
      risk_score: 12,
      risk_level: 'LOW',
      verdict: 'Safe to proceed',
      signals: [{ name: 'Valid Merchant', severity: 'low', detail: 'Known merchant' }],
      explanation: 'No deceptive indicators detected.',
      recommended_action: 'Safe to proceed.',
      analyzed_at: new Date().toISOString(),
      type: 'url'
    };

    renderWithContext(<ResultCard result={lowResult} />);
    expect(screen.getByText('LOW RISK')).toBeInTheDocument();
    expect(screen.getByText('Safe to proceed')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
    expect(screen.getByText('Clean')).toBeInTheDocument();
  });

  it('renders MEDIUM risk card correctly with caution state', () => {
    const medResult = {
      risk_score: 55,
      risk_level: 'MEDIUM',
      verdict: 'Proceed with caution',
      signals: [{ name: 'Unusual Time', severity: 'medium', detail: 'Sent late at night' }],
      explanation: 'Parameters deviate from typical patterns.',
      recommended_action: 'Verify payee carefully.',
      analyzed_at: new Date().toISOString(),
      type: 'transaction'
    };

    renderWithContext(<ResultCard result={medResult} />);
    expect(screen.getByText('MEDIUM RISK')).toBeInTheDocument();
    expect(screen.getByText('Proceed with caution')).toBeInTheDocument();
    expect(screen.getByText('55')).toBeInTheDocument();
    expect(screen.getByText('Suspicious')).toBeInTheDocument();
  });

  it('renders HIGH risk card correctly with danger state', () => {
    const highResult = {
      risk_score: 88,
      risk_level: 'HIGH',
      verdict: 'Do not proceed',
      signals: [{ name: 'Brand Phishing', severity: 'high', detail: 'Spoofs bank login' }],
      explanation: 'Critical phishing attack identified.',
      recommended_action: 'Do not pay or disclose PIN.',
      analyzed_at: new Date().toISOString(),
      type: 'qr'
    };

    renderWithContext(<ResultCard result={highResult} />);
    expect(screen.getByText('HIGH RISK')).toBeInTheDocument();
    expect(screen.getByText('Do not proceed')).toBeInTheDocument();
    expect(screen.getByText('88')).toBeInTheDocument();
    expect(screen.getByText('Dangerous')).toBeInTheDocument();
  });
});

describe('3. Real-Time Warning Modal (Safety Gating & Actions)', () => {
  const highRiskResult = {
    risk_score: 92,
    risk_level: 'HIGH',
    verdict: 'Do not proceed',
    signals: [],
    explanation: 'Scammers frequently use this pattern to drain accounts.',
    recommended_action: 'Cancel payment immediately.',
    analyzed_at: new Date().toISOString(),
    type: 'url'
  };

  it('disables proceed button until checkbox is checked', () => {
    const onProceed = vi.fn();
    const onClose = vi.fn();

    renderWithContext(
      <WarningModal
        isOpen={true}
        result={highRiskResult}
        onClose={onClose}
        onProceedConfirmed={onProceed}
      />
    );

    const proceedBtn = screen.getByTestId('proceed-payment-btn');
    const checkbox = screen.getByTestId('risk-confirm-checkbox');

    expect(proceedBtn).toBeDisabled();

    // Check the box
    fireEvent.click(checkbox);
    expect(proceedBtn).not.toBeDisabled();

    // Click proceed
    fireEvent.click(proceedBtn);
    expect(onProceed).toHaveBeenCalledTimes(1);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('triggers cancel payment when cancel button is clicked', () => {
    const onClose = vi.fn();
    renderWithContext(
      <WarningModal
        isOpen={true}
        result={highRiskResult}
        onClose={onClose}
      />
    );

    const cancelBtn = screen.getByTestId('cancel-payment-btn');
    fireEvent.click(cancelBtn);
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});

describe('4. URL Validation & Input Handling', () => {
  it('flags empty URL submission with validation error', async () => {
    renderWithContext(<CheckLinkTab />);
    const submitBtn = screen.getByTestId('analyze-url-btn');

    fireEvent.click(submitBtn);
    expect(await screen.findByText(/Please enter a URL or payment link/i)).toBeInTheDocument();
  });
});

