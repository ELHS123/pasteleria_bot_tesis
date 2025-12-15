from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime, date
from .wit_client import consultar_wit
from .models import Cliente, Pedido, DetallePedido, Producto
from django.db.models import Sum, Count
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404




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
            mensaje_usuario = data.get('mensaje', '').lower().strip()
            
            # --- 1. BOTÓN DE PÁNICO (Se mantiene) ---
            palabras_reinicio = ['reiniciar', 'inicio', 'reset', 'borrar', 'cancelar todo']
            if any(p in mensaje_usuario for p in palabras_reinicio):
                request.session.flush()
                return JsonResponse({'respuesta': "🔄 ¡Sistema reiniciado! Memoria borrada. 👋 ¿Qué torta buscas hoy?"})

            # --- 2. MÁQUINA DE ESTADOS (Datos personales) ---
            step = request.session.get('step', 'cotizando') 
            
            if step == 'pidiendo_nombre':
                request.session['nombre_cliente'] = data.get('mensaje', '') 
                request.session['step'] = 'pidiendo_telefono'
                return JsonResponse({'respuesta': f"Un gusto. 📱 ¿Me podrías dar tu número de teléfono?"})

            elif step == 'pidiendo_telefono':
                request.session['telefono_cliente'] = mensaje_usuario
                request.session['step'] = 'pidiendo_direccion'
                return JsonResponse({'respuesta': "Anotado. 📍 Por último, ¿cuál es la dirección para el despacho?"})

            elif step == 'pidiendo_direccion':
                direccion = data.get('mensaje', '')
                nombre = request.session.get('nombre_cliente')
                telefono = request.session.get('telefono_cliente')
                sabor = request.session.get('sabor')
                cantidad = request.session.get('cantidad')
                fecha = request.session.get('fecha')
                tematica = request.session.get('tematica')
                precio = 10000 + (cantidad * 1500)

                # Guardado
                cliente_obj, _ = Cliente.objects.update_or_create(nombre=nombre, defaults={'telefono': telefono, 'direccion': direccion})
                producto_obj, _ = Producto.objects.get_or_create(nombre=sabor, defaults={'precio': 10000})
                nuevo_pedido = Pedido.objects.create(cliente=cliente_obj, estado='RECIBIDO', total=precio, fecha_entrega=fecha, tematica=tematica)
                DetallePedido.objects.create(pedido=nuevo_pedido, producto=producto_obj, cantidad=cantidad, subtotal=precio)

                request.session.flush()
                return JsonResponse({'respuesta': f"✅ ¡Listo {nombre}! Pedido #{nuevo_pedido.id} agendado para el {fecha}. ¡Gracias!"})


            # --- 3. INTELIGENCIA ARTIFICIAL (Wit.ai) ---
            analisis = consultar_wit(mensaje_usuario)
            
            if analisis:
                # A. DATOS BÁSICOS (Volvemos a lo simple y seguro)
                if analisis.get('sabor'): request.session['sabor'] = analisis['sabor'].title()
                
                # --- AQUÍ ESTÁ EL CAMBIO (Revertido a simple) ---
                # Aceptamos la fecha tal cual viene, sin validaciones complejas
                if analisis.get('fecha'): request.session['fecha'] = analisis['fecha']
                # ------------------------------------------------

                if analisis.get('tematica'): request.session['tematica'] = analisis['tematica']
                
                # B. LÍMITE DE PERSONAS (Esto sí lo dejamos porque funcionaba bien)
                if analisis.get('cantidad'):
                    try:
                        cant = int(analisis['cantidad'])
                        if cant > 50:
                            return JsonResponse({'respuesta': f"¡Wow! 🤯 {cant} personas es demasiado. Máximo **50 personas**. Intenta un número menor."})
                        else:
                            request.session['cantidad'] = cant
                    except ValueError:
                        pass

            # --- 4. RESPUESTAS ---
            sabor = request.session.get('sabor')
            cantidad = request.session.get('cantidad')
            fecha = request.session.get('fecha')
            tematica = request.session.get('tematica')

            if sabor and cantidad and fecha and tematica:
                precio = 10000 + (cantidad * 1500)
                palabras_si = ['si', 'sí', 'confirmo', 'ok', 'dale', 'bueno']
                
                if any(x in mensaje_usuario for x in palabras_si):
                    request.session['step'] = 'pidiendo_nombre'
                    return JsonResponse({'respuesta': "¡Excelente! 📝 Para finalizar, necesito tus datos. ¿Cuál es tu **Nombre**?"})
                elif 'no' in mensaje_usuario:
                    request.session.flush()
                    return JsonResponse({'respuesta': "Pedido cancelado. 👋 Escribe 'Hola' para empezar de nuevo."})
                else:
                    return JsonResponse({'respuesta': f"Resumen: Torta de 🍰 **{sabor}** ({tematica}) para el 📅 **{fecha}**.\nPersonas: 👥 **{cantidad}** | Total: 💰 **${precio:,}**.\n¿Confirmas? (Responde Sí)"})

            elif not sabor: return JsonResponse({'respuesta': "¡Hola! 👋 ¿De qué sabor buscas tu torta?"})
            elif not cantidad: return JsonResponse({'respuesta': f"Ok, de {sabor}. ¿Para cuántas personas? (Máx 50)"})
            elif not fecha: return JsonResponse({'respuesta': f"¿Para qué fecha la necesitas?"})
            elif not tematica: return JsonResponse({'respuesta': f"Anotado para el {fecha}. ¿Qué diseño te gustaría?"})

            return JsonResponse({'respuesta': "No entendí bien. ¿Podrías repetir?"})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Método no permitido'}, status=405)

@staff_member_required
def dashboard_admin(request):
    # 1. Obtener todos los pedidos
    pedidos = Pedido.objects.all()
    
    # 2. CALCULAR GANANCIA HISTÓRICA (Suma total)
    total_ventas = pedidos.filter(estado='ENTREGADO').aggregate(Sum('total'))['total__sum'] or 0
    
    # 3. CALCULAR VENTAS DEL MES (Forma segura para Texto)
    hoy = date.today()
    mes_iso = hoy.strftime('%Y-%m')   # Busca formato '2025-12' (Chatbot)
    mes_lat = hoy.strftime('/%m/%Y')  # Busca formato '/12/2025' (Manual)
    
    ventas_mes = 0
    # Recorremos los pedidos entregados y sumamos solo si coinciden con este mes
    for p in pedidos.filter(estado='ENTREGADO'):
        fecha_txt = str(p.fecha_entrega) # Nos aseguramos que sea texto
        if mes_iso in fecha_txt or mes_lat in fecha_txt:
            ventas_mes += p.total

    # 4. CALCULAR CANTIDADES (Para los Gráficos)
    c_recibido = pedidos.filter(estado='RECIBIDO').count()
    c_preparacion = pedidos.filter(estado='EN_PRODUCCION').count()
    c_listo = pedidos.filter(estado='LISTO').count()
    c_entregado = pedidos.filter(estado='ENTREGADO').count()
    c_cancelado = pedidos.filter(estado='CANCELADO').count()
    
    # Lista para los gráficos
    conteo_estados = [c_recibido, c_preparacion, c_listo, c_entregado, c_cancelado]
    
    context = {
        'total_ventas': total_ventas, 
        'ventas_mes': ventas_mes,     
        'conteo_estados': conteo_estados, 
    }
    
    return render(request, 'pedidos/dashboard.html', context)


@staff_member_required
def comprobante_pedido(request, pedido_id):
    # Buscamos el pedido (o error 404 si no existe)
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    # Buscamos los productos de ese pedido
    detalles = DetallePedido.objects.filter(pedido=pedido)
    
    context = {
        'pedido': pedido,
        'detalles': detalles,
        'hoy': date.today()
    }
    return render(request, 'pedidos/comprobante.html', context)
