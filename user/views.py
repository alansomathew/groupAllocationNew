from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages


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

