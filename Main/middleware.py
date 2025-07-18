# Main/middleware.py
import json
import logging
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.db import IntegrityError, OperationalError
from rest_framework.views import exception_handler
from rest_framework import status

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware:
    """Global error handling middleware"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """Handle uncaught exceptions"""
        
        # Database errors
        if isinstance(exception, OperationalError):
            logger.error(f"Database operational error: {str(exception)}")
            return JsonResponse({
                'success': False,
                'message': 'Database is currently unavailable. Please try again later.',
                'error': 'DATABASE_ERROR'
            }, status=500)
        
        if isinstance(exception, IntegrityError):
            logger.error(f"Database integrity error: {str(exception)}")
            return JsonResponse({
                'success': False,
                'message': 'Data integrity error. Please check your input.',
                'error': 'INTEGRITY_ERROR'
            }, status=400)
        
        # Validation errors
        if isinstance(exception, ValidationError):
            logger.error(f"Validation error: {str(exception)}")
            return JsonResponse({
                'success': False,
                'message': 'Invalid data provided.',
                'error': 'VALIDATION_ERROR'
            }, status=400)
        
        # Log unexpected errors
        logger.error(f"Unexpected error: {str(exception)}", exc_info=True)
        
        # Don't handle in debug mode
        from django.conf import settings
        if settings.DEBUG:
            return None
        
        # Generic error for production
        return JsonResponse({
            'success': False,
            'message': 'An unexpected error occurred. Please try again later.',
            'error': 'SERVER_ERROR'
        }, status=500)


def custom_exception_handler(exc, context):
    """Custom DRF exception handler"""
    response = exception_handler(exc, context)
    
    if response is not None:
        custom_response_data = {
            'success': False,
            'message': 'Request failed',
            'errors': response.data
        }
        
        # Handle different error types
        if response.status_code == 404:
            custom_response_data['message'] = 'Resource not found'
            custom_response_data['error'] = 'NOT_FOUND'
        elif response.status_code == 403:
            custom_response_data['message'] = 'Permission denied'
            custom_response_data['error'] = 'PERMISSION_DENIED'
        elif response.status_code == 401:
            custom_response_data['message'] = 'Authentication required'
            custom_response_data['error'] = 'AUTHENTICATION_REQUIRED'
        elif response.status_code == 400:
            custom_response_data['message'] = 'Invalid request data'
            custom_response_data['error'] = 'VALIDATION_ERROR'
        elif response.status_code >= 500:
            custom_response_data['message'] = 'Server error occurred'
            custom_response_data['error'] = 'SERVER_ERROR'
        
        response.data = custom_response_data
    
    return response