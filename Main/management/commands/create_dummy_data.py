# Create this file at: Main/management/commands/create_dummy_data.py

import random
from datetime import date, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from Main.models import Category, SubCategory, Product, ProductImage, ContactMessage, Favorite

User = get_user_model()

class Command(BaseCommand):
    help = 'Create dummy data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=10,
            help='Number of users to create (default: 10)'
        )
        parser.add_argument(
            '--products',
            type=int,
            default=50,
            help='Number of products to create (default: 50)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating dummy data...'))
        
        # Create Categories
        self.create_categories()
        
        # Create Users
        self.create_users(options['users'])
        
        # Create Products
        self.create_products(options['products'])
        
        # Create Contact Messages
        self.create_contact_messages()
        
        # Create Favorites
        self.create_favorites()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created dummy data!')
        )

    def create_categories(self):
        """Create categories and subcategories"""
        categories_data = [
            {
                'name': 'Vegetables',
                'description': 'Fresh vegetables from farms',
                'subcategories': ['Leafy Greens', 'Root Vegetables', 'Tomatoes', 'Onions', 'Potatoes']
            },
            {
                'name': 'Fruits',
                'description': 'Fresh seasonal fruits',
                'subcategories': ['Citrus Fruits', 'Tropical Fruits', 'Berries', 'Stone Fruits', 'Apples']
            },
            {
                'name': 'Grains',
                'description': 'Various grains and cereals',
                'subcategories': ['Rice', 'Wheat', 'Barley', 'Oats', 'Quinoa']
            },
            {
                'name': 'Pulses',
                'description': 'Lentils, beans and legumes',
                'subcategories': ['Lentils', 'Chickpeas', 'Black Beans', 'Kidney Beans', 'Peas']
            },
            {
                'name': 'Herbs & Spices',
                'description': 'Fresh herbs and aromatic spices',
                'subcategories': ['Fresh Herbs', 'Dried Spices', 'Garlic & Ginger', 'Chilies', 'Medicinal Herbs']
            },
            {
                'name': 'Dairy',
                'description': 'Fresh dairy products',
                'subcategories': ['Milk', 'Cheese', 'Yogurt', 'Butter', 'Ghee']
            }
        ]
        
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            
            if created:
                self.stdout.write(f'Created category: {category.name}')
            
            # Create subcategories
            for subcat_name in cat_data['subcategories']:
                subcategory, created = SubCategory.objects.get_or_create(
                    category=category,
                    name=subcat_name,
                    defaults={'description': f'{subcat_name} in {category.name}'}
                )
                
                if created:
                    self.stdout.write(f'  Created subcategory: {subcategory.name}')

    def create_users(self, count):
        """Create farmer and HoReCa users"""
        
        # Create farmers
        farmer_names = [
            ('Ravi', 'Kumar'), ('Sunita', 'Sharma'), ('Mohan', 'Singh'),
            ('Priya', 'Patel'), ('Rajesh', 'Gupta'), ('Anita', 'Verma'),
            ('Suresh', 'Yadav'), ('Geeta', 'Joshi'), ('Amit', 'Pandey'),
            ('Kavita', 'Agarwal')
        ]
        
        farm_locations = [
            'Punjab', 'Haryana', 'Uttar Pradesh', 'Bihar', 'West Bengal',
            'Maharashtra', 'Karnataka', 'Tamil Nadu', 'Andhra Pradesh', 'Gujarat'
        ]
        
        for i in range(count // 2):
            if i < len(farmer_names):
                first_name, last_name = farmer_names[i]
            else:
                first_name, last_name = f'Farmer{i}', f'User{i}'
            
            email = f'farmer{i+1}@agrozor.com'
            
            farmer, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone': f'+91{random.randint(7000000000, 9999999999)}',
                    'user_type': 'farmer',
                    'is_verified': True,
                    'farm_name': f'{first_name} {last_name} Farm',
                    'farm_location': random.choice(farm_locations),
                    'farm_size': Decimal(str(random.uniform(1.0, 50.0)))
                }
            )
            
            if created:
                farmer.set_password('farmer123')
                farmer.save()
                self.stdout.write(f'Created farmer: {farmer.email}')
        
        # Create HoReCa users
        business_names = [
            'Green Restaurant', 'Spice Garden Hotel', 'Farm Fresh Cafe',
            'Organic Bistro', 'Fresh Kitchen', 'Garden Restaurant',
            'Harvest Hotel', 'Nature\'s Plate', 'Pure Food Cafe', 'Earth Kitchen'
        ]
        
        business_types = ['restaurant', 'hotel', 'cafe', 'catering', 'bakery']
        business_locations = [
            'Delhi', 'Mumbai', 'Bangalore', 'Chennai', 'Kolkata',
            'Pune', 'Hyderabad', 'Ahmedabad', 'Jaipur', 'Lucknow'
        ]
        
        for i in range(count // 2):
            email = f'horeca{i+1}@agrozor.com'
            
            horeca, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': f'Manager{i+1}',
                    'last_name': 'Admin',
                    'phone': f'+91{random.randint(7000000000, 9999999999)}',
                    'user_type': 'horeca',
                    'is_verified': True,
                    'business_name': business_names[i % len(business_names)],
                    'business_type': random.choice(business_types),
                    'business_address': f'{random.randint(1, 999)} Main Street, {random.choice(business_locations)}'
                }
            )
            
            if created:
                horeca.set_password('horeca123')
                horeca.save()
                self.stdout.write(f'Created HoReCa: {horeca.email}')

    def create_products(self, count):
        """Create products"""
        farmers = User.objects.filter(user_type='farmer')
        categories = Category.objects.all()
        
        if not farmers.exists() or not categories.exists():
            self.stdout.write(
                self.style.ERROR('No farmers or categories found. Create them first.')
            )
            return
        
        product_names = [
            # Vegetables
            'Organic Tomatoes', 'Fresh Spinach', 'Green Lettuce', 'Red Onions',
            'White Onions', 'Potatoes', 'Sweet Potatoes', 'Carrots', 'Beetroot',
            'Cabbage', 'Cauliflower', 'Broccoli', 'Bell Peppers', 'Green Chilies',
            'Okra', 'Eggplant', 'Cucumber', 'Zucchini', 'Radish', 'Turnip',
            
            # Fruits
            'Fresh Apples', 'Ripe Bananas', 'Juicy Oranges', 'Sweet Mangoes',
            'Fresh Grapes', 'Strawberries', 'Blueberries', 'Pomegranates',
            'Pineapples', 'Papayas', 'Guavas', 'Lemons', 'Limes', 'Kiwis',
            
            # Grains
            'Basmati Rice', 'Brown Rice', 'Wheat Flour', 'Whole Wheat',
            'Oats', 'Barley', 'Quinoa', 'Millets',
            
            # Pulses
            'Red Lentils', 'Green Lentils', 'Chickpeas', 'Black Beans',
            'Kidney Beans', 'Green Peas', 'Black Eyed Peas',
            
            # Herbs & Spices
            'Fresh Coriander', 'Fresh Mint', 'Basil', 'Turmeric', 'Ginger',
            'Garlic', 'Red Chili Powder', 'Cumin Seeds', 'Cardamom'
        ]
        
        units = ['kg', 'g', 'piece', 'dozen', 'bunch', 'box', 'bag']
        locations = [
            'Punjab', 'Haryana', 'UP', 'Bihar', 'West Bengal',
            'Maharashtra', 'Karnataka', 'Tamil Nadu', 'Gujarat', 'Rajasthan'
        ]
        
        for i in range(count):
            farmer = random.choice(farmers)
            category = random.choice(categories)
            subcategories = category.subcategories.all()
            subcategory = random.choice(subcategories) if subcategories.exists() else None
            
            product_name = random.choice(product_names)
            
            # Generate realistic prices based on product type
            if 'Organic' in product_name:
                price = Decimal(str(random.uniform(80, 200)))
            elif category.name == 'Fruits':
                price = Decimal(str(random.uniform(50, 150)))
            elif category.name == 'Vegetables':
                price = Decimal(str(random.uniform(20, 100)))
            elif category.name == 'Grains':
                price = Decimal(str(random.uniform(30, 80)))
            else:
                price = Decimal(str(random.uniform(40, 120)))
            
            product = Product.objects.create(
                farmer=farmer,
                category=category,
                subcategory=subcategory,
                name=f"{product_name} - {farmer.farm_location}",
                description=f"Fresh {product_name.lower()} from {farmer.farm_name}. High quality, farm-fresh produce delivered directly from our fields.",
                price=price,
                unit=random.choice(units),
                quantity_available=Decimal(str(random.uniform(10, 500))),
                min_order_quantity=Decimal(str(random.uniform(1, 10))),
                harvest_date=date.today() - timedelta(days=random.randint(1, 7)),
                expiry_date=date.today() + timedelta(days=random.randint(3, 30)),
                organic=random.choice([True, False]),
                location=random.choice(locations),
                status=random.choice(['available', 'available', 'available', 'out_of_stock']),
                is_featured=random.choice([True, False, False, False])  # 25% chance of being featured
            )
            
            if i % 10 == 0:
                self.stdout.write(f'Created {i} products...')
        
        self.stdout.write(f'Created {count} products')

    def create_contact_messages(self):
        """Create contact messages"""
        subjects = ['general', 'support', 'partnership', 'complaint', 'other']
        names = ['John Doe', 'Jane Smith', 'Raj Patel', 'Priya Singh', 'Mike Johnson']
        
        messages = [
            "I'm interested in partnering with your platform.",
            "I have some technical issues with my account.",
            "Great platform! Keep up the good work.",
            "I need help with placing an order.",
            "How can I become a verified farmer on your platform?",
            "I'm facing login issues. Please help.",
            "The quality of products is excellent!",
            "I want to expand my business through your platform."
        ]
        
        for i in range(15):
            ContactMessage.objects.create(
                name=random.choice(names),
                email=f'contact{i}@example.com',
                phone=f'+91{random.randint(7000000000, 9999999999)}',
                subject=random.choice(subjects),
                message=random.choice(messages),
                user=random.choice(User.objects.all()) if random.choice([True, False]) else None
            )
        
        self.stdout.write('Created contact messages')

    def create_favorites(self):
        """Create favorite relationships"""
        horeca_users = User.objects.filter(user_type='horeca')
        products = Product.objects.all()
        
        if not horeca_users.exists() or not products.exists():
            return
        
        # Create some random favorites
        for horeca in horeca_users:
            # Each HoReCa user favorites 3-8 products
            favorite_products = random.sample(
                list(products), 
                min(random.randint(3, 8), products.count())
            )
            
            for product in favorite_products:
                Favorite.objects.get_or_create(
                    user=horeca,
                    product=product
                )
        
        self.stdout.write('Created favorites')
