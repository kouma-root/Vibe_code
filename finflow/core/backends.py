import logging
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone

logger = logging.getLogger(__name__)

User = get_user_model()


class UsernameOrEmailBackend(ModelBackend):
    """
    Custom authentication backend that allows users to authenticate
    using either their username or email address.
    
    This backend also logs failed authentication attempts for security monitoring.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate a user using username or email.
        
        Args:
            request: The HTTP request object
            username: Username or email address
            password: User password
            **kwargs: Additional keyword arguments
            
        Returns:
            User object if authentication successful, None otherwise
        """
        if username is None or password is None:
            return None
            
        try:
            # Try to find user by username or email
            user = User.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )
            
            # Check if user account is active
            if not user.is_active:
                self._log_failed_attempt(
                    username=username,
                    reason="Account is inactive",
                    request=request
                )
                return None
            
            # Verify password
            if user.check_password(password):
                # Log successful authentication
                logger.info(
                    f"Successful authentication for user: {user.username} "
                    f"(IP: {self._get_client_ip(request)})"
                )
                return user
            else:
                # Log failed password attempt
                self._log_failed_attempt(
                    username=username,
                    reason="Invalid password",
                    request=request,
                    user_found=True
                )
                return None
                
        except User.DoesNotExist:
            # Log failed attempt for non-existent user
            self._log_failed_attempt(
                username=username,
                reason="User not found",
                request=request,
                user_found=False
            )
            return None
        except User.MultipleObjectsReturned:
            # This shouldn't happen with proper database constraints
            # but we handle it gracefully
            logger.error(
                f"Multiple users found for username/email: {username} "
                f"(IP: {self._get_client_ip(request)})"
            )
            return None
        except Exception as e:
            # Log any unexpected errors
            logger.error(
                f"Authentication error for username: {username} "
                f"(IP: {self._get_client_ip(request)}): {str(e)}"
            )
            return None
    
    def get_user(self, user_id):
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User object if found and active, None otherwise
        """
        try:
            user = User.objects.get(pk=user_id)
            return user if user.is_active else None
        except User.DoesNotExist:
            return None
    
    def _log_failed_attempt(self, username, reason, request=None, user_found=True):
        """
        Log failed authentication attempts for security monitoring.
        
        Args:
            username: Username or email that was attempted
            reason: Reason for failure
            request: HTTP request object
            user_found: Whether a user was found with this username/email
        """
        client_ip = self._get_client_ip(request)
        user_agent = self._get_user_agent(request)
        
        # Log with appropriate level based on severity
        if user_found:
            # More serious - someone tried to access an existing account
            logger.warning(
                f"Failed authentication attempt - {reason} for user: {username} "
                f"(IP: {client_ip}, User-Agent: {user_agent})"
            )
        else:
            # Less serious - someone tried a non-existent username/email
            logger.info(
                f"Failed authentication attempt - {reason} for username/email: {username} "
                f"(IP: {client_ip}, User-Agent: {user_agent})"
            )
    
    def _get_client_ip(self, request):
        """
        Get the client IP address from the request.
        
        Args:
            request: HTTP request object
            
        Returns:
            Client IP address as string
        """
        if not request:
            return "Unknown"
            
        # Check for forwarded IP first (in case of proxy/load balancer)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Take the first IP in the chain
            return x_forwarded_for.split(',')[0].strip()
        
        # Fall back to remote address
        return request.META.get('REMOTE_ADDR', 'Unknown')
    
    def _get_user_agent(self, request):
        """
        Get the user agent from the request.
        
        Args:
            request: HTTP request object
            
        Returns:
            User agent string
        """
        if not request:
            return "Unknown"
            
        return request.META.get('HTTP_USER_AGENT', 'Unknown')[:200]  # Limit length
