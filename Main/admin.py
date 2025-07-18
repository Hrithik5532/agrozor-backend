from django.contrib import admin
from .models import User, Category, SubCategory, Product, ProductImage, ContactMessage, Favorite
# Register your models here.

admin.site.register(User)
admin.site.register(Category)
admin.site.register(SubCategory)
admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(ContactMessage)
admin.site.register(Favorite)