import json

import requests

# Replace with the actual API endpoint of your LLM
API_URL = "http://130.86.176.68:9002/v1/chat/completions/"

# Replace with your API key or authentication token, if required
API_KEY = "foo"


def local_model_request(prompt: str):
    # Define the headers for the request, including content type and authorization
    headers = {
        "Content-Type": "application/json",
    }

    # Define the data payload for the request
    data = {
        "model": "gemma3:12b",  # Replace with the model you want to use, e.g., "gpt-3.5-turbo"
        "messages": [
            {
                "role": "system",
                "content": "You are an expert at evaluating Python code and providing feedback.",
            },
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 1000,
    }

    # Send the POST request to the API endpoint
    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(data))
        response.raise_for_status()  # Raise an exception for HTTP errors
        # Parse the JSON response
        response_json = response.json()

        # Extract and print the LLM's response
        print(response_json)

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except KeyError:
        print("Failed to extract the text, check the API response format.")
    except json.JSONDecodeError:
        print("Failed to decode JSON response.")

    return response_json["choices"][0]["message"]["content"]
