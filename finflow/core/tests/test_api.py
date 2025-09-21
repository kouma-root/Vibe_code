"""
Test cases for finflow.core API endpoints.

This module contains comprehensive tests for:
- API authentication (login, logout, profile)
- Portfolio CRUD operations
- Investment CRUD operations
- Transaction CRUD operations
- API permissions and access control
- API response formats and status codes
"""

import json
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.utils import timezone

from ..models import Portfolio, Investment, Transaction

User = get_user_model()


class AuthenticationAPITest(APITestCase):
    """Test cases for authentication API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'testpass123',
            'risk_tolerance': 'moderate',
            'investment_style': 'balanced'
        }
        self.user = User.objects.create_user(**self.user_data)
        self.login_url = reverse('core:api_login')
        self.logout_url = reverse('core:api_logout')
        self.profile_url = reverse('core:api_user_profile')
    
    def test_api_login_with_username(self):
        """Test API login with username."""
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'Authentication successful')
        self.assertIn('token', response.data)
        self.assertIn('user', response.data)
        
        # Check user data in response
        user_data = response.data['user']
        self.assertEqual(user_data['username'], 'testuser')
        self.assertEqual(user_data['email'], 'test@example.com')
        self.assertEqual(user_data['risk_tolerance'], 'moderate')
        self.assertEqual(user_data['investment_style'], 'balanced')
    
    def test_api_login_with_email(self):
        """Test API login with email address."""
        login_data = {
            'username': 'test@example.com',  # Using email as username
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'Authentication successful')
        self.assertIn('token', response.data)
    
    def test_api_login_invalid_credentials(self):
        """Test API login with invalid credentials."""
        login_data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(self.login_url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invalid credentials')
    
    def test_api_login_missing_fields(self):
        """Test API login with missing required fields."""
        # Missing password
        login_data = {
            'username': 'testuser'
        }
        
        response = self.client.post(self.login_url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Username and password are required')
        
        # Missing username
        login_data = {
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Username and password are required')
    
    def test_api_login_inactive_user(self):
        """Test API login with inactive user."""
        self.user.is_active = False
        self.user.save()
        
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invalid credentials')
    
    def test_api_login_invalid_json(self):
        """Test API login with invalid JSON."""
        response = self.client.post(
            self.login_url,
            'invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invalid JSON format')
    
    def test_api_logout(self):
        """Test API logout functionality."""
        # First login to get a token
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        token = login_response.data['token']
        
        # Set the token for authentication
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        
        # Test logout
        response = self.client.post(self.logout_url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'Successfully logged out')
        
        # Verify token is deleted
        self.assertFalse(Token.objects.filter(key=token).exists())
    
    def test_api_logout_without_token(self):
        """Test API logout without authentication token."""
        response = self.client.post(self.logout_url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_api_user_profile(self):
        """Test API user profile retrieval."""
        # First login to get a token
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        token = login_response.data['token']
        
        # Set the token for authentication
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        
        # Test profile retrieval
        response = self.client.get(self.profile_url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        
        user_data = response.data['user']
        self.assertEqual(user_data['username'], 'testuser')
        self.assertEqual(user_data['email'], 'test@example.com')
        self.assertEqual(user_data['first_name'], 'Test')
        self.assertEqual(user_data['last_name'], 'User')
        self.assertEqual(user_data['risk_tolerance'], 'moderate')
        self.assertEqual(user_data['investment_style'], 'balanced')
    
    def test_api_user_profile_without_token(self):
        """Test API user profile without authentication token."""
        response = self.client.get(self.profile_url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PortfolioAPITest(APITestCase):
    """Test cases for Portfolio API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            risk_tolerance='moderate',
            investment_style='balanced'
        )
        self.token, _ = Token.objects.get_or_create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        # Create another user for permission tests
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        self.portfolio_data = {
            'name': 'Test Portfolio',
            'description': 'A test portfolio for API testing',
            'is_active': True
        }
    
    def test_create_portfolio(self):
        """Test creating a new portfolio."""
        response = self.client.post('/api/portfolios/', self.portfolio_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Test Portfolio')
        self.assertEqual(response.data['description'], 'A test portfolio for API testing')
        self.assertTrue(response.data['is_active'])
        self.assertEqual(response.data['user'], self.user.id)
        
        # Verify portfolio was created in database
        portfolio = Portfolio.objects.get(id=response.data['id'])
        self.assertEqual(portfolio.user, self.user)
        self.assertEqual(portfolio.name, 'Test Portfolio')
    
    def test_create_portfolio_without_authentication(self):
        """Test creating a portfolio without authentication."""
        self.client.credentials()  # Remove authentication
        
        response = self.client.post('/api/portfolios/', self.portfolio_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_portfolio_duplicate_name(self):
        """Test creating a portfolio with duplicate name for same user."""
        # Create first portfolio
        Portfolio.objects.create(user=self.user, name='Test Portfolio')
        
        # Try to create second portfolio with same name
        response = self.client.post('/api/portfolios/', self.portfolio_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_portfolio_different_users_same_name(self):
        """Test that different users can have portfolios with same name."""
        # Create portfolio for first user
        portfolio1 = Portfolio.objects.create(user=self.user, name='Test Portfolio')
        
        # Create portfolio with same name for second user
        portfolio2_data = self.portfolio_data.copy()
        portfolio2_data['user'] = self.other_user.id
        
        # Switch to other user's token
        other_token, _ = Token.objects.get_or_create(user=self.other_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {other_token.key}')
        
        response = self.client.post('/api/portfolios/', portfolio2_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Test Portfolio')
        self.assertEqual(response.data['user'], self.other_user.id)
    
    def test_list_portfolios(self):
        """Test listing user's portfolios."""
        # Create test portfolios
        portfolio1 = Portfolio.objects.create(
            user=self.user,
            name='Portfolio 1',
            description='First portfolio'
        )
        portfolio2 = Portfolio.objects.create(
            user=self.user,
            name='Portfolio 2',
            description='Second portfolio'
        )
        
        # Create portfolio for other user (should not appear in list)
        Portfolio.objects.create(
            user=self.other_user,
            name='Other Portfolio',
            description='Other user portfolio'
        )
        
        response = self.client.get('/api/portfolios/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        portfolio_names = [p['name'] for p in response.data['results']]
        self.assertIn('Portfolio 1', portfolio_names)
        self.assertIn('Portfolio 2', portfolio_names)
        self.assertNotIn('Other Portfolio', portfolio_names)
    
    def test_retrieve_portfolio(self):
        """Test retrieving a specific portfolio."""
        portfolio = Portfolio.objects.create(
            user=self.user,
            name='Test Portfolio',
            description='A test portfolio'
        )
        
        response = self.client.get(f'/api/portfolios/{portfolio.id}/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], portfolio.id)
        self.assertEqual(response.data['name'], 'Test Portfolio')
        self.assertEqual(response.data['description'], 'A test portfolio')
        self.assertEqual(response.data['user'], self.user.id)
    
    def test_retrieve_other_user_portfolio(self):
        """Test retrieving another user's portfolio (should be forbidden)."""
        portfolio = Portfolio.objects.create(
            user=self.other_user,
            name='Other Portfolio',
            description='Other user portfolio'
        )
        
        response = self.client.get(f'/api/portfolios/{portfolio.id}/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_portfolio(self):
        """Test updating a portfolio."""
        portfolio = Portfolio.objects.create(
            user=self.user,
            name='Original Name',
            description='Original description'
        )
        
        update_data = {
            'name': 'Updated Name',
            'description': 'Updated description',
            'is_active': False
        }
        
        response = self.client.put(f'/api/portfolios/{portfolio.id}/', update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Name')
        self.assertEqual(response.data['description'], 'Updated description')
        self.assertFalse(response.data['is_active'])
        
        # Verify changes in database
        portfolio.refresh_from_db()
        self.assertEqual(portfolio.name, 'Updated Name')
        self.assertEqual(portfolio.description, 'Updated description')
        self.assertFalse(portfolio.is_active)
    
    def test_partial_update_portfolio(self):
        """Test partial update of a portfolio."""
        portfolio = Portfolio.objects.create(
            user=self.user,
            name='Original Name',
            description='Original description',
            is_active=True
        )
        
        update_data = {
            'name': 'Updated Name'
        }
        
        response = self.client.patch(f'/api/portfolios/{portfolio.id}/', update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Name')
        self.assertEqual(response.data['description'], 'Original description')  # Should remain unchanged
        self.assertTrue(response.data['is_active'])  # Should remain unchanged
    
    def test_delete_portfolio(self):
        """Test deleting a portfolio."""
        portfolio = Portfolio.objects.create(
            user=self.user,
            name='Test Portfolio',
            description='A test portfolio'
        )
        
        response = self.client.delete(f'/api/portfolios/{portfolio.id}/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify portfolio was deleted
        self.assertFalse(Portfolio.objects.filter(id=portfolio.id).exists())
    
    def test_delete_other_user_portfolio(self):
        """Test deleting another user's portfolio (should be forbidden)."""
        portfolio = Portfolio.objects.create(
            user=self.other_user,
            name='Other Portfolio',
            description='Other user portfolio'
        )
        
        response = self.client.delete(f'/api/portfolios/{portfolio.id}/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Verify portfolio still exists
        self.assertTrue(Portfolio.objects.filter(id=portfolio.id).exists())


class InvestmentAPITest(APITestCase):
    """Test cases for Investment API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token, _ = Token.objects.get_or_create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.portfolio = Portfolio.objects.create(
            user=self.user,
            name='Test Portfolio',
            description='A test portfolio'
        )
        
        self.investment_data = {
            'portfolio': self.portfolio.id,
            'symbol': 'AAPL',
            'quantity': '100.000000',
            'purchase_price': '150.50',
            'purchase_date': timezone.now().isoformat()
        }
    
    def test_create_investment(self):
        """Test creating a new investment."""
        response = self.client.post('/api/investments/', self.investment_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['symbol'], 'AAPL')
        self.assertEqual(response.data['quantity'], '100.000000')
        self.assertEqual(response.data['purchase_price'], '150.50')
        self.assertEqual(response.data['portfolio'], self.portfolio.id)
        
        # Verify investment was created in database
        investment = Investment.objects.get(id=response.data['id'])
        self.assertEqual(investment.portfolio, self.portfolio)
        self.assertEqual(investment.symbol, 'AAPL')
        self.assertEqual(investment.quantity, Decimal('100.000000'))
        self.assertEqual(investment.purchase_price, Decimal('150.50'))
    
    def test_create_investment_without_authentication(self):
        """Test creating an investment without authentication."""
        self.client.credentials()  # Remove authentication
        
        response = self.client.post('/api/investments/', self.investment_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_investment_duplicate_symbol(self):
        """Test creating an investment with duplicate symbol in same portfolio."""
        # Create first investment
        Investment.objects.create(
            portfolio=self.portfolio,
            symbol='AAPL',
            quantity=Decimal('100.000000'),
            purchase_price=Decimal('150.50')
        )
        
        # Try to create second investment with same symbol
        response = self.client.post('/api/investments/', self.investment_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_investment_different_portfolios_same_symbol(self):
        """Test that different portfolios can have investments with same symbol."""
        # Create second portfolio
        portfolio2 = Portfolio.objects.create(
            user=self.user,
            name='Second Portfolio',
            description='Another portfolio'
        )
        
        # Create investment in first portfolio
        investment1 = Investment.objects.create(
            portfolio=self.portfolio,
            symbol='AAPL',
            quantity=Decimal('100.000000'),
            purchase_price=Decimal('150.50')
        )
        
        # Create investment with same symbol in second portfolio
        investment2_data = self.investment_data.copy()
        investment2_data['portfolio'] = portfolio2.id
        
        response = self.client.post('/api/investments/', investment2_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['symbol'], 'AAPL')
        self.assertEqual(response.data['portfolio'], portfolio2.id)
    
    def test_list_investments(self):
        """Test listing investments."""
        # Create test investments
        investment1 = Investment.objects.create(
            portfolio=self.portfolio,
            symbol='AAPL',
            quantity=Decimal('100.000000'),
            purchase_price=Decimal('150.50')
        )
        investment2 = Investment.objects.create(
            portfolio=self.portfolio,
            symbol='MSFT',
            quantity=Decimal('50.000000'),
            purchase_price=Decimal('300.00')
        )
        
        response = self.client.get('/api/investments/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        symbols = [inv['symbol'] for inv in response.data['results']]
        self.assertIn('AAPL', symbols)
        self.assertIn('MSFT', symbols)
    
    def test_retrieve_investment(self):
        """Test retrieving a specific investment."""
        investment = Investment.objects.create(
            portfolio=self.portfolio,
            symbol='AAPL',
            quantity=Decimal('100.000000'),
            purchase_price=Decimal('150.50')
        )
        
        response = self.client.get(f'/api/investments/{investment.id}/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], investment.id)
        self.assertEqual(response.data['symbol'], 'AAPL')
        self.assertEqual(response.data['quantity'], '100.000000')
        self.assertEqual(response.data['purchase_price'], '150.50')
    
    def test_update_investment(self):
        """Test updating an investment."""
        investment = Investment.objects.create(
            portfolio=self.portfolio,
            symbol='AAPL',
            quantity=Decimal('100.000000'),
            purchase_price=Decimal('150.50')
        )
        
        update_data = {
            'portfolio': self.portfolio.id,
            'symbol': 'AAPL',
            'quantity': '150.000000',
            'purchase_price': '160.00',
            'purchase_date': timezone.now().isoformat()
        }
        
        response = self.client.put(f'/api/investments/{investment.id}/', update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['quantity'], '150.000000')
        self.assertEqual(response.data['purchase_price'], '160.00')
        
        # Verify changes in database
        investment.refresh_from_db()
        self.assertEqual(investment.quantity, Decimal('150.000000'))
        self.assertEqual(investment.purchase_price, Decimal('160.00'))
    
    def test_delete_investment(self):
        """Test deleting an investment."""
        investment = Investment.objects.create(
            portfolio=self.portfolio,
            symbol='AAPL',
            quantity=Decimal('100.000000'),
            purchase_price=Decimal('150.50')
        )
        
        response = self.client.delete(f'/api/investments/{investment.id}/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify investment was deleted
        self.assertFalse(Investment.objects.filter(id=investment.id).exists())


class TransactionAPITest(APITestCase):
    """Test cases for Transaction API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token, _ = Token.objects.get_or_create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.portfolio = Portfolio.objects.create(
            user=self.user,
            name='Test Portfolio',
            description='A test portfolio'
        )
        
        self.investment = Investment.objects.create(
            portfolio=self.portfolio,
            symbol='AAPL',
            quantity=Decimal('100.000000'),
            purchase_price=Decimal('150.50')
        )
        
        self.transaction_data = {
            'investment': self.investment.id,
            'transaction_type': 'buy',
            'quantity': '50.000000',
            'price': '155.00',
            'transaction_date': timezone.now().isoformat(),
            'notes': 'Test transaction'
        }
    
    def test_create_transaction(self):
        """Test creating a new transaction."""
        response = self.client.post('/api/transactions/', self.transaction_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['transaction_type'], 'buy')
        self.assertEqual(response.data['quantity'], '50.000000')
        self.assertEqual(response.data['price'], '155.00')
        self.assertEqual(response.data['investment'], self.investment.id)
        self.assertEqual(response.data['notes'], 'Test transaction')
        
        # Verify transaction was created in database
        transaction = Transaction.objects.get(id=response.data['id'])
        self.assertEqual(transaction.investment, self.investment)
        self.assertEqual(transaction.transaction_type, 'buy')
        self.assertEqual(transaction.quantity, Decimal('50.000000'))
        self.assertEqual(transaction.price, Decimal('155.00'))
    
    def test_create_transaction_without_authentication(self):
        """Test creating a transaction without authentication."""
        self.client.credentials()  # Remove authentication
        
        response = self.client.post('/api/transactions/', self.transaction_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_list_transactions(self):
        """Test listing transactions."""
        # Create test transactions
        transaction1 = Transaction.objects.create(
            investment=self.investment,
            transaction_type='buy',
            quantity=Decimal('50.000000'),
            price=Decimal('155.00')
        )
        transaction2 = Transaction.objects.create(
            investment=self.investment,
            transaction_type='sell',
            quantity=Decimal('25.000000'),
            price=Decimal('160.00')
        )
        
        response = self.client.get('/api/transactions/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        transaction_types = [t['transaction_type'] for t in response.data['results']]
        self.assertIn('buy', transaction_types)
        self.assertIn('sell', transaction_types)
    
    def test_retrieve_transaction(self):
        """Test retrieving a specific transaction."""
        transaction = Transaction.objects.create(
            investment=self.investment,
            transaction_type='buy',
            quantity=Decimal('50.000000'),
            price=Decimal('155.00')
        )
        
        response = self.client.get(f'/api/transactions/{transaction.id}/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], transaction.id)
        self.assertEqual(response.data['transaction_type'], 'buy')
        self.assertEqual(response.data['quantity'], '50.000000')
        self.assertEqual(response.data['price'], '155.00')
    
    def test_update_transaction(self):
        """Test updating a transaction."""
        transaction = Transaction.objects.create(
            investment=self.investment,
            transaction_type='buy',
            quantity=Decimal('50.000000'),
            price=Decimal('155.00')
        )
        
        update_data = {
            'investment': self.investment.id,
            'transaction_type': 'buy',
            'quantity': '75.000000',
            'price': '160.00',
            'transaction_date': timezone.now().isoformat(),
            'notes': 'Updated transaction'
        }
        
        response = self.client.put(f'/api/transactions/{transaction.id}/', update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['quantity'], '75.000000')
        self.assertEqual(response.data['price'], '160.00')
        self.assertEqual(response.data['notes'], 'Updated transaction')
        
        # Verify changes in database
        transaction.refresh_from_db()
        self.assertEqual(transaction.quantity, Decimal('75.000000'))
        self.assertEqual(transaction.price, Decimal('160.00'))
        self.assertEqual(transaction.notes, 'Updated transaction')
    
    def test_delete_transaction(self):
        """Test deleting a transaction."""
        transaction = Transaction.objects.create(
            investment=self.investment,
            transaction_type='buy',
            quantity=Decimal('50.000000'),
            price=Decimal('155.00')
        )
        
        response = self.client.delete(f'/api/transactions/{transaction.id}/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify transaction was deleted
        self.assertFalse(Transaction.objects.filter(id=transaction.id).exists())


class APIPermissionsTest(APITestCase):
    """Test cases for API permissions and access control."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        
        # Create tokens
        self.token1, _ = Token.objects.get_or_create(user=self.user1)
        self.token2, _ = Token.objects.get_or_create(user=self.user2)
        
        # Create portfolios
        self.portfolio1 = Portfolio.objects.create(
            user=self.user1,
            name='User1 Portfolio',
            description='User1 portfolio'
        )
        self.portfolio2 = Portfolio.objects.create(
            user=self.user2,
            name='User2 Portfolio',
            description='User2 portfolio'
        )
        
        # Create investments
        self.investment1 = Investment.objects.create(
            portfolio=self.portfolio1,
            symbol='AAPL',
            quantity=Decimal('100.000000'),
            purchase_price=Decimal('150.50')
        )
        self.investment2 = Investment.objects.create(
            portfolio=self.portfolio2,
            symbol='MSFT',
            quantity=Decimal('50.000000'),
            purchase_price=Decimal('300.00')
        )
    
    def test_user_cannot_access_other_user_portfolios(self):
        """Test that users cannot access other users' portfolios."""
        # User1 tries to access User2's portfolio
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        
        response = self.client.get(f'/api/portfolios/{self.portfolio2.id}/', format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # User2 tries to access User1's portfolio
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token2.key}')
        
        response = self.client.get(f'/api/portfolios/{self.portfolio1.id}/', format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_user_cannot_modify_other_user_portfolios(self):
        """Test that users cannot modify other users' portfolios."""
        # User1 tries to update User2's portfolio
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        
        update_data = {
            'name': 'Hacked Portfolio',
            'description': 'This should not work',
            'is_active': False
        }
        
        response = self.client.put(f'/api/portfolios/{self.portfolio2.id}/', update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Verify portfolio was not modified
        self.portfolio2.refresh_from_db()
        self.assertEqual(self.portfolio2.name, 'User2 Portfolio')
        self.assertEqual(self.portfolio2.description, 'User2 portfolio')
        self.assertTrue(self.portfolio2.is_active)
    
    def test_user_cannot_access_other_user_investments(self):
        """Test that users cannot access other users' investments."""
        # User1 tries to access User2's investment
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        
        response = self.client.get(f'/api/investments/{self.investment2.id}/', format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_user_cannot_modify_other_user_investments(self):
        """Test that users cannot modify other users' investments."""
        # User1 tries to update User2's investment
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        
        update_data = {
            'portfolio': self.portfolio1.id,  # Try to move to own portfolio
            'symbol': 'HACKED',
            'quantity': '999.000000',
            'purchase_price': '999.99',
            'purchase_date': timezone.now().isoformat()
        }
        
        response = self.client.put(f'/api/investments/{self.investment2.id}/', update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Verify investment was not modified
        self.investment2.refresh_from_db()
        self.assertEqual(self.investment2.symbol, 'MSFT')
        self.assertEqual(self.investment2.quantity, Decimal('50.000000'))
        self.assertEqual(self.investment2.purchase_price, Decimal('300.00'))
    
    def test_user_cannot_create_investment_in_other_user_portfolio(self):
        """Test that users cannot create investments in other users' portfolios."""
        # User1 tries to create investment in User2's portfolio
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        
        investment_data = {
            'portfolio': self.portfolio2.id,
            'symbol': 'HACKED',
            'quantity': '100.000000',
            'purchase_price': '100.00',
            'purchase_date': timezone.now().isoformat()
        }
        
        response = self.client.post('/api/investments/', investment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verify investment was not created
        self.assertFalse(Investment.objects.filter(symbol='HACKED').exists())


class APIResponseFormatTest(APITestCase):
    """Test cases for API response formats and status codes."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token, _ = Token.objects.get_or_create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
    
    def test_api_response_content_type(self):
        """Test that API responses have correct content type."""
        response = self.client.get('/api/portfolios/', format='json')
        self.assertEqual(response['Content-Type'], 'application/json')
    
    def test_api_pagination_format(self):
        """Test that API responses include pagination information."""
        # Create multiple portfolios to trigger pagination
        for i in range(25):  # Assuming default page size is 20
            Portfolio.objects.create(
                user=self.user,
                name=f'Portfolio {i}',
                description=f'Portfolio number {i}'
            )
        
        response = self.client.get('/api/portfolios/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIn('results', response.data)
        self.assertEqual(response.data['count'], 25)
    
    def test_api_error_response_format(self):
        """Test that API error responses have consistent format."""
        # Test with invalid data
        invalid_data = {
            'name': '',  # Empty name should cause validation error
            'description': 'Test description'
        }
        
        response = self.client.post('/api/portfolios/', invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)  # Should contain field-specific errors
    
    def test_api_not_found_response(self):
        """Test that API returns 404 for non-existent resources."""
        response = self.client.get('/api/portfolios/99999/', format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_api_method_not_allowed(self):
        """Test that API returns 405 for unsupported HTTP methods."""
        # Try to use PATCH on a list endpoint (not allowed)
        response = self.client.patch('/api/portfolios/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
