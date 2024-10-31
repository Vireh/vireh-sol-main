import json
import os
from twitter.account import Account
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def load_auth_tokens():
    cookies = os.getenv("X_AUTH_TOKENS")
    if not cookies:
        raise ValueError("X_AUTH_TOKENS environment variable not found.")
    
    try:
        auth_tokens = json.loads(cookies)
    except json.JSONDecodeError:
        raise ValueError("Error decoding X_AUTH_TOKENS JSON.")
    
    return auth_tokens

def main():
    try:
        # Load and validate authentication tokens
        auth_tokens = load_auth_tokens()
        
        # Initialize Account with loaded tokens
        account = Account(cookies=auth_tokens)
        
        # Fetch and print the latest timeline
        timeline = account.home_latest_timeline(10)
        print(timeline)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
