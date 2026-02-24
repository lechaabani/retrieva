import os


class SearchBarPlugin:
    def __init__(self, config=None):
        cfg = config or {}
        self.placeholder = cfg.get("placeholder", "Search...")
        self.api_endpoint = cfg.get("api_endpoint", "/api/v1/search")
        self.debounce_ms = cfg.get("debounce_ms", 300)
        self._assets_dir = os.path.join(os.path.dirname(__file__), "assets")

    def get_assets(self):
        return {
            "js": os.path.join(self._assets_dir, "search.js"),
            "css": os.path.join(self._assets_dir, "search.css"),
        }

    def render_config(self):
        return {
            "placeholder": self.placeholder,
            "apiEndpoint": self.api_endpoint,
            "debounceMs": self.debounce_ms,
        }
