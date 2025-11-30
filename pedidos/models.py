from django.db import models
import uuid

# Basado en la entidad Cliente [cite: 333]


class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    correo = models.EmailField(max_length=100)

    def __str__(self):
        return str(self.nombre)

# Basado en la entidad Producto [cite: 334]


class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.TextField()
    imagen_url = models.URLField(
        max_length=500, blank=True, null=True)  # "text" en tu diseño
    visible = models.BooleanField(default=True)

    def __str__(self):
        return str(self.nombre)

# Basado en la entidad Pedido [cite: 335]


class Pedido(models.Model):
    # Estados definidos en RF3 y BPMN [cite: 171, 303]
    ESTADOS = [
        ('RECIBIDO', 'Recibido'),
        ('EN_PRODUCCION', 'En Producción'),
        ('LISTO', 'Listo para entrega'),
        ('ENTREGADO', 'Entregado'),
        ('CANCELADO', 'Cancelado'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=20, choices=ESTADOS, default='RECIBIDO')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # Generamos un código único corto automáticamente si no viene uno
    codigo_pedido = models.CharField(max_length=20, unique=True, blank=True)
    fecha_entrega = models.CharField(max_length=100, blank=True, null=True)
    tematica = models.CharField(max_length=200, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.codigo_pedido:
            self.codigo_pedido = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Pedido {self.codigo_pedido} - {self.cliente}"

# Basado en la entidad DetallePedido [cite: 336]


class DetallePedido(models.Model):
    pedido = models.ForeignKey(
        Pedido, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        # Calculamos subtotal automáticamente: precio * cantidad
        self.subtotal = self.producto.precio * self.cantidad
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"

# Basado en la entidad Notificacion [cite: 337]


class Notificacion(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    canal = models.CharField(
        max_length=30, default='WhatsApp')  # "varchar(30)"
    plantilla = models.CharField(max_length=60)  # Nombre del template usado
    estado_envio = models.CharField(max_length=20, default='Pendiente')
    fecha_envio = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notificación {self.id} - {self.estado_envio}"
