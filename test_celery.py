#!/usr/bin/env python3
"""
Test script for Celery configuration and tasks.
This script tests the Celery setup and runs various tasks.
"""

import os
import sys
import time
import django

# Add the project directory to Python path
sys.path.append('/home/kouma/Desktop/Personal_Projects/Vibe_code')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finflow.settings')
django.setup()

from finflow.core.tasks import (
    refresh_portfolio_analytics,
    cleanup_old_logs,
    health_check,
    test_task,
    long_running_task,
    generate_portfolio_report
)
from finflow.celery import app


def test_celery_connection():
    """Test Celery broker connection."""
    print("Testing Celery broker connection...")
    
    try:
        # Test broker connection
        inspect = app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            print("✓ Celery broker connection successful")
            print(f"  Active workers: {len(stats)}")
            for worker, worker_stats in stats.items():
                print(f"    - {worker}: {worker_stats.get('total', 0)} tasks processed")
        else:
            print("⚠ No active workers found (this is normal if no workers are running)")
            print("  Broker connection appears to be working")
        
        return True
        
    except Exception as e:
        print(f"✗ Celery broker connection failed: {e}")
        return False


def test_task_execution():
    """Test basic task execution."""
    print("\nTesting basic task execution...")
    
    try:
        # Test simple task
        result = test_task.delay("Hello from test script!")
        print(f"✓ Test task submitted: {result.id}")
        
        # Wait for result
        print("  Waiting for task completion...")
        task_result = result.get(timeout=10)
        print(f"✓ Task completed: {task_result}")
        
        return True
        
    except Exception as e:
        print(f"✗ Task execution failed: {e}")
        return False


def test_analytics_task():
    """Test the portfolio analytics task."""
    print("\nTesting portfolio analytics task...")
    
    try:
        # Run analytics task
        result = refresh_portfolio_analytics.delay()
        print(f"✓ Analytics task submitted: {result.id}")
        
        # Wait for result
        print("  Waiting for analytics task completion...")
        task_result = result.get(timeout=30)
        print(f"✓ Analytics task completed:")
        print(f"    Status: {task_result.get('status')}")
        print(f"    Message: {task_result.get('message')}")
        print(f"    Task ID: {task_result.get('task_id')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Analytics task failed: {e}")
        return False


def test_health_check():
    """Test the health check task."""
    print("\nTesting health check task...")
    
    try:
        # Run health check task
        result = health_check.delay()
        print(f"✓ Health check task submitted: {result.id}")
        
        # Wait for result
        print("  Waiting for health check completion...")
        task_result = result.get(timeout=15)
        print(f"✓ Health check completed:")
        print(f"    Database status: {task_result.get('database', {}).get('status')}")
        print(f"    Cache status: {task_result.get('cache', {}).get('status')}")
        print(f"    Redis status: {task_result.get('redis', {}).get('status')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Health check task failed: {e}")
        return False


def test_long_running_task():
    """Test long running task with progress updates."""
    print("\nTesting long running task...")
    
    try:
        # Run long running task (5 seconds)
        result = long_running_task.delay(5)
        print(f"✓ Long running task submitted: {result.id}")
        
        # Monitor progress
        print("  Monitoring task progress...")
        while not result.ready():
            try:
                info = result.info
                if info and 'current' in info:
                    print(f"    Progress: {info['current']}/{info['total']} - {info.get('status', '')}")
                time.sleep(1)
            except:
                pass
        
        # Get final result
        task_result = result.get(timeout=10)
        print(f"✓ Long running task completed: {task_result.get('message')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Long running task failed: {e}")
        return False


def test_periodic_tasks():
    """Test periodic task configuration."""
    print("\nTesting periodic task configuration...")
    
    try:
        # Check beat schedule
        beat_schedule = app.conf.beat_schedule
        print(f"✓ Beat schedule configured with {len(beat_schedule)} tasks:")
        
        for task_name, task_config in beat_schedule.items():
            print(f"    - {task_name}: {task_config['task']}")
            print(f"      Schedule: {task_config['schedule']}")
            print(f"      Queue: {task_config['options'].get('queue', 'default')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Periodic task configuration failed: {e}")
        return False


def test_task_routes():
    """Test task routing configuration."""
    print("\nTesting task routing configuration...")
    
    try:
        # Check task routes
        task_routes = app.conf.task_routes
        print(f"✓ Task routes configured for {len(task_routes)} patterns:")
        
        for pattern, route in task_routes.items():
            print(f"    - {pattern}: {route}")
        
        return True
        
    except Exception as e:
        print(f"✗ Task routing configuration failed: {e}")
        return False


def main():
    """Main test function."""
    print("Celery Configuration Test Suite")
    print("=" * 50)
    
    tests = [
        ("Celery Connection", test_celery_connection),
        ("Task Execution", test_task_execution),
        ("Analytics Task", test_analytics_task),
        ("Health Check", test_health_check),
        ("Long Running Task", test_long_running_task),
        ("Periodic Tasks", test_periodic_tasks),
        ("Task Routes", test_task_routes),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Celery is properly configured.")
    else:
        print(f"\n⚠ {total - passed} tests failed. Check the configuration.")
    
    print("\n" + "=" * 50)
    print("Commands to run Celery:")
    print("=" * 50)
    print("\n1. Start Celery Worker:")
    print("   celery -A finflow worker --loglevel=info")
    print("\n2. Start Celery Beat (for periodic tasks):")
    print("   celery -A finflow beat --loglevel=info")
    print("\n3. Start Celery Flower (monitoring):")
    print("   celery -A finflow flower")
    print("\n4. Start all in one command:")
    print("   celery -A finflow worker --beat --loglevel=info")
    print("\n5. Test specific task:")
    print("   python manage.py shell")
    print("   >>> from finflow.core.tasks import refresh_portfolio_analytics")
    print("   >>> result = refresh_portfolio_analytics.delay()")
    print("   >>> result.get()")


if __name__ == '__main__':
    main()
