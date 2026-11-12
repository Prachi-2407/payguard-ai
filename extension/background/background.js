// PayGuard AI - Background Service Worker (Manifest V3)

const DEFAULT_MAIN_API = "http://localhost:8000";
const DEFAULT_EXTRAS_API = "http://localhost:8001";
const CACHE_TTL_MS = 10 * 60 * 1000; // 10 minutes

// In-memory cache: key -> { result, timestamp }
const scanCache = new Map();
// Ongoing in-flight requests to prevent duplicate network calls: key -> Promise
const inFlightRequests = new Map();

// Helper to get configured API URLs
async function getApiUrls() {
  return new Promise((resolve) => {
    chrome.storage.local.get(["mainApiUrl", "extrasApiUrl"], (items) => {
      resolve({
        mainApi: items.mainApiUrl || DEFAULT_MAIN_API,
        extrasApi: items.extrasApiUrl || DEFAULT_EXTRAS_API,
      });
    });
  });
}

// Setup Context Menus on installation
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "payguard-check-link-or-text",
    title: "Check with PayGuard AI",
    contexts: ["link", "selection"],
  });
  console.log("PayGuard AI context menus registered.");
});

// Context Menu Action Handler
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === "payguard-check-link-or-text") {
    if (info.linkUrl) {
      console.log("Context menu analyzing link:", info.linkUrl);
      const res = await checkUrlWithApi(info.linkUrl);
      handleScanResultNotification(res, "Link: " + info.linkUrl);
    } else if (info.selectionText) {
      console.log("Context menu analyzing selected text:", info.selectionText.slice(0, 50));
      const res = await checkTextWithApi(info.selectionText);
      handleScanResultNotification(res, "Selected Text");
    }
  }
});

function handleScanResultNotification(result, targetLabel) {
  if (!result) return;
  chrome.storage.local.set({ lastResult: result, lastTarget: targetLabel });

  if (result.risk_level === "HIGH") {
    chrome.notifications.create({
      type: "basic",
      iconUrl: chrome.runtime.getURL("icons/icon128.png"),
      title: "🚨 PayGuard AI High Risk Alert!",
      message: `Warning (${result.risk_score}/100): ${result.verdict}. ${result.recommended_action}`,
      priority: 2,
    });
  } else if (result.risk_level === "MEDIUM") {
    chrome.notifications.create({
      type: "basic",
      iconUrl: chrome.runtime.getURL("icons/icon48.png"),
      title: "⚠️ PayGuard AI Caution",
      message: `Score: ${result.risk_score}/100 - ${result.verdict}. Review signals in popup.`,
      priority: 1,
    });
  }
}

// Local lightweight URL heuristics fallback when backend is offline
function evaluateLocalUrlHeuristics(url) {
  let score = 20;
  const signals = [];
  const lower = url.toLowerCase();

  const suspiciousTlds = [".xyz", ".top", ".tk", ".ml", ".ga", ".click", ".buzz", ".site", ".online", ".icu", ".club"];
  for (const tld of suspiciousTlds) {
    if (lower.includes(tld)) {
      score += 45;
      signals.push({ name: "Suspicious TLD", severity: "high", detail: `Domain ends with high-abuse extension '${tld}'.` });
      break;
    }
  }

  const suspiciousKws = ["sbi", "hdfc", "icici", "paytm", "gpay", "kyc", "verify", "login", "update", "refund"];
  const matched = suspiciousKws.filter(k => lower.includes(k));
  if (matched.length > 0 && !lower.includes("sbi.co.in") && !lower.includes("hdfcbank.com") && !lower.includes("paytm.com")) {
    score += 40;
    signals.push({ name: "Banking Keyword Spoofing", severity: "high", detail: `Link embeds sensitive banking keywords: ${matched.join(", ")}.` });
  }

  score = Math.min(100, Math.max(0, score));
  const level = score >= 70 ? "HIGH" : score >= 40 ? "MEDIUM" : "LOW";
  const verdict = level === "HIGH" ? "Do not proceed" : level === "MEDIUM" ? "Proceed with caution" : "Safe to proceed";

  signals.push({ name: "Local Extension Heuristics", severity: "low", detail: "Analyzed locally by extension." });

  return {
    risk_score: score,
    risk_level: level,
    verdict: verdict,
    signals: signals,
    explanation: level === "HIGH" ? "CRITICAL: This link bears hallmarks of credential phishing." : "Link appears to have low detected risk.",
    recommended_action: level === "HIGH" ? "Do not open link or enter passwords." : "Safe to proceed.",
    analyzed_at: new Date().toISOString(),
    type: "url"
  };
}

// Check URL with caching and duplicate suppression
async function checkUrlWithApi(url) {
  const cacheKey = "url:" + url.trim().toLowerCase();

  // Check 10-minute cache
  const cached = scanCache.get(cacheKey);
  if (cached && (Date.now() - cached.timestamp < CACHE_TTL_MS)) {
    return cached.result;
  }

  // Deduplicate simultaneous requests
  if (inFlightRequests.has(cacheKey)) {
    return inFlightRequests.get(cacheKey);
  }

  const promise = (async () => {
    const { mainApi } = await getApiUrls();
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2500);

      const resp = await fetch(`${mainApi.replace(/\/+$/, "")}/api/analyze/url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url.trim() }),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (resp.ok) {
        const data = await resp.json();
        scanCache.set(cacheKey, { result: data, timestamp: Date.now() });
        return data;
      } else {
        const fallback = evaluateLocalUrlHeuristics(url);
        scanCache.set(cacheKey, { result: fallback, timestamp: Date.now() });
        return fallback;
      }
    } catch (e) {
      console.warn("Main API unreachable, using extension local heuristics:", e);
      const fallback = evaluateLocalUrlHeuristics(url);
      scanCache.set(cacheKey, { result: fallback, timestamp: Date.now() });
      return fallback;
    } finally {
      inFlightRequests.delete(cacheKey);
    }
  })();

  inFlightRequests.set(cacheKey, promise);
  return promise;
}

// Check Message Text
async function checkTextWithApi(text) {
  const { extrasApi } = await getApiUrls();
  const cacheKey = "msg:" + text.trim().slice(0, 100);

  const cached = scanCache.get(cacheKey);
  if (cached && (Date.now() - cached.timestamp < CACHE_TTL_MS)) {
    return cached.result;
  }

  try {
    const resp = await fetch(`${extrasApi.replace(/\/+$/, "")}/api/ext/analyze/message`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text.trim(), source: "other" }),
    });

    if (resp.ok) {
      const data = await resp.json();
      scanCache.set(cacheKey, { result: data, timestamp: Date.now() });
      return data;
    } else {
      throw new Error(`Extras API error: ${resp.status}`);
    }
  } catch (e) {
    console.warn("Extras API unreachable for text check:", e);
    return {
      risk_score: 50,
      risk_level: "MEDIUM",
      verdict: "Service Offline",
      signals: [{ name: "Service Unreachable", severity: "medium", detail: "Could not connect to Extras Intelligence API." }],
      explanation: "Unable to analyze text because the PayGuard Extras service is offline.",
      recommended_action: "Verify the extras service is running on port 8001.",
      analyzed_at: new Date().toISOString(),
      type: "message",
      extracted: { urls: [], upi_ids: [], phone_numbers: [], scam_category: "OTHER" }
    };
  }
}

// Runtime messaging listener
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "CHECK_URL") {
    checkUrlWithApi(request.url).then((res) => sendResponse(res));
    return true; // async sendResponse
  }
  if (request.action === "CHECK_TEXT") {
    checkTextWithApi(request.text).then((res) => sendResponse(res));
    return true;
  }
  if (request.action === "GET_LAST_RESULT") {
    chrome.storage.local.get(["lastResult", "lastTarget"], (items) => {
      sendResponse({ result: items.lastResult, target: items.lastTarget });
    });
    return true;
  }
});

