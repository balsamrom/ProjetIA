from django.urls import path
from admin_volt import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    # Index
    path('', views.index, name="index"),

    # Pages
    path('pages/dashboard/', views.dashboard, name="dashboard"),
    path('pages/transaction/', views.transaction, name="transaction"),
    path('pages/settings/', views.settings, name="settings"),

    # Hotels CRUD (Volt Dashboard)
    path('pages/hotels/', views.hotel_list_volt, name='volt_hotel_list'),
    path('pages/hotels/new/', views.hotel_create_volt, name='volt_hotel_create'),
    path('pages/hotels/<int:pk>/', views.hotel_detail_volt, name='volt_hotel_detail'),
    path('pages/hotels/<int:pk>/edit/', views.hotel_update_volt, name='volt_hotel_update'),
    path('pages/hotels/<int:pk>/delete/', views.hotel_delete_volt, name='volt_hotel_delete'),

    # Rooms CRUD (Volt Dashboard)
    path('pages/rooms/', views.room_list_volt, name='volt_room_list'),
    path('pages/rooms/new/', views.room_create_volt, name='volt_room_create'),
    path('pages/rooms/<int:pk>/edit/', views.room_update_volt, name='volt_room_update'),
    path('pages/rooms/<int:pk>/delete/', views.room_delete_volt, name='volt_room_delete'),

    # Reservations CRUD (Volt Dashboard)
    path('pages/reservations/', views.reservation_list_volt, name='volt_reservation_list'),
    path('pages/reservations/new/', views.reservation_create_volt, name='volt_reservation_create'),
    path('pages/reservations/<int:pk>/edit/', views.reservation_update_volt, name='volt_reservation_update'),
    path('pages/reservations/<int:pk>/delete/', views.reservation_delete_volt, name='volt_reservation_delete'),

    # Reviews (Volt) list/delete
    path('pages/reviews/', views.review_list_volt, name='volt_review_list'),
    path('pages/reviews/<int:pk>/delete/', views.review_delete_volt, name='volt_review_delete'),

    # Events CRUD (Volt Dashboard)
    path('pages/events/', views.event_list_volt, name='volt_event_list'),
    path('pages/events/new/', views.event_create_volt, name='volt_event_create'),
    path('pages/events/<int:pk>/', views.event_detail_volt, name='volt_event_detail'),
    path('pages/events/<int:pk>/edit/', views.event_update_volt, name='volt_event_update'),
    path('pages/events/<int:pk>/delete/', views.event_delete_volt, name='volt_event_delete'),

    # Tables
    path('tables/bs-tables/', views.bs_tables, name="bs_tables"),

    # Components
    path('components/buttons/', views.buttons, name="buttons"),
    path('components/notifications/', views.notifications, name="notifications"),
    path('components/forms/', views.forms, name="forms"),
    path('components/modals/', views.modals, name="modals"),
    path('components/typography/', views.typography, name="typography"),

    # Authentication
    path('accounts/register/', views.register_view, name="register"),
    path('accounts/login/', views.UserLoginView.as_view(), name="login"),
    path('accounts/logout/', views.logout_view, name="logout"),
    path('accounts/password-change/', views.UserPasswordChangeView.as_view(), name='password_change'),
    path('accounts/password-change-done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password-change-done.html'
    ), name="password_change_done"),
    path('accounts/password-reset/', views.UserPasswordResetView.as_view(), name="password_reset"),
    path('accounts/password-reset-confirm/<uidb64>/<token>/',
        views.UserPasswrodResetConfirmView.as_view(), name="password_reset_confirm"
    ),
    path('accounts/password-reset-done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password-reset-done.html'
    ), name='password_reset_done'),
    path('accounts/password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password-reset-complete.html'
  ), name='password_reset_complete'),

    path('accounts/lock/', views.lock, name="lock"),

    # Errors
    path('error/404/', views.error_404, name="error_404"),
    path('error/500/', views.error_500, name="error_500"),

    # Extra
    path('pages/upgrade-to-pro/', views.upgrade_to_pro, name="upgrade_to_pro"),


    
]
