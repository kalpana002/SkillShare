from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

SIGNUP = 'signup'

urlpatterns = [
    path('', auth_views.LoginView.as_view(template_name='accounts/login.html')),
    path('signup/', views.signup_view, name=SIGNUP),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
]
