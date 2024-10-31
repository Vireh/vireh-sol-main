import requests
import re
from twitter.account import Account
from twitter.scraper import Scraper
from models import User

def extract_twitter_usernames(posts):
    twitter_pattern = re.compile(r"@([A-Za-z0-9_]{1,15})")
    twitter_usernames = set()  # Using a set to avoid duplicates

    for post in posts:
        found_usernames = twitter_pattern.findall(str(post))
        twitter_usernames.update(found_usernames)

    return list(twitter_usernames)

def filter_existing_usernames(db, usernames):
    existing_usernames = db.query(User.username).filter(User.username.in_(usernames)).all()
    existing_usernames = {username[0] for username in existing_usernames}  # Using a set for faster lookups

    return [username for username in usernames if username not in existing_usernames]

def add_new_usernames_to_db(db, usernames):
    for username in usernames:
        db.add(User(username=username))
    db.commit()

def generate_decision_prompt(posts, usernames):
    return f"""
    Analyze the following recent posts:

    Recent posts:
    {posts}

    Twitter usernames:
    {usernames}

    Decide whether to follow any of the Twitter usernames and assign a score from 0 to 1 (1 being the highest).

    If you choose to follow anyone, return a JSON object with a list of objects, each containing 'username' and 'score'.
    If you choose not to follow anyone, return an empty JSON object.

    Example Response:
    [
        {{"username": "username1", "score": 0.8}},
        {{"username": "username2", "score": 0.5}}
    ]

    Example Response if not following anyone:
    []
    """

def get_decision_from_ai(prompt, openrouter_api_key):
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {openrouter_api_key}"},
        json={
            "model": "meta-llama/llama-3.1-70b-instruct",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
        },
    )

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise Exception(f"Error generating decision: {response.text}")

def decide_to_follow_users(db, posts, openrouter_api_key: str):
    # Extract Twitter usernames from posts
    twitter_usernames = extract_twitter_usernames(posts)

    # Filter out existing usernames
    new_usernames = filter_existing_usernames(db, twitter_usernames)

    # Add new usernames to the database
    add_new_usernames_to_db(db, new_usernames)

    # Prepare the AI prompt
    prompt = generate_decision_prompt(posts, new_usernames)

    # Get decision from AI
    return get_decision_from_ai(prompt, openrouter_api_key)

def get_user_id(account: Account, username):
    scraper = Scraper(account.session.cookies)
    users = scraper.users([username])
    return users[0].id if users else None

def follow_user(account: Account, user_id):
    return account.follow(user_id)

def follow_by_username(account: Account, username):
    target_id = get_user_id(account, username)
    if target_id:
        follow_user(account, target_id)
