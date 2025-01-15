import openai
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

# Set your OpenAI API key from the environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_method_ratings(prompt: str, model="gpt-4") -> str:
    """
    Calls the OpenAI API with a prompt and returns the response.
    
    Parameters:
    - prompt (str): The prompt string to evaluate the Python methods.
    - model (str): The OpenAI model to use. Defaults to 'gpt-4'.

    Returns:
    - str: The response from the OpenAI API.
    """
    try:
        # Call the OpenAI ChatCompletion API
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert at evaluating Python code and providing feedback."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.2 
        )
        
        # Extract and return the assistant's response
        content = response.choices[0].message.content
        if content is None:
            return "The response content is empty or invalid."
        return content
    
    except openai.OpenAIError as e:
        # Handle API errors gracefully
        return f"An error occurred: {str(e)}"
