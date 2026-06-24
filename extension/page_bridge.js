(() => {
  if (window.__anirudhanLeetcodeBridgeInstalled) {
    return;
  }
  window.__anirudhanLeetcodeBridgeInstalled = true;

  function readMonaco() {
    const editor = window.monaco && window.monaco.editor;
    if (!editor || typeof editor.getModels !== "function") {
      return null;
    }
    const models = editor.getModels();
    if (!models.length) {
      return null;
    }
    const model = models.reduce((best, current) => {
      if (!best) {
        return current;
      }
      return current.getValue().length > best.getValue().length ? current : best;
    }, null);
    return {
      code: model.getValue(),
      languageId: typeof model.getLanguageId === "function" ? model.getLanguageId() : ""
    };
  }

  window.addEventListener("message", (event) => {
    const message = event.data || {};
    if (
      event.source !== window ||
      message.source !== "anirudhan-leetcode-content" ||
      message.type !== "GET_EDITOR"
    ) {
      return;
    }
    window.postMessage(
      {
        source: "anirudhan-leetcode-page",
        type: "EDITOR_DATA",
        requestId: message.requestId,
        payload: readMonaco()
      },
      "*"
    );
  });
})();

