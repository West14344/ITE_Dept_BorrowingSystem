from django.contrib import admin
from .models import Equipment, Borrower, BorrowRecord, Category, UserProfile, AdminLog, UserLog


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ['name', 'created_at']
    search_fields = ['name']


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display  = ['name', 'category', 'serial_no', 'quantity', 'status']
    list_filter   = ['status', 'category']
    search_fields = ['name', 'serial_no']


@admin.register(Borrower)
class BorrowerAdmin(admin.ModelAdmin):
    list_display  = ['name', 'id_number', 'department', 'email']
    search_fields = ['name', 'id_number']


@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display  = ['equipment', 'processed_by', 'date_borrowed', 'due_date', 'status']
    list_filter   = ['status']
    search_fields = ['equipment__name', 'processed_by__username']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_approved', 'is_disabled', 'created_at']
    list_filter  = ['is_approved', 'is_disabled']


@admin.register(AdminLog)
class AdminLogAdmin(admin.ModelAdmin):
    list_display  = ['admin', 'action', 'timestamp']
    search_fields = ['action']


@admin.register(UserLog)
class UserLogAdmin(admin.ModelAdmin):
    list_display  = ['user', 'action', 'timestamp']
    search_fields = ['action']