from core.generation.guardrails import Guardrails


class DefaultGuardrailPlugin:
    def __init__(self, config=None):
        cfg = config or {}
        self._impl = Guardrails(
            enabled=cfg.get("enabled", True),
        )

    def check(self, text):
        return self._impl.check(text)

    def filter_response(self, response):
        return self._impl.filter_response(response)
