from django.contrib import admin
from .models import Cliente, Producto, Pedido, DetallePedido, Notificacion

# Configuración para ver los detalles del pedido dentro de la pantalla del pedido


class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 1
    readonly_fields = ('subtotal',)


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('codigo_pedido', 'cliente',
                    'estado', 'fecha_pedido', 'total')
    list_filter = ('estado', 'fecha_pedido')
    search_fields = ('codigo_pedido', 'cliente__nombre')
    inlines = [DetallePedidoInline]
    readonly_fields = ('codigo_pedido', 'fecha_pedido')


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'visible')
    list_editable = ('precio', 'visible')
    search_fields = ('nombre',)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'correo')
    search_fields = ('nombre', 'telefono')


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('pedido', 'canal', 'estado_envio', 'fecha_envio')
    readonly_fields = ('fecha_envio',)
