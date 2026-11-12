// PayGuard AI - Options Script

const DEFAULT_MAIN_API = "http://localhost:8000";
const DEFAULT_EXTRAS_API = "http://localhost:8001";

document.addEventListener("DOMContentLoaded", () => {
  const mainApiInput = document.getElementById("main-api");
  const extrasApiInput = document.getElementById("extras-api");
  const saveBtn = document.getElementById("save-btn");
  const resetBtn = document.getElementById("reset-btn");
  const statusMsg = document.getElementById("status-msg");

  // Load existing settings
  chrome.storage.local.get(["mainApiUrl", "extrasApiUrl"], (items) => {
    mainApiInput.value = items.mainApiUrl || DEFAULT_MAIN_API;
    extrasApiInput.value = items.extrasApiUrl || DEFAULT_EXTRAS_API;
  });

  // Save settings
  saveBtn.addEventListener("click", () => {
    const mainVal = mainApiInput.value.trim() || DEFAULT_MAIN_API;
    const extrasVal = extrasApiInput.value.trim() || DEFAULT_EXTRAS_API;

    chrome.storage.local.set(
      {
        mainApiUrl: mainVal,
        extrasApiUrl: extrasVal,
      },
      () => {
        statusMsg.textContent = "Settings saved successfully!";
        setTimeout(() => {
          statusMsg.textContent = "";
        }, 3000);
      }
    );
  });

  // Reset to defaults
  resetBtn.addEventListener("click", () => {
    mainApiInput.value = DEFAULT_MAIN_API;
    extrasApiInput.value = DEFAULT_EXTRAS_API;
    chrome.storage.local.remove(["mainApiUrl", "extrasApiUrl"], () => {
      statusMsg.textContent = "Reset to default endpoints.";
      setTimeout(() => {
        statusMsg.textContent = "";
      }, 3000);
    });
  });
});

