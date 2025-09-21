#!/usr/bin/env python3
"""
Test script for the custom authentication backend.
This script demonstrates how to test the authentication functionality.
"""

import os
import sys
import django
import requests
import json

# Add the project directory to Python path
sys.path.append('/home/kouma/Desktop/Personal_Projects/Vibe_code')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finflow.settings')
django.setup()

from django.contrib.auth import authenticate
from finflow.core.models import User
from django.test import RequestFactory


def create_test_user():
    """Create a test user for authentication testing."""
    try:
        # Check if user already exists
        user = User.objects.get(username='testuser')
        print(f"✓ Test user already exists: {user.username}")
        return user
    except User.DoesNotExist:
        # Create new test user
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            risk_tolerance='moderate',
            investment_style='balanced'
        )
        print(f"✓ Created test user: {user.username} ({user.email})")
        return user


def test_backend_authentication():
    """Test the custom authentication backend directly."""
    print("\n" + "="*50)
    print("TESTING CUSTOM AUTHENTICATION BACKEND")
    print("="*50)
    
    # Create a mock request
    factory = RequestFactory()
    request = factory.post('/login/', {
        'username': 'testuser',
        'password': 'testpass123'
    })
    request.META['REMOTE_ADDR'] = '127.0.0.1'
    request.META['HTTP_USER_AGENT'] = 'Test Script/1.0'
    
    # Test 1: Authentication with username
    print("\n1. Testing authentication with username...")
    user = authenticate(request=request, username='testuser', password='testpass123')
    if user:
        print(f"   ✓ SUCCESS: Authenticated user {user.username}")
    else:
        print("   ✗ FAILED: Authentication failed")
    
    # Test 2: Authentication with email
    print("\n2. Testing authentication with email...")
    user = authenticate(request=request, username='test@example.com', password='testpass123')
    if user:
        print(f"   ✓ SUCCESS: Authenticated user {user.username} via email")
    else:
        print("   ✗ FAILED: Email authentication failed")
    
    # Test 3: Invalid password
    print("\n3. Testing invalid password...")
    user = authenticate(request=request, username='testuser', password='wrongpassword')
    if user:
        print("   ✗ FAILED: Should not authenticate with wrong password")
    else:
        print("   ✓ SUCCESS: Correctly rejected invalid password")
    
    # Test 4: Non-existent user
    print("\n4. Testing non-existent user...")
    user = authenticate(request=request, username='nonexistent', password='testpass123')
    if user:
        print("   ✗ FAILED: Should not authenticate non-existent user")
    else:
        print("   ✓ SUCCESS: Correctly rejected non-existent user")


def test_api_endpoints():
    """Test the API authentication endpoints."""
    print("\n" + "="*50)
    print("TESTING API AUTHENTICATION ENDPOINTS")
    print("="*50)
    
    base_url = 'http://localhost:8000'
    
    # Test 1: Login with username
    print("\n1. Testing API login with username...")
    try:
        response = requests.post(f'{base_url}/api/auth/login/', 
                               json={'username': 'testuser', 'password': 'testpass123'},
                               timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ SUCCESS: API login successful")
            print(f"   Token: {data.get('token', 'N/A')[:20]}...")
            return data.get('token')
        else:
            print(f"   ✗ FAILED: API login failed with status {response.status_code}")
            print(f"   Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"   ⚠ SKIPPED: Could not connect to server ({e})")
        return None
    
    # Test 2: Login with email
    print("\n2. Testing API login with email...")
    try:
        response = requests.post(f'{base_url}/api/auth/login/', 
                               json={'username': 'test@example.com', 'password': 'testpass123'},
                               timeout=5)
        if response.status_code == 200:
            print(f"   ✓ SUCCESS: API email login successful")
        else:
            print(f"   ✗ FAILED: API email login failed with status {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ⚠ SKIPPED: Could not connect to server ({e})")
    
    # Test 3: Invalid credentials
    print("\n3. Testing API with invalid credentials...")
    try:
        response = requests.post(f'{base_url}/api/auth/login/', 
                               json={'username': 'testuser', 'password': 'wrongpassword'},
                               timeout=5)
        if response.status_code == 401:
            print(f"   ✓ SUCCESS: Correctly rejected invalid credentials")
        else:
            print(f"   ✗ FAILED: Should return 401 for invalid credentials")
    except requests.exceptions.RequestException as e:
        print(f"   ⚠ SKIPPED: Could not connect to server ({e})")
    
    return None


def test_user_profile_api(token):
    """Test the user profile API endpoint."""
    if not token:
        print("\n⚠ SKIPPING: No token available for profile test")
        return
    
    print("\n4. Testing user profile API...")
    try:
        headers = {'Authorization': f'Token {token}'}
        response = requests.get('http://localhost:8000/api/auth/profile/', 
                              headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            user_data = data.get('user', {})
            print(f"   ✓ SUCCESS: Retrieved user profile")
            print(f"   Username: {user_data.get('username')}")
            print(f"   Email: {user_data.get('email')}")
            print(f"   Risk Tolerance: {user_data.get('risk_tolerance')}")
        else:
            print(f"   ✗ FAILED: Profile API failed with status {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ⚠ SKIPPED: Could not connect to server ({e})")


def main():
    """Main test function."""
    print("CUSTOM AUTHENTICATION BACKEND TEST SCRIPT")
    print("="*50)
    
    # Create test user
    user = create_test_user()
    
    # Test backend authentication
    test_backend_authentication()
    
    # Test API endpoints
    token = test_api_endpoints()
    
    # Test profile API
    test_user_profile_api(token)
    
    print("\n" + "="*50)
    print("TEST COMPLETED")
    print("="*50)
    print("\nTo run the Django development server:")
    print("python manage.py runserver")
    print("\nThen visit:")
    print("- http://localhost:8000/login/ (Login form)")
    print("- http://localhost:8000/dashboard/ (Protected dashboard)")
    print("- http://localhost:8000/api/auth/login/ (API endpoint)")
    print("\nCheck logs in:")
    print("- logs/auth.log (Authentication logs)")
    print("- logs/django.log (General Django logs)")


if __name__ == '__main__':
    main()
