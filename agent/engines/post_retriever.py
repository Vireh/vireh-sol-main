import requests
from typing import List, Dict
from sqlalchemy.orm import Session
from models import Post
from sqlalchemy.orm import class_mapper
from twitter.account import Account
from twitter.scraper import Scraper
from engines.json_formatter import process_twitter_json

def sqlalchemy_obj_to_dict(obj):
    """Convert a SQLAlchemy object to a dictionary."""
    if obj is None:
        return None
    columns = [column.key for column in class_mapper(obj.__class__).columns]
    return {column: getattr(obj, column) for column in columns}


def convert_posts_to_dict(posts):
    """Convert a list of SQLAlchemy Post objects to a list of dictionaries."""
    return [sqlalchemy_obj_to_dict(post) for post in posts]


def retrieve_recent_posts(db: Session, limit: int = 10) -> List[Dict]:
    """
    Retrieve the most recent posts from the database.
    """
    recent_posts = db.query(Post).order_by(Post.created_at.desc()).limit(limit).all()
    return [post_to_dict(post) for post in recent_posts]


def post_to_dict(post: Post) -> Dict:
    """Convert a Post object to a dictionary."""
    return {
        "id": post.id,
        "content": post.content,
        "user_id": post.user_id,
        "created_at": post.created_at.isoformat() if post.created_at else None,
        "updated_at": post.updated_at.isoformat() if post.updated_at else None,
        "type": post.type,
        "comment_count": post.comment_count,
        "image_path": post.image_path,
        "tweet_id": post.tweet_id,
    }

def format_post_list(posts) -> str:
    """
    Format posts into a readable string, handling both pre-formatted strings 
    and lists of post dictionaries.
    """
    if isinstance(posts, str):
        return posts
        
    if not posts:
        return "No recent posts"
    
    if isinstance(posts, list):
        formatted = []
        for post in posts:
            content = post.get('content', '') if isinstance(post, dict) else str(post)
            formatted.append(f"- {content}")
        return "\n".join(formatted)
    
    return str(posts)


def fetch_external_context(api_key: str, query: str) -> List[str]:
    """
    Fetch external context from a news API or other source.
    """
    url = f"https://newsapi.org/v2/everything?q={query}&apiKey={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        news_items = response.json().get("articles", [])
        return [item["title"] for item in news_items[:5]]
    return []


def parse_tweet_data(tweet_data):
    """Parse tweet data from the X API response."""
    try:
        all_tweets_info = []
        entries = tweet_data['data']['home']['home_timeline_urt']['instructions'][0]['entries']
        
        for entry in entries:
            entry_id = entry.get('entryId', '')
            tweet_id = entry_id.replace('tweet-', '') if entry_id.startswith('tweet-') else None
            
            if 'itemContent' not in entry.get('content', {}) or \
               'tweet_results' not in entry.get('content', {}).get('itemContent', {}):
                continue
                
            tweet_info = entry['content']['itemContent']['tweet_results'].get('result')
            if not tweet_info:
                continue
                
            user_info = tweet_info['core']['user_results']['result']['legacy']
            tweet_details = tweet_info['legacy']
            
            readable_format = {
                "Tweet ID": tweet_id or tweet_details.get('id_str'),
                "Entry ID": entry_id,
                "Tweet Information": {
                    "text": tweet_details['full_text'],
                    "created_at": tweet_details['created_at'],
                    "likes": tweet_details['favorite_count'],
                    "retweets": tweet_details['retweet_count'],
                    "replies": tweet_details['reply_count'],
                    "language": tweet_details['lang'],
                    "tweet_id": tweet_details['id_str']
                },
                "Author Information": {
                    "name": user_info['name'],
                    "username": user_info['screen_name'],
                    "followers": user_info['followers_count'],
                    "following": user_info['friends_count'],
                    "account_created": user_info['created_at'],
                    "profile_image": user_info['profile_image_url_https']
                },
                "Tweet Metrics": {
                    "views": tweet_info.get('views', {}).get('count', '0'),
                    "bookmarks": tweet_details.get('bookmark_count', 0)
                }
            }
            if tweet_details['favorite_count'] > 20 and user_info['followers_count'] > 300 and tweet_details['reply_count'] > 3:
                all_tweets_info.append(readable_format)
                
        return all_tweets_info
            
    except KeyError as e:
        return f"Error parsing data: {e}"


def get_timeline(account: Account) -> List[str]:
    """Get timeline using the new Account-based approach."""
    timeline = account.home_latest_timeline(20)

    if 'errors' in timeline[0]:
        print(timeline[0])

    tweets_info = parse_tweet_data(timeline[0])
    return [f'New post on my timeline from @{t["Author Information"]["username"]}: {t["Tweet Information"]["text"]}' for t in tweets_info]


def fetch_notification_context(account: Account) -> str:
    """Fetch notification context using the new Account-based approach."""
    context = get_timeline(account)
    context.extend(find_all_conversations(account.notifications()))
    return "\n".join(context)
