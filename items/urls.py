from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Core navigation
    path('', views.home, name='home'),
    path('browse/', views.browse_items, name='browse'),
    path('items/<int:pk>/', views.item_detail, name='item_detail'),

    # Reporting items
    path('report/lost/', views.report_lost_item, name='report_lost'),
    path('report/found/', views.report_found_item, name='report_found'),
    path('items/<int:pk>/edit/', views.edit_item, name='edit_item'),
    path('items/<int:pk>/status/', views.update_item_status, name='update_item_status'),
    path('items/<int:pk>/report/', views.report_listing, name='report_listing'),

    # Recovery requests
    path('items/<int:pk>/claim/', views.submit_recovery_request, name='submit_claim'),
    path('claims/<int:request_id>/manage/', views.manage_recovery_request, name='manage_claim'),
    path('my-claims/', views.my_recovery_requests, name='my_claims'),

    # User personal hub
    path('dashboard/', views.dashboard, name='dashboard'),
    path('my-listings/', views.my_listings, name='my_listings'),
    path('profile/', views.user_profile, name='profile'),

    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # Assessment Requirements
    path('faqs/', views.faqs_view, name='faqs'),
    path('faq/', views.faqs_view, name='faq_alias'),
    path('support/', views.support_center, name='support_center'),
    path('support/tickets/', views.my_support_tickets, name='my_support_tickets'),
    path('support/tickets/<str:ticket_number>/update/', views.ticket_update_view, name='ticket_update'),
    path('support/tickets/<str:ticket_number>/delete/', views.ticket_delete_view, name='ticket_delete'),
    path('support/mongo-logs/', views.mongo_logs_view, name='mongo_logs'),
    path('mongo-logs/', views.mongo_logs_view, name='mongo_logs_alias'),
    path('errors/', views.error_catalog_view, name='error_catalog'),
    path('status/', views.error_catalog_view, name='status_alias'),
    path('errors/<str:code>/', views.error_detail_view, name='error_detail'),
    path('status/<str:code>/', views.simulate_error, name='status_detail_alias'),
    path('errors/simulate/<str:code>/', views.simulate_error, name='simulate_error'),
    path('health/', views.health_check, name='health_check'),

    # AI Assistant & Support APIs
    path('api/chat/', views.chat_api, name='chat_api'),
    path('api/assistant/', views.chat_api, name='api_assistant'),
    path('api/chat/feedback/', views.chat_feedback_api, name='chat_feedback_api'),
    path('api/health/', views.health_check, name='api_health'),
    path('api/faqs/', views.api_faqs, name='api_faqs'),
    path('api/errors/', views.api_errors, name='api_errors'),
    path('api/tickets/lookup/', views.ticket_lookup_api, name='ticket_lookup_api'),
    path('api/tickets/email/', views.ticket_email_api, name='ticket_email_api'),
    path('api/tickets/', views.api_ticket_crud, name='api_ticket_crud_list'),
    path('api/tickets/<str:ticket_number>/', views.api_ticket_crud, name='api_ticket_crud'),
]

