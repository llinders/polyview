from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from polyview.core.llm_config import llm
from polyview.core.state import State


def summarize_node(state: State):
    """
    Summarizes content into a neutral and balanced text for the user to read,
    based on different perspectives and core arguments
    """
    prompt_template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                You are a critical summarizer node in a LangGraph. Your task is to read a list of distinct perspectives, each accompanied by its core arguments. Your goal is to synthesize these perspectives into a few short, clear paragraphs that offer the user a holistic, fair-minded, and critically informed overview of the issue.
    
                Instructions:
    
                1. **Balanced and Neutral Tone**: Represent each perspective in a neutral and respectful tone. Avoid emotive or biased language. Use proportionate language that does not exaggerate or minimize any viewpoint.
    
                2. **Critical Evaluation**:
                    - Do **not** treat all perspectives as equally valid by default.
                    - If a perspective is based on flawed reasoning, false premises, weak evidence, or misrepresented data, explicitly note that—but do so without dismissiveness or ridicule.
                    - When evidence quality varies, weight stronger arguments more heavily in your synthesis.
    
                3. **Holistic Integration**:
                    - Highlight common ground where it exists.
                    - Identify trade-offs, tensions, and areas of genuine disagreement.
                    - Recognize and make explicit where uncertainty or ambiguity remains.
    
                4. **Concise and Clear**:
                    - The output should be 2–4 short paragraphs.
                    - Use plain, precise language that communicates nuance without overcomplicating.
    
                5. **Avoid False Equivalence**:
                    - Avoid presenting weak or debunked claims as equally credible alternatives.
                    - If a perspective is unsupported by data or contradicts well-established evidence, explain that succinctly.
    
                6. **No Conclusions or Opinions**:
                    - Do not offer recommendations, predictions, or personal takes.
                    - Focus on summarizing and evaluating the inputs, not generating new views.
    
                You are a synthesis layer—honest, rigorous, and epistemically responsible.
    
                Inputs:
                - A list of perspectives, each with:
                  - Label or identifier
                  - Core argument(s)
                  - Supporting rationale, if provided
                  - It's strengths and weaknesses
    
                  Summary:"""
            ),
            (
                "user",
                """**Perspectives**
                ```json
                {perspectives}
                ```
                """
            )
        ]
    )

    chain = prompt_template | llm | StrOutputParser()

    summary_result = chain.invoke({"perspectives": state.get("identified_perspectives")})

    print(summary_result)
    return {"summary": summary_result}
