import os
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from openai import OpenAI
from dotenv import load_dotenv
from models import User, Post, Comment, Like, LongTermMemory
from db.db_setup import SessionLocal

# Load environment variables
load_dotenv()

# Constants
MAX_POSTS = 5
MAX_COMMENTS_PER_POST = 2
MAX_MEMORIES = 3

def load_example_content(filename: str = "examples.txt") -> list[str]:
    """Load and parse example content from a text file."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, filename)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            # Split on double newlines to separate different examples
            examples = [x.strip() for x in content.split('\n\n') if x.strip()]
            print(f"Successfully loaded {len(examples)} examples from {file_path}")
            return examples
    except FileNotFoundError:
        print(f"Could not find file at {file_path}")
        print("Current working directory:", os.getcwd())
        print("Looking for file in:", current_dir)
        raise

def create_embedding(text: str) -> list[float]:
    """Create embedding using OpenAI API."""
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def add_users(db: Session, examples: list[str]) -> None:
    """Add users to the database if they do not exist."""
    existing_users = db.query(User).all()
    print(f"Existing users: {existing_users}")
    
    if not existing_users:
        users = [User(username="vireh_vireh_he", email="vireh_vireh_he@example.com")]
        db.add_all(users)
        db.commit()

def add_posts(db: Session, examples: list[str], users: list[User]) -> None:
    """Add posts to the database."""
    num_posts = min(MAX_POSTS, len(examples))  # Use up to MAX_POSTS examples for posts
    post_examples = random.sample(examples, num_posts)
    
    for content in post_examples:
        post = Post(
            content=content,
            user_id=random.choice(users).id,
            type="text",
            created_at=datetime.now() - timedelta(days=random.randint(0, 30))
        )
        db.add(post)
    
    db.commit()
    return post_examples

def add_comments(db: Session, posts: list[Post], examples: list[str], users: list[User]) -> None:
    """Add comments to posts in the database."""
    remaining_examples = [ex for ex in examples if ex not in post_examples]
    
    for post in posts:
        if remaining_examples:
            num_comments = random.randint(0, MAX_COMMENTS_PER_POST)
            for _ in range(num_comments):
                if remaining_examples:
                    content = remaining_examples.pop(0)
                    random_user = random.choice(users)
                    comment = Comment(
                        content=content,
                        user_id=random_user.id,
                        username=random_user.username,
                        post_id=post.id,
                        created_at=post.created_at + timedelta(hours=random.randint(1, 24))
                    )
                    db.add(comment)
    db.commit()

def add_likes(db: Session, posts: list[Post], users: list[User]) -> None:
    """Add likes to posts in the database."""
    for post in posts:
        for user in random.sample(users, k=random.randint(0, len(users))):
            like = Like(user_id=user.id, post_id=post.id, is_like=True)
            db.add(like)
    db.commit()

def add_long_term_memories(db: Session, remaining_examples: list[str]) -> None:
    """Add long-term memories to the database."""
    if remaining_examples:
        num_memories = min(MAX_MEMORIES, len(remaining_examples))
        memory_examples = random.sample(remaining_examples, num_memories)

        for content in memory_examples:
            embedding = create_embedding(content)
            memory = LongTermMemory(
                content=content,
                embedding=str(embedding),
                significance_score=random.uniform(7.0, 10.0)
            )
            db.add(memory)
        db.commit()

def seed_database() -> None:
    """Seed the database with example content."""
    db = SessionLocal()
    try:
        # Load example content
        examples = load_example_content()
        
        # Create users if they don't exist
        add_users(db, examples)
        users = db.query(User).all()

        # Create posts using some of the examples
        post_examples = add_posts(db, examples, users)
        posts = db.query(Post).all()

        # Create comments using different examples
        add_comments(db, posts, examples, users)

        # Create likes
        add_likes(db, posts, users)

        # Create long-term memories using remaining examples
        remaining_examples = [ex for ex in examples if ex not in post_examples]
        add_long_term_memories(db, remaining_examples)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
    print("Database seeded successfully.")
