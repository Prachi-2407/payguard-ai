// PayGuard AI - Non-Invasive Link Inspection Content Script
// Target Hosts: web.whatsapp.com, mail.google.com, and local test playgrounds

(function () {
  console.log("PayGuard AI Content Script initialized.");

  const inspectedUrlsCache = new Map();
  const MAX_LINKS_PER_SCAN = 15;
  let debounceTimer = null;

  function isElementVisible(el) {
    if (!el || !el.getBoundingClientRect) return false;
    const rect = el.getBoundingClientRect();
    return (
      rect.width > 0 &&
      rect.height > 0 &&
      rect.top < (window.innerHeight || document.documentElement.clientHeight) + 300 &&
      rect.bottom > -300
    );
  }

  function shouldInspectHref(href) {
    if (!href || typeof href !== "string") return false;
    const lower = href.toLowerCase().trim();
    if (!lower.startsWith("http://") && !lower.startsWith("https://")) return false;

    // Ignore internal navigation links
    if (
      lower.includes("mail.google.com") ||
      lower.includes("accounts.google.com") ||
      lower.includes("web.whatsapp.com") ||
      lower.includes("faq.whatsapp.com")
    ) {
      return false;
    }

    return true;
  }

  function injectBadge(linkEl, result) {
    if (linkEl.nextSibling && linkEl.nextSibling.classList && linkEl.nextSibling.classList.contains("payguard-link-badge")) {
      return; // Already badged
    }

    const level = (result.risk_level || "LOW").toUpperCase();
    const score = result.risk_score || 0;
    const badge = document.createElement("span");
    badge.className = `payguard-link-badge payguard-${level.toLowerCase()}`;
    badge.setAttribute("data-payguard-ignore", "true");

    let icon = "🛡️";
    let text = "SAFE";
    if (level === "HIGH") {
      icon = "🚨";
      text = "DANGER";
    } else if (level === "MEDIUM") {
      icon = "⚠️";
      text = "CAUTION";
    }

    badge.innerHTML = `<span class="payguard-icon">${icon}</span><span class="payguard-text">${text}</span>`;
    badge.title = `PayGuard AI Risk: ${score}/100 (${level})\nVerdict: ${result.verdict || ''}\nAction: ${result.recommended_action || ''}`;

    // Non-interfering: click prevents default on badge itself so it doesn't navigate
    badge.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      alert(`PayGuard AI Security Assessment:\n\nTarget: ${linkEl.href}\nRisk Score: ${score}/100 [${level}]\nVerdict: ${result.verdict}\n\n${result.explanation}\n\nRecommendation: ${result.recommended_action}`);
    });

    linkEl.insertAdjacentElement("afterend", badge);
  }

  function scanVisibleLinks() {
    const candidateLinks = Array.from(document.querySelectorAll("a[href]:not([data-payguard-inspected])"));
    let scannedCount = 0;

    for (const link of candidateLinks) {
      if (scannedCount >= MAX_LINKS_PER_SCAN) break;
      const href = link.href;

      if (!shouldInspectHref(href)) {
        link.setAttribute("data-payguard-inspected", "ignored");
        continue;
      }

      if (!isElementVisible(link)) {
        continue;
      }

      link.setAttribute("data-payguard-inspected", "true");
      scannedCount++;

      // Check cache first
      if (inspectedUrlsCache.has(href)) {
        injectBadge(link, inspectedUrlsCache.get(href));
        continue;
      }

      // Query background service worker
      chrome.runtime.sendMessage({ action: "CHECK_URL", url: href }, (response) => {
        if (response) {
          inspectedUrlsCache.set(href, response);
          injectBadge(link, response);
        }
      });
    }
  }

  function debouncedScan() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(scanVisibleLinks, 600);
  }

  // Observe DOM modifications (messages arriving in WhatsApp Web or emails in Gmail)
  const observer = new MutationObserver((mutations) => {
    let hasRelevantNodes = false;
    for (const m of mutations) {
      if (m.addedNodes.length > 0) {
        hasRelevantNodes = true;
        break;
      }
    }
    if (hasRelevantNodes) {
      debouncedScan();
    }
  });

  observer.observe(document.body || document.documentElement, {
    childList: true,
    subtree: true,
  });

  // Initial scan after page load
  window.addEventListener("load", debouncedScan);
  setTimeout(debouncedScan, 1200);
})();

