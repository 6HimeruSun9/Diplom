from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('lesson/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('test/<int:lesson_id>/', views.test_view, name='test'),
    path('test/<int:lesson_id>/submit/', views.submit_test, name='submit_test'),
    path('profile/', views.profile, name='profile'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='lessons/auth/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('section/<int:section_id>/', views.section_detail, name='section_detail'),
]