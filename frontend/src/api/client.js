// src/api/client.js
import { USE_MOCK, API_BASE_URL, EXTRAS_API_URL } from '../config';
import * as mockApi from './mockApi';

// Sanitize base URLs
const cleanBaseUrl = (API_BASE_URL || 'https://payguard-ai-izry.onrender.com')
  .replace(/\/+$/, '')
  .replace(/\/api$/, '');

const cleanExtrasUrl = (EXTRAS_API_URL || cleanBaseUrl)
  .replace(/\/+$/, '')
  .replace(/\/api$/, '');

function fallbackExtras(endpoint, options = {}, url = '') {
  try {
    if (endpoint.includes('analyze/message')) {
      const body = options.body ? JSON.parse(options.body) : {};
      return mockApi.mockAnalyzeMessage(body);
    }
    if (endpoint.includes('reports')) {
      const body = options.body ? JSON.parse(options.body) : {};
      return mockApi.mockSubmitReport(body);
    }
    if (endpoint.includes('reputation')) {
      let val = '';
      try {
        const u = new URL(url, 'http://localhost');
        val = u.searchParams.get('value') || '';
      } catch (e) {}
      return mockApi.mockGetReputation(val);
    }
  } catch (e) {}
  return null;
}

async function fetchExtrasApi(endpoint, options = {}) {
  const url = `${cleanExtrasUrl}${endpoint}`;
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
      if (res.status === 404) {
        console.warn(`[PayGuard] Extras endpoint ${endpoint} not ready on ${cleanExtrasUrl}; using client fallback.`);
        const fallback = fallbackExtras(endpoint, options, url);
        if (fallback) return fallback;
      }
      const err = new Error(data.error || `Request failed with status ${res.status}`);
      err.status = res.status;
      err.data = data;
      throw err;
    }
    return data;
  } catch (error) {
    const fallback = fallbackExtras(endpoint, options, url);
    if (fallback) return fallback;

    if (error.status) throw error;
    const netErr = new Error("Unable to connect to PayGuard Extras service. Please ensure extras service is running on port 8001.");
    netErr.status = 503;
    netErr.data = { error: "Extras server unreachable at " + cleanExtrasUrl, code: 503 };
    throw netErr;
  }
}

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

export async function analyzeMessage(payload) {
  if (USE_MOCK) {
    return mockApi.mockAnalyzeMessage(payload);
  }
  return fetchExtrasApi('/api/ext/analyze/message', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function submitReport(payload) {
  if (USE_MOCK) {
    return mockApi.mockSubmitReport(payload);
  }
  return fetchExtrasApi('/api/ext/reports', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getReputation(value) {
  if (USE_MOCK) {
    return mockApi.mockGetReputation(value);
  }
  const params = new URLSearchParams({ value });
  return fetchExtrasApi(`/api/ext/reputation?${params.toString()}`);
}

