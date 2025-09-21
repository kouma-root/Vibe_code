import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finflow.settings')

app = Celery('finflow')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Schedule Configuration
app.conf.beat_schedule = {
    'refresh-portfolio-analytics': {
        'task': 'finflow.core.tasks.refresh_portfolio_analytics',
        'schedule': crontab(minute=0),  # Run every hour at minute 0
        'options': {
            'queue': 'analytics',
            'priority': 5,
        }
    },
    'cleanup-old-logs': {
        'task': 'finflow.core.tasks.cleanup_old_logs',
        'schedule': crontab(hour=2, minute=0),  # Run daily at 2 AM
        'options': {
            'queue': 'maintenance',
            'priority': 3,
        }
    },
    'health-check': {
        'task': 'finflow.core.tasks.health_check',
        'schedule': 60.0,  # Run every 60 seconds
        'options': {
            'queue': 'monitoring',
            'priority': 1,
        }
    },
}

# Celery Task Routes
app.conf.task_routes = {
    'finflow.core.tasks.refresh_portfolio_analytics': {'queue': 'analytics'},
    'finflow.core.tasks.cleanup_old_logs': {'queue': 'maintenance'},
    'finflow.core.tasks.health_check': {'queue': 'monitoring'},
    'finflow.core.tasks.*': {'queue': 'default'},
}

# Celery Task Time Limits
app.conf.task_time_limit = 300  # 5 minutes
app.conf.task_soft_time_limit = 240  # 4 minutes

# Celery Worker Configuration
app.conf.worker_prefetch_multiplier = 1
app.conf.task_acks_late = True
app.conf.worker_disable_rate_limits = False

# Celery Result Backend Configuration
app.conf.result_expires = 3600  # 1 hour
app.conf.result_persistent = True

# Celery Beat Configuration
app.conf.beat_scheduler = 'django_celery_beat.schedulers:DatabaseScheduler'

@app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery functionality."""
    print(f'Request: {self.request!r}')
    return f'Debug task executed successfully: {self.request.id}'
