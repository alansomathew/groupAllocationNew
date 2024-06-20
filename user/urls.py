
from django.urls import path,include

from user import views

urlpatterns = [
    path('',views.home,name='home'),
    path('login/', views.user_login, name="login"),
    path('logout/', views.user_logout, name="logout"),
    path('signup/', views.signup, name="signup"),
    path('participate/', views.participate, name="participate"),
]
