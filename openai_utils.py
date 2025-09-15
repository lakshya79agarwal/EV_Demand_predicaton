import openai
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

def get_openai_response(user_query, forecast_summary):
    prompt = f"""You are an expert data analyst. Here is the EV forecast summary: 
    {forecast_summary}
    Answer the user's question based on this data:
    "{user_query}"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You provide clear insights based on EV forecasts."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300,
    )

    return response['choices'][0]['message']['content']