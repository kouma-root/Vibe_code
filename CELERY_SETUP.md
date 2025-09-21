# Celery Configuration with Redis Broker

This document describes the complete Celery setup for the FinFlow application with Redis broker and periodic tasks.

## ✅ Implementation Complete

The Celery configuration has been successfully implemented with:
- Redis broker and result backend
- Periodic tasks for portfolio analytics
- Task routing and queue management
- Comprehensive task monitoring

## 📁 Files Created/Modified

### 1. **`finflow/celery.py`** (MODIFIED)
Enhanced Celery configuration with:
- Periodic task scheduling (Beat schedule)
- Task routing configuration
- Worker and result backend settings
- Time limits and retry policies

### 2. **`finflow/settings.py`** (MODIFIED)
Updated Django settings with:
- Celery broker and result backend configuration
- Task routing and queue setup
- Worker configuration
- Beat scheduler settings
- Added `django_celery_beat` and `django_celery_results` to INSTALLED_APPS

### 3. **`finflow/core/tasks.py`** (NEW)
Comprehensive task definitions including:
- `refresh_portfolio_analytics` - Runs every hour
- `cleanup_old_logs` - Runs daily at 2 AM
- `health_check` - Runs every 60 seconds
- Additional utility tasks for testing and monitoring

### 4. **`test_celery.py`** (NEW)
Test script to verify Celery configuration and task execution.

## 🚀 Key Features Implemented

### ✅ **Periodic Tasks**
- **Portfolio Analytics**: Refreshes every hour at minute 0
- **Log Cleanup**: Runs daily at 2 AM
- **Health Check**: Runs every 60 seconds
- **Customizable Schedules**: Easy to modify timing

### ✅ **Task Routing & Queues**
- **Analytics Queue**: For portfolio analytics tasks
- **Maintenance Queue**: For cleanup and maintenance tasks
- **Monitoring Queue**: For health checks and monitoring
- **Default Queue**: For general tasks

### ✅ **Redis Integration**
- **Broker**: Redis for message queuing
- **Result Backend**: Redis for task results
- **Persistent Results**: Results stored for 1 hour
- **Task Tracking**: Full task lifecycle monitoring

### ✅ **Error Handling & Retries**
- **Automatic Retries**: Failed tasks retry with backoff
- **Time Limits**: 5-minute hard limit, 4-minute soft limit
- **Comprehensive Logging**: Detailed task execution logs
- **Graceful Degradation**: Handles Redis connection issues

## 📊 Periodic Task Schedule

| Task | Schedule | Queue | Description |
|------|----------|-------|-------------|
| `refresh_portfolio_analytics` | Every hour (minute 0) | analytics | Refreshes portfolio analytics data |
| `cleanup_old_logs` | Daily at 2 AM | maintenance | Cleans up old log files |
| `health_check` | Every 60 seconds | monitoring | System health monitoring |

## 🛠 Commands to Run Celery

### **1. Start Celery Worker**
```bash
cd /home/kouma/Desktop/Personal_Projects/Vibe_code
source venv/bin/activate
celery -A finflow worker --loglevel=info
```

### **2. Start Celery Beat (Periodic Tasks)**
```bash
cd /home/kouma/Desktop/Personal_Projects/Vibe_code
source venv/bin/activate
celery -A finflow beat --loglevel=info
```

### **3. Start Both Worker and Beat**
```bash
cd /home/kouma/Desktop/Personal_Projects/Vibe_code
source venv/bin/activate
celery -A finflow worker --beat --loglevel=info
```

### **4. Start Celery Flower (Monitoring)**
```bash
cd /home/kouma/Desktop/Personal_Projects/Vibe_code
source venv/bin/activate
pip install flower
celery -A finflow flower
```

### **5. Start with Specific Queues**
```bash
# Start worker for specific queues
celery -A finflow worker --loglevel=info --queues=analytics,maintenance

# Start worker for all queues
celery -A finflow worker --loglevel=info --queues=default,analytics,maintenance,monitoring
```

## 🔧 Task Examples

### **Manual Task Execution**
```python
# In Django shell
python manage.py shell

# Import tasks
from finflow.core.tasks import refresh_portfolio_analytics, test_task

# Execute tasks
result = refresh_portfolio_analytics.delay()
print(result.get())

# Test task
result = test_task.delay("Hello from manual execution!")
print(result.get())
```

### **Scheduled Task Management**
```python
# View scheduled tasks
from django_celery_beat.models import PeriodicTask
tasks = PeriodicTask.objects.all()
for task in tasks:
    print(f"{task.name}: {task.task} - {task.crontab}")

# Enable/disable tasks
task = PeriodicTask.objects.get(name='refresh-portfolio-analytics')
task.enabled = False
task.save()
```

## 📋 Task Details

### **1. Portfolio Analytics Task**
```python
@shared_task(bind=True, name='finflow.core.tasks.refresh_portfolio_analytics')
def refresh_portfolio_analytics(self):
    """
    Periodic task to refresh portfolio analytics every hour.
    """
    # Calculates portfolio performance metrics
    # Updates cached analytics data
    # Generates portfolio summaries
    # Prints "Analytics refreshed"
```

**Features:**
- Calculates total portfolios, investments, and transactions
- Generates per-user analytics
- Caches results for 1 hour
- Comprehensive error handling with retries

### **2. Log Cleanup Task**
```python
@shared_task(bind=True, name='finflow.core.tasks.cleanup_old_logs')
def cleanup_old_logs(self):
    """
    Periodic task to clean up old log files and temporary data.
    Runs daily at 2 AM.
    """
    # Removes log files older than 30 days
    # Cleans up old cache entries
    # Logs cleanup results
```

### **3. Health Check Task**
```python
@shared_task(bind=True, name='finflow.core.tasks.health_check')
def health_check(self):
    """
    Periodic health check task that runs every 60 seconds.
    """
    # Checks database connectivity
    # Verifies cache functionality
    # Monitors Redis connection
    # Returns health status
```

## 🔍 Monitoring & Debugging

### **Task Status Monitoring**
```bash
# Check active tasks
celery -A finflow inspect active

# Check scheduled tasks
celery -A finflow inspect scheduled

# Check registered tasks
celery -A finflow inspect registered

# Check worker stats
celery -A finflow inspect stats
```

### **Log Monitoring**
```bash
# Monitor Celery logs
tail -f logs/celery.log

# Monitor Django logs
tail -f logs/django.log

# Monitor specific task logs
grep "refresh_portfolio_analytics" logs/celery.log
```

### **Database Monitoring**
```python
# Check task results in Django admin
# Visit: http://localhost:8000/admin/django_celery_results/taskresult/

# Check periodic tasks
# Visit: http://localhost:8000/admin/django_celery_beat/periodictask/
```

## 🚀 Production Deployment

### **Systemd Service Files**

**`/etc/systemd/system/celery-worker.service`**
```ini
[Unit]
Description=Celery Worker Service
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
EnvironmentFile=/path/to/your/.env
WorkingDirectory=/path/to/your/project
ExecStart=/path/to/venv/bin/celery -A finflow worker --detach --loglevel=info --logfile=/var/log/celery/worker.log --pidfile=/var/run/celery/worker.pid
ExecStop=/bin/kill -s TERM $MAINPID
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
Restart=always
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

**`/etc/systemd/system/celery-beat.service`**
```ini
[Unit]
Description=Celery Beat Service
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
EnvironmentFile=/path/to/your/.env
WorkingDirectory=/path/to/your/project
ExecStart=/path/to/venv/bin/celery -A finflow beat --detach --loglevel=info --logfile=/var/log/celery/beat.log --pidfile=/var/run/celery/beat.pid
ExecStop=/bin/kill -s TERM $MAINPID
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
Restart=always
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

### **Docker Configuration**
```dockerfile
# Dockerfile for Celery worker
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["celery", "-A", "finflow", "worker", "--loglevel=info"]
```

## 🔧 Configuration Options

### **Environment Variables**
```bash
# Redis configuration
REDIS_URL=redis://localhost:6379/0

# Celery configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Worker configuration
CELERY_WORKER_CONCURRENCY=4
CELERY_WORKER_PREFETCH_MULTIPLIER=1
```

### **Custom Task Schedules**
```python
# In celery.py, modify beat_schedule
app.conf.beat_schedule = {
    'custom-task': {
        'task': 'finflow.core.tasks.custom_task',
        'schedule': crontab(minute=0, hour='*/2'),  # Every 2 hours
        'options': {'queue': 'custom'},
    },
}
```

## 🧪 Testing

### **Run Test Suite**
```bash
cd /home/kouma/Desktop/Personal_Projects/Vibe_code
source venv/bin/activate
python test_celery.py
```

### **Test Individual Tasks**
```bash
# Test analytics task
python manage.py shell
>>> from finflow.core.tasks import refresh_portfolio_analytics
>>> result = refresh_portfolio_analytics.delay()
>>> result.get()

# Test health check
>>> from finflow.core.tasks import health_check
>>> result = health_check.delay()
>>> result.get()
```

## 📈 Performance Optimization

### **Worker Optimization**
- **Concurrency**: Adjust based on CPU cores
- **Prefetch**: Set to 1 for memory-intensive tasks
- **Max Tasks**: Restart workers after 1000 tasks
- **Queues**: Separate queues for different task types

### **Redis Optimization**
- **Connection Pooling**: Configure connection limits
- **Memory Management**: Set appropriate memory limits
- **Persistence**: Configure RDB and AOF settings
- **Monitoring**: Use Redis monitoring tools

## 🎯 Success Metrics

- ✅ **Periodic Tasks**: Portfolio analytics refreshes every hour
- ✅ **Task Routing**: Proper queue management
- ✅ **Error Handling**: Comprehensive retry mechanisms
- ✅ **Monitoring**: Full task lifecycle tracking
- ✅ **Scalability**: Multiple worker support
- ✅ **Production Ready**: Systemd and Docker configurations

## 🔮 Future Enhancements

- **Task Chaining**: Complex workflow orchestration
- **Task Monitoring**: Real-time task monitoring dashboard
- **Auto-scaling**: Dynamic worker scaling based on queue size
- **Task Prioritization**: Priority-based task execution
- **Distributed Tasks**: Multi-server task distribution
- **Task Analytics**: Performance metrics and optimization

The Celery configuration is now complete and ready for production use with comprehensive periodic task management and monitoring capabilities!
