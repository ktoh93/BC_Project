from django.http import HttpResponse

def index(request):
    return HttpResponse("<h1>서비스 준비중입니다..</h1>")