from polyview.utils.llm import ChatGoogleGenerativeAIWithDelayedRetry

llm = ChatGoogleGenerativeAIWithDelayedRetry(
    model="gemini-2.5-flash",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=0,
)

llm_lite = ChatGoogleGenerativeAIWithDelayedRetry(
    model="gemini-2.5-flash-lite-preview-06-17",
    temperature=0.3,
    max_tokens=None,
    timeout=None,
    max_retries=0,
)
