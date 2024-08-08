from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from organiser.utils import generate_code
from user.models import Event, Group, Interest, Levels, Participant, PrivateCodes, TimeMatrix
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from collections import defaultdict
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, value, PULP_CBC_CMD
import numpy as np

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

    happiness_matrix = np.zeros((len(groups), len(groups)))
    for i, group_i in enumerate(groups):
        for j, group_j in enumerate(groups):
            if i == j:
                happiness_matrix[i, j] = x_value
            else:
                travel_time = travel_times[group_i.id].get(group_j.id, 0)
                if travel_time != 0:
                    happiness_matrix[i, j] = x_value / travel_time
                else:
                    happiness_matrix[i, j] = 0

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
    event.is_private = False
    event.save()
    messages.success(request, 'Event started successfully.')
    return redirect('display_event_details', event_id=event_id)


def stop_event(request, event_id):
    event = Event.objects.get(id=event_id)
    event.is_active = False
    event.is_private = True
    event.save()
    messages.success(request, 'Event stopped successfully.')
    return redirect('display_event_details', event_id=event_id)


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
        participate_base_url = request.build_absolute_uri(
            reverse('participate'))
        return render(request, 'organiser/generate_code.html', {'event': event, 'codes': codes, 'participate_base_url': participate_base_url})


def time_details_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    # Get all groups related to the event
    groups = Group.objects.filter(level__event=event)
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
    participants = Participant.objects.filter(event=event)
    return render(request, 'organiser/view_participants.html', {'event': event, 'participants': participants})

# Assuming you have a method to calculate the happiness matrix


def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.delete()
    messages.success(request, 'Event deleted successfully.')
    # Redirect to the home page or any other relevant page
    return redirect('home')


def participants_interests(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    participants = Participant.objects.filter(event=event)

    participants_with_interests = []
    for participant in participants:
        interests = Interest.objects.filter(from_participant=participant)
        participants_with_interests.append((participant, interests))

    context = {
        'event': event,
        'participants_with_interests': participants_with_interests,
    }
    return render(request, 'organiser/preference.html', context)


def calculate_happiness_matrix_for_participants(participants, happiness_matrix, group_indices):
    participant_happiness_matrix = defaultdict(dict)

    for participant in participants:
        participant_id = participant.id
        prefs = [interest.to_participant.id for interest in Interest.objects.filter(from_participant=participant, is_interested=True)]
        for group_id in group_indices:
            happiness = 0
            for pref in prefs:
                if pref in participants.values_list('id', flat=True):
                    preferred_group_index = group_indices[group_id]
                    happiness += happiness_matrix[group_indices[group_id], preferred_group_index]
            participant_happiness_matrix[participant_id][group_id] = happiness

    return participant_happiness_matrix



def calculate_current_happiness(participants, happiness_matrix, group_index_map):
    current_happiness = 0
    for participant in participants:
        if participant.group:
            participant_group_idx = group_index_map[participant.group.id]
            for interest in Interest.objects.filter(from_participant=participant, is_interested=True):
                if interest.to_participant.group:
                    to_group_idx = group_index_map[interest.to_participant.group.id]
                    current_happiness += happiness_matrix[participant_group_idx][to_group_idx]
    return current_happiness



def solve_ilp(groups, participants, happiness_matrix):
    group_indices = {group.id: idx for idx, group in enumerate(groups)}
    participant_happiness_matrix = calculate_happiness_matrix_for_participants(participants, happiness_matrix, group_indices)

    prob = LpProblem("Maximize_Happiness", LpMaximize)

    x = LpVariable.dicts("x", ((p.id, g) for p in participants for g in group_indices), 0, 1, cat='Binary')

    # Objective function
    prob += lpSum(participant_happiness_matrix[p.id][g] * x[p.id, g] for p in participants for g in group_indices)

    # Constraints: Capacity constraint
    for g in group_indices:
        prob += lpSum(x[p.id, g] for p in participants) <= groups.get(id=g).capacity, f"Capacity_{g}"

    # Constraints: Each participant must be assigned to exactly one group
    for p in participants:
        prob += lpSum(x[p.id, g] for g in group_indices) <= 1, f"Assignment_{p.id}"

    # Solve the problem
    solver = PULP_CBC_CMD(msg=True)
    prob.solve(solver)

    allocation = defaultdict(list)
    not_allocated = []
    for p in participants:
        assigned = False
        for g in group_indices:
            if value(x[p.id, g]) == 1:
                if len(allocation[g]) < groups.get(id=g).capacity:
                    allocation[g].append(p.id)
                    assigned = True
                    break
        if not assigned:
            not_allocated.append(p.id)
    allocation["not_allocated"] = not_allocated

    optimum_happiness = value(prob.objective)

    return allocation, optimum_happiness


def allocate_participants(request, event_id):
    event = Event.objects.get(id=event_id)
    levels = Levels.objects.filter(event=event)
    groups = Group.objects.filter(level__in=levels)
    happiness_matrix = create_happiness_matrix(event_id)

    # Fetch participants and their preferences
    participants_qs = Participant.objects.filter(event=event)
    participants = {}
    for participant in participants_qs:
        interests = Interest.objects.filter(from_participant=participant, is_interested=True)
        preferences = [interest.to_participant.id for interest in interests]
        participants[participant.id] = preferences

    allocation, optimum_happiness = solve_ilp(groups, participants_qs, happiness_matrix)

    # Update participant groups
    for group_id, participant_ids in allocation.items():
        group = Group.objects.get(id=group_id) if group_id != "not_allocated" else None
        for participant_id in participant_ids:
            participant = Participant.objects.get(id=participant_id)
            participant.group = group
            participant.save()

    event.optimum_happiness = optimum_happiness
    event.save()

    messages.success(request, "Allocation completed successfully.")

    return redirect('view_allocation', event_id=event_id)

def calculate_individual_happiness(participant, happiness_matrix, group_index_map):
    happiness = 0
    if participant.group:
        participant_group_idx = group_index_map[participant.group.id]
        for interest in Interest.objects.filter(from_participant=participant, is_interested=True):
            if interest.to_participant.group:
                to_group_idx = group_index_map[interest.to_participant.group.id]
                happiness += happiness_matrix[participant_group_idx][to_group_idx]
    return happiness

def view_allocation(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    groups = Group.objects.filter(level__event=event)
    participants = Participant.objects.filter(event=event).select_related('group')
    happiness_matrix = create_happiness_matrix(event_id)

    # Create a mapping from group IDs to matrix indices
    group_index_map = {group.id: idx for idx, group in enumerate(groups)}
    
    current_happiness = calculate_current_happiness(participants, happiness_matrix, group_index_map)

    # Calculate individual happiness for each participant
    individual_happiness = {}
    for participant in participants:
        happiness = 0
        participant_group_idx = group_index_map.get(participant.group.id, None) if participant.group else None
        if participant_group_idx is not None:
            for interest in Interest.objects.filter(from_participant=participant, is_interested=True):
                if interest.to_participant.group:
                    to_group_idx = group_index_map.get(interest.to_participant.group.id, None)
                    if to_group_idx is not None:
                        happiness += float(happiness_matrix[participant_group_idx][to_group_idx])
        individual_happiness[participant.id] = float(happiness)

    # Check group capacities
    exceeded_capacity_messages = []
    for group in groups:
        allocated_count = participants.filter(group=group).count()
        if allocated_count > group.capacity:
            exceeded_capacity_messages.append(
                f"Group '{group.name}' capacity exceeded. Maximum capacity is {group.capacity}. Currently allocated: {allocated_count}."
            )

    context = {
        'event': event,
        'groups': groups,
        'participants': participants,
        'optimum_happiness': event.optimum_happiness,
        'current_happiness': current_happiness,
        'exceeded_capacity_messages': exceeded_capacity_messages,
        'individual_happiness': individual_happiness,
    }
    return render(request, 'organiser/allocation_results.html', context)



def edit_allocation(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    groups = Group.objects.filter(level__event=event)
    participants = Participant.objects.filter(event=event).select_related('group')

    if request.method == 'POST':
        new_allocations = {}
        group_counts = {group.id: 0 for group in groups}

        for participant in participants:
            group_id = request.POST.get(f'group_{participant.id}')
            if group_id:
                group_id = int(group_id)
                if group_id in new_allocations:
                    new_allocations[group_id].append(participant)
                else:
                    new_allocations[group_id] = [participant]
                group_counts[group_id] += 1

        # Check for capacity issues
        for group_id, count in group_counts.items():
            group = Group.objects.get(id=group_id)
            if count > group.capacity:
                messages.warning(request, f"Group '{group.name}' capacity exceeded. Maximum capacity is {group.capacity}. Currently allocated: {count}.")

        # Update the participants' group assignments
        for participant in participants:
            group_id = request.POST.get(f'group_{participant.id}')
            if group_id:
                group = Group.objects.get(id=int(group_id))
                participant.group = group
            else:
                participant.group = None
            participant.save()

        messages.success(request, "Allocation updated successfully.")
        return redirect('view_allocation', event_id=event_id)

    context = {
        'event': event,
        'groups': groups,
        'participants': participants,
    }
    return render(request, 'organiser/edit_allocation.html', context)
