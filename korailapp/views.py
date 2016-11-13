from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views import View

from .korail.korail import Korail
from .models import ReserveQueue

class KorailDeleteView(View):
    def get(self, request, pk):
        reserveq = ReserveQueue.objects.get(id=pk)
        reserveq.delete()
        return redirect('/korail/')

class KorailView(View):
    def get(self, request):
        # <view logic>
        reserve_list = ReserveQueue.objects.filter()
        return render(request, 'index.html', {'reserve_list': reserve_list})

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        dep = request.POST.get('dep')
        arr = request.POST.get('arr')
        date = request.POST.get('date')
        time = request.POST.get('time')
        train_type = request.POST.get('train_type')

        korail = Korail(username, password)
        if not korail.login():
            return HttpResponse("Login fail")

        ReserveQueue.objects.create(
            username=username,
            password=password,
            dep=dep,
            arr=arr,
            date=date,
            time=time,
            train_type=train_type
        )
        return redirect('/korail/')

