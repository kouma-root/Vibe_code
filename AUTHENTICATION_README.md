# Custom Authentication Backend Implementation

This document explains the custom authentication backend implementation that allows users to authenticate using either their username or email address, with comprehensive logging of failed attempts.

## Features

- **Dual Authentication**: Users can login with either username or email
- **Security Logging**: All failed authentication attempts are logged with IP address and user agent
- **Account Status Validation**: Checks for active user accounts
- **Error Handling**: Comprehensive error handling and logging
- **API and Form Support**: Works with both REST API and traditional form-based authentication

## Files Created/Modified

### 1. `finflow/core/backends.py` (NEW)
Custom authentication backend that implements username/email authentication with logging.

### 2. `finflow/settings.py` (MODIFIED)
- Added `AUTHENTICATION_BACKENDS` configuration
- Added comprehensive logging configuration

### 3. `finflow/core/views.py` (MODIFIED)
- Added API authentication endpoints
- Added traditional Django authentication views
- Demonstrates usage of the custom backend

### 4. `finflow/core/urls.py` (MODIFIED)
- Added authentication URL patterns

### 5. Templates (NEW)
- `templates/core/login.html` - Login form template
- `templates/core/dashboard.html` - Protected dashboard template

## Configuration

### Authentication Backends
```python
AUTHENTICATION_BACKENDS = [
    'finflow.core.backends.UsernameOrEmailBackend',  # Custom backend
    'django.contrib.auth.backends.ModelBackend',     # Fallback
]
```

### Logging Configuration
The system logs authentication events to:
- `logs/auth.log` - Authentication-specific logs
- `logs/django.log` - General Django logs
- Console output for development

## Usage Examples

### 1. API Authentication

#### Login with Username
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "password": "password123"
  }'
```

#### Login with Email
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john@example.com",
    "password": "password123"
  }'
```

#### Successful Response
```json
{
  "success": true,
  "message": "Authentication successful",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "risk_tolerance": "moderate",
    "investment_style": "balanced",
    "is_active": true,
    "date_joined": "2024-01-01T00:00:00Z"
  },
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
  "token_created": false
}
```

#### Failed Authentication Response
```json
{
  "error": "Invalid credentials"
}
```

### 2. Traditional Django Views

#### Login Form
Visit `/login/` to access the login form that uses the custom authentication backend.

#### Dashboard
Visit `/dashboard/` (requires authentication) to see the protected dashboard.

### 3. Programmatic Usage

```python
from django.contrib.auth import authenticate

# Authenticate with username
user = authenticate(request=request, username='johndoe', password='password123')

# Authenticate with email
user = authenticate(request=request, username='john@example.com', password='password123')

if user is not None:
    if user.is_active:
        login(request, user)
        # User is authenticated
    else:
        # Account is inactive
        pass
else:
    # Invalid credentials
    pass
```

## Security Features

### 1. Failed Attempt Logging
All failed authentication attempts are logged with:
- Username/email attempted
- Reason for failure (user not found, invalid password, inactive account)
- Client IP address
- User agent string
- Timestamp

### 2. Log Levels
- **INFO**: Non-existent username/email attempts
- **WARNING**: Failed attempts for existing accounts
- **ERROR**: System errors during authentication

### 3. IP Address Detection
The backend properly handles:
- Direct connections (REMOTE_ADDR)
- Proxy/load balancer connections (HTTP_X_FORWARDED_FOR)

## API Endpoints

| Endpoint | Method | Description | Authentication Required |
|----------|--------|-------------|------------------------|
| `/api/auth/login/` | POST | User authentication | No |
| `/api/auth/logout/` | POST | User logout | Yes |
| `/api/auth/profile/` | GET | Get user profile | Yes |
| `/login/` | GET/POST | Login form | No |
| `/logout/` | POST | Logout | Yes |
| `/dashboard/` | GET | Protected dashboard | Yes |

## Testing the Implementation

### 1. Create a Test User
```bash
python manage.py shell
```

```python
from finflow.core.models import User

# Create a test user
user = User.objects.create_user(
    username='testuser',
    email='test@example.com',
    password='testpass123',
    first_name='Test',
    last_name='User'
)
```

### 2. Test Authentication
```bash
# Test with username
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'

# Test with email
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "test@example.com", "password": "testpass123"}'

# Test with invalid credentials
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "wrongpassword"}'
```

### 3. Check Logs
```bash
# View authentication logs
tail -f logs/auth.log

# View general Django logs
tail -f logs/django.log
```

## Customization

### Adding More Authentication Methods
You can extend the backend to support additional authentication methods:

```python
def authenticate(self, request, username=None, password=None, **kwargs):
    # Add phone number authentication
    phone = kwargs.get('phone')
    if phone:
        user = User.objects.get(phone=phone)
        # ... authentication logic
```

### Custom Logging
Modify the `_log_failed_attempt` method to add custom logging logic:

```python
def _log_failed_attempt(self, username, reason, request=None, user_found=True):
    # Add custom logging logic
    # Send alerts, update database, etc.
    pass
```

## Security Considerations

1. **Rate Limiting**: Consider implementing rate limiting for authentication attempts
2. **Account Lockout**: Implement account lockout after multiple failed attempts
3. **Two-Factor Authentication**: Add 2FA support for enhanced security
4. **Audit Trail**: Consider storing authentication events in the database
5. **HTTPS**: Always use HTTPS in production environments

## Troubleshooting

### Common Issues

1. **Logs Directory Not Found**
   ```bash
   mkdir -p logs
   ```

2. **Permission Errors**
   ```bash
   chmod 755 logs/
   ```

3. **Authentication Not Working**
   - Check `AUTHENTICATION_BACKENDS` in settings.py
   - Verify the backend path is correct
   - Check Django logs for errors

4. **Token Authentication Issues**
   - Ensure `rest_framework.authtoken` is in `INSTALLED_APPS`
   - Run migrations: `python manage.py migrate`

## Production Deployment

1. **Environment Variables**: Use environment variables for sensitive settings
2. **Log Rotation**: Implement log rotation for production
3. **Monitoring**: Set up monitoring for authentication events
4. **Backup**: Regular backup of authentication logs
5. **Security Headers**: Implement proper security headers

This implementation provides a robust, secure, and flexible authentication system that can be easily extended and customized for your specific needs.
