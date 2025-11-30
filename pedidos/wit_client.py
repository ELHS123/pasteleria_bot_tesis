import requests
from datetime import datetime

# --- TU TOKEN ---
# <--- ¡ASEGÚRATE DE QUE ESTÉ TU TOKEN AQUÍ!
WIT_TOKEN = "6JILEI2CGHG6JYV3ZS7OWG6GN3Z5TD2X"


def consultar_wit(mensaje_usuario):
    url = f"https://api.wit.ai/message?v=20230215&q={mensaje_usuario}"
    headers = {'Authorization': f'Bearer {WIT_TOKEN}'}

    try:
        response = requests.get(url, headers=headers)
        data = response.json()

        resultado = {
            'intencion': 'cotizar_torta',
            'sabor': None,
            'cantidad': None,
            'fecha': None,  # Valor nuevo agregado
            'tematica': None  # Valor nuevo agregado
        }

        # 1 Intención
        if data.get('intents') and len(data['intents']) > 0:
            resultado['intencion'] = data['intents'][0]['name']

        entities = data.get('entities', {})

        # 2 Sabor (sabor)
        sabor_data = entities.get('sabor:sabor', [])
        if sabor_data:
            resultado['sabor'] = sabor_data[0]['value']

        # 3 Cantidad (cantidad)
        numeros = entities.get('wit$number:number', [])
        max_valor = 0
        for n in numeros:
            if float(n['value']) > max_valor:
                max_valor = float(n['value'])
        if max_valor > 1:
            resultado['cantidad'] = int(max_valor)

        # 4 Fecha (datetime)
        fecha_data = entities.get('wit$datetime:datetime', [])
        if fecha_data:
            fecha_iso = fecha_data[0]['value']
            try:
                fecha_obj = datetime.strptime(fecha_iso[:10], "%Y-%m-%d")
                resultado['fecha'] = fecha_obj.strftime("%d/%m/%Y")
            except:
                resultado['fecha'] = fecha_data[0]['body']

        # 5 Tematica (tematica)
        tema_data = entities.get('tematica:tematica', [])
        if tema_data:
            resultado['tematica'] = tema_data[0]['value']
        return resultado

    except Exception as e:
        print(f"Error Wit: {e}")
        return None
