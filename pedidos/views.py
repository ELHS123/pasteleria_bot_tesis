from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import random  # Para respuestas aleatorias más naturales
from .wit_client import consultar_wit
from .models import Cliente, Pedido, DetallePedido, Producto


def index(request):
    request.session.flush()
    return render(request, 'pedidos/chat.html')


@csrf_exempt
def chat_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mensaje_usuario = data.get('mensaje', '')

            # 1. Consultar IA
            analisis = consultar_wit(mensaje_usuario)
            if not analisis:
                return JsonResponse({'respuesta': 'Tuve un pequeño problema técnico 🧠'}, status=500)

            # 2. Actualizar Memoria (Sessions)
            if analisis.get('sabor'):
                request.session['sabor'] = analisis['sabor']
            if analisis.get('cantidad'):
                request.session['cantidad'] = analisis['cantidad']
            if analisis.get('fecha'):
                request.session['fecha'] = analisis['fecha']
            if analisis.get('tematica'):
                request.session['tematica'] = analisis['tematica']

            # Recuperar estado actual
            sabor = request.session.get('sabor')
            cantidad = request.session.get('cantidad')
            fecha = request.session.get('fecha')
            tematica = request.session.get('tematica')

            respuesta_texto = ""

            # --- LÓGICA CONVERSACIONAL NATURAL ---

            # Caso: Reiniciar
            if 'borrar' in mensaje_usuario.lower() or 'otra' in mensaje_usuario.lower():
                request.session.flush()
                respuesta_texto = "¡Claro! Empecemos de nuevo. ¿Qué tienes en mente?"

            # CASO FINAL: Tenemos TODOS los datos
            elif sabor and cantidad and fecha and tematica:
                # Precio base + extra si es temática compleja (lógica simple para MVP)
                precio = 10000 + (cantidad * 1500)

                # Confirmación
                if 'si' in mensaje_usuario.lower() or 'confirmo' in mensaje_usuario.lower():

                    # --- GUARDAR EN BD ---
                    cliente_obj, _ = Cliente.objects.get_or_create(
                        nombre="Usuario Web")

                    # Guardamos o buscamos el producto
                    producto_obj, _ = Producto.objects.get_or_create(
                        nombre=sabor, defaults={'precio': 10000}
                    )

                    nuevo_pedido = Pedido.objects.create(
                        cliente=cliente_obj,
                        estado='RECIBIDO',
                        total=precio,
                        # AQUÍ GUARDAMOS LOS NUEVOS DATOS
                        fecha_entrega=fecha,
                        tematica=tematica
                    )

                    DetallePedido.objects.create(
                        pedido=nuevo_pedido,
                        producto=producto_obj,
                        cantidad=cantidad,
                        subtotal=precio
                    )

                    respuestas_exito = [
                        f"✅ ¡Listo! Pedido #{nuevo_pedido.codigo_pedido} agendado. Será de {sabor} con diseño de {tematica}.",
                        f"🎉 ¡Excelente! Ya anoté tu pedido de {sabor} para el {fecha}. Nos vemos pronto.",
                    ]
                    respuesta_texto = random.choice(respuestas_exito)
                    request.session.flush()

                else:
                    # Resumen antes de confirmar
                    respuesta_texto = (
                        f"Perfecto, revisemos: Torta de 🍰 **{sabor}** con diseño de 🎨 **{tematica}**.\n"
                        f"Sería para el 📅 **{fecha}** y calculo unas 👥 **{cantidad} personas**.\n"
                        f"El valor aproximado es 💰 **${precio:,}**.\n"
                        "¿Te parece bien para confirmar?"
                    )

            # CASOS FALTANTES (Preguntas Naturales)
            elif not sabor:
                opts = ["¡Hola! 👋 ¿De qué sabor te gustaría tu torta?",
                        "¿Qué tal? Cuéntame, ¿qué sabor estás buscando hoy?"]
                respuesta_texto = random.choice(opts)

            elif not cantidad:
                respuesta_texto = f"¡Qué rico {sabor}! 😋 ¿Para cuántas personas la necesitas más o menos?"

            elif not fecha:
                respuesta_texto = f"Entendido, para {cantidad} personas. 🗓️ ¿Para qué fecha la necesitas?"

            elif not tematica:
                respuesta_texto = f"Anotado para el {fecha}. 🎨 ¿Quieres algún diseño o temática especial? (Ej: Frozen, Spiderman, Clásica)"

            return JsonResponse({'respuesta': respuesta_texto})

        except Exception as e:
            print(f"ERROR: {e}")
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Método no permitido'}, status=405)
