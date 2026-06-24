const DEFAULT_SERVER_URL = "http://127.0.0.1:8766";

function getStorage(defaults) {
  return new Promise((resolve) => chrome.storage.local.get(defaults, resolve));
}

function setStorage(values) {
  return new Promise((resolve) => chrome.storage.local.set(values, resolve));
}

function showStatus(text) {
  document.getElementById("status").textContent = text;
}

async function loadOptions() {
  const values = await getStorage({ serverUrl: DEFAULT_SERVER_URL, token: "" });
  document.getElementById("serverUrl").value = values.serverUrl || DEFAULT_SERVER_URL;
  document.getElementById("token").value = values.token || "";
}

async function saveOptions() {
  const serverUrl = document.getElementById("serverUrl").value.trim() || DEFAULT_SERVER_URL;
  const token = document.getElementById("token").value.trim();
  await setStorage({ serverUrl, token });
  showStatus("Saved.");
}

async function testServer() {
  await saveOptions();
  const serverUrl = document.getElementById("serverUrl").value.trim() || DEFAULT_SERVER_URL;
  try {
    const response = await fetch(`${serverUrl.replace(/\/$/, "")}/health`);
    const data = await response.json();
    if (!response.ok || !data.ok) {
      throw new Error(data.error || `HTTP ${response.status}`);
    }
    showStatus(`Connected.\nRepository: ${data.repoRoot}`);
  } catch (error) {
    showStatus(`Server test failed: ${error.message}`);
  }
}

document.getElementById("save").addEventListener("click", saveOptions);
document.getElementById("test").addEventListener("click", testServer);
loadOptions();
