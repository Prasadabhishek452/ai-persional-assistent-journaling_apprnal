from rest_framework.views import exception_handler
from rest_framework.exceptions import AuthenticationFailed, Throttled, NotAuthenticated
from rest_framework import status
from rest_framework.response import Response

def custom_exception_handler(exc, context):
    # Call the default exception handler to get the standard error response
    response = exception_handler(exc, context)

    if isinstance(exc, AuthenticationFailed):
        # Handle the InvalidToken exception
        response = Response(
            {
                'responsecode': status.HTTP_401_UNAUTHORIZED,
                'responsemessage': 'Given token not valid for any token type',
            },
            status=status.HTTP_401_UNAUTHORIZED
        )
        
    elif isinstance(exc, Throttled):
        # Handle the Throttled exception
        custom_response_data = {
            'message': 'Request limit exceeded',
            'availableIn': f"{exc.wait} seconds"
        }
        response = Response(custom_response_data, status=status.HTTP_429_TOO_MANY_REQUESTS)
        response['Retry-After'] = exc.wait

    elif isinstance(exc, NotAuthenticated):
        # Handle the NotAuthenticated exception
        response = Response(
            {
                'responsecode': status.HTTP_401_UNAUTHORIZED,
                'responsemessage': 'Authentication credentials were not provided.',
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    return response
