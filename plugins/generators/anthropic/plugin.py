from core.generation.engine import GenerationEngine


class AnthropicGeneratorPlugin:
    def __init__(self, config=None):
        cfg = config or {}
        self._impl = GenerationEngine(
            provider="anthropic",
            **{k: v for k, v in cfg.items() if k != "provider"},
        )

    def generate(self, prompt, context=None, **kwargs):
        return self._impl.generate(prompt, context=context, **kwargs)
