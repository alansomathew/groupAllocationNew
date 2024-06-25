from django.shortcuts import get_object_or_404, render, redirect
from organiser.utils import generate_code
from user.models import Event, Group, Levels, Particpant, PrivateCodes, TimeMatrix
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse

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
        participants = int(request.POST.get('ln'))
        code = request.POST.get('code')

        # Do some validation on the data received
        # ...

        # Save to database or whatever you want to do with the data

        # ...
        events = Event.objects.create(
            name=name, description=description, participants=participants, code=code, created_by=request.user)

        for j in range(participants):
            code = generate_code()
            PrivateCodes.objects.create(event=events, code=code)
        events.save()

        return redirect('add_level', id=events.id)

    else:
        return render(request, 'organiser/event.html')


@login_required
def add_level(request, id):
    event_id = id  # Assuming 'id' is the event ID passed from the URL

    if request.method == "POST":
        # Check if the 'finish' button was pressed
        if 'finish' in request.POST:
            level_counter = 1

            while True:
                level_key = f'Level_{level_counter}'

                if level_key not in request.POST:
                    break

                # Create level
                level = Levels.objects.create(
                    event_id=event_id, created_by=request.user)

                group_counter = 1
                while True:
                    group_name_key = f'group_name_{
                        level_counter}_{group_counter}'
                    capacity_key = f'capacity_{level_counter}_{group_counter}'

                    if group_name_key not in request.POST or capacity_key not in request.POST:
                        break

                    # Get group name and capacity
                    group_name = request.POST.get(group_name_key)
                    capacity = int(request.POST.get(capacity_key))

                    # Create group
                    Group.objects.create(
                        level=level, name=group_name, capacity=capacity, created_by=request.user)

                    group_counter += 1

                level_counter += 1

            # Redirect to the next step
            return redirect('add_time_matrix', id=event_id)

    # For GET requests, render the levels page
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
        return redirect('add_x_value', id=id)  # Redirect to a success page

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
    groups = Group.objects.filter(level__in=levels).order_by('id')

    # Prefetch travel times to reduce database queries
    travel_times = {}
    for group in groups:
        travel_times[group.id] = {
            t.group_to_id: t.travel_time
            for t in TimeMatrix.objects.filter(group_from=group)
        }

    happiness_matrix = []

    # Create header row
    header_row = [" "]
    for group in groups:
        header_row.append("group " + str(group.id))
    happiness_matrix.append(header_row)

    # Populate matrix rows
    for i, group_i in enumerate(groups):
        row = ["group " + str(group_i.id)]
        for j, group_j in enumerate(groups):
            if i == j:
                row.append(x_value)
            else:
                travel_time = travel_times[group_i.id].get(group_j.id, 0)
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


# start event and stop event
def start_event(request, event_id):
    event = Event.objects.get(id=event_id)
    event.is_active = True
    event.save()
    messages.success(request, 'Event started successfully.')
    return redirect('event_details', event_id=event_id)


def stop_event(request, event_id):
    event = Event.objects.get(id=event_id)
    event.is_active = False
    event.save()
    messages.success(request, 'Event stopped successfully.')
    return redirect('event_details', event_id=event_id)


@login_required
def generate_codes_view(request, event_id):
    event = get_object_or_404(Event, id=event_id, created_by=request.user)
    if request.method == 'POST':
        additional_codes = int(request.POST.get('additional_codes', 0))
        total_codes = event.participants + additional_codes
        existing_codes_count = PrivateCodes.objects.filter(event=event).count()
        new_codes_needed = total_codes - existing_codes_count

        if new_codes_needed > 0:
            for _ in range(new_codes_needed):
                while True:
                    code = generate_code()
                    if not PrivateCodes.objects.filter(code=code).exists():
                        PrivateCodes.objects.create(code=code, event=event)
                        break

            # Update the event's participant count
            event.participants = total_codes
            event.save()

            messages.success(
                request, f'{new_codes_needed} new codes generated.')
        else:
            messages.info(request, 'No new codes needed.')

        return redirect(reverse('generate_codes', args=[event_id]))
    else:
        codes = PrivateCodes.objects.filter(event=event)
        return render(request, 'organiser/generate_code.html', {'event': event, 'codes': codes})


def time_details_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    groups = Group.objects.filter(level__event=event)  # Get all groups related to the event
    time_matrix = TimeMatrix.objects.all()  # Get all time matrix data
    return render(request, 'organiser/time_details.html', {'event': event, 'groups': groups, 'time_matrix': time_matrix})



@login_required
def happiness_matrix_view(request, event_id):
    event = get_object_or_404(Event, id=event_id,)
    # Assuming you have a model or method to calculate happiness matrix
    happiness_matrix = create_happiness_matrix(event_id)
    return render(request, 'organiser/happiness_matrix.html', {'event': event, 'happiness_matrix': happiness_matrix})


@login_required
def participants_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    participants = Particpant.objects.filter(event=event)
    return render(request, 'organiser/view_participants.html', {'event': event, 'participants': participants})

# Assuming you have a method to calculate the happiness matrix
