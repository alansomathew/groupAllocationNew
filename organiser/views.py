from django.shortcuts import render
from user.models import Event

# Create your views here.
def index(request):
    events = Event.objects.filter(created_by=request.user).order_by('-created_on')
    return render(request, 'organiser/home.html',{'events':events})

def event(request):
    if request.method == "POST":
        name = request.POST.get('fn')
        description = request.POST.get('description')
        participants = request.POST.get('ln')
        
        # Do some validation on the data received
        # ...

        # Save to database or whatever you want to do with the data
        # ...
        events=Event.objects.create(name=name, description=description, participants=participants,created_by=request.user)
        events.save()
        
        return render(request, 'organiser/event.html',)
    
    else:
        return render(request, 'organiser/event.html')