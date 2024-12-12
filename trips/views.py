"""
Views for the trips app.
"""

from django.shortcuts import render


def index(request):
    """
    Render the app's homepage.
    """

    return render(request, "trips/index.html")
