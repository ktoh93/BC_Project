from django.shortcuts import render

def login(request):
    return render(request, 'login.html')

def signup(request):
    return render(request, 'signup.html')

def find_id(request):
    return render(request, 'findID.html')

def find_pw(request):
    return render(request, 'findPW.html')