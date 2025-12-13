from django.contrib import admin
from .models import Cliente, Producto, Pedido, DetallePedido
from django.utils.html import format_html

# Configuración visual para los Pedidos
class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 0 # No muestra filas vacías extra
    readonly_fields = ('subtotal',) # Para que no editen precios a mano por error

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    # 1. COLUMNAS QUE SE VEN EN LA LISTA
    list_display = ('id', 'nombre_cliente', 'fecha_entrega', 'total_formato', 'estado', 'tematica_corta')
    
    # 2. FILTROS LATERALES (Esto reemplaza el dashboard de "ventas del mes")
    list_filter = ('estado', 'fecha_entrega', 'fecha_pedido')
    
    # 3. BARRA DE BÚSQUEDA
    search_fields = ('cliente__nombre', 'cliente__telefono', 'tematica')
    
    # 4. ORDENAR (Lo más nuevo primero)
    ordering = ('-fecha_pedido',)
    
    # 5. EDITAR EL DETALLE DENTRO DEL PEDIDO
    inlines = [DetallePedidoInline]

    # --- Funciones auxiliares para mostrar datos bonitos ---
    
    def nombre_cliente(self, obj):
        return obj.cliente.nombre
    nombre_cliente.short_description = "Cliente"

    def total_formato(self, obj):
        return f"${obj.total:,}"
    total_formato.short_description = "Total a Pagar"

    def tematica_corta(self, obj):
        return (obj.tematica[:30] + '...') if len(obj.tematica) > 30 else obj.tematica
    tematica_corta.short_description = "Diseño"

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'direccion')
    search_fields = ('nombre', 'telefono')

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio')
