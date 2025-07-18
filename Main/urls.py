# urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views


urlpatterns = [
    # Authentication URLs
    path('auth/farmer/register/', views.FarmerRegistrationView.as_view(), name='farmer-register'),
    path('auth/horeca/register/', views.HorecaRegistrationView.as_view(), name='horeca-register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/profile/', views.UserProfileView.as_view(), name='profile'),
    path('auth/change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    
    # Categories URLs
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories/<int:category_id>/subcategories/', views.SubCategoryListView.as_view(), name='subcategory-list'),
    
    # Products URLs
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('products/featured/', views.FeaturedProductsView.as_view(), name='featured-products'),
    path('products/create/', views.ProductCreateView.as_view(), name='product-create'),
    path('products/<int:pk>/update/', views.ProductUpdateView.as_view(), name='product-update'),
    path('products/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product-delete'),
    path('my-products/', views.MyProductsView.as_view(), name='my-products'),
    
    # Favorites URLs
    path('favorites/', views.FavoriteListView.as_view(), name='favorite-list'),
    path('favorites/toggle/<int:product_id>/', views.FavoriteToggleView.as_view(), name='favorite-toggle'),
    
    # Contact URLs
    path('contact/', views.ContactUsView.as_view(), name='contact-us'),
    
    # Utility URLs
    path('dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),
    path('search/suggestions/', views.search_suggestions, name='search-suggestions'),
]