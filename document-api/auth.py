"""
Authentication module for Document API using Supabase.

This module provides JWT token verification and user resolution
following the same patterns as LangConnect.
"""

from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import create_client

from config import settings

security = HTTPBearer()


class AuthenticatedUser:
    """An authenticated user model."""

    def __init__(self, user_id: str, email: str, display_name: str = None) -> None:
        """Initialize the AuthenticatedUser.

        Args:
            user_id: Unique identifier for the user (from Supabase).
            email: User's email address.
            display_name: Display name for the user (optional).
        """
        self.user_id = user_id
        self.email = email
        self.display_name = display_name or email

    @property
    def is_authenticated(self) -> bool:
        """Return True if the user is authenticated."""
        return True

    @property
    def identity(self) -> str:
        """Return the identity of the user. This is a unique identifier."""
        return self.user_id


def get_current_user(authorization: str) -> dict:
    """Authenticate a user by validating their JWT token against Supabase.

    This function verifies the provided JWT token by making a request to Supabase.
    It requires the SUPABASE_URL and SUPABASE_ANON_KEY environment variables to be
    properly configured.

    Args:
        authorization: JWT token string to validate

    Returns:
        dict: A Supabase User object containing the authenticated user's information

    Raises:
        HTTPException: With status code 401 if token is invalid or authentication fails
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise HTTPException(
            status_code=500,
            detail="Supabase configuration missing. Please set SUPABASE_URL and SUPABASE_ANON_KEY.",
        )

    try:
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        response = supabase.auth.get_user(authorization)
        user = response.user

        if not user:
            raise HTTPException(
                status_code=401, detail="Invalid token or user not found"
            )
        return user
    except Exception as e:
        # Log the error for debugging
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


def resolve_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> AuthenticatedUser:
    """Resolve user from the credentials.

    This dependency can be used in FastAPI route handlers to automatically
    authenticate requests and extract user information.

    Args:
        credentials: HTTP Bearer token credentials

    Returns:
        AuthenticatedUser: An authenticated user object

    Raises:
        HTTPException: With status code 401 if authentication fails
    """
    if credentials.scheme != "Bearer":
        raise HTTPException(status_code=401, detail="Invalid authentication scheme")

    if not credentials.credentials:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = get_current_user(credentials.credentials)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Extract user metadata
    user_metadata = user.user_metadata if hasattr(user, "user_metadata") else {}
    display_name = user_metadata.get("name") or user_metadata.get("display_name")

    return AuthenticatedUser(
        user_id=user.id, email=user.email, display_name=display_name
    )
