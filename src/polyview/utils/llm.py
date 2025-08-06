from langchain_google_genai import ChatGoogleGenerativeAI

from .retry import gemini_api_delayed_retry


class ChatGoogleGenerativeAIWithDelayedRetry(ChatGoogleGenerativeAI):
    @gemini_api_delayed_retry()
    def invoke(self, *args, **kwargs):
        return super().invoke(*args, **kwargs)

    @gemini_api_delayed_retry()
    def stream(self, *args, **kwargs):
        return super().stream(*args, **kwargs)

    @gemini_api_delayed_retry()
    def batch(self, *args, **kwargs):
        return super().batch(*args, **kwargs)

    @gemini_api_delayed_retry()
    async def ainvoke(self, *args, **kwargs):
        return await super().ainvoke(*args, **kwargs)

    @gemini_api_delayed_retry()
    async def astream(self, *args, **kwargs):
        return await super().astream(*args, **kwargs)

    @gemini_api_delayed_retry()
    async def abatch(self, *args, **kwargs):
        return await super().abatch(*args, **kwargs)
