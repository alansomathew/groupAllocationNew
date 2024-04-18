
from django.urls import path,include

from organiser import views

urlpatterns = [
    path('index/',views.index,name='index'),
    path('event/',views.event,name='event'),

]
