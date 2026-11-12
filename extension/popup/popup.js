// PayGuard AI - Popup Script

document.addEventListener("DOMContentLoaded", () => {
  const urlInput = document.getElementById("url-input");
  const checkBtn = document.getElementById("check-btn");
  const loading = document.getElementById("loading");
  const resultCard = document.getElementById("result-card");
  const emptyState = document.getElementById("empty-state");
  const optionsBtn = document.getElementById("options-btn");

  const gaugeScore = document.getElementById("gauge-score");
  const riskGauge = document.querySelector(".risk-gauge");
  const riskBadge = document.getElementById("risk-badge");
  const verdictText = document.getElementById("verdict-text");
  const signalsList = document.getElementById("signals-list");
  const actionText = document.getElementById("action-text");

  // Open Options page
  optionsBtn.addEventListener("click", (e) => {
    e.preventDefault();
    if (chrome.runtime.openOptionsPage) {
      chrome.runtime.openOptionsPage();
    } else {
      window.open(chrome.runtime.getURL("options/options.html"));
    }
  });

  // Check if active tab has a URL to prefill
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs && tabs[0] && tabs[0].url && tabs[0].url.startsWith("http")) {
      const activeUrl = tabs[0].url;
      // If not empty, fill
      if (!urlInput.value) {
        urlInput.value = activeUrl;
      }
    }
  });

  // Check for any recently stored context menu scan result
  chrome.runtime.sendMessage({ action: "GET_LAST_RESULT" }, (response) => {
    if (response && response.result) {
      if (response.target && response.target.startsWith("Link:")) {
        urlInput.value = response.target.replace("Link: ", "");
      }
      displayResult(response.result);
    }
  });

  // Handle Check Button Click
  checkBtn.addEventListener("click", () => {
    const rawUrl = urlInput.value.trim();
    if (!rawUrl) {
      urlInput.focus();
      return;
    }

    loading.classList.remove("hidden");
    resultCard.classList.add("hidden");
    emptyState.classList.add("hidden");

    chrome.runtime.sendMessage({ action: "CHECK_URL", url: rawUrl }, (result) => {
      loading.classList.add("hidden");
      if (result) {
        displayResult(result);
      } else {
        emptyState.innerHTML = "<p style='color:#ef4444;'>Failed to inspect link. Check backend connection.</p>";
        emptyState.classList.remove("hidden");
      }
    });
  });

  // Allow pressing Enter in text field
  urlInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      checkBtn.click();
    }
  });

  function displayResult(res) {
    emptyState.classList.add("hidden");
    resultCard.classList.remove("hidden");

    const score = res.risk_score || 0;
    const level = (res.risk_level || "LOW").toUpperCase();

    gaugeScore.textContent = score;

    // Reset classes
    riskGauge.className = "risk-gauge";
    riskBadge.className = "badge";

    if (level === "HIGH") {
      riskGauge.classList.add("high");
      riskBadge.classList.add("high");
      riskBadge.textContent = "CRITICAL RISK";
    } else if (level === "MEDIUM") {
      riskGauge.classList.add("medium");
      riskBadge.classList.add("medium");
      riskBadge.textContent = "SUSPICIOUS";
    } else {
      riskBadge.classList.add("low");
      riskBadge.textContent = "SAFE";
    }

    verdictText.textContent = res.verdict || (level === "HIGH" ? "Do not proceed" : "Safe to proceed");

    // Render Top 3 Signals
    signalsList.innerHTML = "";
    const signals = res.signals || [];
    if (signals.length === 0) {
      signalsList.innerHTML = "<div class='signal-item'><div class='signal-name'>No risk signals detected</div><div class='signal-detail'>Verified by automated threat rules.</div></div>";
    } else {
      const top3 = signals.slice(0, 3);
      top3.forEach((s) => {
        const item = document.createElement("div");
        item.className = `signal-item ${s.severity || 'low'}`;
        item.innerHTML = `
          <div class="signal-name">${escapeHtml(s.name)}</div>
          <div class="signal-detail">${escapeHtml(s.detail)}</div>
        `;
        signalsList.appendChild(item);
      });
    }

    actionText.textContent = res.recommended_action || "Verify link authenticity before entering sensitive credentials.";
  }

  function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/[&<>"']/g, (m) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;"
    }[m]));
  }
});

