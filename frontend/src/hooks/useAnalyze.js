// src/hooks/useAnalyze.js
import { useState, useCallback } from 'react';

export function useAnalyze(analyzeFn) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const execute = useCallback(async (payload) => {
    setLoading(true);
    setError(null);
    try {
      const data = await analyzeFn(payload);
      setResult(data);

      // Auditory / vibration feedback for high-risk warnings
      if (data.risk_level === 'HIGH') {
        if ('vibrate' in navigator) {
          try { navigator.vibrate([200, 100, 200]); } catch (e) {}
        }
      }

      return data;
    } catch (err) {
      const msg = err.data?.error || err.message || 'An error occurred during analysis';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [analyzeFn]);

  const reset = useCallback(() => {
    setLoading(false);
    setError(null);
    setResult(null);
  }, []);

  return { loading, error, result, execute, reset, setResult };
}

