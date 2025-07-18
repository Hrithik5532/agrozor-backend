# views.py
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
import logging

from .models import User, Category, SubCategory, Product, ContactMessage, Favorite
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer,
    CategorySerializer, SubCategorySerializer, ProductListSerializer,
    ProductDetailSerializer, ProductCreateUpdateSerializer, ContactMessageSerializer,
    FavoriteSerializer, PasswordChangeSerializer
)
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes


logger = logging.getLogger(__name__)
class FarmerRegistrationView(APIView):
    """Registration endpoint for farmers"""
    @extend_schema(
        summary="Register a new farmer",
        description="Create a new farmer account with farm details",
        request=UserRegistrationSerializer,
        responses={
            201: {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "message": {"type": "string"},
                    "user": {"type": "object"},
                    "tokens": {
                        "type": "object",
                        "properties": {
                            "access": {"type": "string"},
                            "refresh": {"type": "string"}
                        }
                    }
                }
            },
            400: {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "message": {"type": "string"},
                    "errors": {"type": "object"}
                }
            }
        },
        examples=[
            OpenApiExample(
                "Farmer Registration Example",
                value={
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "farmer@example.com",
                    "phone": "+1234567890",
                    "password": "securepassword123",
                    "password_confirm": "securepassword123",
                    "farm_name": "Green Valley Farm",
                    "farm_location": "Delhi, India",
                    "farm_size": "10.5"
                },
                request_only=True
            )
        ],
        tags=['Authentication']
    )
    def post(self, request):
            print(f"DEBUG: Request data: {request.data}")
        
        # try:
            data = request.data.copy()
            data['user_type'] = 'farmer'
            
            print(f"DEBUG: Data with user_type: {data}")
            
            serializer = UserRegistrationSerializer(data=data)
            
            if serializer.is_valid():
                print("DEBUG: Serializer is valid")
                try:
                    with transaction.atomic():
                        user = serializer.save()
                        refresh = RefreshToken.for_user(user)
                        return Response({
                            'success': True,
                            'message': 'Farmer registered successfully',
                            'user': UserProfileSerializer(user).data,
                            'tokens': {
                                'refresh': str(refresh),
                                'access': str(refresh.access_token),
                            }
                        }, status=status.HTTP_201_CREATED)
                except Exception as save_error:
                    print(f"DEBUG: Error saving user: {str(save_error)}")
                    print(f"DEBUG: Error type: {type(save_error)}")
                    return Response({
                        'success': False,
                        'message': f'Registration failed: {str(save_error)}',
                        'error': 'SAVE_ERROR'
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                print(f"DEBUG: Serializer errors: {serializer.errors}")
                
                # Handle validation errors with user-friendly messages
                errors = {}
                for field, field_errors in serializer.errors.items():
                    if field == 'email':
                        if 'already exists' in str(field_errors).lower():
                            errors[field] = ['This email is already registered. Please try logging in instead.']
                        else:
                            errors[field] = ['Please enter a valid email address.']
                    elif field == 'phone':
                        if 'already exists' in str(field_errors).lower():
                            errors[field] = ['This phone number is already registered.']
                        else:
                            errors[field] = ['Please enter a valid phone number (e.g., +1234567890).']
                    elif field == 'password':
                        errors[field] = ['Password must be at least 8 characters long and secure.']
                    else:
                        errors[field] = field_errors
                
                return Response({
                    'success': False,
                    'message': 'Registration failed. Please check the errors below.',
                    'errors': errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
        # except Exception as e:
        #     print(f"DEBUG: Outer exception: {str(e)}")
        #     print(f"DEBUG: Exception type: {type(e)}")
        #     import traceback
        #     print(f"DEBUG: Full traceback: {traceback.format_exc()}")
            
        #     return Response({
        #         'success': False,
        #         'message': 'Registration failed due to a server error. Please try again later.',
        #         'error': 'SERVER_ERROR',
        #         'debug_error': str(e)  # Remove this in production
        #     }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HorecaRegistrationView(APIView):
    """Registration endpoint for HoReCa businesses"""
    
    def post(self, request):
        try:
            data = request.data.copy()
            data['user_type'] = 'horeca'
            
            serializer = UserRegistrationSerializer(data=data)
            if serializer.is_valid():
                with transaction.atomic():
                    user = serializer.save()
                    refresh = RefreshToken.for_user(user)
                    return Response({
                        'success': True,
                        'message': 'HoReCa registered successfully',
                        'user': UserProfileSerializer(user).data,
                        'tokens': {
                            'refresh': str(refresh),
                            'access': str(refresh.access_token),
                        }
                    }, status=status.HTTP_201_CREATED)
            
            # Handle validation errors with user-friendly messages
            errors = {}
            for field, field_errors in serializer.errors.items():
                if field == 'email':
                    if 'already exists' in str(field_errors).lower():
                        errors[field] = ['This email is already registered. Please try logging in instead.']
                    else:
                        errors[field] = ['Please enter a valid email address.']
                elif field == 'phone':
                    if 'already exists' in str(field_errors).lower():
                        errors[field] = ['This phone number is already registered.']
                    else:
                        errors[field] = ['Please enter a valid phone number (e.g., +1234567890).']
                elif field == 'business_name':
                    errors[field] = ['Business name is required for HoReCa registration.']
                else:
                    errors[field] = field_errors
            
            return Response({
                'success': False,
                'message': 'Registration failed. Please check the errors below.',
                'errors': errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except IntegrityError as e:
            logger.error(f"Database integrity error during HoReCa registration: {str(e)}")
            return Response({
                'success': False,
                'message': 'Registration failed. Email or phone number might already be in use.',
                'error': 'DUPLICATE_ENTRY'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error during HoReCa registration: {str(e)}")
            return Response({
                'success': False,
                'message': 'Registration failed due to a server error. Please try again later.',
                'error': 'SERVER_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LoginView(APIView):
    """Login endpoint for both farmers and HoReCa"""
    
    def post(self, request):
        try:
            serializer = UserLoginSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.validated_data['user']
                refresh = RefreshToken.for_user(user)
                return Response({
                    'success': True,
                    'message': 'Login successful',
                    'user': UserProfileSerializer(user).data,
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    }
                }, status=status.HTTP_200_OK)
            
            # Handle login errors with user-friendly messages
            return Response({
                'success': False,
                'message': 'Invalid email or password. Please check your credentials and try again.',
                'error': 'INVALID_CREDENTIALS',
                'errors': serializer.errors  # Include validation errors
            }, status=status.HTTP_401_UNAUTHORIZED)
            
        except Exception as e:
            logger.error(f"Unexpected error during login: {str(e)}")
            return Response({
                'success': False,
                'message': 'Login failed due to a server error. Please try again later.',
                'error': 'SERVER_ERROR'  # Changed from 'error': e
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LogoutView(APIView):
    """Logout endpoint"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            if not refresh_token:
                return Response({
                    'success': False,
                    'message': 'Refresh token is required for logout.',
                    'error': 'MISSING_TOKEN'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({
                'success': True,
                'message': 'Logout successful'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error during logout: {str(e)}")
            return Response({
                'success': True,
                'message': 'Logout completed successfully'
            }, status=status.HTTP_200_OK)  # Still return success for logout


class UserProfileView(APIView):
    """Get and update user profile"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            serializer = UserProfileSerializer(request.user)
            return Response({
                'success': True,
                'user': serializer.data
            })
        except Exception as e:
            logger.error(f"Error retrieving user profile: {str(e)}")
            return Response({
                'success': False,
                'message': 'Unable to retrieve profile information.',
                'error': 'PROFILE_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request):
        try:
            serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
            if serializer.is_valid():
                with transaction.atomic():
                    serializer.save()
                    return Response({
                        'success': True,
                        'message': 'Profile updated successfully',
                        'user': serializer.data
                    })
            
            return Response({
                'success': False,
                'message': 'Profile update failed. Please check the errors below.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            return Response({
                'success': False,
                'message': 'Profile update failed due to a server error.',
                'error': 'UPDATE_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChangePasswordView(APIView):
    """Change user password"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                with transaction.atomic():
                    user = request.user
                    user.set_password(serializer.validated_data['new_password'])
                    user.save()
                    return Response({
                        'success': True,
                        'message': 'Password changed successfully'
                    })
            
            return Response({
                'success': False,
                'message': 'Password change failed. Please check the errors below.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error changing password: {str(e)}")
            return Response({
                'success': False,
                'message': 'Password change failed due to a server error.',
                'error': 'PASSWORD_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CategoryListView(generics.ListAPIView):
    """List all categories"""
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'success': True,
                'categories': serializer.data
            })
        except Exception as e:
            logger.error(f"Error fetching categories: {str(e)}")
            return Response({
                'success': False,
                'message': 'Unable to fetch categories. Please try again later.',
                'error': 'FETCH_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SubCategoryListView(generics.ListAPIView):
    """List subcategories by category"""
    serializer_class = SubCategorySerializer
    
    def get_queryset(self):
        category_id = self.kwargs.get('category_id')
        return SubCategory.objects.filter(category_id=category_id, is_active=True)
    
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'success': True,
                'subcategories': serializer.data
            })
        except Exception as e:
            logger.error(f"Error fetching subcategories: {str(e)}")
            return Response({
                'success': False,
                'message': 'Unable to fetch subcategories. Please try again later.',
                'error': 'FETCH_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductListView(generics.ListAPIView):
    """List products with filtering and search"""
    serializer_class = ProductListSerializer
    
    def get_queryset(self):
        queryset = Product.objects.filter(status='available')
        
        # Filter by category
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Filter by subcategory
        subcategory_id = self.request.query_params.get('subcategory')
        if subcategory_id:
            queryset = queryset.filter(subcategory_id=subcategory_id)
        
        # Filter by location
        location = self.request.query_params.get('location')
        if location:
            queryset = queryset.filter(location__icontains=location)
        
        # Filter by organic
        organic = self.request.query_params.get('organic')
        if organic:
            queryset = queryset.filter(organic=organic.lower() == 'true')
        
        # Filter by farmer
        farmer_id = self.request.query_params.get('farmer')
        if farmer_id:
            queryset = queryset.filter(farmer_id=farmer_id)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(category__name__icontains=search)
            )
        
        # Sort
        sort_by = self.request.query_params.get('sort', '-created_at')
        if sort_by in ['price', '-price', 'name', '-name', 'created_at', '-created_at']:
            queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response({
                    'success': True,
                    'products': serializer.data
                })

            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'success': True,
                'products': serializer.data
            })
        except Exception as e:
            logger.error(f"Error fetching products: {str(e)}")
            return Response({
                'success': False,
                'message': 'Unable to fetch products. Please try again later.',
                'error': 'FETCH_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductDetailView(generics.RetrieveAPIView):
    """Get product details"""
    queryset = Product.objects.all()
    serializer_class = ProductDetailSerializer
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response({
                'success': True,
                'product': serializer.data
            })
        except Product.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Product not found.',
                'error': 'NOT_FOUND'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error fetching product details: {str(e)}")
            return Response({
                'success': False,
                'message': 'Unable to fetch product details.',
                'error': 'FETCH_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MyProductsView(generics.ListAPIView):
    """List products for authenticated farmer"""
    serializer_class = ProductListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if not self.request.user.is_farmer:
            return Product.objects.none()
        return Product.objects.filter(farmer=self.request.user)
    
    def list(self, request, *args, **kwargs):
        try:
            if not request.user.is_farmer:
                return Response({
                    'success': False,
                    'message': 'Only farmers can access this endpoint.',
                    'error': 'PERMISSION_DENIED'
                }, status=status.HTTP_403_FORBIDDEN)
            
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'success': True,
                'products': serializer.data
            })
        except Exception as e:
            logger.error(f"Error fetching farmer products: {str(e)}")
            return Response({
                'success': False,
                'message': 'Unable to fetch your products.',
                'error': 'FETCH_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductCreateView(generics.CreateAPIView):
    """Create new product (farmers only)"""
    serializer_class = ProductCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        try:
            if not request.user.is_farmer:
                return Response({
                    'success': False,
                    'message': 'Only farmers can create products.',
                    'error': 'PERMISSION_DENIED'
                }, status=status.HTTP_403_FORBIDDEN)
            
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                with transaction.atomic():
                    product = serializer.save(farmer=request.user)
                    return Response({
                        'success': True,
                        'message': 'Product created successfully',
                        'product': ProductDetailSerializer(product, context={'request': request}).data
                    }, status=status.HTTP_201_CREATED)
            
            return Response({
                'success': False,
                'message': 'Product creation failed. Please check the errors below.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error creating product: {str(e)}")
            return Response({
                'success': False,
                'message': 'Product creation failed due to a server error.',
                'error': 'CREATION_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductUpdateView(generics.UpdateAPIView):
    """Update product (farmers only)"""
    serializer_class = ProductCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Product.objects.filter(farmer=self.request.user)
    
    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            
            if serializer.is_valid():
                with transaction.atomic():
                    product = serializer.save()
                    return Response({
                        'success': True,
                        'message': 'Product updated successfully',
                        'product': ProductDetailSerializer(product, context={'request': request}).data
                    })
            
            return Response({
                'success': False,
                'message': 'Product update failed. Please check the errors below.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Product.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Product not found or you don\'t have permission to update it.',
                'error': 'NOT_FOUND'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error updating product: {str(e)}")
            return Response({
                'success': False,
                'message': 'Product update failed due to a server error.',
                'error': 'UPDATE_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductDeleteView(generics.DestroyAPIView):
    """Delete product (farmers only)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Product.objects.filter(farmer=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            with transaction.atomic():
                instance.delete()
                return Response({
                    'success': True,
                    'message': 'Product deleted successfully'
                }, status=status.HTTP_200_OK)
                
        except Product.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Product not found or you don\'t have permission to delete it.',
                'error': 'NOT_FOUND'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error deleting product: {str(e)}")
            return Response({
                'success': False,
                'message': 'Product deletion failed due to a server error.',
                'error': 'DELETE_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FeaturedProductsView(generics.ListAPIView):
    """List featured products"""
    serializer_class = ProductListSerializer
    queryset = Product.objects.filter(is_featured=True, status='available')
    
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'success': True,
                'products': serializer.data
            })
        except Exception as e:
            logger.error(f"Error fetching featured products: {str(e)}")
            return Response({
                'success': False,
                'message': 'Unable to fetch featured products.',
                'error': 'FETCH_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ContactUsView(APIView):
    """Contact us endpoint"""
    
    def post(self, request):
        try:
            serializer = ContactMessageSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                with transaction.atomic():
                    message = serializer.save()
                    return Response({
                        'success': True,
                        'message': 'Your message has been sent successfully. We will get back to you within 24 hours.',
                        'reference_id': message.id
                    }, status=status.HTTP_201_CREATED)
            
            return Response({
                'success': False,
                'message': 'Message sending failed. Please check the errors below.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error sending contact message: {str(e)}")
            return Response({
                'success': False,
                'message': 'Unable to send message due to a server error. Please try again later.',
                'error': 'CONTACT_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FavoriteToggleView(APIView):
    """Add/remove product from favorites"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, product_id):
        try:
            if not request.user.is_horeca:
                return Response({
                    'success': False,
                    'message': 'Only HoReCa users can manage favorites.',
                    'error': 'PERMISSION_DENIED'
                }, status=status.HTTP_403_FORBIDDEN)
            
            try:
                product = Product.objects.get(id=product_id, status='available')
            except Product.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Product not found or no longer available.',
                    'error': 'PRODUCT_NOT_FOUND'
                }, status=status.HTTP_404_NOT_FOUND)
            
            with transaction.atomic():
                favorite, created = Favorite.objects.get_or_create(
                    user=request.user,
                    product=product
                )
                
                if created:
                    return Response({
                        'success': True,
                        'message': 'Product added to favorites',
                        'action': 'added'
                    }, status=status.HTTP_201_CREATED)
                else:
                    favorite.delete()
                    return Response({
                        'success': True,
                        'message': 'Product removed from favorites',
                        'action': 'removed'
                    }, status=status.HTTP_200_OK)
                    
        except Exception as e:
            logger.error(f"Error toggling favorite: {str(e)}")
            return Response({
                'success': False,
                'message': 'Unable to update favorites. Please try again.',
                'error': 'FAVORITE_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FavoriteListView(generics.ListAPIView):
    """List user's favorite products"""
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)
    
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'success': True,
                'favorites': serializer.data
            })
        except Exception as e:
            logger.error(f"Error fetching favorites: {str(e)}")
            return Response({
                'success': False,
                'message': 'Unable to fetch favorites.',
                'error': 'FETCH_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_stats(request):
    """Dashboard statistics for farmers"""
    try:
        if not request.user.is_farmer:
            return Response({
                'success': False,
                'message': 'Only farmers can access dashboard statistics.',
                'error': 'PERMISSION_DENIED'
            }, status=status.HTTP_403_FORBIDDEN)
        
        products = Product.objects.filter(farmer=request.user)
        stats = {
            'total_products': products.count(),
            'available_products': products.filter(status='available').count(),
            'out_of_stock': products.filter(status='out_of_stock').count(),
            'featured_products': products.filter(is_featured=True).count(),
            'organic_products': products.filter(organic=True).count(),
        }
        
        return Response({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {str(e)}")
        return Response({
            'success': False,
            'message': 'Unable to fetch dashboard statistics.',
            'error': 'STATS_ERROR'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def search_suggestions(request):
    """Search suggestions for auto-complete"""
    try:
        query = request.GET.get('q', '')
        if len(query) < 2:
            return Response({
                'success': True,
                'suggestions': []
            })
        
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query),
            status='available'
        ).values_list('name', flat=True)[:10]
        
        categories = Category.objects.filter(
            name__icontains=query,
            is_active=True
        ).values_list('name', flat=True)[:5]
        
        suggestions = list(products) + list(categories)
        return Response({
            'success': True,
            'suggestions': suggestions[:10]
        })
        
    except Exception as e:
        logger.error(f"Error fetching search suggestions: {str(e)}")
        return Response({
            'success': False,
            'message': 'Unable to fetch search suggestions.',
            'error': 'SEARCH_ERROR'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)