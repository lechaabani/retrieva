(function () {
  "use strict";

  var DEFAULT_CONFIG = {
    title: "Chat with us",
    position: "bottom-right",
    primaryColor: "#4F46E5",
    textColor: "#FFFFFF",
    placeholder: "Type a message...",
    welcomeMessage: "",
    showSources: false,
    apiEndpoint: "/widget/query",
    apiKey: "",
    widgetId: "",
    apiBase: "",
  };

  class RetrievaChatWidget {
    constructor(config) {
      this.config = Object.assign({}, DEFAULT_CONFIG, config || {});
      this.isOpen = false;
      this.messages = [];
      this._init();
    }

    _init() {
      this._applyTheme();
      this._createWidget();
      this._attachEvents();
      if (this.config.welcomeMessage) {
        this._appendMessage("assistant", this.config.welcomeMessage);
      }
    }

    _applyTheme() {
      // Inject CSS variables on document root
      var root = document.documentElement;
      root.style.setProperty("--retrieva-primary", this.config.primaryColor);
      root.style.setProperty("--retrieva-text", this.config.textColor);
    }

    _createWidget() {
      this.container = document.createElement("div");
      this.container.id = "retrieva-chat-widget";
      this.container.className = "retrieva-widget " + this.config.position;
      this.container.innerHTML =
        '<button class="retrieva-widget-toggle" aria-label="Toggle chat">' +
        '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
        '<path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>' +
        "</svg></button>" +
        '<div class="retrieva-widget-panel">' +
        '<div class="retrieva-widget-header">' +
        "<span>" +
        this.config.title +
        "</span>" +
        '<button class="retrieva-widget-close" aria-label="Close">&times;</button>' +
        "</div>" +
        '<div class="retrieva-widget-messages"></div>' +
        '<div class="retrieva-widget-input">' +
        '<input type="text" placeholder="' +
        this.config.placeholder +
        '" />' +
        '<button class="retrieva-widget-send" aria-label="Send">&#9654;</button>' +
        "</div></div>";
      document.body.appendChild(this.container);
    }

    _attachEvents() {
      var self = this;
      this.container
        .querySelector(".retrieva-widget-toggle")
        .addEventListener("click", function () {
          self.toggle();
        });
      this.container
        .querySelector(".retrieva-widget-close")
        .addEventListener("click", function () {
          self.close();
        });
      this.container
        .querySelector(".retrieva-widget-send")
        .addEventListener("click", function () {
          self._sendMessage();
        });
      this.container
        .querySelector(".retrieva-widget-input input")
        .addEventListener("keypress", function (e) {
          if (e.key === "Enter") self._sendMessage();
        });
    }

    toggle() {
      this.isOpen = !this.isOpen;
      this.container.classList.toggle("open", this.isOpen);
    }

    close() {
      this.isOpen = false;
      this.container.classList.remove("open");
    }

    async _sendMessage() {
      var input = this.container.querySelector(".retrieva-widget-input input");
      var text = input.value.trim();
      if (!text) return;
      input.value = "";
      this._appendMessage("user", text);

      // Show typing indicator
      var typingEl = this._appendMessage("assistant", "...");
      typingEl.classList.add("retrieva-message-typing");

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
            question: text,
            widget_id: this.config.widgetId,
          }),
        });
        var data = await response.json();

        // Replace typing indicator
        typingEl.textContent = data.answer || "Sorry, I could not find an answer.";
        typingEl.classList.remove("retrieva-message-typing");

        // Show sources if enabled
        if (this.config.showSources && data.sources && data.sources.length > 0) {
          var sourcesHtml = '<div class="retrieva-sources">';
          data.sources.forEach(function (s) {
            sourcesHtml +=
              '<div class="retrieva-source-item">' +
              '<span class="retrieva-source-title">' +
              (s.title || "Source") +
              "</span></div>";
          });
          sourcesHtml += "</div>";
          var sourcesEl = document.createElement("div");
          sourcesEl.className = "retrieva-message retrieva-message-sources";
          sourcesEl.innerHTML = sourcesHtml;
          this.container
            .querySelector(".retrieva-widget-messages")
            .appendChild(sourcesEl);
        }
      } catch (err) {
        typingEl.textContent = "Sorry, something went wrong.";
        typingEl.classList.remove("retrieva-message-typing");
      }

      var messagesEl = this.container.querySelector(".retrieva-widget-messages");
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    _appendMessage(role, text) {
      this.messages.push({ role: role, text: text });
      var messagesEl = this.container.querySelector(
        ".retrieva-widget-messages"
      );
      var msg = document.createElement("div");
      msg.className = "retrieva-message retrieva-message-" + role;
      msg.textContent = text;
      messagesEl.appendChild(msg);
      messagesEl.scrollTop = messagesEl.scrollHeight;
      return msg;
    }
  }

  window.RetrievaChatWidget = RetrievaChatWidget;

  // Auto-initialize from script tag data attributes
  var currentScript = document.currentScript;
  if (currentScript && currentScript.hasAttribute("data-widget-id")) {
    var widgetId = currentScript.getAttribute("data-widget-id");
    var apiKey = currentScript.getAttribute("data-key") || "";
    var apiBase = currentScript.getAttribute("data-api") || "";

    // Load CSS
    var link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = apiBase + "/widget/chatbot.css";
    document.head.appendChild(link);

    // Fetch config and initialize
    fetch(apiBase + "/widget/config/" + widgetId)
      .then(function (r) {
        return r.json();
      })
      .then(function (cfg) {
        new RetrievaChatWidget({
          title: cfg.title || DEFAULT_CONFIG.title,
          position: cfg.position || DEFAULT_CONFIG.position,
          primaryColor: cfg.primary_color || DEFAULT_CONFIG.primaryColor,
          textColor: cfg.text_color || DEFAULT_CONFIG.textColor,
          placeholder: cfg.placeholder || DEFAULT_CONFIG.placeholder,
          welcomeMessage: cfg.welcome_message || "",
          showSources: cfg.show_sources || false,
          apiEndpoint: "/widget/query",
          apiKey: apiKey,
          widgetId: widgetId,
          apiBase: apiBase,
        });
      })
      .catch(function (err) {
        console.error("[Retrieva] Failed to load widget config:", err);
        // Fallback: initialize with defaults
        new RetrievaChatWidget({
          apiKey: apiKey,
          widgetId: widgetId,
          apiBase: apiBase,
        });
      });
  }
})();
