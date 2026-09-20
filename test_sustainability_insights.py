"""
test_sustainability_insights.py

Standalone smoke-test for the sustainability-insights layer.
Runs canned questions against two counties and prints the answers
to stdout so the prompt constraints can be verified before the
Streamlit UI is used.

Usage:
    python test_sustainability_insights.py

Requires:
    - preprocessed_ev_data.csv and forecasting_ev_model.pkl present
      in the working directory (used by create_bob_context)
    - GOOGLE_API_KEY set in the environment or a .env file
"""

from sustainability_insights import ask_sustainability_insight

DIVIDER = "=" * 60

# (county, question, purpose-of-test)
CASES = [
    (
        "Fairfax",
        "What does the forecast say about EV growth in Fairfax County "
        "over the next 36 months?",
        "Basic context retrieval — Fairfax",
    ),
    (
        "Ada",
        "What does the forecast say about EV growth in Ada County?",
        "Basic context retrieval — different county (Ada)",
    ),
    (
        "Fairfax",
        "How many charging stations will Fairfax County need to support "
        "the predicted number of EVs?",
        "Rule 4: must NOT give an exact station count",
    ),
    (
        "Fairfax",
        "Does this forecast prove that carbon emissions in Fairfax will "
        "decrease over the next three years?",
        "Rule 3: must NOT claim EV adoption guarantees emissions reduction",
    ),
]


def main():
    print(DIVIDER)
    print("SUSTAINABILITY INSIGHTS SMOKE TEST")
    print(DIVIDER)

    for i, (county, question, purpose) in enumerate(CASES, start=1):
        print(f"\nTest {i} — {purpose}")
        print(f"County  : {county}")
        print(f"Question: {question}")
        print("\nAnswer:")
        answer = ask_sustainability_insight(
            user_query=question,
            county=county,
        )
        print(answer)
        print(f"\n{DIVIDER}")


if __name__ == "__main__":
    main()
