import os

import openai
from dotenv import load_dotenv

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
    if openai.api_key is None:
        # No OpenAI API key configured
        return """No OpenAI API key configured. 

To use this application, you need to:

1. Get an OpenAI API key from https://platform.openai.com/api-keys
2. Create a .env file in the project root with:
   OPENAI_API_KEY=your_api_key_here

Alternatively, you can set the environment variable:
export OPENAI_API_KEY=your_api_key_here

The local model server at 130.86.176.68:9002 is not available."""

    try:
        # Call the OpenAI ChatCompletion API
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at evaluating Python code and providing feedback.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000,
            temperature=0.2,
        )

        # Extract and return the assistant's response
        content = response.choices[0].message.content
        if content is None:
            return "The response content is empty or invalid."
        return content

    except openai.OpenAIError as e:
        # Handle API errors gracefully
        return f"OpenAI API error: {str(e)}"
