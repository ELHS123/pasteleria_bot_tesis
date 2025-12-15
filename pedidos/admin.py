from django.contrib import admin
from django.utils.html import format_html
from .models import Cliente, Producto, Pedido, DetallePedido
from django.urls import reverse  


# Configuración visual para ver los productos dentro del pedido
class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 0
    readonly_fields = ('subtotal',)

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    # 1. Agregamos 'estado_color' a la lista en lugar de 'estado' normal
    list_display = ('id', 'nombre_cliente', 'fecha_entrega', 'total_formato', 'estado_color', 'acciones')

    # 2. Filtros y Búsqueda
    list_filter = ('estado', 'fecha_entrega', 'fecha_pedido')
    search_fields = ('cliente__nombre', 'cliente__telefono', 'tematica')
    ordering = ('-fecha_pedido',)
    inlines = [DetallePedidoInline]

    # --- FUNCIONES VISUALES ---
    def acciones(self, obj):
        url = reverse('imprimir_pedido', args=[obj.id])
        return format_html(
            '<a class="button" href="{}" target="_blank" style="background-color: #6c757d; color: white; padding: 5px 10px; border-radius: 5px; text-decoration: none;">🖨️ Ver</a>',
            url
        )
    acciones.short_description = "Comprobante"

    def nombre_cliente(self, obj):
        return obj.cliente.nombre
    nombre_cliente.short_description = "Cliente"

    def total_formato(self, obj):
        return f"${obj.total:,}"
    total_formato.short_description = "Total"

    def tematica_corta(self, obj):
        # Corta el texto si es muy largo para que no deforme la tabla
        return (obj.tematica[:30] + '...') if len(obj.tematica) > 30 else obj.tematica
    tematica_corta.short_description = "Diseño"

    # --- ETIQUETAS DE COLOR ---
    def estado_color(self, obj):
        # Diccionario de colores
        colores = {
            'RECIBIDO': 'orange',      # Naranja
            'PREPARACION': '#17a2b8',  # Azul Claro (Info)
            'ENTREGADO': '#28a745',    # Verde (Éxito)
            'CANCELADO': '#dc3545',    # Rojo (Peligro)
        }
        color_fondo = colores.get(obj.estado, 'gray') # Gris por defecto
        
        # Creamos el HTML de la etiqueta
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 15px; font-weight: bold; font-size: 12px;">{}</span>',
            color_fondo,
            obj.get_estado_display()
        )
    estado_color.short_description = "Estado del Pedido"

# Registros simples
@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'direccion')
    search_fields = ('nombre',)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio')
