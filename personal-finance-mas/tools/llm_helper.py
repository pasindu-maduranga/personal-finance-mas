"""
llm_helper.py
~~~~~~~~~~~~~
Custom tool for the Savings Goal Agent.

Provides a thin, typed wrapper around the langchain-ollama LLM so that
agents can call local phi3 models without coupling themselves to the
langchain_ollama API directly.
"""

from langchain_ollama import OllamaLLM


def get_llm_response(prompt: str, model: str = "phi3") -> str:
    """
    Send a prompt to a locally hosted Ollama language model and return the
    generated response.

    This function wraps the langchain_ollama OllamaLLM client.  It assumes
    the Ollama service is running locally (default: http://localhost:11434).
    Run `ollama serve` and `ollama pull <model>` before calling this function.

    Args:
        prompt: The full prompt string to send to the model.  Should include
                all context and instructions needed to generate a useful
                response — the model has no memory between calls.
        model:  The Ollama model identifier to use.  Defaults to 'phi3'.
                Other supported local models: 'llama3:8b', 'qwen', etc.

    Returns:
        str: The model's generated response text, stripped of leading and
             trailing whitespace.

    Raises:
        RuntimeError: If the Ollama service is not running or the requested
                      model has not been pulled.
        ValueError: If the prompt is empty or whitespace-only.

    Example:
        >>> advice = get_llm_response("Give me a 3-sentence savings tip.", model="phi3")
        >>> isinstance(advice, str)
        True
        >>> len(advice) > 0
        True
    """
    if not prompt or not prompt.strip():
        raise ValueError(
            "Prompt must not be empty or whitespace-only. "
            "Provide a meaningful prompt string."
        )

    try:
        llm = OllamaLLM(model=model)
        response: str = llm.invoke(prompt)
        return response.strip()
    except Exception as exc:
        raise RuntimeError(
            f"LLM call to model '{model}' failed. "
            "Ensure Ollama is running (`ollama serve`) and the model is "
            f"available (`ollama pull {model}`). Error: {exc}"
        ) from exc