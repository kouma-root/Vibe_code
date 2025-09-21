"""
Test cases for finflow.core models.

This module contains comprehensive tests for:
- User model functionality
- Portfolio creation and retrieval
- Investment unique constraints
- Model relationships and properties
- Custom managers and querysets
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

from ..models import User, Portfolio, Investment, Transaction


class UserModelTest(TestCase):
    """Test cases for the User model."""
    
    def setUp(self):
        """Set up test data."""
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'testpass123',
            'risk_tolerance': 'moderate',
            'investment_style': 'balanced'
        }
    
    def test_user_creation(self):
        """Test basic user creation."""
        user = User.objects.create_user(**self.user_data)
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertEqual(user.risk_tolerance, 'moderate')
        self.assertEqual(user.investment_style, 'balanced')
        self.assertTrue(user.is_active)
        self.assertIsNotNone(user.created_at)
        self.assertIsNotNone(user.updated_at)
    
    def test_user_full_name_property(self):
        """Test the full_name property."""
        # Test with first and last name
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.full_name, 'Test User')
        
        # Test with only first name
        user.first_name = 'Test'
        user.last_name = ''
        user.save()
        self.assertEqual(user.full_name, 'Test')
        
        # Test with only last name
        user.first_name = ''
        user.last_name = 'User'
        user.save()
        self.assertEqual(user.full_name, 'User')
        
        # Test with no first or last name
        user.first_name = ''
        user.last_name = ''
        user.save()
        self.assertEqual(user.full_name, 'testuser')
    
    def test_user_str_representation(self):
        """Test the string representation of User."""
        user = User.objects.create_user(**self.user_data)
        expected = f"{user.username} ({user.get_risk_tolerance_display()})"
        self.assertEqual(str(user), expected)
    
    def test_user_risk_tolerance_choices(self):
        """Test risk tolerance choices validation."""
        valid_choices = ['conservative', 'moderate', 'aggressive', 'very_aggressive']
        
        for i, choice in enumerate(valid_choices):
            user_data = self.user_data.copy()
            user_data['username'] = f'testuser_{i}'
            user_data['email'] = f'test{i}@example.com'
            user_data['risk_tolerance'] = choice
            user = User.objects.create_user(**user_data)
            self.assertEqual(user.risk_tolerance, choice)
    
    def test_user_investment_style_choices(self):
        """Test investment style choices validation."""
        valid_choices = [
            'value', 'growth', 'income', 'index', 'momentum',
            'dividend', 'balanced', 'sector_rotation'
        ]
        
        for i, choice in enumerate(valid_choices):
            user_data = self.user_data.copy()
            user_data['username'] = f'testuser_style_{i}'
            user_data['email'] = f'teststyle{i}@example.com'
            user_data['investment_style'] = choice
            user = User.objects.create_user(**user_data)
            self.assertEqual(user.investment_style, choice)


class PortfolioModelTest(TestCase):
    """Test cases for the Portfolio model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            risk_tolerance='moderate',
            investment_style='balanced'
        )
        
        self.portfolio_data = {
            'user': self.user,
            'name': 'Test Portfolio',
            'description': 'A test portfolio for unit testing',
            'is_active': True
        }
    
    def test_portfolio_creation(self):
        """Test basic portfolio creation."""
        portfolio = Portfolio.objects.create(**self.portfolio_data)
        
        self.assertEqual(portfolio.user, self.user)
        self.assertEqual(portfolio.name, 'Test Portfolio')
        self.assertEqual(portfolio.description, 'A test portfolio for unit testing')
        self.assertTrue(portfolio.is_active)
        self.assertIsNotNone(portfolio.created_at)
        self.assertIsNotNone(portfolio.updated_at)
    
    def test_portfolio_str_representation(self):
        """Test the string representation of Portfolio."""
        portfolio = Portfolio.objects.create(**self.portfolio_data)
        expected = f"{self.user.username} - {portfolio.name}"
        self.assertEqual(str(portfolio), expected)
    
    def test_portfolio_age_days_property(self):
        """Test the age_days property."""
        portfolio = Portfolio.objects.create(**self.portfolio_data)
        
        # Test with a portfolio created now
        self.assertEqual(portfolio.age_days, 0)
        
        # Test with a portfolio created 5 days ago
        old_date = timezone.now() - timedelta(days=5)
        portfolio.created_at = old_date
        portfolio.save()
        self.assertEqual(portfolio.age_days, 5)
    
    def test_portfolio_unique_constraint(self):
        """Test that a user cannot have two portfolios with the same name."""
        # Create first portfolio
        Portfolio.objects.create(**self.portfolio_data)
        
        # Try to create second portfolio with same name for same user
        with self.assertRaises(IntegrityError):
            Portfolio.objects.create(**self.portfolio_data)
    
    def test_portfolio_unique_constraint_different_users(self):
        """Test that different users can have portfolios with the same name."""
        # Create second user
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        # Create portfolio for first user
        portfolio1 = Portfolio.objects.create(**self.portfolio_data)
        
        # Create portfolio with same name for second user
        portfolio2_data = self.portfolio_data.copy()
        portfolio2_data['user'] = user2
        portfolio2 = Portfolio.objects.create(**portfolio2_data)
        
        self.assertEqual(portfolio1.name, portfolio2.name)
        self.assertNotEqual(portfolio1.user, portfolio2.user)
    
    def test_portfolio_ordering(self):
        """Test that portfolios are ordered by created_at descending."""
        # Create portfolios with different creation times
        portfolio1 = Portfolio.objects.create(**self.portfolio_data)
        
        portfolio2_data = self.portfolio_data.copy()
        portfolio2_data['name'] = 'Second Portfolio'
        portfolio2 = Portfolio.objects.create(**portfolio2_data)
        
        portfolio3_data = self.portfolio_data.copy()
        portfolio3_data['name'] = 'Third Portfolio'
        portfolio3 = Portfolio.objects.create(**portfolio3_data)
        
        # Get all portfolios
        portfolios = list(Portfolio.objects.all())
        
        # Should be ordered by created_at descending (newest first)
        self.assertEqual(portfolios[0], portfolio3)
        self.assertEqual(portfolios[1], portfolio2)
        self.assertEqual(portfolios[2], portfolio1)
    
    def test_portfolio_user_relationship(self):
        """Test the relationship between Portfolio and User."""
        portfolio = Portfolio.objects.create(**self.portfolio_data)
        
        # Test forward relationship
        self.assertEqual(portfolio.user, self.user)
        
        # Test reverse relationship
        user_portfolios = self.user.portfolios.all()
        self.assertIn(portfolio, user_portfolios)
        self.assertEqual(user_portfolios.count(), 1)
    
    def test_portfolio_inactive_status(self):
        """Test portfolio inactive status."""
        portfolio = Portfolio.objects.create(**self.portfolio_data)
        self.assertTrue(portfolio.is_active)
        
        # Deactivate portfolio
        portfolio.is_active = False
        portfolio.save()
        
        self.assertFalse(portfolio.is_active)
    
    def test_portfolio_without_description(self):
        """Test portfolio creation without description."""
        portfolio_data = self.portfolio_data.copy()
        del portfolio_data['description']
        
        portfolio = Portfolio.objects.create(**portfolio_data)
        self.assertIsNone(portfolio.description)


class InvestmentModelTest(TestCase):
    """Test cases for the Investment model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.portfolio = Portfolio.objects.create(
            user=self.user,
            name='Test Portfolio',
            description='A test portfolio'
        )
        
        self.investment_data = {
            'portfolio': self.portfolio,
            'symbol': 'AAPL',
            'quantity': Decimal('100.000000'),
            'purchase_price': Decimal('150.50'),
            'purchase_date': timezone.now()
        }
    
    def test_investment_creation(self):
        """Test basic investment creation."""
        investment = Investment.objects.create(**self.investment_data)
        
        self.assertEqual(investment.portfolio, self.portfolio)
        self.assertEqual(investment.symbol, 'AAPL')
        self.assertEqual(investment.quantity, Decimal('100.000000'))
        self.assertEqual(investment.purchase_price, Decimal('150.50'))
        self.assertIsNotNone(investment.purchase_date)
        self.assertIsNotNone(investment.created_at)
        self.assertIsNotNone(investment.updated_at)
    
    def test_investment_str_representation(self):
        """Test the string representation of Investment."""
        investment = Investment.objects.create(**self.investment_data)
        expected = f"AAPL - 100.000000 shares @ $150.50"
        self.assertEqual(str(investment), expected)
    
    def test_investment_total_value_property(self):
        """Test the total_value property calculation."""
        investment = Investment.objects.create(**self.investment_data)
        expected_value = Decimal('100.000000') * Decimal('150.50')
        self.assertEqual(investment.total_value, expected_value)
    
    def test_investment_unique_constraint(self):
        """Test that a portfolio cannot have two investments with the same symbol."""
        # Create first investment
        Investment.objects.create(**self.investment_data)
        
        # Try to create second investment with same symbol in same portfolio
        with self.assertRaises(IntegrityError):
            Investment.objects.create(**self.investment_data)
    
    def test_investment_unique_constraint_different_portfolios(self):
        """Test that different portfolios can have investments with the same symbol."""
        # Create second portfolio
        portfolio2 = Portfolio.objects.create(
            user=self.user,
            name='Second Portfolio',
            description='Another test portfolio'
        )
        
        # Create investment in first portfolio
        investment1 = Investment.objects.create(**self.investment_data)
        
        # Create investment with same symbol in second portfolio
        investment2_data = self.investment_data.copy()
        investment2_data['portfolio'] = portfolio2
        investment2 = Investment.objects.create(**investment2_data)
        
        self.assertEqual(investment1.symbol, investment2.symbol)
        self.assertNotEqual(investment1.portfolio, investment2.portfolio)
    
    def test_investment_ordering(self):
        """Test that investments are ordered by purchase_date descending."""
        # Create investments with different purchase dates
        investment1 = Investment.objects.create(**self.investment_data)
        
        investment2_data = self.investment_data.copy()
        investment2_data['symbol'] = 'MSFT'
        investment2_data['purchase_date'] = timezone.now() - timedelta(days=1)
        investment2 = Investment.objects.create(**investment2_data)
        
        investment3_data = self.investment_data.copy()
        investment3_data['symbol'] = 'GOOGL'
        investment3_data['purchase_date'] = timezone.now() - timedelta(days=2)
        investment3 = Investment.objects.create(**investment3_data)
        
        # Get all investments
        investments = list(Investment.objects.all())
        
        # Should be ordered by purchase_date descending (newest first)
        self.assertEqual(investments[0], investment1)
        self.assertEqual(investments[1], investment2)
        self.assertEqual(investments[2], investment3)
    
    def test_investment_portfolio_relationship(self):
        """Test the relationship between Investment and Portfolio."""
        investment = Investment.objects.create(**self.investment_data)
        
        # Test forward relationship
        self.assertEqual(investment.portfolio, self.portfolio)
        
        # Test reverse relationship
        portfolio_investments = self.portfolio.investments.all()
        self.assertIn(investment, portfolio_investments)
        self.assertEqual(portfolio_investments.count(), 1)
    
    def test_investment_decimal_precision(self):
        """Test decimal field precision for quantity and price."""
        # Test with high precision quantities
        investment_data = self.investment_data.copy()
        investment_data['quantity'] = Decimal('123.456789')
        investment_data['purchase_price'] = Decimal('999.99')
        
        investment = Investment.objects.create(**investment_data)
        
        self.assertEqual(investment.quantity, Decimal('123.456789'))
        self.assertEqual(investment.purchase_price, Decimal('999.99'))
    
    def test_investment_symbol_case_insensitive(self):
        """Test that symbol field preserves case but can be queried case-insensitively."""
        investment = Investment.objects.create(**self.investment_data)
        
        # Test case preservation
        self.assertEqual(investment.symbol, 'AAPL')
        
        # Test case-insensitive querying (this would be tested in manager/queryset tests)
        # For now, just verify the symbol is stored as provided
        investment.symbol = 'aapl'
        investment.save()
        self.assertEqual(investment.symbol, 'aapl')


class InvestmentManagerTest(TestCase):
    """Test cases for the Investment custom manager and queryset."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.portfolio1 = Portfolio.objects.create(
            user=self.user,
            name='Portfolio 1',
            description='First portfolio'
        )
        
        self.portfolio2 = Portfolio.objects.create(
            user=self.user,
            name='Portfolio 2',
            description='Second portfolio'
        )
        
        # Create test investments
        self.investment1 = Investment.objects.create(
            portfolio=self.portfolio1,
            symbol='AAPL',
            quantity=Decimal('100.000000'),
            purchase_price=Decimal('150.50')
        )
        
        self.investment2 = Investment.objects.create(
            portfolio=self.portfolio1,
            symbol='MSFT',
            quantity=Decimal('50.000000'),
            purchase_price=Decimal('300.00')
        )
        
        self.investment3 = Investment.objects.create(
            portfolio=self.portfolio2,
            symbol='GOOGL',
            quantity=Decimal('25.000000'),
            purchase_price=Decimal('2500.00')
        )
        
        # Create investment with zero quantity
        self.investment4 = Investment.objects.create(
            portfolio=self.portfolio1,
            symbol='TSLA',
            quantity=Decimal('0.000000'),
            purchase_price=Decimal('200.00')
        )
    
    def test_total_invested(self):
        """Test the total_invested method."""
        total = Investment.objects.total_invested()
        expected = (
            Decimal('100.000000') * Decimal('150.50') +  # AAPL
            Decimal('50.000000') * Decimal('300.00') +   # MSFT
            Decimal('25.000000') * Decimal('2500.00') +  # GOOGL
            Decimal('0.000000') * Decimal('200.00')      # TSLA (zero quantity)
        )
        self.assertEqual(total, expected)
    
    def test_average_purchase_price_all(self):
        """Test average purchase price for all investments."""
        avg_price = Investment.objects.average_purchase_price()
        expected = (
            Decimal('150.50') + Decimal('300.00') + Decimal('2500.00') + Decimal('200.00')
        ) / 4
        self.assertEqual(avg_price, expected)
    
    def test_average_purchase_price_symbol(self):
        """Test average purchase price for specific symbol."""
        # Create another AAPL investment in different portfolio
        Investment.objects.create(
            portfolio=self.portfolio2,
            symbol='AAPL',
            quantity=Decimal('75.000000'),
            purchase_price=Decimal('160.00')
        )
        
        avg_price = Investment.objects.average_purchase_price('AAPL')
        expected = (Decimal('150.50') + Decimal('160.00')) / 2
        self.assertEqual(avg_price, expected)
    
    def test_by_symbol(self):
        """Test filtering investments by symbol (case-insensitive)."""
        # Test exact case
        aapl_investments = Investment.objects.by_symbol('AAPL')
        self.assertEqual(aapl_investments.count(), 1)
        self.assertEqual(aapl_investments.first(), self.investment1)
        
        # Test lowercase
        aapl_investments_lower = Investment.objects.by_symbol('aapl')
        self.assertEqual(aapl_investments_lower.count(), 1)
        self.assertEqual(aapl_investments_lower.first(), self.investment1)
        
        # Test uppercase
        aapl_investments_upper = Investment.objects.by_symbol('AAPL')
        self.assertEqual(aapl_investments_upper.count(), 1)
        self.assertEqual(aapl_investments_upper.first(), self.investment1)
    
    def test_active_investments(self):
        """Test filtering active investments (quantity > 0)."""
        active_investments = Investment.objects.active_investments()
        
        # Should include investments with quantity > 0
        self.assertIn(self.investment1, active_investments)
        self.assertIn(self.investment2, active_investments)
        self.assertIn(self.investment3, active_investments)
        
        # Should exclude investments with quantity = 0
        self.assertNotIn(self.investment4, active_investments)
        
        self.assertEqual(active_investments.count(), 3)
    
    def test_by_portfolio(self):
        """Test filtering investments by portfolio."""
        portfolio1_investments = Investment.objects.by_portfolio(self.portfolio1)
        portfolio2_investments = Investment.objects.by_portfolio(self.portfolio2)
        
        # Portfolio 1 should have 3 investments (including zero quantity)
        self.assertEqual(portfolio1_investments.count(), 3)
        self.assertIn(self.investment1, portfolio1_investments)
        self.assertIn(self.investment2, portfolio1_investments)
        self.assertIn(self.investment4, portfolio1_investments)
        
        # Portfolio 2 should have 1 investment
        self.assertEqual(portfolio2_investments.count(), 1)
        self.assertIn(self.investment3, portfolio2_investments)


class ModelRelationshipsTest(TestCase):
    """Test cases for model relationships and cascading behavior."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
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
    
    def test_user_portfolio_cascade(self):
        """Test that deleting a user cascades to portfolios."""
        portfolio_id = self.portfolio.id
        investment_id = self.investment.id
        
        # Delete user
        self.user.delete()
        
        # Portfolio and investment should be deleted
        self.assertFalse(Portfolio.objects.filter(id=portfolio_id).exists())
        self.assertFalse(Investment.objects.filter(id=investment_id).exists())
    
    def test_portfolio_investment_cascade(self):
        """Test that deleting a portfolio cascades to investments."""
        investment_id = self.investment.id
        
        # Delete portfolio
        self.portfolio.delete()
        
        # Investment should be deleted
        self.assertFalse(Investment.objects.filter(id=investment_id).exists())
        
        # User should still exist
        self.assertTrue(User.objects.filter(id=self.user.id).exists())
    
    def test_related_objects_access(self):
        """Test accessing related objects through relationships."""
        # Test user -> portfolios -> investments
        user_portfolios = self.user.portfolios.all()
        self.assertEqual(user_portfolios.count(), 1)
        
        portfolio = user_portfolios.first()
        portfolio_investments = portfolio.investments.all()
        self.assertEqual(portfolio_investments.count(), 1)
        
        investment = portfolio_investments.first()
        self.assertEqual(investment.symbol, 'AAPL')
        
        # Test investment -> portfolio -> user
        investment_portfolio = self.investment.portfolio
        self.assertEqual(investment_portfolio, self.portfolio)
        
        portfolio_user = investment_portfolio.user
        self.assertEqual(portfolio_user, self.user)
    
    def test_multiple_portfolios_per_user(self):
        """Test that a user can have multiple portfolios."""
        portfolio2 = Portfolio.objects.create(
            user=self.user,
            name='Second Portfolio',
            description='Another portfolio'
        )
        
        portfolio3 = Portfolio.objects.create(
            user=self.user,
            name='Third Portfolio',
            description='Yet another portfolio'
        )
        
        user_portfolios = self.user.portfolios.all()
        self.assertEqual(user_portfolios.count(), 3)
        
        portfolio_names = [p.name for p in user_portfolios]
        self.assertIn('Test Portfolio', portfolio_names)
        self.assertIn('Second Portfolio', portfolio_names)
        self.assertIn('Third Portfolio', portfolio_names)
    
    def test_multiple_investments_per_portfolio(self):
        """Test that a portfolio can have multiple investments."""
        investment2 = Investment.objects.create(
            portfolio=self.portfolio,
            symbol='MSFT',
            quantity=Decimal('50.000000'),
            purchase_price=Decimal('300.00')
        )
        
        investment3 = Investment.objects.create(
            portfolio=self.portfolio,
            symbol='GOOGL',
            quantity=Decimal('25.000000'),
            purchase_price=Decimal('2500.00')
        )
        
        portfolio_investments = self.portfolio.investments.all()
        self.assertEqual(portfolio_investments.count(), 3)
        
        investment_symbols = [inv.symbol for inv in portfolio_investments]
        self.assertIn('AAPL', investment_symbols)
        self.assertIn('MSFT', investment_symbols)
        self.assertIn('GOOGL', investment_symbols)