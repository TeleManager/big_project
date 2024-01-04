from django.urls import path, reverse, reverse_lazy
from django.views.generic import TemplateView, ListView, CreateView, DetailView, UpdateView, DeleteView
from . import views
from .models import *
from .views import ClientListView
from django.shortcuts import render


app_name = 'client'

def index(request):
    return render(request, 'index.html')

def audio(request):
    return render(request, 'client/audio.html')

urlpatterns = [
    path('', ClientListView.as_view(), name = 'list'),
    path('upload/',views.upload_excel, name='upload'),
    path('edit/<int:client_id>/', views.edit_client, name='edit_client'),
    path('delete/<int:client_id>/', views.delete_client, name='delete_client'),
    path('delete_selected/', views.DeleteSelectedClientsView.as_view(), name='delete_selected'),
    path('selected_items/', views.selected_items, name='selected_items'),
    path('start_tm/',views.start_tm, name='start_tm'),
    path('error/', views.error_page, name='error'),


    path('delete_selected/', views.DeleteSelectedClientsView.as_view(), name='delete_selected'),
    # path('audio/', audio, name='audio'),
    # path('save_audio/', views.save_audio, name='save_audio'),
]


