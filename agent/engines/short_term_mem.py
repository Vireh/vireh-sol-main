import json
import time
from typing import List, Dict
import requests
from engines.prompts import get_short_term_memory_prompt

def generate_short_term_memory(posts: List[Dict], external_context: List[str], llm_api_key: str) -> str:
    # Prepare the prompt for the LLM
    prompt = get_short_term_memory_prompt(posts, external_context)
    
    # Set maximum retry attempts for the API call
    max_tries = 3
    for attempt in range(max_tries):
        try:
            # Define the API endpoint and headers
            url = "https://api.hyperbolic.xyz/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {llm_api_key}"
            }
            
            # Prepare the request payload
            data = {
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": "Respond only with your internal monologue based on the given context."}
                ],
                "model": "meta-llama/Meta-Llama-3.1-70B-Instruct",
                "max_tokens": 512,
                "temperature": 1,
                "top_p": 0.95,
                "top_k": 40,
                "stream": False,
            }
            
            # Make the POST request to the API
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()  # Raise an error for bad responses
            
            # Extract the generated content from the response
            content = response.json()['choices'][0]['message']['content'].strip()
            if content:
                print(f"Short-term memory generated with response: {content}")
                return content
            
        except requests.RequestException as e:
            print(f"Request failed on attempt {attempt + 1}: {e}")
        except Exception as e:
            print(f"Error on attempt {attempt + 1}: {str(e)}")
        
        # Wait before retrying
        time.sleep(5)  
    
    print("Max attempts reached. Short-term memory generation failed.")
    return ""
