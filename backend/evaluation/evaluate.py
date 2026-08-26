from services import llm_service


def run_evaluation() -> None:
    """Quick smoke test of the LLM service on a few prompts."""
    questions = [
        "What can you do in 20 seconds?",
        "Explain machine learning in one sentence.",
        "Hello!",
    ]
    for question in questions:
        print(f"\nQ: {question}")
        print(f"A: {llm_service.ask_gemini(question)}")


if __name__ == "__main__":
    run_evaluation()
