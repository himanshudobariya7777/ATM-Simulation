"""
Admin domain model representing an administrative user.
"""

from dataclasses import dataclass

@dataclass
class Admin:
    admin_id: str
    username: str
    password_hash: str
    salt: str
    created_at: str
