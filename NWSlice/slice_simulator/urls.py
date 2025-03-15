from django.urls import path
from . import views

from .views import *

urlpatterns = [
    path('', views.home, name='home'),

    path('simulator', views.start_simulation, name='start_simulation'),
]
