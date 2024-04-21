
from django.urls import path,include

from organiser import views

urlpatterns = [
    path('index/',views.index,name='index'),
    path('event/',views.event,name='event'),
    path('levels/<str:id>/',views.add_level,name='add_level'),
    path('time/matrix/<str:id>/',views.add_time_matrix,name='add_time_matrix'),
    path('add/x/value/<str:id>/',views.add_x_value,name='add_x_value'),
    path('display/event/details/<str:event_id>/',views.display_event_details,name='display_event_details'),

]
