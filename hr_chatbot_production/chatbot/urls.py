from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.api_login),
    path('chat/', views.api_chat),
    path('logout/', views.logout_view, name='logout'),
]
