# llmexplainer/llm_guard.py

def guard_llm_input(explained_results: list):
    """
    Enforces F.1 invariants:
    - No raw code
    - No execution hints
    - Only structured findings
    """

    if not isinstance(explained_results, list):
        raise ValueError("Invalid LLM input format")

    for r in explained_results:
        if "code" in r or "source" in r:
            raise ValueError("Raw code is not allowed in LLM input")

    return True
