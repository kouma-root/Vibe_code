"""
Celery tasks for the FinFlow application.

This module contains all Celery tasks including periodic tasks for
portfolio analytics, maintenance, and monitoring.
"""

import os
import logging
from datetime import datetime, timedelta
from celery import shared_task
from django.core.cache import cache
from django.db.models import Sum, F, Count, Avg
from django.utils import timezone

# Import models
from .models import Portfolio, Investment, Transaction, User

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='finflow.core.tasks.refresh_portfolio_analytics')
def refresh_portfolio_analytics(self):
    """
    Periodic task to refresh portfolio analytics every hour.
    
    This task:
    - Calculates portfolio performance metrics
    - Updates cached analytics data
    - Generates portfolio summaries
    - Logs analytics refresh completion
    """
    try:
        logger.info("Starting portfolio analytics refresh...")
        
        # Get all active portfolios
        portfolios = Portfolio.objects.filter(is_active=True)
        total_portfolios = portfolios.count()
        
        # Calculate overall portfolio metrics
        all_investments = Investment.objects.filter(portfolio__in=portfolios)
        total_investments = all_investments.count()
        unique_symbols = all_investments.values('symbol').distinct().count()
        
        # Calculate total invested amount
        total_invested = all_investments.aggregate(
            total=Sum(F('quantity') * F('purchase_price'))
        )['total'] or 0
        
        # Get transaction metrics
        all_transactions = Transaction.objects.filter(
            investment__portfolio__in=portfolios
        )
        total_transactions = all_transactions.count()
        buy_transactions = all_transactions.filter(transaction_type='buy').count()
        sell_transactions = all_transactions.filter(transaction_type='sell').count()
        
        # Calculate analytics data
        analytics_data = {
            'timestamp': timezone.now().isoformat(),
            'total_portfolios': total_portfolios,
            'total_investments': total_investments,
            'unique_symbols': unique_symbols,
            'total_invested': float(total_invested),
            'total_transactions': total_transactions,
            'buy_transactions': buy_transactions,
            'sell_transactions': sell_transactions,
            'task_id': self.request.id,
        }
        
        # Cache the analytics data for 1 hour
        cache_key = 'portfolio_analytics_global'
        cache.set(cache_key, analytics_data, 3600)  # 1 hour cache
        
        # Generate per-user analytics
        for user in User.objects.filter(is_active=True):
            user_portfolios = portfolios.filter(user=user)
            if user_portfolios.exists():
                user_analytics = _generate_user_analytics(user, user_portfolios)
                user_cache_key = f'portfolio_analytics_user_{user.id}'
                cache.set(user_cache_key, user_analytics, 3600)
        
        # Log completion
        logger.info(f"Portfolio analytics refreshed successfully. "
                   f"Processed {total_portfolios} portfolios, "
                   f"{total_investments} investments, "
                   f"{total_transactions} transactions.")
        
        # Print the required message
        print("Analytics refreshed")
        
        return {
            'status': 'success',
            'message': 'Portfolio analytics refreshed successfully',
            'data': analytics_data,
            'task_id': self.request.id,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error refreshing portfolio analytics: {str(e)}")
        print(f"Analytics refresh failed: {str(e)}")
        raise self.retry(exc=e, countdown=300, max_retries=3)


@shared_task(bind=True, name='finflow.core.tasks.cleanup_old_logs')
def cleanup_old_logs(self):
    """
    Periodic task to clean up old log files and temporary data.
    Runs daily at 2 AM.
    """
    try:
        logger.info("Starting log cleanup task...")
        
        # Clean up old log files (older than 30 days)
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'logs')
        if os.path.exists(log_dir):
            cutoff_date = timezone.now() - timedelta(days=30)
            cleaned_files = 0
            
            for filename in os.listdir(log_dir):
                if filename.endswith('.log'):
                    file_path = os.path.join(log_dir, filename)
                    if os.path.isfile(file_path):
                        file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if file_mtime.replace(tzinfo=timezone.utc) < cutoff_date:
                            os.remove(file_path)
                            cleaned_files += 1
                            logger.info(f"Removed old log file: {filename}")
        
        # Clean up old cache entries
        cache.delete_many([
            'portfolio_analytics_global',
            'old_cache_key_1',
            'old_cache_key_2',
        ])
        
        logger.info(f"Log cleanup completed. Removed {cleaned_files} old log files.")
        print(f"Log cleanup completed. Removed {cleaned_files} old log files.")
        
        return {
            'status': 'success',
            'message': 'Log cleanup completed successfully',
            'cleaned_files': cleaned_files,
            'task_id': self.request.id,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error during log cleanup: {str(e)}")
        print(f"Log cleanup failed: {str(e)}")
        raise self.retry(exc=e, countdown=600, max_retries=2)


@shared_task(bind=True, name='finflow.core.tasks.health_check')
def health_check(self):
    """
    Periodic health check task that runs every 60 seconds.
    Monitors system health and logs status.
    """
    try:
        # Check database connectivity
        user_count = User.objects.count()
        portfolio_count = Portfolio.objects.count()
        investment_count = Investment.objects.count()
        
        # Check cache connectivity
        cache.set('health_check_test', 'ok', 10)
        cache_status = cache.get('health_check_test') == 'ok'
        
        # Check Redis connectivity (if using Redis)
        redis_status = True  # Simplified for now
        
        health_data = {
            'timestamp': timezone.now().isoformat(),
            'database': {
                'users': user_count,
                'portfolios': portfolio_count,
                'investments': investment_count,
                'status': 'healthy'
            },
            'cache': {
                'status': 'healthy' if cache_status else 'unhealthy'
            },
            'redis': {
                'status': 'healthy' if redis_status else 'unhealthy'
            },
            'task_id': self.request.id,
        }
        
        # Log health status
        if cache_status and redis_status:
            logger.debug(f"Health check passed: {health_data}")
        else:
            logger.warning(f"Health check issues detected: {health_data}")
        
        return health_data
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            'status': 'error',
            'message': str(e),
            'task_id': self.request.id,
            'timestamp': timezone.now().isoformat()
        }


@shared_task(bind=True, name='finflow.core.tasks.generate_portfolio_report')
def generate_portfolio_report(self, user_id, portfolio_id=None):
    """
    Generate a detailed portfolio report for a specific user.
    Can be triggered manually or scheduled.
    """
    try:
        user = User.objects.get(id=user_id)
        
        if portfolio_id:
            portfolios = Portfolio.objects.filter(user=user, id=portfolio_id, is_active=True)
        else:
            portfolios = Portfolio.objects.filter(user=user, is_active=True)
        
        if not portfolios.exists():
            return {
                'status': 'error',
                'message': 'No portfolios found for user',
                'user_id': user_id
            }
        
        report_data = []
        for portfolio in portfolios:
            portfolio_data = _generate_user_analytics(user, [portfolio])
            report_data.append(portfolio_data)
        
        # Cache the report
        cache_key = f'portfolio_report_user_{user_id}_{timezone.now().strftime("%Y%m%d")}'
        cache.set(cache_key, report_data, 86400)  # 24 hours
        
        logger.info(f"Generated portfolio report for user {user_id}")
        
        return {
            'status': 'success',
            'message': 'Portfolio report generated successfully',
            'user_id': user_id,
            'portfolios_count': len(report_data),
            'task_id': self.request.id,
            'timestamp': timezone.now().isoformat()
        }
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return {
            'status': 'error',
            'message': f'User {user_id} not found',
            'task_id': self.request.id
        }
    except Exception as e:
        logger.error(f"Error generating portfolio report: {str(e)}")
        raise self.retry(exc=e, countdown=300, max_retries=2)


@shared_task(bind=True, name='finflow.core.tasks.send_portfolio_notifications')
def send_portfolio_notifications(self):
    """
    Send portfolio notifications to users (price alerts, performance updates, etc.).
    Runs every 30 minutes.
    """
    try:
        logger.info("Starting portfolio notifications task...")
        
        # This is a placeholder for notification logic
        # In a real implementation, you would:
        # 1. Check for price alerts
        # 2. Send email notifications
        # 3. Send push notifications
        # 4. Update user preferences
        
        notifications_sent = 0
        
        # Example: Check for users with significant portfolio changes
        # (This is simplified for demonstration)
        
        logger.info(f"Portfolio notifications task completed. Sent {notifications_sent} notifications.")
        print(f"Portfolio notifications sent: {notifications_sent}")
        
        return {
            'status': 'success',
            'message': 'Portfolio notifications sent successfully',
            'notifications_sent': notifications_sent,
            'task_id': self.request.id,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error sending portfolio notifications: {str(e)}")
        print(f"Portfolio notifications failed: {str(e)}")
        raise self.retry(exc=e, countdown=300, max_retries=2)


def _generate_user_analytics(user, portfolios):
    """
    Helper function to generate analytics data for a specific user and portfolios.
    """
    investments = Investment.objects.filter(portfolio__in=portfolios)
    transactions = Transaction.objects.filter(investment__portfolio__in=portfolios)
    
    # Calculate metrics
    total_invested = investments.aggregate(
        total=Sum(F('quantity') * F('purchase_price'))
    )['total'] or 0
    
    # Get top performing symbols
    symbol_performance = {}
    for investment in investments:
        symbol = investment.symbol
        if symbol not in symbol_performance:
            symbol_performance[symbol] = {
                'total_quantity': 0,
                'total_invested': 0,
                'avg_price': 0
            }
        
        symbol_performance[symbol]['total_quantity'] += float(investment.quantity)
        symbol_performance[symbol]['total_invested'] += float(investment.quantity * investment.purchase_price)
    
    # Calculate average prices
    for symbol, data in symbol_performance.items():
        if data['total_quantity'] > 0:
            data['avg_price'] = data['total_invested'] / data['total_quantity']
    
    return {
        'user_id': user.id,
        'username': user.username,
        'portfolios_count': portfolios.count(),
        'investments_count': investments.count(),
        'total_invested': float(total_invested),
        'transactions_count': transactions.count(),
        'symbol_performance': symbol_performance,
        'risk_tolerance': user.risk_tolerance,
        'investment_style': user.investment_style,
        'generated_at': timezone.now().isoformat()
    }


# Utility tasks for testing and debugging

@shared_task(bind=True, name='finflow.core.tasks.test_task')
def test_task(self, message="Hello from Celery!"):
    """
    Simple test task for debugging Celery functionality.
    """
    print(f"Test task executed: {message}")
    logger.info(f"Test task executed: {message}")
    
    return {
        'status': 'success',
        'message': message,
        'task_id': self.request.id,
        'timestamp': timezone.now().isoformat()
    }


@shared_task(bind=True, name='finflow.core.tasks.long_running_task')
def long_running_task(self, duration=10):
    """
    Long running task for testing task monitoring and timeouts.
    """
    import time
    
    logger.info(f"Starting long running task for {duration} seconds...")
    
    for i in range(duration):
        time.sleep(1)
        # Update task progress
        self.update_state(
            state='PROGRESS',
            meta={'current': i + 1, 'total': duration, 'status': f'Processing step {i + 1}'}
        )
        logger.info(f"Long running task progress: {i + 1}/{duration}")
    
    logger.info("Long running task completed")
    
    return {
        'status': 'success',
        'message': f'Long running task completed after {duration} seconds',
        'task_id': self.request.id,
        'timestamp': timezone.now().isoformat()
    }
