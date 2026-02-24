(function () {
  "use strict";

  var DEFAULT_CONFIG = {
    placeholder: "Search...",
    apiEndpoint: "/widget/search",
    debounceMs: 300,
    apiKey: "",
    widgetId: "",
    apiBase: "",
  };

  class RetrievaSearchBar {
    constructor(targetSelector, config) {
      this.config = Object.assign({}, DEFAULT_CONFIG, config || {});
      this.target =
        typeof targetSelector === "string"
          ? document.querySelector(targetSelector)
          : targetSelector;
      this._debounceTimer = null;
      this._init();
    }

    _init() {
      this._createSearchBar();
      this._attachEvents();
    }

    _createSearchBar() {
      this.container = document.createElement("div");
      this.container.className = "retrieva-search";
      this.container.innerHTML =
        '<div class="retrieva-search-input-wrapper">' +
        '<svg class="retrieva-search-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
        '<circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>' +
        "</svg>" +
        '<input type="text" class="retrieva-search-input" placeholder="' +
        this.config.placeholder +
        '" />' +
        "</div>" +
        '<div class="retrieva-search-results"></div>';
      this.target.appendChild(this.container);
    }

    _attachEvents() {
      var self = this;
      var input = this.container.querySelector(".retrieva-search-input");
      input.addEventListener("input", function () {
        clearTimeout(self._debounceTimer);
        var query = input.value.trim();
        if (!query) {
          self._clearResults();
          return;
        }
        self._debounceTimer = setTimeout(function () {
          self._search(query);
        }, self.config.debounceMs);
      });
    }

    async _search(query) {
      var resultsEl = this.container.querySelector(".retrieva-search-results");
      try {
        var endpoint = this.config.apiBase + this.config.apiEndpoint;
        var headers = { "Content-Type": "application/json" };
        if (this.config.apiKey) {
          headers["Authorization"] = "Bearer " + this.config.apiKey;
        }
        var response = await fetch(endpoint, {
          method: "POST",
          headers: headers,
          body: JSON.stringify({
            query: query,
            widget_id: this.config.widgetId,
          }),
        });
        var data = await response.json();
        var results = data.results || [];
        resultsEl.innerHTML = "";
        if (results.length === 0) {
          resultsEl.innerHTML =
            '<div class="retrieva-search-empty">No results found</div>';
          resultsEl.classList.add("visible");
          return;
        }
        results.forEach(function (result) {
          var item = document.createElement("div");
          item.className = "retrieva-search-result-item";
          item.innerHTML =
            '<div class="retrieva-search-result-title">' +
            (result.title || "") +
            "</div>" +
            '<div class="retrieva-search-result-snippet">' +
            (result.content || "") +
            "</div>";
          resultsEl.appendChild(item);
        });
        resultsEl.classList.add("visible");
      } catch (err) {
        resultsEl.innerHTML =
          '<div class="retrieva-search-empty">Search failed</div>';
        resultsEl.classList.add("visible");
      }
    }

    _clearResults() {
      var resultsEl = this.container.querySelector(".retrieva-search-results");
      resultsEl.innerHTML = "";
      resultsEl.classList.remove("visible");
    }
  }

  window.RetrievaSearchBar = RetrievaSearchBar;

  // Auto-initialize from script tag data attributes
  var currentScript = document.currentScript;
  if (currentScript && currentScript.hasAttribute("data-widget-id")) {
    var widgetId = currentScript.getAttribute("data-widget-id");
    var apiKey = currentScript.getAttribute("data-key") || "";
    var apiBase = currentScript.getAttribute("data-api") || "";
    var targetId = currentScript.getAttribute("data-target") || null;

    // Load CSS
    var link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = apiBase + "/widget/search.css";
    document.head.appendChild(link);

    // Find or create target element
    var target = targetId ? document.getElementById(targetId) : null;
    if (!target) {
      target = document.createElement("div");
      target.id = "retrieva-search-container";
      // Insert before the script tag
      currentScript.parentNode.insertBefore(target, currentScript);
    }

    // Fetch config and initialize
    fetch(apiBase + "/widget/config/" + widgetId)
      .then(function (r) {
        return r.json();
      })
      .then(function (cfg) {
        new RetrievaSearchBar(target, {
          placeholder: cfg.placeholder || DEFAULT_CONFIG.placeholder,
          apiEndpoint: "/widget/search",
          apiKey: apiKey,
          widgetId: widgetId,
          apiBase: apiBase,
        });
      })
      .catch(function (err) {
        console.error("[Retrieva] Failed to load widget config:", err);
        new RetrievaSearchBar(target, {
          apiKey: apiKey,
          widgetId: widgetId,
          apiBase: apiBase,
        });
      });
  }
})();
