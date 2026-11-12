// src/api/client.js
import { USE_MOCK, API_BASE_URL } from '../config';
import * as mockApi from './mockApi';

// Sanitize base URL: strip trailing slashes and redundant trailing '/api'
const cleanBaseUrl = (API_BASE_URL || 'https://payguard-ai-izry.onrender.com')
  .replace(/\/+$/, '')
  .replace(/\/api$/, '');

async function fetchRealApi(endpoint, options = {}) {
  const url = `${cleanBaseUrl}${endpoint}`;
  try {
    const res = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const err = new Error(data.error || `Request failed with status ${res.status}`);
      err.status = res.status;
      err.data = data;
      throw err;
    }
    return data;
  } catch (error) {
    if (error.status) throw error;
    // Network / unreachable error
    const netErr = new Error("Unable to connect to PayGuard API server. Please ensure backend is running.");
    netErr.status = 503;
    netErr.data = { error: "Backend server unreachable at " + cleanBaseUrl, code: 503 };
    throw netErr;
  }
}

export async function analyzeUrl(payload) {
  if (USE_MOCK) {
    return mockApi.mockAnalyzeUrl(payload);
  }
  return fetchRealApi('/api/analyze/url', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function analyzeQr(payload) {
  if (USE_MOCK) {
    return mockApi.mockAnalyzeQr(payload);
  }
  return fetchRealApi('/api/analyze/qr', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function analyzeTransaction(payload) {
  if (USE_MOCK) {
    return mockApi.mockAnalyzeTransaction(payload);
  }
  return fetchRealApi('/api/analyze/transaction', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getHistory(limit = 20, type = null, risk_level = null) {
  if (USE_MOCK) {
    return mockApi.mockGetHistory(limit, type, risk_level);
  }
  const params = new URLSearchParams();
  if (limit) params.append('limit', limit);
  if (type) params.append('type', type);
  if (risk_level) params.append('risk_level', risk_level);
  const qs = params.toString() ? `?${params.toString()}` : '';
  return fetchRealApi(`/api/history${qs}`);
}

export async function getHealth() {
  if (USE_MOCK) {
    return mockApi.mockGetHealth();
  }
  return fetchRealApi('/api/health');
}

