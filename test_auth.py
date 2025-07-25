#!/usr/bin/env python3
"""
Simple test script to demonstrate the OAuth2 authentication system.
Run this after starting the server with: uvicorn server:app --reload
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_registration():
    """Test user registration"""
    print("🔐 Testing User Registration...")
    
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "securepass123",
        "full_name": "Test User"
    }
    
    response = requests.post(f"{BASE_URL}/v1/auth/register", json=user_data)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Registration successful!")
        print(f"📧 User: {data['user']['email']}")
        print(f"🔑 Token: {data['access_token'][:20]}...")
        return data['access_token']
    else:
        print("❌ Registration failed:")
        print(f"Status: {response.status_code}")
        print(f"Error: {response.text}")
        return None

def test_login():
    """Test user login"""
    print("\n🔐 Testing User Login...")
    
    login_data = {
        "email": "test@example.com",
        "password": "securepass123"
    }
    
    response = requests.post(f"{BASE_URL}/v1/auth/login", json=login_data)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Login successful!")
        print(f"📧 User: {data['user']['email']}")
        print(f"🔑 Token: {data['access_token'][:20]}...")
        return data['access_token']
    else:
        print("❌ Login failed:")
        print(f"Status: {response.status_code}")
        print(f"Error: {response.text}")
        return None

def test_protected_endpoint(token):
    """Test accessing protected endpoint"""
    print("\n🛡️ Testing Protected Endpoint...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(f"{BASE_URL}/v1/auth/me", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Protected endpoint access successful!")
        print(f"👤 User ID: {data['id']}")
        print(f"📧 Email: {data['email']}")
        print(f"👥 Username: {data['username']}")
        return True
    else:
        print("❌ Protected endpoint access failed:")
        print(f"Status: {response.status_code}")
        print(f"Error: {response.text}")
        return False

def test_without_auth():
    """Test accessing protected endpoint without authentication"""
    print("\n🚫 Testing Endpoint Without Authentication...")
    
    # Try to access a protected endpoint without token
    response = requests.get(f"{BASE_URL}/v1/auth/me")
    
    if response.status_code == 403:
        print("✅ Correctly blocked unauthorized access!")
        print(f"Status: {response.status_code}")
    else:
        print("❌ Security issue: Unauthorized access allowed!")
        print(f"Status: {response.status_code}")

if __name__ == "__main__":
    print("🚀 OAuth2 Authentication System Test")
    print("=" * 50)
    
    # Test registration (or login if user exists)
    token = test_registration()
    if not token:
        token = test_login()
    
    if token:
        # Test protected endpoint access
        test_protected_endpoint(token)
    
    # Test unauthorized access
    test_without_auth()
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")