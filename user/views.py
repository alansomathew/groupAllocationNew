from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from user.models import Event,Particpant, PrivateCodes

# Create your views here.

def home(request):
    return render(request, 'user/home.html')


def user_login(request):
    try:
        if request.method == 'POST':
            username = request.POST.get('email').strip()
            password = request.POST.get('pass').strip()
            user = authenticate(
                request, username=username, password=password)
            if user is not None:
                # print(user)
                login(request, user)
                if user.is_superuser:
                    login(request, user)
                    request.session['user_id'] = user.id
                    print(user)
                    return redirect("index")

                else:
                    login(request, user)
                    # Set the user ID in the session
                    request.session['user_id'] = user.id
                    print(user)
                    return redirect("index")
            else:
                messages.error(request, 'Invalid email or password')
                return render(request, 'Guest/login.html')
        else:
            return render(request, 'Guest/login.html')
    except Exception as e:
        print(e)
        messages.error(request, 'Error viewing data!')
        return render(request, 'Guest/login.html')


def user_logout(request):
    logout(request)
    return redirect('home')


def signup(request):
    try:
        if request.method == 'POST':
            password = request.POST.get('password').strip()
            first_name = request.POST.get('firstname').strip()
            last_name = request.POST.get('lastname').strip()
            email = request.POST.get('email').strip()

            user = User.objects.create_user(
                username=email, password=password, first_name=first_name, last_name=last_name,  email=email)
            user.save()
            messages.success(request, 'Account created successfully')
            return redirect('login')
        else:
            return render(request, 'Guest/Signup.html')
    except Exception as e:
        print(e)
        messages.error(request, 'Error viewing data!')
        return render(request, 'Guest/Signup.html')

def participate(request):
    # try:
        if request.method == 'POST':
            user_id = request.POST.get('participantName')
            event_code = request.POST.get('event_code')
            participant_code = request.POST.get('participantCode')
            
            # Get the event
            try:
                eventObj = Event.objects.get(code=event_code, is_active=True,)
            except Event.DoesNotExist:
                messages.error(request, 'Invalid or inactive event code!')
                return render(request, 'user/participate.html')

            # Check if the private code exists for the event
            private_code_obj = PrivateCodes.objects.filter(event=eventObj, code=participant_code).first()
            if not private_code_obj:
                messages.error(request, 'Invalid participant code!')
                return render(request, 'user/participate.html')

            # Check if the user has already registered for this event with the same private code
            user_exists = Particpant.objects.filter(privatecode=participant_code, name=user_id, event=eventObj).exists()
            if user_exists:
                messages.warning(request, 'You have already registered for this event with the same private code.')
                return render(request, 'user/participate.html')
           

            # Check if the private code is already used
            if private_code_obj.status:
                messages.warning(request, 'The private code is already used.')
                return render(request, 'user/participate.html')

            # Create a new participant
            Particpant.objects.create(name=user_id, event=eventObj, privatecode=participant_code)
            private_code_obj.status = True
            private_code_obj.save()
            messages.success(request, 'You have successfully participated in the event!')
            return redirect("participate")

        else:
            return render(request, 'user/participate.html')
    # except Exception as e:
    #     print(e)
    #     messages.error(request, 'Error viewing data!')
    #     return render(request, 'user/participate.html')
