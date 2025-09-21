from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.db.models import Sum, Avg, Q
from decimal import Decimal


class User(AbstractUser):
    """
    Custom User model extending AbstractUser with additional financial profile fields.
    """
    RISK_TOLERANCE_CHOICES = [
        ('conservative', 'Conservative'),
        ('moderate', 'Moderate'),
        ('aggressive', 'Aggressive'),
        ('very_aggressive', 'Very Aggressive'),
    ]
    
    INVESTMENT_STYLE_CHOICES = [
        ('value', 'Value Investing'),
        ('growth', 'Growth Investing'),
        ('income', 'Income Investing'),
        ('index', 'Index Investing'),
        ('momentum', 'Momentum Investing'),
        ('dividend', 'Dividend Investing'),
        ('balanced', 'Balanced'),
        ('sector_rotation', 'Sector Rotation'),
    ]
    
    risk_tolerance = models.CharField(
        max_length=20,
        choices=RISK_TOLERANCE_CHOICES,
        default='moderate',
        help_text='User\'s risk tolerance level for investments'
    )
    
    investment_style = models.CharField(
        max_length=50,
        choices=INVESTMENT_STYLE_CHOICES,
        default='balanced',
        help_text='User\'s preferred investment style'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'auth_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['risk_tolerance']),
            models.Index(fields=['investment_style']),
        ]
    
    def __str__(self):
        return f"{self.username} ({self.get_risk_tolerance_display()})"
    
    @property
    def full_name(self):
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip() or self.username


class Portfolio(models.Model):
    """
    Portfolio model representing a user's investment portfolio.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='portfolios',
        help_text='The user who owns this portfolio'
    )
    
    name = models.CharField(
        max_length=100,
        help_text='Name of the portfolio'
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        help_text='Optional description of the portfolio'
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text='When the portfolio was created'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='When the portfolio was last updated'
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text='Whether the portfolio is currently active'
    )
    
    class Meta:
        db_table = 'core_portfolio'
        verbose_name = 'Portfolio'
        verbose_name_plural = 'Portfolios'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['created_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'name'],
                name='unique_user_portfolio_name'
            )
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"
    
    @property
    def age_days(self):
        """Return the age of the portfolio in days."""
        return (timezone.now() - self.created_at).days


class InvestmentQuerySet(models.QuerySet):
    """
    Custom QuerySet for Investment model with financial calculations.
    """
    
    def total_invested(self):
        """Calculate total amount invested across all investments."""
        return self.aggregate(
            total=Sum(models.F('quantity') * models.F('purchase_price'))
        )['total'] or Decimal('0.00')
    
    def average_purchase_price(self, symbol=None):
        """Calculate average purchase price for a specific symbol or all investments."""
        queryset = self
        if symbol:
            queryset = queryset.filter(symbol__iexact=symbol)
        
        result = queryset.aggregate(
            avg_price=Avg('purchase_price')
        )['avg_price']
        return result or Decimal('0.00')
    
    def by_symbol(self, symbol):
        """Filter investments by symbol (case-insensitive)."""
        return self.filter(symbol__iexact=symbol)
    
    def active_investments(self):
        """Return investments with quantity > 0."""
        return self.filter(quantity__gt=0)
    
    def by_portfolio(self, portfolio):
        """Filter investments by portfolio."""
        return self.filter(portfolio=portfolio)


class InvestmentManager(models.Manager):
    """
    Custom Manager for Investment model.
    """
    
    def get_queryset(self):
        return InvestmentQuerySet(self.model, using=self._db)
    
    def total_invested(self):
        return self.get_queryset().total_invested()
    
    def average_purchase_price(self, symbol=None):
        return self.get_queryset().average_purchase_price(symbol)
    
    def by_symbol(self, symbol):
        return self.get_queryset().by_symbol(symbol)
    
    def active_investments(self):
        return self.get_queryset().active_investments()
    
    def by_portfolio(self, portfolio):
        return self.get_queryset().by_portfolio(portfolio)


class Investment(models.Model):
    """
    Investment model representing individual stock/asset holdings in a portfolio.
    """
    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        related_name='investments',
        help_text='The portfolio containing this investment'
    )
    
    symbol = models.CharField(
        max_length=20,
        help_text='Stock symbol or asset identifier (e.g., AAPL, MSFT)'
    )
    
    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        help_text='Number of shares/units held'
    )
    
    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Price per share/unit at purchase'
    )
    
    purchase_date = models.DateTimeField(
        default=timezone.now,
        help_text='Date when the investment was purchased'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = InvestmentManager()
    
    class Meta:
        db_table = 'core_investment'
        verbose_name = 'Investment'
        verbose_name_plural = 'Investments'
        ordering = ['-purchase_date']
        indexes = [
            models.Index(fields=['portfolio', 'symbol']),
            models.Index(fields=['symbol']),
            models.Index(fields=['purchase_date']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['portfolio', 'symbol'],
                name='unique_portfolio_symbol'
            )
        ]
    
    def __str__(self):
        return f"{self.symbol} - {self.quantity} shares @ ${self.purchase_price}"
    
    @property
    def total_value(self):
        """Calculate total value of this investment."""
        return self.quantity * self.purchase_price
    
    @property
    def days_held(self):
        """Calculate number of days this investment has been held."""
        return (timezone.now() - self.purchase_date).days


class Transaction(models.Model):
    """
    Transaction model representing buy/sell transactions for investments.
    """
    TRANSACTION_TYPE_CHOICES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
        ('dividend', 'Dividend'),
        ('split', 'Stock Split'),
        ('transfer', 'Transfer'),
    ]
    
    investment = models.ForeignKey(
        Investment,
        on_delete=models.CASCADE,
        related_name='transactions',
        help_text='The investment this transaction relates to'
    )
    
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES,
        help_text='Type of transaction performed'
    )
    
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text='Transaction amount (positive for buy, negative for sell)'
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text='When the transaction occurred'
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        help_text='Optional notes about the transaction'
    )
    
    class Meta:
        db_table = 'core_transaction'
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['investment', 'timestamp']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.investment.symbol} - ${self.amount}"
    
    @property
    def is_buy(self):
        """Check if this is a buy transaction."""
        return self.transaction_type == 'buy'
    
    @property
    def is_sell(self):
        """Check if this is a sell transaction."""
        return self.transaction_type == 'sell'
