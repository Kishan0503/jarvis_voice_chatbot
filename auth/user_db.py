import sqlite3
from typing import Optional
from .auth_models import User, UserCreate
from .auth_utils import get_password_hash, verify_password

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            hashed_password TEXT NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()

# Initialize database on module load
init_db()

def get_user(email: str) -> Optional[dict]:
    """Get user by email."""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    conn.close()
    
    if user:
        return {
            "email": user[0],
            "username": user[1],
            "hashed_password": user[2],
            "is_active": bool(user[3])
        }
    return None

def create_user(user: UserCreate) -> User:
    """Create a new user."""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    # Check if email exists
    c.execute('SELECT 1 FROM users WHERE email = ?', (user.email,))
    if c.fetchone():
        conn.close()
        raise ValueError("Email already registered")
    
    hashed_password = get_password_hash(user.password)
    
    try:
        c.execute('''
            INSERT INTO users (email, username, hashed_password, is_active)
            VALUES (?, ?, ?, ?)
        ''', (user.email, user.username, hashed_password, True))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError("Email already registered")
    
    conn.close()
    
    return User(
        email=user.email,
        username=user.username,
        is_active=True
    )

def authenticate_user(email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password."""
    user_dict = get_user(email)
    if not user_dict:
        return None
    if not verify_password(password, user_dict["hashed_password"]):
        return None
    return User(**{k: v for k, v in user_dict.items() if k != "hashed_password"}) 