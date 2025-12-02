import json
import os
import bcrypt
from typing import Optional, Dict

USERS_FILE = "memories/users.json"

def _load_users() -> Dict[str, str]:
    """Load users from the JSON file."""
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def _save_users(users: Dict[str, str]):
    """Save users to the JSON file."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def create_user(username: str, password: str) -> bool:
    """
    Create a new user. Returns True if successful, False if user already exists.
    """
    users = _load_users()
    if username in users:
        return False
    
    # Hash password
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    users[username] = hashed
    _save_users(users)
    return True

def authenticate_user(username: str, password: str) -> Optional[str]:
    """
    Verify credentials. Returns user_id (username) if valid, None otherwise.
    """
    users = _load_users()
    if username not in users:
        return None
    
    hashed = users[username]
    if bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8')):
        return username
    return None
