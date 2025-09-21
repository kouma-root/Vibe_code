from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import ListView
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.authtoken.models import Token
from django.db.models import Sum, F, Count, Avg
from .models import Portfolio, Investment, Transaction, User
from .serializers import (
    PortfolioSerializer, PortfolioCreateSerializer, PortfolioUpdateSerializer,
    PortfolioDetailSerializer, InvestmentSerializer, TransactionSerializer
)
import json

# Create your views here.

def home(request):
    """Home page view"""
    return render(request, 'core/home.html')

@api_view(['GET'])
@permission_classes([AllowAny])
def api_health(request):
    """API health check endpoint"""
    return Response({
        'status': 'healthy',
        'message': 'FinFlow API is running',
        'version': '1.0.0'
    }, status=status.HTTP_200_OK)


class PortfolioViewSet(ModelViewSet):
    """
    ViewSet for managing portfolios with user-restricted access.
    Supports list, retrieve, create, update, delete operations.
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Restrict queryset to portfolios owned by the logged-in user."""
        return Portfolio.objects.filter(user=self.request.user).prefetch_related('investments')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return PortfolioCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PortfolioUpdateSerializer
        elif self.action == 'retrieve':
            return PortfolioDetailSerializer
        return PortfolioSerializer
    
    def perform_create(self, serializer):
        """Set the user to the current user when creating a portfolio."""
        serializer.save(user=self.request.user)
    
    def perform_update(self, serializer):
        """Ensure only the owner can update the portfolio."""
        if serializer.instance.user != self.request.user:
            return Response(
                {'detail': 'You do not have permission to perform this action.'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer.save()
    
    def perform_destroy(self, instance):
        """Ensure only the owner can delete the portfolio."""
        if instance.user != self.request.user:
            return Response(
                {'detail': 'You do not have permission to perform this action.'},
                status=status.HTTP_403_FORBIDDEN
            )
        instance.delete()
    
    @action(detail=True, methods=['get'])
    def investments(self, request, pk=None):
        """Get all investments for a specific portfolio."""
        portfolio = self.get_object()
        investments = portfolio.investments.all()
        serializer = InvestmentSerializer(investments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_investment(self, request, pk=None):
        """Add a new investment to the portfolio."""
        portfolio = self.get_object()
        serializer = InvestmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(portfolio=portfolio)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """Get portfolio summary with financial metrics."""
        portfolio = self.get_object()
        investments = portfolio.investments.all()
        
        # Calculate financial metrics
        from django.db.models import F
        total_invested = investments.aggregate(
            total=Sum(F('quantity') * F('purchase_price'))
        )['total'] or 0
        
        # Get investment count by symbol
        symbol_counts = {}
        for investment in investments:
            symbol = investment.symbol
            if symbol in symbol_counts:
                symbol_counts[symbol] += investment.quantity
            else:
                symbol_counts[symbol] = investment.quantity
        
        summary_data = {
            'portfolio_id': portfolio.id,
            'portfolio_name': portfolio.name,
            'total_investments': investments.count(),
            'total_invested': float(total_invested),
            'unique_symbols': len(symbol_counts),
            'holdings_by_symbol': symbol_counts,
            'created_at': portfolio.created_at,
            'age_days': portfolio.age_days
        }
        
        return Response(summary_data)
    
    @action(detail=False, methods=['get'])
    def my_portfolios(self, request):
        """Get all portfolios for the current user with summary data."""
        portfolios = self.get_queryset()
        serializer = self.get_serializer(portfolios, many=True)
        return Response(serializer.data)


class InvestmentViewSet(ModelViewSet):
    """
    ViewSet for managing investments within portfolios.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = InvestmentSerializer
    
    def get_queryset(self):
        """Restrict queryset to investments in portfolios owned by the logged-in user."""
        return Investment.objects.filter(
            portfolio__user=self.request.user
        ).select_related('portfolio')
    
    def perform_create(self, serializer):
        """Ensure the portfolio belongs to the current user."""
        portfolio_id = self.request.data.get('portfolio')
        if portfolio_id:
            try:
                portfolio = Portfolio.objects.get(id=portfolio_id, user=self.request.user)
                serializer.save(portfolio=portfolio)
            except Portfolio.DoesNotExist:
                return Response(
                    {'detail': 'Portfolio not found or access denied.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {'detail': 'Portfolio ID is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """Get all transactions for a specific investment."""
        investment = self.get_object()
        transactions = investment.transactions.all()
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_transaction(self, request, pk=None):
        """Add a new transaction to the investment."""
        investment = self.get_object()
        serializer = TransactionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(investment=investment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TransactionViewSet(ModelViewSet):
    """
    ViewSet for managing transactions.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionSerializer
    
    def get_queryset(self):
        """Restrict queryset to transactions for investments owned by the logged-in user."""
        return Transaction.objects.filter(
            investment__portfolio__user=self.request.user
        ).select_related('investment', 'investment__portfolio')


@method_decorator(cache_page(60 * 15), name='dispatch')  # Cache for 15 minutes
class PortfolioAnalyticsView(ListView):
    """
    Class-based view for portfolio analytics dashboard.
    Caches the entire page for 15 minutes.
    """
    model = Portfolio
    template_name = 'core/portfolio_analytics.html'
    context_object_name = 'portfolios'
    
    def get_queryset(self):
        """Get portfolios for the logged-in user."""
        if self.request.user.is_authenticated:
            return Portfolio.objects.filter(user=self.request.user).prefetch_related('investments')
        return Portfolio.objects.none()
    
    def get_context_data(self, **kwargs):
        """Add analytics data to context."""
        context = super().get_context_data(**kwargs)
        
        # Get cached analytics or generate new ones
        cache_key = f"portfolio_analytics_{self.request.user.id}"
        analytics = cache.get(cache_key)
        
        if analytics is None:
            analytics = self._generate_analytics()
            cache.set(cache_key, analytics, 60 * 15)  # Cache for 15 minutes
        
        context['analytics'] = analytics
        return context
    
    def _generate_analytics(self):
        """Generate analytics data for the user's portfolios."""
        if not self.request.user.is_authenticated:
            return {}
        
        portfolios = self.get_queryset()
        investments = Investment.objects.filter(portfolio__in=portfolios)
        transactions = Transaction.objects.filter(
            investment__portfolio__in=portfolios
        )
        
        # Basic portfolio metrics
        total_portfolios = portfolios.count()
        active_portfolios = portfolios.filter(is_active=True).count()
        
        # Investment metrics
        total_investments = investments.count()
        unique_symbols = investments.values('symbol').distinct().count()
        
        # Financial metrics
        total_invested = investments.aggregate(
            total=Sum(F('quantity') * F('purchase_price'))
        )['total'] or 0
        
        # Transaction metrics
        total_transactions = transactions.count()
        buy_transactions = transactions.filter(transaction_type='buy').count()
        sell_transactions = transactions.filter(transaction_type='sell').count()
        
        # Top performing symbols (mock data for now)
        top_symbols = [
            {'symbol': 'AAPL', 'value': 15000, 'change': 12.5, 'change_type': 'positive'},
            {'symbol': 'MSFT', 'value': 12000, 'change': 8.3, 'change_type': 'positive'},
            {'symbol': 'GOOGL', 'value': 8500, 'change': -2.1, 'change_type': 'negative'},
            {'symbol': 'TSLA', 'value': 6500, 'change': 15.7, 'change_type': 'positive'},
            {'symbol': 'AMZN', 'value': 4200, 'change': -5.2, 'change_type': 'negative'},
        ]
        
        # Portfolio performance (mock data)
        portfolio_performance = [
            {'name': 'Growth Portfolio', 'value': 45000, 'change': 8.5, 'change_type': 'positive'},
            {'name': 'Conservative Portfolio', 'value': 32000, 'change': 3.2, 'change_type': 'positive'},
            {'name': 'Tech Portfolio', 'value': 28000, 'change': -1.8, 'change_type': 'negative'},
        ]
        
        # Recent transactions (mock data)
        recent_transactions = [
            {'symbol': 'AAPL', 'type': 'Buy', 'amount': 5000, 'date': '2024-01-15'},
            {'symbol': 'MSFT', 'type': 'Sell', 'amount': -2000, 'date': '2024-01-14'},
            {'symbol': 'GOOGL', 'type': 'Buy', 'amount': 3000, 'date': '2024-01-13'},
            {'symbol': 'TSLA', 'type': 'Buy', 'amount': 1500, 'date': '2024-01-12'},
        ]
        
        # Risk analysis (mock data)
        risk_analysis = {
            'overall_risk': 'Moderate',
            'risk_score': 6.5,
            'diversification_score': 7.2,
            'volatility': 'Medium',
            'recommendations': [
                'Consider adding more bonds to reduce volatility',
                'Diversify across different sectors',
                'Review position sizes for better balance'
            ]
        }
        
        # Market trends (mock data)
        market_trends = {
            'market_status': 'Bull Market',
            'sector_performance': [
                {'sector': 'Technology', 'performance': 12.5, 'change_type': 'positive'},
                {'sector': 'Healthcare', 'performance': 8.3, 'change_type': 'positive'},
                {'sector': 'Finance', 'performance': 5.1, 'change_type': 'positive'},
                {'sector': 'Energy', 'performance': -3.2, 'change_type': 'negative'},
            ]
        }
        
        return {
            'overview': {
                'total_portfolios': total_portfolios,
                'active_portfolios': active_portfolios,
                'total_investments': total_investments,
                'unique_symbols': unique_symbols,
                'total_invested': float(total_invested),
                'total_transactions': total_transactions,
                'buy_transactions': buy_transactions,
                'sell_transactions': sell_transactions,
            },
            'top_symbols': top_symbols,
            'portfolio_performance': portfolio_performance,
            'recent_transactions': recent_transactions,
            'risk_analysis': risk_analysis,
            'market_trends': market_trends,
        }


# Authentication Views

@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    """
    API endpoint for user authentication using username or email.
    Demonstrates the custom authentication backend usage.
    
    Expected JSON payload:
    {
        "username": "user@example.com" or "username",
        "password": "userpassword"
    }
    
    Returns:
    - 200: Successful authentication with user data and token
    - 400: Invalid credentials or missing fields
    - 401: Authentication failed
    """
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return Response({
                'error': 'Username and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Use Django's authenticate function which will use our custom backend
        user = authenticate(request=request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                # Create or get authentication token
                token, created = Token.objects.get_or_create(user=user)
                
                # Log successful login
                login(request, user)
                
                return Response({
                    'success': True,
                    'message': 'Authentication successful',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'full_name': user.full_name,
                        'risk_tolerance': user.risk_tolerance,
                        'investment_style': user.investment_style,
                        'is_active': user.is_active,
                        'date_joined': user.date_joined,
                    },
                    'token': token.key,
                    'token_created': created
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Account is inactive'
                }, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
    except json.JSONDecodeError:
        return Response({
            'error': 'Invalid JSON format'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': f'Authentication error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_logout(request):
    """
    API endpoint for user logout.
    Invalidates the authentication token.
    """
    try:
        # Delete the token
        Token.objects.filter(user=request.user).delete()
        
        # Logout the user
        logout(request)
        
        return Response({
            'success': True,
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Logout error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_user_profile(request):
    """
    API endpoint to get current user profile information.
    """
    user = request.user
    return Response({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.full_name,
            'risk_tolerance': user.risk_tolerance,
            'investment_style': user.investment_style,
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'date_joined': user.date_joined,
            'last_login': user.last_login,
        }
    }, status=status.HTTP_200_OK)


# Traditional Django Views for form-based authentication

def login_view(request):
    """
    Traditional Django login view for form-based authentication.
    Demonstrates the custom authentication backend usage with forms.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            # Use Django's authenticate function which will use our custom backend
            user = authenticate(request=request, username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return JsonResponse({
                        'success': True,
                        'message': 'Login successful',
                        'redirect_url': '/dashboard/'
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Account is inactive'
                    })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid credentials'
                })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Username and password are required'
            })
    
    # GET request - show login form
    return render(request, 'core/login.html')


@login_required
def logout_view(request):
    """
    Traditional Django logout view.
    """
    logout(request)
    return JsonResponse({
        'success': True,
        'message': 'Logout successful',
        'redirect_url': '/'
    })


@login_required
def dashboard_view(request):
    """
    Protected dashboard view that requires authentication.
    """
    user = request.user
    context = {
        'user': user,
        'portfolios_count': Portfolio.objects.filter(user=user).count(),
        'investments_count': Investment.objects.filter(portfolio__user=user).count(),
    }
    return render(request, 'core/dashboard.html', context)


def live_portfolio_view(request):
    """
    Live portfolio view with WebSocket integration.
    Shows real-time portfolio price updates.
    """
    return render(request, 'core/live_portfolio.html')


def portfolios_view(request):
    """
    Portfolios management view.
    Shows portfolio cards and management interface.
    """
    return render(request, 'core/portfolios.html')


def transactions_view(request):
    """
    Transactions history view.
    Shows transaction history and management interface.
    """
    return render(request, 'core/transactions.html')
