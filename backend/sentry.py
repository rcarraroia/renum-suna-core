import sentry_sdk
from sentry_sdk.integrations.dramatiq import DramatiqIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.redis import RedisIntegration
# SQLAlchemy integration removed - not installed
from sentry_sdk.integrations.logging import LoggingIntegration
import os
import logging

def before_send(event, hint):
    """
    Filter function to modify or drop events before sending to Sentry
    """
    # Skip health check endpoints
    if event.get('request', {}).get('url', '').endswith('/health'):
        return None
    
    # Skip certain log levels in development
    if os.getenv('ENVIRONMENT', 'development') == 'development':
        if event.get('level') == 'info':
            return None
    
    # Add custom tags
    event.setdefault('tags', {})
    event['tags']['component'] = 'suna-backend'
    
    return event

def get_release_version():
    """
    Get release version from environment or git
    """
    # Try environment variable first
    release = os.getenv('RELEASE_VERSION')
    if release:
        return release
    
    # Try to get from git
    try:
        import subprocess
        result = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    
    return 'unknown'

# Initialize Sentry
sentry_dsn = os.getenv("SENTRY_DSN", None)
environment = os.getenv("ENVIRONMENT", "development")

if sentry_dsn:
    # Configure logging integration
    logging_integration = LoggingIntegration(
        level=logging.INFO,        # Capture info and above as breadcrumbs
        event_level=logging.ERROR  # Send errors as events
    )
    
    # Initialize Sentry with enhanced configuration
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=environment,
        release=get_release_version(),
        integrations=[
            DramatiqIntegration(),
            FastApiIntegration(auto_enabling_integrations=False),
            RedisIntegration(),
            # SqlalchemyIntegration(),  # Not installed
            logging_integration,
        ],
        traces_sample_rate=0.1 if environment == 'production' else 0.0,
        profiles_sample_rate=0.1 if environment == 'production' else 0.0,
        send_default_pii=False,  # Changed to False for better privacy
        before_send=before_send,
        max_breadcrumbs=50,
        attach_stacktrace=True,
        _experiments={
            "enable_logs": True,
        },
    )
    
    # Set global tags
    sentry_sdk.set_tag("service", "suna-backend")
    sentry_sdk.set_tag("environment", environment)
    
    print(f"✅ Sentry initialized for environment: {environment}")
else:
    print("⚠️  Sentry DSN not configured - error tracking disabled")

sentry = sentry_sdk
