from django import forms
from django.contrib.auth.models import User
from .models import Equipment, Borrower, BorrowRecord, Category


class CategoryForm(forms.ModelForm):
    class Meta:
        model   = Category
        fields  = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Laptop, Camera...'
            }),
        }


class EquipmentForm(forms.ModelForm):
    class Meta:
        model   = Equipment
        fields  = ['name', 'category', 'description', 'serial_no', 'quantity', 'status', 'image']
        widgets = {
            'name'       : forms.TextInput(attrs={'class': 'form-control'}),
            'category'   : forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'serial_no'  : forms.TextInput(attrs={'class': 'form-control'}),
            'quantity'   : forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'status'     : forms.Select(attrs={'class': 'form-select'}),
            'image'      : forms.FileInput(attrs={'class': 'form-control'}),
        }


class BorrowerForm(forms.ModelForm):
    class Meta:
        model   = Borrower
        fields  = ['name', 'id_number', 'department', 'email', 'contact_no']
        widgets = {
            'name'      : forms.TextInput(attrs={'class': 'form-control'}),
            'id_number' : forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. BSIT, Admin Office, Faculty...'
            }),
            'email'     : forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_no': forms.TextInput(attrs={'class': 'form-control'}),
        }


class BorrowForm(forms.Form):
    category   = forms.ModelChoiceField(
        queryset    = Category.objects.all(),
        empty_label = '-- Select Category --',
        widget      = forms.Select(attrs={'class': 'form-select', 'id': 'id_category'}),
        label       = 'Category'
    )
    equipment  = forms.ModelChoiceField(
        queryset    = Equipment.objects.filter(status='available', quantity__gt=0),
        empty_label = '-- Select Equipment --',
        widget      = forms.Select(attrs={'class': 'form-select', 'id': 'id_equipment'}),
        label       = 'Equipment'
    )
    department = forms.CharField(
        widget = forms.TextInput(attrs={
            'class'      : 'form-control',
            'placeholder': 'e.g. BSIT, Admin Office, Faculty...'
        }),
        label  = 'Department / Office'
    )
    due_date   = forms.DateField(
        widget = forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label  = 'Return Date'
    )
    due_time   = forms.TimeField(
        widget = forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        label  = 'Return Time'
    )
    remarks    = forms.CharField(
        widget   = forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required = False,
        label    = 'Remarks'
    )


class HolyChildRegisterForm(forms.Form):
    full_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Juan Dela Cruz'
        }),
        label='Full Name'
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'yourname@holychild.edu.ph'
        }),
        label='Holy Child Email'
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'id': 'password1'}),
        label='Password'
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'id': 'password2'}),
        label='Confirm Password'
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email.endswith('@holychild.edu.ph'):
            raise forms.ValidationError('Only @holychild.edu.ph email addresses are allowed.')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned_data

    def save(self):
        email      = self.cleaned_data['email']
        password   = self.cleaned_data['password1']
        full_name  = self.cleaned_data['full_name']
        username   = email.split('@')[0]
        name_parts = full_name.strip().split(' ', 1)
        first_name = name_parts[0]
        last_name  = name_parts[1] if len(name_parts) > 1 else ''
        user = User.objects.create_user(
            username   = username,
            email      = email,
            password   = password,
            first_name = first_name,
            last_name  = last_name,
        )
        return user