from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'core'

# Create DRF router
router = DefaultRouter()
router.register(r'portfolios', views.PortfolioViewSet, basename='portfolio')
router.register(r'investments', views.InvestmentViewSet, basename='investment')
router.register(r'transactions', views.TransactionViewSet, basename='transaction')

urlpatterns = [
    path('', views.home, name='home'),
    path('analytics/', views.PortfolioAnalyticsView.as_view(), name='portfolio_analytics'),
    path('live-portfolio/', views.live_portfolio_view, name='live_portfolio'),
    path('api/health/', views.api_health, name='api_health'),

    # Authentication URLs
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Dashboard Pages
    path('portfolios/', views.portfolios_view, name='portfolios'),
    path('transactions/', views.transactions_view, name='transactions'),

    # API Authentication URLs
    path('api/auth/login/', views.api_login, name='api_login'),
    path('api/auth/logout/', views.api_logout, name='api_logout'),
    path('api/auth/profile/', views.api_user_profile, name='api_user_profile'),

    # DRF Router URLs
    path('api/', include(router.urls)),
]
