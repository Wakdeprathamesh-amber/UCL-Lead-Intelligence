"""
Basic Authentication Module
Provides simple authentication for the application
"""

import hashlib
import os
import streamlit as st
from typing import Optional, Dict
from datetime import datetime, timedelta


class SimpleAuth:
    """Simple authentication system using session state"""
    
    def __init__(self):
        """Initialize authentication"""
        # Default credentials (should be changed in production)
        # In production, use environment variables or a proper auth system
        self.default_username = os.getenv("AUTH_USERNAME", "admin")
        self.default_password_hash = self._hash_password(
            os.getenv("AUTH_PASSWORD", "admin123")
        )
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str) -> bool:
        """Verify password against stored hash"""
        password_hash = self._hash_password(password)
        return password_hash == self.default_password_hash
    
    def login(self, username: str, password: str) -> bool:
        """Attempt login"""
        if username == self.default_username and self.verify_password(password):
            return True
        return False
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return st.session_state.get("authenticated", False)
    
    def set_authenticated(self, value: bool, username: Optional[str] = None):
        """Set authentication status"""
        st.session_state["authenticated"] = value
        if value and username:
            st.session_state["username"] = username
            st.session_state["login_time"] = datetime.now()
        elif not value:
            if "username" in st.session_state:
                del st.session_state["username"]
            if "login_time" in st.session_state:
                del st.session_state["login_time"]
    
    def get_username(self) -> Optional[str]:
        """Get current username"""
        return st.session_state.get("username", None)
    
    def get_session_id(self) -> str:
        """Get or create session ID"""
        if "session_id" not in st.session_state:
            import uuid
            st.session_state["session_id"] = str(uuid.uuid4())
        return st.session_state["session_id"]
    
    def logout(self):
        """Logout user"""
        self.set_authenticated(False)


# Global auth instance
_auth_instance: Optional[SimpleAuth] = None


def get_auth() -> SimpleAuth:
    """Get or create global auth instance"""
    global _auth_instance
    if _auth_instance is None:
        _auth_instance = SimpleAuth()
    return _auth_instance


def require_auth(func):
    """Decorator to require authentication for a function"""
    def wrapper(*args, **kwargs):
        auth = get_auth()
        if not auth.is_authenticated():
            st.error("🔒 Authentication required. Please log in.")
            show_login_page()
            return None
        return func(*args, **kwargs)
    return wrapper


def show_login_page():
    """Show login page"""
    st.title("🔒 UCL Lead Intelligence - Login")
    st.markdown("---")
    
    auth = get_auth()
    
    with st.form("login_form"):
        username = st.text_input("Username", value="")
        password = st.text_input("Password", type="password", value="")
        submit = st.form_submit_button("Login")
        
        if submit:
            if auth.login(username, password):
                auth.set_authenticated(True, username)
                st.success("✅ Login successful!")
                st.rerun()
            else:
                st.error("❌ Invalid username or password")
    
    st.info("💡 Default credentials: admin / admin123 (change in production)")

