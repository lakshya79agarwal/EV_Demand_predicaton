import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# NEW: Initialize the client (v1.0+ syntax)
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)

def get_openai_response(user_query, forecast_summary):
    # Construct the system prompt
    system_prompt = f"""
    You are an expert EV market analyst. 
    Here is the latest forecast summary data: {forecast_summary}
    
    Please answer the user's question based on this data.
    """

    try:
        # NEW: Updated syntax for chat completions
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use "gpt-4" if you have access
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            max_tokens=300
        )
        
        # NEW: Updated syntax to access the answer
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error communicating with OpenAI: {str(e)}"
