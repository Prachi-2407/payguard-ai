// src/components/OfflineBanner.jsx
import React, { useState, useEffect } from 'react';
import { WifiOff, AlertCircle } from 'lucide-react';
import { USE_MOCK, API_BASE_URL } from '../config';
import { getHealth } from '../api/client';

export function OfflineBanner() {
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    if (USE_MOCK) return;

    let mounted = true;
    const check = async () => {
      try {
        await getHealth();
        if (mounted) setOffline(false);
      } catch (err) {
        if (mounted) setOffline(true);
      }
    };

    check();
    const interval = setInterval(check, 10000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  if (!offline) return null;

  return (
    <div className="bg-amber-500 text-slate-950 px-4 py-2 text-xs font-semibold flex items-center justify-center space-x-2 shadow-sm">
      <WifiOff className="w-4 h-4" />
      <span>
        Backend API server is unreachable at {API_BASE_URL}. Operating in offline demo fallback mode.
      </span>
    </div>
  );
}

