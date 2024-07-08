
from django.urls import path,include

from user import views

urlpatterns = [
    path('',views.home,name='home'),
    path('login/', views.user_login, name="login"),
    path('logout/', views.user_logout, name="logout"),
    path('signup/', views.signup, name="signup"),
    path('participate/', views.participate, name="participate"),
    path('participant-list/<str:event_id>/', views.participant_list, name='participant_list'),
    path('express-interest/<str:participant_id>/', views.express_interest, name='express_interest'),
    path('remove_interest/<str:participant_id>/', views.remove_interest, name='remove_interest'),
]
