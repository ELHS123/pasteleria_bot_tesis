from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .wit_client import consultar_wit
from .models import Cliente, Pedido, DetallePedido, Producto
from django.db.models import Sum, Count
from django.contrib.admin.views.decorators import staff_member_required
import datetime



def home(request):
    return render(request, 'pedidos/landing.html')

def chat_view(request):
    # Limpiamos sesión al entrar al chat para evitar confusiones
    request.session.flush()
    return render(request, 'pedidos/chat.html')

@csrf_exempt
def chat_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mensaje_usuario = data.get('mensaje', '')
            
            # --- MÁQUINA DE ESTADOS (FLUJO SECUENCIAL) ---
            # Verificamos en qué paso vamos. Si no hay paso, es 'cotizando'.
            step = request.session.get('step', 'cotizando') 
            respuesta_texto = ""

            # 2. SI EL BOT ESTABA ESPERANDO EL NOMBRE:
            if step == 'pidiendo_nombre':
                request.session['nombre_cliente'] = mensaje_usuario
                request.session['step'] = 'pidiendo_telefono' # Pasamos al siguiente paso
                return JsonResponse({'respuesta': f"Un gusto, {mensaje_usuario}. 📱 ¿Me podrías dar tu número de teléfono para contactarte?"})

            # 3. SI EL BOT ESTABA ESPERANDO EL TELÉFONO:
            elif step == 'pidiendo_telefono':
                request.session['telefono_cliente'] = mensaje_usuario
                request.session['step'] = 'pidiendo_direccion' # Pasamos al siguiente paso
                return JsonResponse({'respuesta': "Anotado. 📍 Por último, ¿cuál es la dirección para el despacho?"})

            # 4. SI EL BOT ESTABA ESPERANDO LA DIRECCIÓN (Paso Final):
            elif step == 'pidiendo_direccion':
                direccion = mensaje_usuario
                # Recuperamos todo lo que fuimos guardando en la memoria (sesión)
                nombre = request.session.get('nombre_cliente')
                telefono = request.session.get('telefono_cliente')
                
                sabor = request.session.get('sabor')
                cantidad = request.session.get('cantidad')
                fecha = request.session.get('fecha')
                tematica = request.session.get('tematica')
                
                # Calculamos precio final
                precio = 10000 + (cantidad * 1500)

                # --- GUARDADO EN BASE DE DATOS ---
                # 1. Guardamos al Cliente
                cliente_obj, created = Cliente.objects.update_or_create(
                    nombre=nombre,
                    defaults={'telefono': telefono, 'direccion': direccion}
                )

                # 2. Guardamos o buscamos el Producto
                producto_obj, _ = Producto.objects.get_or_create(
                    nombre=sabor, defaults={'precio': 10000}
                )

                # 3. Creamos el Pedido Oficial
                nuevo_pedido = Pedido.objects.create(
                    cliente=cliente_obj,
                    estado='RECIBIDO',
                    total=precio,
                    fecha_entrega=fecha,
                    tematica=tematica
                )

                # 4. Detalle del Pedido
                DetallePedido.objects.create(
                    pedido=nuevo_pedido,
                    producto=producto_obj,
                    cantidad=cantidad,
                    subtotal=precio
                )

                # Limpiamos la memoria para el próximo cliente
                request.session.flush() 
                
                return JsonResponse({'respuesta': f"✅ ¡Listo {nombre}! Tu pedido #{nuevo_pedido.codigo_pedido} ha sido agendado para el {fecha} en {direccion}. ¡Gracias por preferirnos!"})


            # --- 1. MODO NORMAL (COTIZACIÓN CON IA) ---
            # Aquí entra si step == 'cotizando'
            analisis = consultar_wit(mensaje_usuario)
            
            if analisis:
                if analisis.get('sabor'): request.session['sabor'] = analisis['sabor']
                if analisis.get('cantidad'): request.session['cantidad'] = analisis['cantidad']
                if analisis.get('fecha'): request.session['fecha'] = analisis['fecha']
                if analisis.get('tematica'): request.session['tematica'] = analisis['tematica']

            # Variables actuales
            sabor = request.session.get('sabor')
            cantidad = request.session.get('cantidad')
            fecha = request.session.get('fecha')
            tematica = request.session.get('tematica')

            # Comandos de limpieza
            if 'borrar' in mensaje_usuario.lower() or 'otra' in mensaje_usuario.lower():
                request.session.flush()
                respuesta_texto = "¡Empecemos de cero! ¿Qué torta buscas?"

            # Si ya tenemos TODOS los datos de la torta, pedimos confirmación
            elif sabor and cantidad and fecha and tematica:
                precio = 10000 + (cantidad * 1500)
                msg_clean = mensaje_usuario.lower().strip()
                palabras_si = ['si', 'sí', 'confirmo', 'ok', 'dale', 'bueno', 'correcto', 'sii', 'yep']

                # SI EL USUARIO DICE QUE SÍ -> CAMBIAMOS DE MODO
                if msg_clean in palabras_si or any(x in msg_clean for x in palabras_si):
                    request.session['step'] = 'pidiendo_nombre' # <--- AQUÍ ACTIVAMOS EL MODO FORMULARIO
                    respuesta_texto = "¡Excelente elección! 📝 Para finalizar, necesito tus datos. ¿Cuál es tu **Nombre**?"
                
                # Si dice que no
                elif msg_clean in ['no', 'cancelar'] or msg_clean.startswith('no '):
                    request.session.flush()
                    respuesta_texto = "Entendido, pedido cancelado. 👋 Escribe algo para comenzar de nuevo."
                
                # Si no confirma aún, mostramos resumen
                else:
                    respuesta_texto = (
                        f"Resumen: Torta de 🍰 **{sabor}** ({tematica}) para el 📅 **{fecha}**.\n"
                        f"Personas: 👥 **{cantidad}** | Total: 💰 **${precio:,}**.\n"
                        "¿Deseas confirmar el pedido? (Responde Sí)"
                    )

            # Si faltan datos, la IA pregunta
            elif not sabor: respuesta_texto = "¡Hola! 👋 ¿De qué sabor buscas tu torta?"
            elif not cantidad: respuesta_texto = f"Ok, de {sabor}. ¿Para cuántas personas?"
            elif not fecha: respuesta_texto = f"¿Para qué fecha la necesitas?"
            elif not tematica: respuesta_texto = f"Anotado para el {fecha}. ¿Qué diseño o temática te gustaría?"

            return JsonResponse({'respuesta': respuesta_texto})

        except Exception as e:
            print(f"ERROR: {e}")
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Método no permitido'}, status=405)

@staff_member_required
def dashboard_admin(request):
    # 1. Datos Generales
    total_pedidos = Pedido.objects.count()
    ganancia_total = Pedido.objects.aggregate(Sum('total'))['total__sum'] or 0

    # 2. Ventas del Mes Actual
    hoy = datetime.date.today()
    pedidos_mes = Pedido.objects.filter(
        fecha_pedido__year=hoy.year, 
        fecha_pedido__month=hoy.month
    )
    ventas_mes = pedidos_mes.aggregate(Sum('total'))['total__sum'] or 0
    cantidad_mes = pedidos_mes.count()

    # 3. Datos para el Gráfico (Estados)
    datos_estados = Pedido.objects.values('estado').annotate(dcount=Count('estado'))

    # Listas para Chart.js
    labels_estados = [item['estado'] for item in datos_estados]
    data_estados = [item['dcount'] for item in datos_estados]

    context = {
        'total_pedidos': total_pedidos,
        'ganancia_total': ganancia_total,
        'ventas_mes': ventas_mes,
        'cantidad_mes': cantidad_mes,
        'labels_estados': labels_estados,
        'data_estados': data_estados,
    }

    return render(request, 'pedidos/dashboard.html', context)
