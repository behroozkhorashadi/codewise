import openai

# Set your OpenAI API key here
#read api key to read from environment variable
openai.api_key = "YOUR_API_KEY"

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
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an assistant helping to rate Python code quality."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=10000,
            temperature=0.2  # Low temperature for consistent, focused responses
        )
        
        # Extract the response content
        return response['choices'][0]['message']['content'].strip()
    
    except openai.error.OpenAIError as e:
        print(f"Error: {e}")
        return None