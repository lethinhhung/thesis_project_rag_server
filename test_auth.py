#!/usr/bin/env python3
"""
OAuth2 Authentication Test Script
This script demonstrates how to use the OAuth2 authentication system.
"""

import requests
import json
from typing import Optional

BASE_URL = "http://localhost:8000"

class AuthTestClient:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
    
    def register_user(self, username: str, email: str, password: str, full_name: str = None):
        """Register a new user"""
        url = f"{self.base_url}/auth/register"
        data = {
            "username": username,
            "email": email,
            "password": password,
            "full_name": full_name,
            "is_active": True
        }
        
        response = requests.post(url, json=data)
        if response.status_code == 201:
            print(f"✅ User registered successfully: {response.json()}")
            return response.json()
        else:
            print(f"❌ Registration failed: {response.json()}")
            return None
    
    def login(self, username: str, password: str):
        """Login and get tokens"""
        url = f"{self.base_url}/auth/token"
        data = {
            "username": username,
            "password": password,
            "grant_type": "password",
            "scope": ""
        }
        
        response = requests.post(url, data=data)
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data["access_token"]
            self.refresh_token = token_data["refresh_token"]
            print(f"✅ Login successful!")
            print(f"   Access Token: {self.access_token[:50]}...")
            print(f"   Refresh Token: {self.refresh_token}")
            return token_data
        else:
            print(f"❌ Login failed: {response.json()}")
            return None
    
    def get_current_user(self):
        """Get current user information"""
        if not self.access_token:
            print("❌ No access token available. Please login first.")
            return None
        
        url = f"{self.base_url}/auth/me"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Current user: {user_data}")
            return user_data
        else:
            print(f"❌ Failed to get user info: {response.json()}")
            return None
    
    def refresh_access_token(self):
        """Refresh the access token"""
        if not self.refresh_token:
            print("❌ No refresh token available.")
            return None
        
        url = f"{self.base_url}/auth/refresh"
        data = {"refresh_token": self.refresh_token}
        
        response = requests.post(url, json=data)
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data["access_token"]
            print(f"✅ Token refreshed successfully!")
            print(f"   New Access Token: {self.access_token[:50]}...")
            return token_data
        else:
            print(f"❌ Token refresh failed: {response.json()}")
            return None
    
    def test_protected_endpoint(self, user_id: str):
        """Test a protected endpoint"""
        if not self.access_token:
            print("❌ No access token available. Please login first.")
            return None
        
        url = f"{self.base_url}/v1/question"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        data = {
            "userId": user_id,
            "query": "What is machine learning?"
        }
        
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            print(f"✅ Protected endpoint accessed successfully!")
            return response.json()
        else:
            print(f"❌ Protected endpoint access failed: {response.json()}")
            return None
    
    def logout(self):
        """Logout by revoking refresh token"""
        if not self.refresh_token or not self.access_token:
            print("❌ No tokens available to logout.")
            return False
        
        url = f"{self.base_url}/auth/logout"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        data = {"refresh_token": self.refresh_token}
        
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            print(f"✅ Logout successful: {response.json()}")
            self.access_token = None
            self.refresh_token = None
            return True
        else:
            print(f"❌ Logout failed: {response.json()}")
            return False

def main():
    """Test the OAuth2 authentication flow"""
    print("🚀 Testing OAuth2 Authentication System")
    print("=" * 50)
    
    client = AuthTestClient()
    
    # Test 1: Login with default admin user
    print("\n1️⃣ Testing login with default admin user...")
    login_result = client.login("admin", "admin123")
    
    if login_result:
        # Test 2: Get current user info
        print("\n2️⃣ Testing get current user...")
        client.get_current_user()
        
        # Test 3: Test refresh token
        print("\n3️⃣ Testing token refresh...")
        client.refresh_access_token()
        
        # Test 4: Test protected endpoint (this will fail without proper Pinecone setup)
        print("\n4️⃣ Testing protected endpoint...")
        user_info = client.get_current_user()
        if user_info:
            client.test_protected_endpoint(user_info["id"])
        
        # Test 5: Logout
        print("\n5️⃣ Testing logout...")
        client.logout()
    
    # Test 6: Register new user
    print("\n6️⃣ Testing user registration...")
    client.register_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        full_name="Test User"
    )
    
    # Test 7: Login with new user
    print("\n7️⃣ Testing login with new user...")
    client.login("testuser", "testpass123")
    
    if client.access_token:
        client.get_current_user()
        client.logout()
    
    print("\n✅ Authentication tests completed!")

if __name__ == "__main__":
    main()