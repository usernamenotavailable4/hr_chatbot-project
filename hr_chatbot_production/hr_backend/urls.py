from django.contrib import admin
from django.urls import path
from chatbot import views as botviews

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", botviews.login_page, name="login"),
    path("login/", botviews.login_page, name="login"),
    path("logout/", botviews.logout_view, name="logout"),
    path("home/", botviews.home, name="home"),
    path("chatbot-widget/", botviews.chatbot_widget, name="chatbot_widget"),
    path("api/chat/", botviews.api_chat, name="api_chat"),
]
