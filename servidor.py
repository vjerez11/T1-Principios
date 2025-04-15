import socket
import threading
import json
import os
from datetime import datetime

HOST = '127.0.0.1'
PORT = 8889

clientes_conectados = {}  # Ahora guarda {socket_conn: correo} para identificar clientes
ejecutivos_conectados = {}  # Ahora guarda {socket_conn: correo} para identificar ejecutivos
cartas_disponibles = []
# Diccionario para mantener las conversaciones activas
chat_activos = {}  # {correo_cliente: {correo_ejecutivo, mensajes: []}}

def cargar_json(nombre_archivo):
    if not os.path.exists(nombre_archivo):
        if nombre_archivo == "cartas.json":
            cartas_iniciales = [
                {"id": 1, "nombre": "Carta Común", "precio": 5.00, "disponible": True},
                {"id": 2, "nombre": "Carta Rara", "precio": 15.00, "disponible": True},
                {"id": 3, "nombre": "Carta Legendaria", "precio": 50.00, "disponible": True}
            ]
            with open(nombre_archivo, 'w') as f:
                json.dump(cartas_iniciales, f, indent=4)
            return cartas_iniciales
        return []
    with open(nombre_archivo, 'r') as f:
        return json.load(f)

def guardar_json(nombre_archivo, datos):
    with open(nombre_archivo, 'w') as f:
        json.dump(datos, f, indent=4)

def guardar_historial(entrada):
    historial = cargar_json("historial.json")
    historial.append(entrada)
    guardar_json("historial.json", historial)

def guardar_chat(correo_cliente, correo_ejecutivo, mensaje, enviado_por):
    chats = cargar_json("chats.json")
    
    # Buscar un chat existente entre este cliente y ejecutivo
    chat_existente = None
    for chat in chats:
        if chat["cliente"] == correo_cliente and chat["ejecutivo"] == correo_ejecutivo:
            chat_existente = chat
            break
    
    # Si no existe, crear uno nuevo
    if not chat_existente:
        chat_existente = {
            "cliente": correo_cliente,
            "ejecutivo": correo_ejecutivo,
            "mensajes": []
        }
        chats.append(chat_existente)
    
    # Añadir el nuevo mensaje
    nuevo_mensaje = {
        "fecha": datetime.now().isoformat(),
        "emisor": enviado_por,
        "contenido": mensaje
    }
    chat_existente["mensajes"].append(nuevo_mensaje)
    
    # Guardar en el archivo
    guardar_json("chats.json", chats)
    
    return True

def autenticar(usuario, tipo):
    lista = cargar_json("usuarios.json" if tipo == "cliente" else "ejecutivos.json")
    for u in lista:
        if u["correo"] == usuario["correo"] and u["clave"] == usuario["clave"]:
            return True
    return False

def registrar_usuario(datos, tipo):
    if tipo != "cliente":
        return False, "Solo se permite el registro de clientes."

    archivo = "usuarios.json"
    usuarios = cargar_json(archivo)

    for u in usuarios:
        if u.get("correo") == datos["correo"]:
            return False, "Ya existe un cliente con ese correo electrónico."

    nuevo_usuario = {
        "nombre": datos["nombre"],
        "correo": datos["correo"],
        "clave": datos["clave"],
        "fecha_registro": datetime.now().isoformat()
    }

    usuarios.append(nuevo_usuario)
    guardar_json(archivo, usuarios)

    historial_entrada = {
        "accion": "registro_cliente",
        "correo": datos["correo"],
        "fecha": datetime.now().isoformat()
    }
    guardar_historial(historial_entrada)

    return True, "Cliente registrado exitosamente."

def manejar_registro(conn, mensaje):
    try:
        accion = mensaje.get("accion")

        if accion == "registro":
            tipo = mensaje.get("tipo")
            datos = mensaje.get("datos")

            if tipo != "cliente":
                conn.send("Solo se permite el registro de clientes.".encode('utf-8'))
                return False

            if not isinstance(datos, dict) or not all(k in datos for k in ["nombre", "correo", "clave"]):
                conn.send("Datos incompletos o mal formateados para registro.".encode('utf-8'))
                return False

            exito, mensaje_respuesta = registrar_usuario(datos, tipo)
            conn.send(mensaje_respuesta.encode('utf-8'))
            return exito

        else:
            conn.send("Acción no reconocida.".encode('utf-8'))
            return False

    except Exception as e:
        conn.send(f"Error en registro: {e}".encode('utf-8'))
        return False

def cambiar_contrasena(correo, nueva_contrasena, tipo="cliente"):
    archivo = "usuarios.json" if tipo == "cliente" else "ejecutivos.json"
    usuarios = cargar_json(archivo)
    
    for usuario in usuarios:
        if usuario["correo"] == correo:
            usuario["clave"] = nueva_contrasena
            guardar_json(archivo, usuarios)
            
            historial_entrada = {
                "accion": "cambio_contrasena",
                "correo": correo,
                "fecha": datetime.now().isoformat()
            }
            guardar_historial(historial_entrada)
            
            return "Contraseña cambiada exitosamente."
    
    return "Error: Usuario no encontrado."

def obtener_historial_cliente(correo):

    historial = cargar_json("historial.json")
    compras = cargar_json("compras.json")
    devoluciones = cargar_json("devoluciones.json")
    
    historial_cliente = [h for h in historial if h.get("correo") == correo]
    compras_cliente = [c for c in compras if c.get("correo_cliente") == correo]
    devoluciones_cliente = [d for d in devoluciones if d.get("correo_cliente") == correo]
    
    # Ordenar todos los registros por fecha (más reciente primero)
    historial_cliente = sorted(historial_cliente, key=lambda x: x.get("fecha", ""), reverse=False)
    compras_cliente = sorted(compras_cliente, key=lambda x: x.get("fecha_compra", ""), reverse=False)
    devoluciones_cliente = sorted(devoluciones_cliente, key=lambda x: x.get("fecha_devolucion", ""), reverse=False)
    
    # Crear el encabezado con bordes decorativos
    resultado = "\n" + "=" * 60 + "\n"
    resultado += f"{'HISTORIAL DE CLIENTE:':^60}\n"
    resultado += f"{'- ' + correo + ' -':^60}\n"
    resultado += "=" * 60 + "\n\n"
    
    # Sección de acciones generales
    if historial_cliente:
        resultado += f"{'ACCIONES REALIZADAS:':^60}\n"
        resultado += "-" * 60 + "\n"
        for i, accion in enumerate(historial_cliente, 1):
            # Formatear la fecha para hacerla más legible
            fecha_str = accion.get("fecha", "Fecha desconocida").split("T")
            fecha = fecha_str[0]
            hora = fecha_str[1][:8] if len(fecha_str) > 1 else ""
            
            # Formatear la acción para mejor visualización
            nombre_accion = accion.get("accion", "desconocida").replace("_", " ").title()
            
            resultado += f"{i:2}. [{fecha} {hora}] {nombre_accion}\n"
            
            # Mostrar detalles adicionales si existen
            detalles = accion.get("detalles", {})
            if detalles:
                for clave, valor in detalles.items():
                    clave_formateada = clave.replace("_", " ").capitalize()
                    resultado += f"    ◦ {clave_formateada}: {valor}\n"
            resultado += "\n"
    else:
        resultado += "No hay acciones registradas para este cliente.\n\n"
    
    # Sección de compras
    if compras_cliente:
        resultado += f"{'COMPRAS REALIZADAS:':^60}\n"
        resultado += "-" * 60 + "\n"
        for i, compra in enumerate(compras_cliente, 1):
            # Formatear fecha de compra
            fecha_str = compra.get("fecha_compra", "Fecha desconocida").split("T")
            fecha = fecha_str[0]
            hora = fecha_str[1][:8] if len(fecha_str) > 1 else ""
            
            # Obtener detalles de la carta comprada
            carta_id = compra.get("carta_id", "?")
            nombre_carta = compra.get("nombre_carta", "Carta desconocida")
            precio = compra.get("precio", 0.0)
            
            resultado += f"{i:2}. [{fecha} {hora}] Compra: {nombre_carta}\n"
            resultado += f"    ◦ ID Carta: {carta_id}\n"
            resultado += f"    ◦ Precio pagado: ${precio:.2f}\n\n"
    else:
        resultado += "No hay compras registradas para este cliente.\n\n"
    
    # Sección de devoluciones
    if devoluciones_cliente:
        resultado += f"{'DEVOLUCIONES REALIZADAS:':^60}\n"
        resultado += "-" * 60 + "\n"
        for i, devolucion in enumerate(devoluciones_cliente, 1):
            # Formatear fecha de devolución
            fecha_str = devolucion.get("fecha_devolucion", "Fecha desconocida").split("T")
            fecha = fecha_str[0]
            hora = fecha_str[1][:8] if len(fecha_str) > 1 else ""
            
            # Obtener detalles de la carta devuelta
            carta_id = devolucion.get("carta_id", "?")
            nombre_carta = devolucion.get("nombre_carta", "Carta desconocida")
            monto_devuelto = devolucion.get("monto_devuelto", 0.0)
            
            resultado += f"{i:2}. [{fecha} {hora}] Devolución: {nombre_carta}\n"
            resultado += f"    ◦ ID Carta: {carta_id}\n"
            resultado += f"    ◦ Monto devuelto: ${monto_devuelto:.2f}\n"
            
            # Mostrar motivo de devolución si existe
            motivo = devolucion.get("motivo", "")
            if motivo:
                resultado += f"    ◦ Motivo: {motivo}\n"
            resultado += "\n"
    else:
        resultado += "No hay devoluciones registradas para este cliente.\n\n"
    
    # Pie de página
    resultado += "=" * 60 + "\n"
    resultado += f"{'Fin del historial':^60}\n"
    resultado += "=" * 60 + "\n"
    
    return resultado

def obtener_catalogo():
    cartas = cargar_json("cartas.json")
    catalogo = [carta for carta in cartas if carta.get("disponible", True)]
    
    # Crear el encabezado con bordes decorativos
    resultado = "\n" + "=" * 60 + "\n"
    resultado += f"{'CATÁLOGO DE CARTAS DISPONIBLES':^60}\n"
    resultado += "=" * 60 + "\n\n"
    
    # Verificar si hay cartas disponibles
    if not catalogo:
        resultado += "No hay cartas disponibles en el catálogo actualmente.\n\n"
    else:
        # Ordenar cartas por nombre para mejor visualización
        catalogo = sorted(catalogo, key=lambda x: x.get("nombre", ""), reverse=False)
        
        # Mostrar el número total de cartas disponibles
        resultado += f"{'Total de cartas disponibles: ' + str(len(catalogo)):^60}\n"
        resultado += "-" * 60 + "\n\n"
        
        # Mostrar cada carta con sus detalles
        for i, carta in enumerate(catalogo, 1):
            nombre = carta.get("nombre", "Sin nombre")
            carta_id = carta.get("id", "?")
            precio = carta.get("precio", 0.0)
            categoria = carta.get("categoria", "No especificada")
            rareza = carta.get("rareza", "Común")
            
            # Encabezado para cada carta
            resultado += f"{i:2}. {nombre} (ID: {carta_id})\n"
            resultado += f"    {'-' * 40}\n"
            
            # Detalles de la carta
            resultado += f"    ◦ Precio: ${precio:.2f}\n"
            resultado += f"    ◦ Categoría: {categoria}\n"
            resultado += f"    ◦ Rareza: {rareza}\n"
            
            # Mostrar descripción si existe
            descripcion = carta.get("descripcion", "")
            if descripcion:
                resultado += f"    ◦ Descripción: {descripcion}\n"
                
            # Mostrar atributos adicionales si existen
            atributos = carta.get("atributos", {})
            if atributos:
                resultado += f"    ◦ Atributos:\n"
                for clave, valor in atributos.items():
                    clave_formateada = clave.replace("_", " ").capitalize()
                    resultado += f"      - {clave_formateada}: {valor}\n"
            
            # Separador entre cartas
            resultado += "\n"
    
    # Pie de página
    resultado += "=" * 60 + "\n"
    resultado += f"{'Fin del catálogo':^60}\n"
    resultado += "=" * 60 + "\n"
    
    return resultado

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

def enviar_mensaje_ejecutivo(correo_cliente, mensaje):
    # Guardar en historial
    historial_entrada = {
        "accion": "mensaje_a_ejecutivo",
        "correo_cliente": correo_cliente,
        "mensaje": mensaje,
        "fecha": datetime.now().isoformat()
    }
    guardar_historial(historial_entrada)
    
    # Notificar a los ejecutivos conectados
    mensajes_enviados = 0
    for conn, correo_ejecutivo in ejecutivos_conectados.items():
        try:
            notificacion = {
                "tipo": "notificacion",
                "subtipo": "solicitud_chat",
                "mensaje": f"Solicitud de chat de {correo_cliente}: {mensaje}",
                "correo_cliente": correo_cliente
            }
            conn.send(json.dumps(notificacion).encode('utf-8'))
            mensajes_enviados += 1
        except:
            pass
    
    if mensajes_enviados > 0:
        return "Mensaje enviado a los ejecutivos disponibles. Espere a que un ejecutivo acepte el chat."
    else:
        return "No hay ejecutivos disponibles en este momento. Su mensaje ha sido registrado."

def notificar_chat_aceptado(correo_cliente, correo_ejecutivo):
    # Buscar el socket del cliente por su correo
    socket_cliente = None
    for conn, correo in clientes_conectados.items():
        if correo == correo_cliente:
            socket_cliente = conn
            break
    
    if socket_cliente:
        try:
            notificacion = {
                "tipo": "notificacion",
                "subtipo": "chat_aceptado",
                "mensaje": f"El ejecutivo {correo_ejecutivo} ha aceptado su solicitud de chat.",
                "correo_ejecutivo": correo_ejecutivo
            }
            socket_cliente.send(json.dumps(notificacion).encode('utf-8'))
            
            # Registrar inicio de chat en historial
            historial_entrada = {
                "accion": "inicio_chat",
                "correo_cliente": correo_cliente,
                "correo_ejecutivo": correo_ejecutivo,
                "fecha": datetime.now().isoformat()
            }
            guardar_historial(historial_entrada)
            
            # Crear o actualizar el chat activo
            if correo_cliente not in chat_activos:
                chat_activos[correo_cliente] = {"correo_ejecutivo": correo_ejecutivo, "mensajes": []}
            else:
                chat_activos[correo_cliente]["correo_ejecutivo"] = correo_ejecutivo
            
            return True
        except:
            return False
    return False

def enviar_mensaje_chat(correo_emisor, correo_destinatario, mensaje, tipo_emisor):
    # Determinar quién es el cliente y quién es el ejecutivo
    correo_cliente = correo_emisor if tipo_emisor == "cliente" else correo_destinatario
    correo_ejecutivo = correo_destinatario if tipo_emisor == "cliente" else correo_emisor
    
    # Registrar mensaje en archivo de chats
    guardar_chat(correo_cliente, correo_ejecutivo, mensaje, correo_emisor)
    
    # Agregar mensaje al chat activo
    if correo_cliente in chat_activos:
        chat_activos[correo_cliente]["mensajes"].append({
            "emisor": correo_emisor,
            "mensaje": mensaje,
            "fecha": datetime.now().isoformat()
        })
    
    # Determinar socket destino
    socket_destino = None
    if tipo_emisor == "cliente":
        # Buscar socket del ejecutivo
        for conn, correo in ejecutivos_conectados.items():
            if correo == correo_ejecutivo:
                socket_destino = conn
                break
    else:
        # Buscar socket del cliente
        for conn, correo in clientes_conectados.items():
            if correo == correo_cliente:
                socket_destino = conn
                break
    
    if socket_destino:
        try:
            mensaje_chat = {
                "tipo": "mensaje_chat",
                "emisor": correo_emisor,
                "mensaje": mensaje,
                "fecha": datetime.now().isoformat()
            }
            socket_destino.send(json.dumps(mensaje_chat).encode('utf-8'))
            return "Mensaje enviado."
        except:
            return "Error al enviar mensaje."
    
    return "Destinatario no conectado. Mensaje guardado."

def terminar_chat(correo_cliente, correo_ejecutivo, iniciado_por):
    # Registrar fin de chat en historial
    historial_entrada = {
        "accion": "fin_chat",
        "correo_cliente": correo_cliente,
        "correo_ejecutivo": correo_ejecutivo,
        "iniciado_por": iniciado_por,
        "fecha": datetime.now().isoformat()
    }
    guardar_historial(historial_entrada)
    
    # Eliminar chat activo
    if correo_cliente in chat_activos:
        del chat_activos[correo_cliente]
    
    # Notificar a la otra parte
    socket_destino = None
    if iniciado_por == "cliente":
        # Buscar socket del ejecutivo
        for conn, correo in ejecutivos_conectados.items():
            if correo == correo_ejecutivo:
                socket_destino = conn
                break
    else:
        # Buscar socket del cliente
        for conn, correo in clientes_conectados.items():
            if correo == correo_cliente:
                socket_destino = conn
                break
    
    if socket_destino:
        try:
            notificacion = {
                "tipo": "notificacion",
                "subtipo": "chat_terminado",
                "mensaje": f"El chat ha sido terminado por {iniciado_por}."
            }
            socket_destino.send(json.dumps(notificacion).encode('utf-8'))
        except:
            pass
    
    return "Chat terminado."

def obtener_historico_chats(correo, tipo):
    chats = cargar_json("chats.json")
    
    if tipo == "cliente":
        historico = [chat for chat in chats if chat["cliente"] == correo]
    else:
        historico = [chat for chat in chats if chat["ejecutivo"] == correo]
    
    return json.dumps(historico, indent=4)

def obtener_chat_activo(correo_cliente, correo_ejecutivo):
    # Buscar en memoria si existe un chat activo
    if correo_cliente in chat_activos and chat_activos[correo_cliente]["correo_ejecutivo"] == correo_ejecutivo:
        return json.dumps(chat_activos[correo_cliente], indent=4)
    
    # Si no está en memoria, verificar en archivo
    chats = cargar_json("chats.json")
    for chat in chats:
        if chat["cliente"] == correo_cliente and chat["ejecutivo"] == correo_ejecutivo:
            return json.dumps(chat, indent=4)
    
    return json.dumps({"error": "No existe un chat entre estos usuarios"})

def listar_compras_cliente(correo):
    compras = cargar_json("compras.json")
    compras_cliente = [c for c in compras if c.get("correo_cliente") == correo]
    return json.dumps(compras_cliente, indent=4)

def manejar_cliente_regular(conn, correo):
    while True:
        try:
            data = conn.recv(1024)
            if not data:
                break

            msg = json.loads(data.decode('utf-8'))
            accion = msg.get("accion")
            respuesta = "Acción no reconocida."

            if accion == "1":  # Cambio de contraseña
                nueva_contrasena = msg.get("contraseña")
                respuesta = cambiar_contrasena(correo, nueva_contrasena)
            
            elif accion == "2":  # Ver historial
                respuesta = obtener_historial_cliente(correo)
            
            elif accion == "3":  # Catálogo / Comprar
                respuesta = obtener_catalogo()
            
            elif accion == "comprar":  # Acción de compra
                id_carta = msg.get("id_carta")
                respuesta = comprar_carta(correo, id_carta)
            
            elif accion == "4":  # Listar compras para devolución
                respuesta = listar_compras_cliente(correo)
            
            elif accion == "devolver":  # Acción de devolución
                id_compra = msg.get("id_compra")
                respuesta = solicitar_devolucion(correo, id_compra)
            
            elif accion == "5":  # Mostrar compras pendientes de envío
                respuesta = listar_compras_cliente(correo)
            
            elif accion == "confirmar_envio":  # Confirmar envío
                id_compra = msg.get("id_compra")
                respuesta = confirmar_envio(correo, id_compra)
            
            elif accion == "6":  # Contactar ejecutivo (solicitar chat)
                mensaje = msg.get("mensaje")
                respuesta = enviar_mensaje_ejecutivo(correo, mensaje)
            
            elif accion == "7":  # Ver histórico de chats
                respuesta = obtener_historico_chats(correo, "cliente")
            
            elif accion == "enviar_mensaje_chat":  # Enviar mensaje en chat activo
                correo_ejecutivo = msg.get("correo_ejecutivo")
                mensaje = msg.get("mensaje")
                respuesta = enviar_mensaje_chat(correo, correo_ejecutivo, mensaje, "cliente")
            
            elif accion == "terminar_chat":  # Terminar un chat activo
                correo_ejecutivo = msg.get("correo_ejecutivo")
                respuesta = terminar_chat(correo, correo_ejecutivo, "cliente")

            conn.send(respuesta.encode('utf-8'))
            
        except Exception as e:
            conn.send(f"Error al procesar solicitud: {e}".encode('utf-8'))
            break

def manejar_ejecutivo(conn, correo):
    while True:
        try:
            data = conn.recv(1024)
            if not data:
                break

            msg = json.loads(data.decode('utf-8'))
            comando = msg.get("comando")
            respuesta = "Comando no reconocido."

            if comando == ":status":
                respuesta = f"Clientes conectados: {len(clientes_conectados)}\nEjecutivos conectados: {len(ejecutivos_conectados)}"
            
            elif comando == ":details":
                clientes_str = ", ".join(clientes_conectados.values())
                respuesta = f"Clientes conectados: {clientes_str if clientes_str else 'Ninguno'}"
            
            elif comando == ":history":
                cliente_correo = msg.get("correo_cliente")
                respuesta = obtener_historial_cliente(cliente_correo)
            
            elif comando == ":catalogue":
                respuesta = obtener_catalogo()
            
            elif comando == ":buy":
                # En una versión real, se solicitaría el correo del cliente y el ID de la carta
                cliente_correo = msg.get("correo_cliente")
                id_carta = msg.get("id_carta")
                if cliente_correo and id_carta:
                    respuesta = comprar_carta(cliente_correo, id_carta)
                else:
                    respuesta = "Datos incompletos para realizar la compra"
            
            elif comando == ":publish":
                nombre = msg.get("nombre")
                precio = msg.get("precio")
                if nombre and precio:
                    respuesta = publicar_carta(nombre, float(precio))
                else:
                    respuesta = "Datos incompletos para publicar carta"
            
            elif comando == ":chats":
                respuesta = obtener_historico_chats(correo, "ejecutivo")
            
            elif comando == ":accept_chat":
                cliente_correo = msg.get("correo_cliente")
                if notificar_chat_aceptado(cliente_correo, correo):
                    respuesta = f"Chat con {cliente_correo} iniciado correctamente"
                else:
                    respuesta = f"Error al iniciar chat con {cliente_correo}"
            
            elif comando == ":send_message":
                cliente_correo = msg.get("correo_cliente")
                mensaje = msg.get("mensaje")
                respuesta = enviar_mensaje_chat(correo, cliente_correo, mensaje, "ejecutivo")
            
            elif comando == ":end_chat":
                cliente_correo = msg.get("correo_cliente")
                respuesta = terminar_chat(cliente_correo, correo, "ejecutivo")
            
            elif comando == ":active_chats":
                chats_activos_ejecutivo = {k: v for k, v in chat_activos.items() if v["correo_ejecutivo"] == correo}
                respuesta = json.dumps(chats_activos_ejecutivo, indent=4)
            
            elif comando == ":disconnect":
                respuesta = "Desconectando..."
                conn.send(respuesta.encode('utf-8'))
                break
            
            elif comando == ":exit":
                respuesta = "Saliendo..."
                conn.send(respuesta.encode('utf-8'))
                break
            
            elif comando == ":create_user":
                respuesta = "Esta funcionalidad ha sido deshabilitada. Los usuarios ahora deben registrarse directamente como clientes."

            conn.send(respuesta.encode('utf-8'))
            
        except Exception as e:
            conn.send(f"Error al procesar comando: {e}".encode('utf-8'))
            break

def manejar_cliente(conn, addr):
    try:
        data = conn.recv(1024).decode('utf-8')
        if not data:
            return

        mensaje = json.loads(data)
        accion = mensaje.get("accion")

        if accion == "registro":
            exito = manejar_registro(conn, mensaje)
            if exito:
                print(f"[SERVIDOR] Nuevo cliente registrado desde {addr}")
            return

        tipo = mensaje.get("tipo")
        correo = mensaje.get("correo")

        if not autenticar(mensaje, tipo):
            conn.send("Credenciales inválidas.".encode('utf-8'))
            return

        if tipo == "cliente":
            conn.send(f"Bienvenido, cliente {correo}".encode('utf-8'))
            clientes_conectados[conn] = correo
            manejar_cliente_regular(conn, correo)
        elif tipo == "ejecutivo":
            conn.send(f"Bienvenido, ejecutivo {correo}".encode('utf-8'))
            ejecutivos_conectados[conn] = correo
            manejar_ejecutivo(conn, correo)
        else:
            conn.send("Tipo no reconocido.".encode('utf-8'))

    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        conn.close()
        if conn in clientes_conectados: del clientes_conectados[conn]
        if conn in ejecutivos_conectados: del ejecutivos_conectados[conn]
        print(f"[SERVIDOR] Conexión cerrada con {addr}")

def main():
    global cartas_disponibles
    cartas_disponibles = cargar_json("cartas.json")

    # Aseguramos que todos los archivos existan
    for archivo in ["usuarios.json", "ejecutivos.json", "historial.json", "compras.json", "devoluciones.json", "chats.json"]:
        if not os.path.exists(archivo):
            guardar_json(archivo, [])
    
    # Crear usuario ejecutivo por defecto si no existe ninguno
    ejecutivos = cargar_json("ejecutivos.json")
    if not ejecutivos:
        ejecutivo_default = {
            "nombre": "Ejecutivo Default",
            "correo": "ejecutivo@sistema.com",
            "clave": "admin123",
            "fecha_registro": datetime.now().isoformat()
        }
        ejecutivos.append(ejecutivo_default)
        guardar_json("ejecutivos.json", ejecutivos)
        print("[SERVIDOR] Se ha creado un ejecutivo por defecto: ejecutivo@sistema.com / admin123")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(10)
        print(f"[SERVIDOR] Corriendo en {HOST}:{PORT}")
        print("[SERVIDOR] Sistema de chat en vivo implementado")

        while True:
            conn, addr = s.accept()
            thread = threading.Thread(target=manejar_cliente, args=(conn, addr))
            thread.start()
            print(f"[SERVIDOR] Total conexiones activas: {threading.active_count() - 1}")

if __name__ == "__main__":
    main()