
from django.urls import path,include

from organiser import views

urlpatterns = [
    path('index/',views.index,name='index'),
    path('event/',views.event,name='event'),
    path('levels/<str:id>/',views.add_level,name='add_level'),
    path('time/matrix/<str:id>/',views.add_time_matrix,name='add_time_matrix'),
    path('add/x/value/<str:id>/',views.add_x_value,name='add_x_value'),
    path('display/event/details/<str:event_id>/',views.display_event_details,name='display_event_details'),
    # start event and stop event
    path('start/event/<str:event_id>/',views.start_event,name='start_event'),
    path('stop/event/<str:event_id>/',views.stop_event,name='stop_event'),
    path('generate-codes/<int:event_id>/', views.generate_codes_view, name='generate_codes'),
     path('time-details/<int:event_id>/', views.time_details_view, name='time_details'),
    path('happiness-matrix/<int:event_id>/', views.happiness_matrix_view, name='happiness_matrix'),
    path('participants/<int:event_id>/', views.participants_view, name='participants'),

]
