from core.generation.engine import GenerationEngine


class OpenAIGeneratorPlugin:
    def __init__(self, config=None):
        cfg = config or {}
        self._impl = GenerationEngine(
            provider="openai",
            **{k: v for k, v in cfg.items() if k != "provider"},
        )

    def generate(self, prompt, context=None, **kwargs):
        return self._impl.generate(prompt, context=context, **kwargs)
