import requests
from twitter.account import Account

def reply_post(account: Account, content: str, tweet_id: str) -> str:
    try:
        response = account.reply(content, tweet_id=tweet_id)
        return response
    except Exception as e:
        print(f"Error while replying to tweet: {e}")
        return None

def send_post_API(auth, content: str) -> str:
    url = 'https://api.twitter.com/2/tweets'
    payload = {'text': content}
    
    try:
        response = requests.post(url, json=payload, auth=auth)
        
        if response.status_code == 201:  # Twitter API returns 201 for successful tweet creation
            tweet_data = response.json()
            return tweet_data['data']['id']
        else:
            print(f'Error: {response.status_code} - {response.text}')
            return None
    except Exception as e:
        print(f'Failed to post tweet: {str(e)}')
        return None

def send_post(account: Account, content: str) -> str:
    try:
        response = account.tweet(content)
        return response
    except Exception as e:
        print(f"Failed to post tweet: {e}")
        return None
