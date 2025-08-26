from langchain_google_genai import ChatGoogleGenerativeAI

from polyview.utils.retry import gemini_api_delayed_retry


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

    async def astream(self, *args, **kwargs):
        # @gemini_api_delayed_retry is not compatible with async generators, so it has been removed.
        async for chunk in super().astream(*args, **kwargs):
            yield chunk

    @gemini_api_delayed_retry()
    async def abatch(self, *args, **kwargs):
        return await super().abatch(*args, **kwargs)
