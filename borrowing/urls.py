from django.urls import path
from . import views

urlpatterns = [
    path('',                                views.dashboard,                 name='dashboard'),

    # Categories
    path('categories/',                     views.category_list,             name='category_list'),
    path('categories/<int:pk>/delete/',     views.category_delete,           name='category_delete'),

    # Equipment
    path('equipment/',                      views.equipment_list,            name='equipment_list'),
    path('equipment/add/',                  views.equipment_add,             name='equipment_add'),
    path('equipment/<int:pk>/edit/',        views.equipment_edit,            name='equipment_edit'),
    path('equipment/<int:pk>/delete/',      views.equipment_delete,          name='equipment_delete'),

    # Borrowers
    path('borrowers/',                      views.borrower_list,             name='borrower_list'),
    path('borrowers/add/',                  views.borrower_add,              name='borrower_add'),
    path('borrowers/<int:pk>/edit/',        views.borrower_edit,             name='borrower_edit'),
    path('borrowers/<int:pk>/delete/',      views.borrower_delete,           name='borrower_delete'),

    # Borrow & Return
    path('borrow/',                         views.borrow_item,               name='borrow_item'),
    path('return/<int:pk>/',                views.return_item,               name='return_item'),
    path('lost/<int:pk>/',                  views.report_lost,               name='report_lost'),
    path('records/',                        views.borrow_records,            name='borrow_records'),
    path('get-equipment/',                  views.get_equipment_by_category, name='get_equipment'),

    # User
    path('my-records/',                     views.user_records,              name='user_records'),
    path('my-activity/',                    views.user_activity_log,         name='user_activity_log'),

    # User Management
    path('pending-users/',                  views.pending_users,             name='pending_users'),
    path('approve/<int:pk>/',               views.approve_user,              name='approve_user'),
    path('reject/<int:pk>/',                views.reject_user,               name='reject_user'),
    path('users/',                          views.user_list,                 name='user_list'),
    path('users/<int:pk>/delete/',          views.delete_user,               name='delete_user'),
    path('users/<int:pk>/disable/',         views.disable_user,              name='disable_user'),

    # Logs
    path('activity-log/',                   views.activity_log,              name='activity_log'),

    # Register & Splash
    path('register/',                       views.register,                  name='register'),
    path('splash/',                         views.splash,                    name='splash'),
]