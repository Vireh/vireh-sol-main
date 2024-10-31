import json
from datetime import datetime
from typing import Dict, Any, List

def parse_users(users_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    cleaned_users = []
    for user_id, user_info in users_data.items():
        cleaned_user = {
            'id': user_info['id'],
            'name': user_info['name'],
            'screen_name': user_info['screen_name'],
            'description': user_info['description'],
            'followers_count': user_info['followers_count'],
            'following_count': user_info['friends_count'],
            'tweet_count': user_info['statuses_count'],
            'location': user_info['location'],
            'created_at': user_info['created_at'],
            'verified': user_info['verified'],
            'is_blue_verified': user_info.get('ext_is_blue_verified', False)
        }
        cleaned_users.append(cleaned_user)
    return cleaned_users

def parse_notifications(notifications_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    cleaned_notifications = []
    for notif_id, notif_info in notifications_data.items():
        timestamp = datetime.fromtimestamp(
            int(notif_info['timestampMs']) / 1000
        ).strftime('%Y-%m-%d %H:%M:%S')
        
        message = notif_info['message']['text']
        notif_type = notif_info['icon']['id']
        
        cleaned_notification = {
            'id': notif_id,
            'timestamp': timestamp,
            'type': notif_type,
            'message': message,
            'referenced_users': [
                entity['ref']['user']['id']
                for entity in notif_info['message'].get('entities', [])
                if 'ref' in entity and 'user' in entity['ref']
            ]
        }
        
        cleaned_notifications.append(cleaned_notification)
    
    return cleaned_notifications

def parse_twitter_data(data: Dict[str, Any]) -> Dict[str, Any]:
    parsed_data = {
        'users': [],
        'notifications': []
    }
    
    if 'globalObjects' in data:
        if 'users' in data['globalObjects']:
            parsed_data['users'] = parse_users(data['globalObjects']['users'])
        
        if 'notifications' in data:
            parsed_data['notifications'] = parse_notifications(data['notifications'])
    
    return parsed_data

def format_user_output(user: Dict[str, Any]) -> str:
    output = [
        f"User: @{user['screen_name']}",
        f"Name: {user['name']}",
        f"Followers: {user['followers_count']:,}",
        f"Following: {user['following_count']:,}",
        f"Tweets: {user['tweet_count']:,}",
        f"Bio: {user['description'] or 'N/A'}",
        f"Verified: {'✓' if user['verified'] else '✗'}",
        f"Blue Verified: {'✓' if user['is_blue_verified'] else '✗'}",
        "-" * 50
    ]
    return "\n".join(output)

def format_notification_output(notification: Dict[str, Any]) -> str:
    output = [
        f"Time: {notification['timestamp']}",
        f"Type: {notification['type']}",
        f"Message: {notification['message']}",
        f"Referenced Users: {', '.join(notification['referenced_users']) if 'referenced_users' in notification else 'None'}",
        "-" * 50
    ]
    return "\n".join(output)

def format_output(parsed_data: Dict[str, Any]) -> str:
    output = ["=== Users ==="]
    for user in parsed_data['users']:
        output.append(format_user_output(user))
    
    output.append("\n=== Notifications ===")
    for notif in parsed_data['notifications']:
        output.append(format_notification_output(notif))
    
    return "\n".join(output)

def process_twitter_json(json_data: str) -> str:
    try:
        # Parse JSON string to dictionary
        data = json.loads(json_data)
        # Parse the data into a cleaner structure
        parsed_data = parse_twitter_data(data)
        # Format the parsed data into readable output
        return format_output(parsed_data)
    except json.JSONDecodeError:
        return "Error: Invalid JSON data"
    except Exception as e:
        return f"Error processing data: {str(e)}"
