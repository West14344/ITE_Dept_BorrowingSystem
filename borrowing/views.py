from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from datetime import timedelta
from .models import Equipment, Borrower, BorrowRecord, UserProfile, AdminLog, UserLog, Category
from .forms import EquipmentForm, BorrowerForm, BorrowForm, HolyChildRegisterForm, CategoryForm


def splash(request):
    return render(request, 'borrowing/splash.html')


def login_view(request):
    if request.method == 'POST':
        email    = request.POST.get('username')
        password = request.POST.get('password')
        try:
            user_obj = User.objects.get(email=email)
            user     = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None
        if user is not None:
            if not user.is_superuser:
                if not hasattr(user, 'profile') or not user.profile.is_approved:
                    return render(request, 'borrowing/login.html', {'pending': True})
                if user.profile.is_disabled:
                    return render(request, 'borrowing/login.html', {'disabled': True})
            auth_login(request, user)
            return render(request, 'borrowing/loading.html', {
                'action'      : 'login',
                'redirect_url': '/system/',
            })
        else:
            return render(request, 'borrowing/login.html', {'error': True})
    return render(request, 'borrowing/login.html')


@csrf_exempt
def logout_view(request):
    auth_logout(request)
    return render(request, 'borrowing/loading.html', {
        'action'      : 'logout',
        'redirect_url': '/login/',
    })


def register(request):
    form = HolyChildRegisterForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Account created! Please wait for admin approval before logging in.')
        return redirect('login')
    return render(request, 'borrowing/register.html', {'form': form})


@login_required
def dashboard(request):
    BorrowRecord.objects.filter(
        status='borrowed',
        due_date__lt=timezone.now().date()
    ).update(status='overdue')

    today = timezone.now().date()
    soon  = today + timedelta(days=3)

    if request.user.is_superuser:
        context = {
            'total_equipment' : Equipment.objects.count(),
            'available'       : Equipment.objects.filter(status='available').count(),
            'borrowed'        : Equipment.objects.filter(status='borrowed').count(),
            'maintenance'     : Equipment.objects.filter(status='maintenance').count(),
            'overdue'         : BorrowRecord.objects.filter(status='overdue').count(),
            'recent_records'  : BorrowRecord.objects.select_related('equipment', 'processed_by').all()[:10],
            'pending_users'   : UserProfile.objects.filter(is_approved=False).count(),
            'total_users'     : User.objects.filter(is_superuser=False).count(),
            'recent_logs'     : AdminLog.objects.all()[:5],
        }
    else:
        my_records     = BorrowRecord.objects.filter(processed_by=request.user).select_related('equipment')
        due_soon       = my_records.filter(status='borrowed', due_date__lte=soon, due_date__gte=today)
        due_soon_count = due_soon.count()
        context = {
            'my_records'     : my_records.order_by('-date_borrowed')[:10],
            'total_borrowed' : my_records.filter(status__in=['borrowed', 'overdue']).count(),
            'total_returned' : my_records.filter(status__in=['returned', 'late']).count(),
            'overdue'        : my_records.filter(status='overdue').count(),
            'due_soon'       : due_soon,
            'due_soon_count' : due_soon_count,
            'today'          : today,
        }
    return render(request, 'borrowing/dashboard.html', context)


def get_equipment_by_category(request):
    category_id = request.GET.get('category_id')
    if category_id:
        equipment = Equipment.objects.filter(
            category_id  = category_id,
            status       = 'available',
            quantity__gt = 0
        ).values('id', 'name', 'serial_no', 'quantity')
    else:
        equipment = Equipment.objects.filter(
            status       = 'available',
            quantity__gt = 0
        ).values('id', 'name', 'serial_no', 'quantity')
    return JsonResponse({'equipment': list(equipment)})


@staff_member_required
def category_list(request):
    categories = Category.objects.all()
    form       = CategoryForm(request.POST or None)
    if form.is_valid():
        form.save()
        AdminLog.objects.create(
            admin  = request.user,
            action = f'➕ Added category: {form.cleaned_data["name"]}'
        )
        messages.success(request, 'Category added.')
        return redirect('category_list')
    return render(request, 'borrowing/category_list.html', {'categories': categories, 'form': form})


@staff_member_required
def category_delete(request, pk):
    obj = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        AdminLog.objects.create(
            admin  = request.user,
            action = f'🗑️ Deleted category: {obj.name}'
        )
        obj.delete()
        messages.success(request, 'Category deleted.')
    return redirect('category_list')


@login_required
def equipment_list(request):
    query     = request.GET.get('q', '')
    equipment = Equipment.objects.filter(name__icontains=query) if query else Equipment.objects.all()
    return render(request, 'borrowing/equipment_list.html', {'equipment': equipment, 'query': query})


@login_required
def equipment_add(request):
    form = EquipmentForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        AdminLog.objects.create(
            admin  = request.user,
            action = f'➕ Added equipment: {form.cleaned_data["name"]}'
        )
        messages.success(request, 'Equipment added successfully.')
        return redirect('equipment_list')
    return render(request, 'borrowing/equipment_form.html', {'form': form, 'title': 'Add Equipment'})


@login_required
def equipment_edit(request, pk):
    obj  = get_object_or_404(Equipment, pk=pk)
    form = EquipmentForm(request.POST or None, request.FILES or None, instance=obj)
    if form.is_valid():
        form.save()
        AdminLog.objects.create(
            admin  = request.user,
            action = f'✏️ Updated equipment: {obj.name}'
        )
        messages.success(request, 'Equipment updated.')
        return redirect('equipment_list')
    return render(request, 'borrowing/equipment_form.html', {'form': form, 'title': 'Edit Equipment'})


@login_required
def equipment_delete(request, pk):
    obj = get_object_or_404(Equipment, pk=pk)
    if request.method == 'POST':
        AdminLog.objects.create(
            admin  = request.user,
            action = f'🗑️ Deleted equipment: {obj.name}'
        )
        obj.delete()
        messages.success(request, 'Equipment deleted.')
        return redirect('equipment_list')
    return render(request, 'borrowing/confirm_delete.html', {'obj': obj, 'type': 'Equipment'})


@login_required
def borrower_list(request):
    query   = request.GET.get('q', '')
    records = BorrowRecord.objects.select_related(
        'equipment', 'equipment__category', 'processed_by'
    ).filter(status__in=['borrowed', 'overdue'])

    if query:
        records = records.filter(equipment__category__name__icontains=query)

    return render(request, 'borrowing/borrower_list.html', {'records': records, 'query': query})


@login_required
def borrower_add(request):
    form = BorrowerForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Borrower added successfully.')
        return redirect('borrower_list')
    return render(request, 'borrowing/borrower_form.html', {'form': form, 'title': 'Add Borrower'})


@login_required
def borrower_edit(request, pk):
    obj  = get_object_or_404(Borrower, pk=pk)
    form = BorrowerForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'Borrower updated.')
        return redirect('borrower_list')
    return render(request, 'borrowing/borrower_form.html', {'form': form, 'title': 'Edit Borrower'})


@login_required
def borrower_delete(request, pk):
    obj = get_object_or_404(Borrower, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Borrower deleted.')
        return redirect('borrower_list')
    return render(request, 'borrowing/confirm_delete.html', {'obj': obj, 'type': 'Borrower'})


@login_required
def borrow_item(request):
    form = BorrowForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        equipment  = form.cleaned_data['equipment']
        department = form.cleaned_data['department']
        due_date   = form.cleaned_data['due_date']
        due_time   = form.cleaned_data['due_time']
        remarks    = form.cleaned_data['remarks']

        if equipment.quantity <= 0 or equipment.status != 'available':
            categories = Category.objects.all()
            return render(request, 'borrowing/borrow_form.html', {
                'form'          : form,
                'unavailable'   : True,
                'equipment_name': equipment.name,
                'categories'    : categories,
            })

        BorrowRecord.objects.create(
            equipment    = equipment,
            processed_by = request.user,
            department   = department,
            due_date     = due_date,
            due_time     = due_time,
            remarks      = remarks,
            status       = 'borrowed',
        )

        equipment.quantity -= 1
        if equipment.quantity == 0:
            equipment.status = 'borrowed'
        equipment.save()

        UserLog.objects.create(
            user   = request.user,
            action = f'📦 Borrowed "{equipment.name}" — Expected return: {due_date} {due_time.strftime("%I:%M %p") if due_time else ""}'
        )

        messages.success(request, f'"{equipment}" successfully borrowed!')
        return redirect('user_records')

    categories = Category.objects.all()
    return render(request, 'borrowing/borrow_form.html', {
        'form'      : form,
        'categories': categories,
    })


@login_required
def return_item(request, pk):
    record = get_object_or_404(BorrowRecord, pk=pk)
    if request.method == 'POST':
        now   = timezone.now()
        today = now.date()

        # Auto detect if late
        if today > record.due_date:
            record.status = 'late'
            log_action    = f'⚠️ Returned LATE: "{record.equipment.name}" — Due: {record.due_date}, Returned: {now.strftime("%b %d, %Y %I:%M %p")}'
        else:
            record.status = 'returned'
            log_action    = f'✅ Returned on time: "{record.equipment.name}" on {now.strftime("%b %d, %Y %I:%M %p")}'

        record.date_returned = now
        record.save()

        # Add quantity back
        record.equipment.quantity += 1
        record.equipment.status   = 'available'
        record.equipment.save()

        # Log user activity
        UserLog.objects.create(
            user   = request.user,
            action = log_action
        )

        messages.success(request, f'"{record.equipment}" has been returned.')
        return redirect('user_records')
    return render(request, 'borrowing/confirm_return.html', {'record': record})


@login_required
def report_lost(request, pk):
    record = get_object_or_404(BorrowRecord, pk=pk)
    if request.method == 'POST':
        record.status        = 'lost'
        record.date_returned = timezone.now()
        record.save()

        # Mark equipment as maintenance, qty stays 0
        record.equipment.status   = 'maintenance'
        record.equipment.quantity = 0
        record.equipment.save()

        # Log user activity
        UserLog.objects.create(
            user   = request.user,
            action = f'❌ Reported LOST: "{record.equipment.name}" on {timezone.now().strftime("%b %d, %Y %I:%M %p")}'
        )

        # Log admin activity
        AdminLog.objects.create(
            admin  = request.user,
            action = f'❌ User {request.user.get_full_name()} reported LOST: {record.equipment.name}'
        )

        messages.error(request, f'"{record.equipment}" has been reported as lost.')
        return redirect('user_records')
    return render(request, 'borrowing/confirm_lost.html', {'record': record})


@login_required
def borrow_records(request):
    status  = request.GET.get('status', '')
    records = BorrowRecord.objects.select_related('equipment', 'processed_by').all()
    if status:
        records = records.filter(status=status)
    return render(request, 'borrowing/borrow_records.html', {'records': records, 'status': status})


@login_required
def user_records(request):
    today   = timezone.now().date()
    soon    = today + timedelta(days=3)
    status  = request.GET.get('status', '')
    records = BorrowRecord.objects.filter(processed_by=request.user).select_related('equipment')
    if status:
        records = records.filter(status=status)
    due_soon = BorrowRecord.objects.filter(
        processed_by  = request.user,
        status        = 'borrowed',
        due_date__lte = soon,
        due_date__gte = today
    )
    due_soon_count = due_soon.count()
    return render(request, 'borrowing/user_records.html', {
        'records'       : records.order_by('-date_borrowed'),
        'status'        : status,
        'due_soon'      : due_soon,
        'due_soon_count': due_soon_count,
        'today'         : today,
    })


@login_required
def user_activity_log(request):
    logs = UserLog.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'borrowing/user_activity_log.html', {'logs': logs})


@staff_member_required
def pending_users(request):
    pending = UserProfile.objects.filter(is_approved=False).select_related('user')
    return render(request, 'borrowing/pending_users.html', {'pending': pending})


@staff_member_required
def approve_user(request, pk):
    profile             = get_object_or_404(UserProfile, pk=pk)
    profile.is_approved = True
    profile.save()
    AdminLog.objects.create(
        admin  = request.user,
        action = f'✅ Approved user: {profile.user.get_full_name()} ({profile.user.email})'
    )
    messages.success(request, f'"{profile.user.get_full_name()}" has been approved.')
    return redirect('pending_users')


@staff_member_required
def reject_user(request, pk):
    profile   = get_object_or_404(UserProfile, pk=pk)
    full_name = profile.user.get_full_name()
    email     = profile.user.email
    AdminLog.objects.create(
        admin  = request.user,
        action = f'❌ Rejected user: {full_name} ({email})'
    )
    profile.user.delete()
    messages.success(request, f'User "{full_name}" has been rejected and removed.')
    return redirect('pending_users')


@staff_member_required
def user_list(request):
    users = User.objects.filter(is_superuser=False).select_related('profile').order_by('-date_joined')
    return render(request, 'borrowing/user_list.html', {'users': users})


@staff_member_required
def delete_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        full_name = user.get_full_name()
        email     = user.email
        AdminLog.objects.create(
            admin  = request.user,
            action = f'🗑️ Deleted user: {full_name} ({email})'
        )
        user.delete()
        messages.success(request, f'User "{full_name}" has been deleted.')
        return redirect('user_list')
    return render(request, 'borrowing/confirm_delete.html', {'obj': user, 'type': 'User'})


@staff_member_required
def disable_user(request, pk):
    user    = get_object_or_404(User, pk=pk)
    profile = user.profile
    if profile.is_disabled:
        profile.is_disabled = False
        user.is_active      = True
        user.save()
        profile.save()
        AdminLog.objects.create(
            admin  = request.user,
            action = f'🔓 Enabled user: {user.get_full_name()} ({user.email})'
        )
        messages.success(request, f'"{user.get_full_name()}" has been enabled.')
    else:
        profile.is_disabled = True
        user.is_active      = False
        user.save()
        profile.save()
        AdminLog.objects.create(
            admin  = request.user,
            action = f'🔒 Disabled user: {user.get_full_name()} ({user.email})'
        )
        messages.success(request, f'"{user.get_full_name()}" has been disabled.')
    return redirect('user_list')


@staff_member_required
def activity_log(request):
    logs = AdminLog.objects.all()
    return render(request, 'borrowing/activity_log.html', {'logs': logs})