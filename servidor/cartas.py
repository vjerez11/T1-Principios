from utilidades import *
from datetime import datetime
from collections import defaultdict

def comprar_carta(correo, id_carta):
    cartas = cargar_json("cartas.json")
    compras = cargar_json("compras.json")
    
    for i, carta in enumerate(cartas):
        if carta["id"] == id_carta and carta.get("disponible", True):
            # Marcar la carta como no disponible
            cartas[i]["disponible"] = False
            guardar_json("cartas.json", cartas)
            
            # Registrar la compra
            nueva_compra = {
                "id_compra": len(compras) + 1,
                "id_carta": id_carta,
                "nombre_carta": carta["nombre"],
                "precio": carta["precio"],
                "correo_cliente": correo,
                "fecha_compra": datetime.now().isoformat(),
                "estado": "pendiente_envio"
            }
            
            compras.append(nueva_compra)
            guardar_json("compras.json", compras)
            
            historial_entrada = {
                "accion": "compra",
                "correo": correo,
                "id_carta": id_carta,
                "fecha": datetime.now().isoformat()
            }
            guardar_historial(historial_entrada)
            
            return f"Compra exitosa: {carta['nombre']} por ${carta['precio']}"
    
    return "Error: Carta no disponible o no encontrada."

def solicitar_devolucion(correo, id_compra):
    compras = cargar_json("compras.json")
    devoluciones = cargar_json("devoluciones.json")
    
    for i, compra in enumerate(compras):
        if compra["id_compra"] == id_compra and compra["correo_cliente"] == correo:
            if compra["estado"] == "enviado" or compra["estado"] == "pendiente_envio":
                # Registrar la devolución
                nueva_devolucion = {
                    "id_devolucion": len(devoluciones) + 1,
                    "id_compra": id_compra,
                    "correo_cliente": correo,
                    "fecha_solicitud": datetime.now().isoformat(),
                    "estado": "pendiente"
                }
                
                devoluciones.append(nueva_devolucion)
                guardar_json("devoluciones.json", devoluciones)
                
                # Actualizar estado de la compra
                compras[i]["estado"] = "en_devolucion"
                guardar_json("compras.json", compras)
                
                historial_entrada = {
                    "accion": "solicitud_devolucion",
                    "correo": correo,
                    "id_compra": id_compra,
                    "fecha": datetime.now().isoformat()
                }
                guardar_historial(historial_entrada)
                
                return "Solicitud de devolución registrada exitosamente."
            else:
                return f"Error: La compra está en estado '{compra['estado']}' y no puede ser devuelta."
    
    return "Error: Compra no encontrada o no pertenece a este cliente."



def obtener_catalogo():
    cartas = cargar_json("cartas.json")
    catalogo = [carta for carta in cartas if carta.get("disponible", True)]

    # Agrupar cartas por nombre
    agrupadas = defaultdict(list)
    for carta in catalogo:
        nombre = carta.get("nombre", "Sin nombre")
        agrupadas[nombre].append(carta)

    resultado = "\n" + "=" * 60 + "\n"
    resultado += f"{'CATÁLOGO DE CARTAS DISPONIBLES':^60}\n"
    resultado += "=" * 60 + "\n\n"

    if not agrupadas:
        resultado += "No hay cartas disponibles en el catálogo actualmente.\n\n"
    else:
        resultado += f"{'Total de tipos de cartas disponibles: ' + str(len(agrupadas)):^60}\n"
        resultado += "-" * 60 + "\n\n"

        for i, (nombre, cartas_con_mismo_nombre) in enumerate(sorted(agrupadas.items()), 1):
            ejemplo = cartas_con_mismo_nombre[0]
            stock = len(cartas_con_mismo_nombre)
            precio = ejemplo.get("precio", 0.0)
            categoria = ejemplo.get("categoria", "No especificada")
            rareza = ejemplo.get("rareza", "Común")

            resultado += f"{i:2}. {nombre}\n"
            resultado += f"    {'-' * 40}\n"
            resultado += f"    ◦ Stock: {stock}\n"
            resultado += f"    ◦ Precio: ${precio:.2f}\n"
            resultado += f"    ◦ Categoría: {categoria}\n"
            resultado += f"    ◦ Rareza: {rareza}\n"

            descripcion = ejemplo.get("descripcion", "")
            if descripcion:
                resultado += f"    ◦ Descripción: {descripcion}\n"

            atributos = ejemplo.get("atributos", {})
            if atributos:
                resultado += f"    ◦ Atributos:\n"
                for clave, valor in atributos.items():
                    clave_formateada = clave.replace("_", " ").capitalize()
                    resultado += f"      - {clave_formateada}: {valor}\n"

            resultado += "\n"

    resultado += "=" * 60 + "\n"
    resultado += f"{'Fin del catálogo':^60}\n"
    resultado += "=" * 60 + "\n"

    return resultado


def confirmar_envio(correo, id_compra):
    compras = cargar_json("compras.json")
    
    for i, compra in enumerate(compras):
        if compra["id_compra"] == id_compra and compra["correo_cliente"] == correo:
            if compra["estado"] == "pendiente_envio":
                # Actualizar estado de la compra
                compras[i]["estado"] = "enviado"
                compras[i]["fecha_envio"] = datetime.now().isoformat()
                guardar_json("compras.json", compras)
                
                historial_entrada = {
                    "accion": "confirmacion_envio",
                    "correo": correo,
                    "id_compra": id_compra,
                    "fecha": datetime.now().isoformat()
                }
                guardar_historial(historial_entrada)
                
                return "Envío confirmado exitosamente."
            else:
                return f"Error: La compra está en estado '{compra['estado']}' y no puede ser enviada."
    
    return "Error: Compra no encontrada o no pertenece a este cliente."

def publicar_carta(nombre, precio):
    cartas = cargar_json("cartas.json")
    
    # Encontrar el ID más alto y sumarle 1
    nuevo_id = 1
    if cartas:
        nuevo_id = max(carta["id"] for carta in cartas) + 1
    
    nueva_carta = {
        "id": nuevo_id,
        "nombre": nombre,
        "precio": float(precio),
        "disponible": True
    }
    
    cartas.append(nueva_carta)
    guardar_json("cartas.json", cartas)
    
    historial_entrada = {
        "accion": "publicacion_carta",
        "id_carta": nuevo_id,
        "fecha": datetime.now().isoformat()
    }
    guardar_historial(historial_entrada)
    
    return f"Carta publicada exitosamente. ID: {nuevo_id}"

def publicar_y_comprar(nombre, precio, correo_cliente):
    nueva_carta = publicar_carta(nombre, precio)
    if isinstance(nueva_carta, str):  # Si hubo error al publicar
        return nueva_carta
    id_carta = nueva_carta['id']
    resultado = comprar_carta(correo_cliente, id_carta)
    return resultado
