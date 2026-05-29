from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Category(models.Model):
    name       = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'


class Equipment(models.Model):
    STATUS_CHOICES = [
        ('available',   'Available'),
        ('borrowed',    'Borrowed'),
        ('maintenance', 'Under Maintenance'),
    ]

    name        = models.CharField(max_length=100)
    category    = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True)
    serial_no   = models.CharField(max_length=100, unique=True)
    quantity    = models.PositiveIntegerField(default=1)
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    image       = models.ImageField(upload_to='equipment/', blank=True, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.serial_no})"

    @property
    def is_available(self):
        return self.quantity > 0 and self.status == 'available'

    class Meta:
        ordering = ['name']


class Borrower(models.Model):
    name       = models.CharField(max_length=100)
    id_number  = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=100, default='N/A')
    email      = models.EmailField(blank=True)
    contact_no = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.name} ({self.id_number})"

    class Meta:
        ordering = ['name']


class BorrowRecord(models.Model):
    STATUS_CHOICES = [
        ('borrowed', 'Borrowed'),
        ('returned', 'Returned'),
        ('late',     'Returned Late'),
        ('overdue',  'Overdue'),
        ('lost',     'Lost'),
    ]

    equipment     = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    borrower      = models.ForeignKey(Borrower, on_delete=models.CASCADE, null=True, blank=True)
    processed_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    department    = models.CharField(max_length=100, blank=True, default='')
    date_borrowed = models.DateTimeField(auto_now_add=True)
    due_date      = models.DateField()
    due_time      = models.TimeField(null=True, blank=True)
    date_returned = models.DateTimeField(null=True, blank=True)
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default='borrowed')
    remarks       = models.TextField(blank=True)

    def __str__(self):
        return f"{self.processed_by} → {self.equipment} ({self.status})"

    class Meta:
        ordering = ['-date_borrowed']


class UserProfile(models.Model):
    user        = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_approved = models.BooleanField(default=False)
    is_disabled = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({'Approved' if self.is_approved else 'Pending'})"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance, is_approved=instance.is_superuser)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()


class AdminLog(models.Model):
    admin     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action    = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.admin.username} — {self.action}"

    class Meta:
        ordering = ['-timestamp']


class UserLog(models.Model):
    user      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action    = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} — {self.action}"

    class Meta:
        ordering = ['-timestamp']