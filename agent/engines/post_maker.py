import time
import requests
from typing import List, Dict
from engines.prompts import get_tweet_prompt

def generate_post(
    short_term_memory: str, 
    long_term_memories: List[Dict], 
    recent_posts: List[Dict], 
    external_context, 
    llm_api_key: str
) -> str:
    prompt = get_tweet_prompt(external_context, short_term_memory, long_term_memories, recent_posts)
    print(f"Generating post with prompt: {prompt}")

    base_model_output = request_tweet(prompt, llm_api_key)
    formatted_tweet = format_tweet(base_model_output, prompt, llm_api_key)
    
    return formatted_tweet

def request_tweet(prompt: str, llm_api_key: str, max_tries: int = 3) -> str:
    return request_with_retries(
        "https://api.hyperbolic.xyz/v1/completions",
        {
            "prompt": prompt,
            "model": "meta-llama/Meta-Llama-3.1-405B",
            "max_tokens": 512,
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 40,
            "stop": ["<|im_end|>", "<"]
        },
        llm_api_key,
        max_tries
    )

def format_tweet(base_model_output: str, prompt: str, llm_api_key: str, max_tries: int = 3) -> str:
    return request_with_retries(
        "https://api.hyperbolic.xyz/v1/chat/completions",
        {
            "messages": [
                {"role": "system", "content": create_system_message(prompt)},
                {"role": "user", "content": base_model_output}
            ],
            "model": "meta-llama/Meta-Llama-3.1-70B-Instruct",
            "max_tokens": 512,
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 40,
            "stream": False,
        },
        llm_api_key,
        max_tries
    )

def request_with_retries(url: str, payload: Dict, api_key: str, max_tries: int) -> str:
    for attempt in range(max_tries):
        try:
            response = requests.post(
                url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                json=payload
            )
            response.raise_for_status()
            content = response.json().get('choices', [{}])[0].get('text', '').strip()
            if content:
                print(f"Generated content: {content}")
                return content
        except requests.RequestException as e:
            print(f"Error on attempt {attempt + 1}: {e}")
            time.sleep(1)
    return ""

def create_system_message(prompt: str) -> str:
    return (
        "You are a tweet formatter. Your task is to take the input text and format it as a clear, "
        "engaging tweet. If it resembles a tweet already, return it as is, removing any prefixes like 'Tweet:' "
        "or 'Post:'. If no valid text is provided, generate a tweet directly from the prompt. "
        "Pick the most relevant content when multiple tweets appear. "
        "Keep it concise—no hashtags, explanations, or extra text. Only return the main tweet content."
    )
