from django.shortcuts import render

def list(request):
    return render(request, 'list.html')

def write(request):
    return render(request, 'write.html')