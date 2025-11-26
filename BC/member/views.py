from django.shortcuts import render

def base(request):
    return render('', 'base.html')
def info(request):
    return render('', 'info.html')
def edit(request):
    return render('', 'info_edit.html')
def edit_password(request):
    return render('', 'info_edit_password.html')
def myreservation(request):
    return render('', 'myreservation.html')
def mycommunity(request):
    return render('', 'mycommunity.html')
def myarticle(request):
    return render('', 'myarticle.html')
def myjoin(request):
    return render('', 'myjoin.html')