import os


class ChatbotWidgetPlugin:
    def __init__(self, config=None):
        cfg = config or {}
        self.title = cfg.get("title", "Chat with us")
        self.position = cfg.get("position", "bottom-right")
        self.primary_color = cfg.get("primary_color", "#4F46E5")
        self.api_endpoint = cfg.get("api_endpoint", "/api/v1/chat")
        self._assets_dir = os.path.join(os.path.dirname(__file__), "assets")

    def get_assets(self):
        return {
            "js": os.path.join(self._assets_dir, "widget.js"),
            "css": os.path.join(self._assets_dir, "widget.css"),
        }

    def render_config(self):
        return {
            "title": self.title,
            "position": self.position,
            "primaryColor": self.primary_color,
            "apiEndpoint": self.api_endpoint,
        }
