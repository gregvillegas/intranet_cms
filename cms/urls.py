from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('announcements/', views.announcement_list, name='announcement_list'),
    path('announcements/<int:pk>/', views.announcement_detail, name='announcement_detail'),
    path('announcements/<int:pk>/comment/', views.add_comment, name='add_comment'),
    path('comments/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('api/announcements/<int:pk>/views/', views.increment_announcement_views, name='increment_announcement_views'),
    path('announcements/new/', views.create_announcement, name='create_announcement'),
    path('announcements/<int:pk>/edit/', views.edit_announcement, name='edit_announcement'),
    path('announcements/<int:pk>/delete/', views.delete_announcement, name='delete_announcement'),
    path('files/<int:pk>/preview', views.document_preview, name='document_preview'),
    path('files/', views.file_list, name='file_list'),
    path('files/<int:pk>/', views.file_detail, name='file_detail'),
    path('files/<int:pk>/update/', views.update_file, name='update_file'),
    path('files/<int:pk>/download/', views.file_download, name='file_download'),
    path('files/<int:pk>/download/<int:version>/', views.file_download_version, name='file_download_version'),
    path('files/upload/', views.upload_file, name='upload_file'),
    path('files/<int:pk>/delete/', views.delete_file, name='delete_file'),
    path('search/', views.search, name='search'),
    path('profile/<int:pk>/', views.profile_view, name='profile_view'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_edit'),
    path('activity/', views.activity_log, name='activity_log'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
]
