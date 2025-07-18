# serializers.py
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, Category, SubCategory, Product, ProductImage, ContactMessage, Favorite

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'password', 'password_confirm',
            'user_type', 'farm_name', 'farm_location', 'farm_size', 
            'business_name', 'business_type', 'business_address'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs
    
    def validate_user_type(self, value):
        if value not in ['farmer', 'horeca']:
            raise serializers.ValidationError("User type must be either 'farmer' or 'horeca'.")
        return value
    
    def create(self, validated_data):
        # Remove fields that need special handling
        password_confirm = validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        email = validated_data.pop('email')  # Remove email from validated_data
        
        # Now create user with email as parameter and remaining data
        user = User.objects.create(
            email=email,
            username=email,
            **validated_data  # This no longer contains email, password, or password_confirm
        )
        user.set_password(password)  # Set the password
        user.save()
        return user



class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials.')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include email and password.')
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'uid', 'first_name', 'last_name', 'email', 'phone', 'profile_picture',
            'user_type', 'is_verified', 'farm_name', 'farm_location', 'farm_size',
            'business_name', 'business_type', 'business_address', 'created_at'
        ]
        read_only_fields = ['uid', 'email', 'user_type', 'is_verified', 'created_at']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'image', 'is_active']


class SubCategorySerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = SubCategory
        fields = ['id', 'name', 'description', 'category', 'category_name', 'is_active']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_primary']


class ProductListSerializer(serializers.ModelSerializer):
    farmer_name = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True)
    primary_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'unit', 'quantity_available',
            'farmer_name', 'category_name', 'subcategory_name', 'location',
            'organic', 'is_featured', 'status', 'primary_image', 'created_at'
        ]
    
    def get_farmer_name(self, obj):
        return f"{obj.farmer.first_name} {obj.farmer.last_name}".strip() or obj.farmer.email
    
    def get_primary_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return self.context['request'].build_absolute_uri(primary_image.image.url)
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    farmer_name = serializers.SerializerMethodField()
    farmer_phone = serializers.CharField(source='farmer.phone', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'unit', 'quantity_available',
            'min_order_quantity', 'harvest_date', 'expiry_date', 'organic',
            'location', 'status', 'farmer_name', 'farmer_phone', 'category_name',
            'subcategory_name', 'images', 'is_favorited', 'created_at', 'updated_at'
        ]
    
    def get_farmer_name(self, obj):
        return f"{obj.farmer.first_name} {obj.farmer.last_name}".strip() or obj.farmer.email
    
    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user, product=obj).exists()
        return False


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'price', 'unit', 'quantity_available',
            'min_order_quantity', 'harvest_date', 'expiry_date', 'organic',
            'location', 'category', 'subcategory', 'images', 'uploaded_images'
        ]
    
    def create(self, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        product = Product.objects.create(**validated_data)
        
        for i, image in enumerate(uploaded_images):
            ProductImage.objects.create(
                product=product,
                image=image,
                is_primary=(i == 0)  # First image is primary
            )
        
        return product
    
    def update(self, instance, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # If new images are uploaded, add them
        if uploaded_images:
            for image in uploaded_images:
                ProductImage.objects.create(
                    product=instance,
                    image=image,
                    is_primary=False
                )
        
        return instance


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'phone', 'subject', 'message', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def create(self, validated_data):
        # If user is authenticated, associate the message with the user
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        return super().create(validated_data)


class FavoriteSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    
    class Meta:
        model = Favorite
        fields = ['id', 'product', 'created_at']
        read_only_fields = ['id', 'created_at']


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match.")
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value