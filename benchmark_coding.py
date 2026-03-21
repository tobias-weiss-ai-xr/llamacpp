#!/usr/bin/env python3
"""Benchmark for coding tasks with different context sizes"""

import requests
import time

API_URL = "http://localhost:8080/v1/chat/completions"


def run_test(name, messages, max_tokens):
    """Run a single test"""
    print(f"\n{name}")
    print("-" * 60)

    start = time.time()
    response = requests.post(
        API_URL,
        json={
            "model": "qwen",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.3,  # Lower temp for code
        },
    )
    elapsed = (time.time() - start) * 1000

    data = response.json()
    usage = data.get("usage", {})
    timings = data.get("timings", {})

    print(f"  Total time: {elapsed:.0f}ms")
    print(f"  TTFT: {timings.get('prompt_ms', 0):.0f}ms")
    print(f"  Generation: {timings.get('predicted_ms', 0):.0f}ms")
    print(f"  Prompt tokens: {usage.get('prompt_tokens', 0)}")
    print(f"  Generated: {usage.get('completion_tokens', 0)} tokens")
    print(f"  Speed: {timings.get('predicted_per_second', 0):.2f} t/s")

    # Show first 200 chars of response
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    print(f"  Preview: {content[:200]}...")

    return {
        "total_ms": elapsed,
        "ttft_ms": timings.get("prompt_ms", 0),
        "tps": timings.get("predicted_per_second", 0),
        "prompt_tokens": usage.get("prompt_tokens", 0),
        "completion_tokens": usage.get("completion_tokens", 0),
    }


def main():
    import subprocess

    # Get GPU memory
    result = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=memory.total,memory.used,memory.free",
            "--format=csv,noheader,nounits",
        ],
        capture_output=True,
        text=True,
    )
    total, used, free = map(int, result.stdout.strip().split(", "))

    print("=" * 60)
    print(f"Coding Benchmark - Qwen3.5-35B-A3B")
    print(f"GPU: {total}MB total, {used}MB used, {free}MB free")
    print("=" * 60)

    # Test 1: Small code context
    run_test(
        "Test 1: Small code context (function completion)",
        [
            {
                "role": "user",
                "content": """Complete this Python function:

```python
def fibonacci(n: int) -> list[int]:
    \"\"\"Return first n Fibonacci numbers\"\"\"
""",
            }
        ],
        100,
    )

    # Test 2: Medium code context (class with multiple methods)
    medium_code = """
class UserService:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def get_user(self, user_id: int) -> User:
        return self.db.query(User).filter(User.id == user_id).first()
    
    def create_user(self, email: str, name: str) -> User:
        user = User(email=email, name=name)
        self.db.add(user)
        self.db.commit()
        return user
    
    def update_user(self, user_id: int, **kwargs) -> User:
        user = self.get_user(user_id)
        if user:
            for key, value in kwargs.items():
                setattr(user, key, value)
            self.db.commit()
        return user
"""

    run_test(
        "Test 2: Medium code context (add method to class)",
        [
            {
                "role": "user",
                "content": f"""Add a delete_user method and a list_users method with pagination to this class:

```python
{medium_code}
```""",
            }
        ],
        150,
    )

    # Test 3: Large code context (full module)
    large_code = '''
"""
Authentication module for the API.
Handles JWT token generation, validation, and user authentication.
"""
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class TokenType(Enum):
    ACCESS = "access"
    REFRESH = "refresh"


@dataclass
class User:
    id: int
    email: str
    password_hash: bytes
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime = None
    last_login: datetime = None


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class TokenExpiredError(AuthenticationError):
    """Raised when a token has expired."""
    pass


class InvalidTokenError(AuthenticationError):
    """Raised when a token is invalid."""
    pass


class AuthService:
    """
    Service for handling user authentication.
    
    Attributes:
        secret_key: Secret key for JWT signing
        algorithm: JWT signing algorithm
        access_token_expire: Access token expiration in minutes
        refresh_token_expire: Refresh token expiration in days
    """
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire: int = 30,
        refresh_token_expire: int = 7
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire = access_token_expire
        self.refresh_token_expire = refresh_token_expire
    
    def hash_password(self, password: str) -> bytes:
        """Hash a password using bcrypt."""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    
    def verify_password(self, password: str, password_hash: bytes) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(password.encode(), password_hash)
    
    def generate_token(
        self,
        user_id: int,
        token_type: TokenType = TokenType.ACCESS,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a JWT token for a user."""
        now = datetime.utcnow()
        
        if token_type == TokenType.ACCESS:
            expire = now + timedelta(minutes=self.access_token_expire)
        else:
            expire = now + timedelta(days=self.refresh_token_expire)
        
        payload = {
            "sub": str(user_id),
            "type": token_type.value,
            "iat": now,
            "exp": expire
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def validate_token(self, token: str, token_type: TokenType = TokenType.ACCESS) -> Dict[str, Any]:
        """Validate a JWT token and return its payload."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            if payload.get("type") != token_type.value:
                raise InvalidTokenError(f"Expected {token_type.value} token")
            
            return payload
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(f"Invalid token: {e}")
    
    def refresh_access_token(self, refresh_token: str) -> str:
        """Generate a new access token using a refresh token."""
        payload = self.validate_token(refresh_token, TokenType.REFRESH)
        return self.generate_token(int(payload["sub"]), TokenType.ACCESS)
    
    def authenticate_user(self, user: User, password: str) -> Dict[str, str]:
        """Authenticate a user and return access and refresh tokens."""
        if not user.is_active:
            raise AuthenticationError("User account is deactivated")
        
        if not self.verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid password")
        
        return {{
            "access_token": self.generate_token(user.id, TokenType.ACCESS),
            "refresh_token": self.generate_token(user.id, TokenType.REFRESH),
            "token_type": "bearer"
        }}
'''

    run_test(
        "Test 3: Large code context (extend auth module)",
        [
            {
                "role": "user",
                "content": f"""Add the following to this authentication module:
1. A rate limiter decorator that limits login attempts
2. A password strength validator
3. A method to revoke tokens (using a blacklist)

```python
{large_code}
```""",
            }
        ],
        300,
    )

    # Test 4: Very large context (simulate full file understanding)
    very_large_code = large_code * 3  # Triple it to simulate larger context

    run_test(
        "Test 4: Very large context (~2000 tokens prompt)",
        [
            {
                "role": "user",
                "content": f"""Review this code and suggest 3 improvements:

```python
{very_large_code}
```""",
            }
        ],
        200,
    )

    print("\n" + "=" * 60)
    print("Benchmark Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
