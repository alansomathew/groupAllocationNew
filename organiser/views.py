from django.shortcuts import render, redirect
from user.models import Event, Group, Levels, TimeMatrix
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Create your views here.

@login_required
def index(request):
    events = Event.objects.filter(
        created_by=request.user).order_by('-created_on')
    return render(request, 'organiser/home.html', {'events': events})

@login_required
def event(request):
    if request.method == "POST":
        name = request.POST.get('fn')
        description = request.POST.get('description')
        participants = request.POST.get('ln')

        # Do some validation on the data received
        # ...

        # Save to database or whatever you want to do with the data
        # ...
        events = Event.objects.create(
            name=name, description=description, participants=participants, created_by=request.user)
        events.save()

        return redirect('add_level', id=events.id)

    else:
        return render(request, 'organiser/event.html')


@login_required
def add_level(request, id):
    event_id = id  # Assuming 'id' is the event ID passed from the URL

    if request.method == "POST":
        num_levels = int(request.POST.get('num_levels'))

        if 'add_level' in request.POST or 'finish' in request.POST:
            # Iterate through each level
            for level_index in range(num_levels):
                # Create level
                level = Levels.objects.create(event_id=event_id, created_by=request.user)

                # Get number of groups for this level
                num_groups = int(request.POST.get(f'num_groups_{level_index}'))
                
                # Create groups for this level
                for group_index in range(num_groups):
                    group_name = request.POST.get(f'group_name_{level_index}_{group_index}')
                    capacity = int(request.POST.get(f'capacity_{level_index}_{group_index}'))
                    Group.objects.create(level=level, name=group_name, capacity=capacity, created_by=request.user)

            # if 'add_level' in request.POST:
            #     # Redirect to the same page with the event ID
            #     return redirect('add_level', id=event_id)
            # elif 'finish' in request.POST:
                # Redirect to a different page or render a different template
            return redirect('add_time_matrix', id=event_id)

    else:
        return render(request, 'organiser/levels.html', {'event_id': event_id})

@login_required
def add_time_matrix(request, id):
    if request.method == 'POST':
        # Retrieve all group ids from the form
        group_ids = request.POST.getlist('group')
        # print(group_ids)  # Verify if group IDs are being retrieved

        # Iterate through all combinations of groups
        for group_id_from in group_ids:
            for group_id_to in group_ids:
                # Retrieve travel time for this combination from the form
                travel_time = request.POST.get(
                    f'time_{group_id_from}_{group_id_to}')
                # print(travel_time)  # Verify if travel time is being retrieved

                # Retrieve group objects based on IDs
                group_from = Group.objects.get(id=group_id_from)
                group_to = Group.objects.get(id=group_id_to)
                travel_time = float(travel_time)

                # Save the time matrix entry
                TimeMatrix.objects.create(
                    group_from=group_from, group_to=group_to, travel_time=travel_time)

        messages.success(request, 'Time matrix added successfully.')
        return redirect('add_x_value',id=id)  # Redirect to a success page

    # Retrieve all groups
    event = Event.objects.get(id=id)
    levels = event.levels_set.all()
    groups = Group.objects.filter(level__in=levels)
    return render(request, 'organiser/matrix.html', {'groups': groups})

@login_required
def add_x_value(request, id):
    if request.method == 'POST':
        x_value = request.POST.get('x_value')
        event = Event.objects.get(id=id)
        event.x_value = x_value
        event.save()
        messages.success(request, 'X value added successfully.')
        return redirect('index')
    else:
        return render(request, 'organiser/x_value.html')
    
def create_happiness_matrix(event_id):
    event = Event.objects.get(id=event_id)
    x_value = event.x_value
    levels = Levels.objects.filter(event=event)
    groups = Group.objects.filter(level__in=levels)

    happiness_matrix = []

    temp = [" "]
    for i in range(1,len(groups)+1):
        temp.append( "group "+i.__str__())
    happiness_matrix.append(temp)

    for i in range(len(groups)):
        row = ["group "+(i+1).__str__()]
        for j in range(len(groups)):
            travel_time = TimeMatrix.objects.filter(group_from=groups[i], group_to=groups[j]).first().travel_time
            if i == j:
                row.append(x_value)
            else:
                if travel_time != 0:
                    row.append(x_value / travel_time)
                else:
                    row.append(0)
        happiness_matrix.append(row)

    return happiness_matrix

def display_event_details(request, event_id):
    event = Event.objects.get(id=event_id)
    levels = Levels.objects.filter(event=event)
    groups = Group.objects.filter(level__in=levels)
    time_matrix = TimeMatrix.objects.filter(group_from__level__event=event)
    happiness_matrix = create_happiness_matrix(event_id)
    # print(happiness_matrix)

    context = {
        'event': event,
        'levels': levels,
        'groups': groups,
        'time_matrix': time_matrix,
        'happiness_matrix': happiness_matrix
    }
    return render(request, 'organiser/event_details.html', context)
