(() => {
  const DEFAULT_SERVER_URL = "http://127.0.0.1:8766";
  const TOKEN_HEADER = "X-Local-LeetCode-Token";
  const CONTENT_SOURCE = "anirudhan-leetcode-content";
  const PAGE_SOURCE = "anirudhan-leetcode-page";
  const ALGORITHM_CATEGORIES = [
    "Backtracking",
    "Basic Array and String",
    "Binary Search",
    "Bit Manipulation",
    "Dynamic Programming",
    "Graph DFS and BFS",
    "Greedy",
    "Hash Map and Frequency",
    "Heap and Priority Queue",
    "Intervals",
    "Linked List",
    "Prefix Sum and Difference Array",
    "Shortest Path and Weighted Graph",
    "Sliding Window",
    "Stack and Monotonic Stack",
    "Topological Sort and Dependency Graphs",
    "Trees and BST",
    "Trie",
    "Two Pointers",
    "Union Find - Disjoint Set Union"
  ];
  const ALGORITHM_RULES = [
    ["Two Pointers", ["Two Pointers"]],
    ["Sliding Window", ["Sliding Window"]],
    ["Prefix Sum and Difference Array", ["Prefix Sum"]],
    ["Stack and Monotonic Stack", ["Stack", "Monotonic Stack"]],
    ["Binary Search", ["Binary Search"]],
    ["Linked List", ["Linked List"]],
    ["Trees and BST", ["Tree", "Binary Tree", "Binary Search Tree"]],
    ["Heap and Priority Queue", ["Heap (Priority Queue)"]],
    ["Backtracking", ["Backtracking"]],
    ["Intervals", ["Interval"]],
    ["Graph DFS and BFS", ["Graph", "Depth-First Search", "Breadth-First Search"]],
    ["Topological Sort and Dependency Graphs", ["Topological Sort"]],
    ["Union Find - Disjoint Set Union", ["Union Find"]],
    ["Greedy", ["Greedy"]],
    ["Dynamic Programming", ["Dynamic Programming"]],
    ["Trie", ["Trie"]],
    ["Bit Manipulation", ["Bit Manipulation"]],
    ["Shortest Path and Weighted Graph", ["Shortest Path"]],
    ["Hash Map and Frequency", ["Hash Table", "Counting"]]
  ];

  if (window.__anirudhanLeetcodeContentInstalled) {
    return;
  }
  window.__anirudhanLeetcodeContentInstalled = true;

  function getStorage(defaults) {
    return new Promise((resolve) => chrome.storage.local.get(defaults, resolve));
  }

  function setStorage(values) {
    return new Promise((resolve) => chrome.storage.local.set(values, resolve));
  }

  function injectBridge() {
    if (document.getElementById("anirudhan-leetcode-bridge")) {
      return;
    }
    const script = document.createElement("script");
    script.id = "anirudhan-leetcode-bridge";
    script.src = chrome.runtime.getURL("page_bridge.js");
    script.onload = () => script.remove();
    (document.head || document.documentElement).appendChild(script);
  }

  function requestEditorData() {
    injectBridge();
    return new Promise((resolve) => {
      const requestId = `${Date.now()}-${Math.random()}`;
      const timeout = window.setTimeout(() => {
        window.removeEventListener("message", onMessage);
        resolve(null);
      }, 1500);

      function onMessage(event) {
        const message = event.data || {};
        if (
          event.source !== window ||
          message.source !== PAGE_SOURCE ||
          message.type !== "EDITOR_DATA" ||
          message.requestId !== requestId
        ) {
          return;
        }
        window.clearTimeout(timeout);
        window.removeEventListener("message", onMessage);
        resolve(message.payload || null);
      }

      window.addEventListener("message", onMessage);
      window.postMessage(
        { source: CONTENT_SOURCE, type: "GET_EDITOR", requestId },
        "*"
      );
    });
  }

  function titleSlugFromUrl() {
    const match = window.location.pathname.match(/^\/problems\/([^/]+)/);
    return match ? match[1] : "";
  }

  async function fetchQuestion(titleSlug) {
    const query = `
      query localLeetCodeQuestion($titleSlug: String!) {
        question(titleSlug: $titleSlug) {
          questionFrontendId
          title
          titleSlug
          difficulty
          content
          topicTags { name slug }
        }
      }
    `;
    const response = await fetch("https://leetcode.com/graphql/", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, variables: { titleSlug } })
    });
    if (!response.ok) {
      throw new Error(`LeetCode GraphQL returned ${response.status}`);
    }
    const data = await response.json();
    if (data.errors && data.errors.length) {
      throw new Error(data.errors.map((error) => error.message).join("; "));
    }
    if (!data.data || !data.data.question) {
      throw new Error("LeetCode question data was not found");
    }
    return data.data.question;
  }

  function fallbackQuestion(titleSlug) {
    const bodyText = document.body.innerText || "";
    const heading =
      document.querySelector('[data-cy="question-title"]') ||
      document.querySelector("h1");
    const headingText = heading ? heading.textContent.trim() : "";
    const headingMatch = headingText.match(/^(\d+)\.\s*(.+)$/);
    const idMatch = bodyText.match(/\b(\d+)\.\s+[A-Z][^\n]+/);
    const difficultyMatch = bodyText.match(/\b(Easy|Medium|Hard)\b/);
    return {
      questionFrontendId: headingMatch ? headingMatch[1] : idMatch ? idMatch[1] : "",
      title: headingMatch ? headingMatch[2] : headingText || titleSlug,
      titleSlug,
      difficulty: difficultyMatch ? difficultyMatch[1] : "Medium",
      content: "",
      topicTags: []
    };
  }

  function visible(element) {
    const style = window.getComputedStyle(element);
    const rect = element.getBoundingClientRect();
    return style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0;
  }

  function textOf(element) {
    if (!element) {
      return "";
    }
    if ("value" in element) {
      return String(element.value || "").trim();
    }
    return String(element.innerText || element.textContent || "").trim();
  }

  function fallbackCode() {
    const candidates = Array.from(
      document.querySelectorAll("textarea, [contenteditable='true']")
    )
      .filter(visible)
      .map(textOf)
      .filter((value) => value.length > 40);
    return (
      candidates.find((value) =>
        /class Solution|def\s+\w+\(|public\s+class|function\s+\w+\(/.test(value)
      ) || ""
    );
  }

  function parseMetric(pageText, label, unit) {
    const compact = pageText.replace(/\s+/g, " ");
    const beatsPattern = new RegExp(
      `${label}\\s+([0-9.]+)\\s*${unit}\\s+Beats\\s+([0-9.]+)%`,
      "i"
    );
    const simplePattern = new RegExp(`${label}\\s+([0-9.]+)\\s*${unit}`, "i");
    const beats = compact.match(beatsPattern);
    if (beats) {
      return { value: beats[1], unit, percentile: beats[2] };
    }
    const simple = compact.match(simplePattern);
    return simple ? { value: simple[1], unit, percentile: "" } : null;
  }

  function cleanNumber(value) {
    return value ? String(Number(value)) : "";
  }

  function formatMetric(metric) {
    if (!metric) {
      return "";
    }
    const value = cleanNumber(metric.value);
    const percentile = cleanNumber(metric.percentile);
    return percentile
      ? `${value} ${metric.unit} (${percentile}%)`
      : `${value} ${metric.unit}`;
  }

  function defaultCommitMessage(runtime, memory) {
    const time = formatMetric(runtime);
    const space = formatMetric(memory);
    return time && space ? `Time: ${time}, Space: ${space}` : "";
  }

  function buildReadme(question) {
    const id = String(question.questionFrontendId || "").trim();
    const title = String(question.title || question.titleSlug || "").trim();
    const difficulty = String(question.difficulty || "").trim();
    const slug = String(question.titleSlug || titleSlugFromUrl()).trim();
    const content = String(question.content || "").trim();
    const heading = `<h2><a href="https://leetcode.com/problems/${slug}">${id}. ${title}</a></h2>`;
    return `${heading}<h3>${difficulty}</h3><hr>${content}`.trim();
  }

  function topicNames(question) {
    return (question.topicTags || [])
      .map((topic) => String(topic.name || "").trim())
      .filter(Boolean);
  }

  function suggestAlgorithm(question) {
    const topics = new Set(topicNames(question));
    for (const [algorithm, matchingTopics] of ALGORITHM_RULES) {
      if (matchingTopics.some((topic) => topics.has(topic))) {
        return algorithm;
      }
    }
    return "Basic Array and String";
  }

  async function collectPageData() {
    const titleSlug = titleSlugFromUrl();
    if (!titleSlug) {
      throw new Error("Open a LeetCode problem page first");
    }
    let question;
    try {
      question = await fetchQuestion(titleSlug);
    } catch (error) {
      question = fallbackQuestion(titleSlug);
    }
    const editor = (await requestEditorData()) || {};
    const pageText = document.body.innerText || "";
    const runtime = parseMetric(pageText, "Runtime", "ms");
    const memory = parseMetric(pageText, "Memory", "MB");
    return {
      question,
      code: String(editor.code || fallbackCode() || ""),
      langSlug: String(editor.languageId || ""),
      accepted: /\bAccepted\b/i.test(pageText),
      commitMessage: defaultCommitMessage(runtime, memory),
      readme: buildReadme(question)
    };
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function problemFolder(question) {
    const id = String(question.questionFrontendId || "").trim();
    const slug = String(question.titleSlug || titleSlugFromUrl()).trim();
    return /^\d+$/.test(id) ? `${String(Number(id)).padStart(4, "0")}-${slug}` : slug;
  }

  function algorithmOptions(selected) {
    return ALGORITHM_CATEGORIES.map((algorithm) => {
      const selectedAttribute = algorithm === selected ? " selected" : "";
      return `<option value="${escapeHtml(algorithm)}"${selectedAttribute}>${escapeHtml(algorithm)}</option>`;
    }).join("");
  }

  async function postLocal(path, payload, options) {
    const serverUrl = (options.serverUrl || DEFAULT_SERVER_URL).replace(/\/$/, "");
    const response = await fetch(`${serverUrl}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        [TOKEN_HEADER]: options.token || ""
      },
      body: JSON.stringify(payload)
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok || data.ok === false) {
      throw new Error(data.error || `Local server returned ${response.status}`);
    }
    return data;
  }

  function payloadFromModal(modal) {
    return {
      problem: {
        frontendId: modal.querySelector("[name='frontendId']").value.trim(),
        title: modal.querySelector("[name='title']").value.trim(),
        slug: modal.querySelector("[name='slug']").value.trim(),
        difficulty: modal.querySelector("[name='difficulty']").value,
        topics: modal
          .querySelector("[name='topics']")
          .value.split(",")
          .map((topic) => topic.trim())
          .filter(Boolean)
      },
      algorithm: modal.querySelector("[name='algorithm']").value,
      language: modal.querySelector("[name='language']").value.trim(),
      langSlug: modal.querySelector("[name='langSlug']").value.trim(),
      code: modal.querySelector("[name='code']").value,
      readmeContent: modal.querySelector("[name='readme']").value,
      commitMessage: modal.querySelector("[name='commitMessage']").value.trim(),
      overwrite: modal.querySelector("[name='overwrite']").checked
    };
  }

  function connectionOptions(modal) {
    return {
      serverUrl: modal.querySelector("[name='serverUrl']").value.trim() || DEFAULT_SERVER_URL,
      token: modal.querySelector("[name='token']").value.trim()
    };
  }

  function setStatus(modal, text) {
    modal.querySelector(".lls-status").textContent = text;
  }

  function showOverwriteConfirmation(modal, preview) {
    modal.querySelector(".lls-confirm-row").hidden = !preview.exists;
  }

  async function preview(modal) {
    const options = connectionOptions(modal);
    await setStorage(options);
    const result = await postLocal("/preview", payloadFromModal(modal), options);
    showOverwriteConfirmation(modal, result.preview);
    setStatus(modal, JSON.stringify(result.preview, null, 2));
    return result.preview;
  }

  async function save(modal) {
    const options = connectionOptions(modal);
    await setStorage(options);
    let payload = payloadFromModal(modal);
    if (!payload.code.trim()) {
      throw new Error("Solution code is empty. Paste it into the code field.");
    }
    if (!payload.readmeContent.trim()) {
      throw new Error("README content is empty.");
    }
    if (!payload.commitMessage) {
      throw new Error("Commit message is required.");
    }
    const previewResult = await postLocal("/preview", payload, options);
    showOverwriteConfirmation(modal, previewResult.preview);
    payload = payloadFromModal(modal);
    if (previewResult.preview.exists && !payload.overwrite) {
      throw new Error("This problem already exists. Check the overwrite confirmation first.");
    }
    const result = await postLocal("/save", payload, options);
    setStatus(modal, JSON.stringify(result, null, 2));
  }

  async function showModal(pageData) {
    const saved = await getStorage({ serverUrl: DEFAULT_SERVER_URL, token: "" });
    const question = pageData.question;
    const difficulty = String(question.difficulty || "Medium").toLowerCase();
    const algorithm = suggestAlgorithm(question);
    const folder = problemFolder(question);
    const overlay = document.createElement("div");
    overlay.className = "lls-overlay";
    overlay.innerHTML = `
      <section class="lls-modal" role="dialog" aria-modal="true">
        <header>
          <h2>Save ${escapeHtml(folder || "LeetCode problem")}</h2>
          <button class="lls-secondary" data-action="close" type="button">Close</button>
        </header>
        <div class="lls-grid">
          <label>
            Server URL
            <input name="serverUrl" value="${escapeHtml(saved.serverUrl || DEFAULT_SERVER_URL)}">
          </label>
          <label>
            Local token
            <input name="token" type="password" value="${escapeHtml(saved.token || "")}">
          </label>
          <label>
            Frontend ID
            <input name="frontendId" value="${escapeHtml(question.questionFrontendId || "")}">
          </label>
          <label>
            Slug
            <input name="slug" value="${escapeHtml(question.titleSlug || titleSlugFromUrl())}">
          </label>
          <label>
            Title
            <input name="title" value="${escapeHtml(question.title || "")}">
          </label>
          <label>
            Difficulty
            <select name="difficulty">
              <option value="easy"${difficulty === "easy" ? " selected" : ""}>easy</option>
              <option value="medium"${difficulty === "medium" ? " selected" : ""}>medium</option>
              <option value="hard"${difficulty === "hard" ? " selected" : ""}>hard</option>
            </select>
          </label>
          <label class="lls-full">
            Primary algorithm
            <select name="algorithm">${algorithmOptions(algorithm)}</select>
          </label>
          <label class="lls-full">
            LeetCode topics
            <input name="topics" value="${escapeHtml(topicNames(question).join(", "))}">
          </label>
          <label>
            Language
            <input name="language" value="${escapeHtml(pageData.langSlug)}" placeholder="python3">
          </label>
          <label>
            Internal language slug
            <input name="langSlug" value="${escapeHtml(pageData.langSlug)}" placeholder="python3">
          </label>
          <label class="lls-full">
            Commit message
            <input name="commitMessage" value="${escapeHtml(pageData.commitMessage)}" placeholder="Time: 0 ms (100%), Space: 20 MB (90%)">
          </label>
          <label class="lls-full">
            Problem README
            <textarea name="readme">${escapeHtml(pageData.readme)}</textarea>
          </label>
          <label class="lls-full">
            Solution code
            <textarea class="lls-code" name="code">${escapeHtml(pageData.code)}</textarea>
          </label>
          <label class="lls-confirm-row lls-full" hidden>
            <input name="overwrite" type="checkbox">
            Existing folder found. Confirm overwrite.
          </label>
        </div>
        <pre class="lls-status">${escapeHtml(
          pageData.accepted
            ? "Accepted result detected. Preview, review, then save."
            : "Accepted status was not detected. You can still review and save manually."
        )}</pre>
        <footer>
          <span>${escapeHtml(folder)}</span>
          <div class="lls-actions">
            <button class="lls-secondary" data-action="preview" type="button">Preview</button>
            <button data-action="save" type="button">Save and commit</button>
          </div>
        </footer>
      </section>
    `;
    document.body.appendChild(overlay);
    const modal = overlay.querySelector(".lls-modal");

    const close = () => overlay.remove();
    overlay.addEventListener("click", (event) => {
      if (event.target === overlay || event.target.dataset.action === "close") {
        close();
      }
    });
    document.addEventListener(
      "keydown",
      (event) => {
        if (event.key === "Escape") {
          close();
        }
      },
      { once: true }
    );
    modal.querySelector("[data-action='preview']").addEventListener("click", async () => {
      try {
        setStatus(modal, "Previewing...");
        await preview(modal);
      } catch (error) {
        setStatus(modal, `Preview failed: ${error.message}`);
      }
    });
    modal.querySelector("[data-action='save']").addEventListener("click", async () => {
      try {
        setStatus(modal, "Saving and committing...");
        await save(modal);
      } catch (error) {
        setStatus(modal, `Save failed: ${error.message}`);
      }
    });
  }

  function installButton() {
    if (document.querySelector(".lls-save-button")) {
      return;
    }
    const button = document.createElement("button");
    button.className = "lls-save-button";
    button.type = "button";
    button.textContent = "Save to Local Repo";
    button.addEventListener("click", async () => {
      button.disabled = true;
      button.textContent = "Reading...";
      try {
        await showModal(await collectPageData());
      } catch (error) {
        window.alert(`Anirudhan LeetCode Sync failed: ${error.message}`);
      } finally {
        button.disabled = false;
        button.textContent = "Save to Local Repo";
      }
    });
    document.documentElement.appendChild(button);
  }

  injectBridge();
  installButton();
  new MutationObserver(installButton).observe(document.documentElement, {
    childList: true,
    subtree: true
  });
})();
