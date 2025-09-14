"""
Repository Pattern Module
Exports all repository classes for data access.
"""
from .base_repository import BaseRepository
from .customer_repository import CustomerRepository
from .whatsapp_repository import WhatsAppMessageRepository
from .user_repository import UserRepository

__all__ = [
    "BaseRepository",
    "CustomerRepository",
    "WhatsAppMessageRepository",
    "UserRepository"
]