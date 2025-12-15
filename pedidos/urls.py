from django.urls import path
from . import views

urlpatterns = [
    # Esta línea le dice a Django: "Si la dirección está vacía, muestra la vista 'index'"
    path('', views.home, name='home'),

    path('chat/', views.chat_view, name='chat'),
    
    #http://127.0.0.1:8000/api/chat/
    path('api/chat/', views.chat_api, name='chat_api'),

    path('admin/dashboard/', views.dashboard_admin, name='dashboard_admin'),

    path('comprobante/pedido/<int:pedido_id>/', views.comprobante_pedido, name='imprimir_pedido'),

]

