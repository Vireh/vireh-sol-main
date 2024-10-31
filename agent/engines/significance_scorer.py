import requests
import time
import re
from engines.prompts import get_significance_score_prompt

def score_significance(memory: str, llm_api_key: str) -> int:
    prompt = get_significance_score_prompt(memory)
    max_tries = 5

    for attempt in range(max_tries):
        try:
            # Make the POST request to the API
            response = requests.post(
                url="https://api.hyperbolic.xyz/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {llm_api_key}",
                },
                json={
                    "messages": [
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": "Respond only with the score you would give for the given memory."}
                    ],
                    "model": "meta-llama/Meta-Llama-3.1-70B-Instruct",
                    "temperature": 1,
                    "top_p": 0.95,
                    "top_k": 40,
                }
            )

            # Check if the response is successful
            response.raise_for_status()  # Raise an error for bad responses
            
            # Extract and process the score from the response
            score_str = response.json()['choices'][0]['message']['content'].strip()
            print(f"Score generated for memory: {score_str}")

            # Attempt to find a numerical score in the response
            numbers = re.findall(r'\d+', score_str)
            if numbers:
                score = int(numbers[0])
                return max(1, min(10, score))  # Ensure the score is between 1 and 10
            
            print(f"No numerical score found in response: {score_str}")

        except requests.RequestException as e:
            print(f"Request failed on attempt {attempt + 1}: {e}")
        except ValueError:
            print(f"Invalid score returned: {score_str}")
        
        # Wait before retrying
        time.sleep(1)
    
    print("Max attempts reached. Significance scoring failed.")
    return 0  # Return a default score or handle it as necessary
