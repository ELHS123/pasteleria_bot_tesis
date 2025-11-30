from django.urls import path
from . import views

urlpatterns = [
    # Esta línea le dice a Django: "Si la dirección está vacía, muestra la vista 'index'"
    path('', views.index, name='index'),
    # Esta será la dirección: http://127.0.0.1:8000/api/chat/
    path('api/chat/', views.chat_api, name='chat_api'),
]
