from django.http import JsonResponse
from django.shortcuts import render


def home(request):
    return render(
        request,
        "core/home.html",
        {
            "name": "IndusCMS",
            "version": "0.1.0",
        },
    )


def health(request):
    return JsonResponse(
        {
            "name": "IndusCMS",
            "status": "healthy",
            "version": "0.1.0",
        }
    )
