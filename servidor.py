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
salas = {}  # {correo_cliente: {correo_ejecutivo, mensajes: []}}

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

def broadcast(sala, mensaje, remitente_socket):
    for cliente_socket, _ in salas[sala]:
        if cliente_socket != remitente_socket:
            try:
                cliente_socket.send(mensaje.encode('utf-8'))
            except:
                cliente_socket.close()
                salas[sala] = [(sock, user) for sock, user in salas[sala] if sock != cliente_socket]


def obtener_sala():
    i = 1
    while i in salas:
        i += 1
    return i

def obtener_nombre_por_correo(correo):
    archivos =["usuarios.json", "ejecutivos.json"]
    for archivo in archivos:
        with open(archivo, 'r') as f:
            clientes = json.load(f)
            for cliente in clientes:
                if cliente['correo'] == correo:
                    return cliente['nombre']
    return None


def enviar_mensaje_ejecutivo(cliente_socket):
    try:
        # Recibir username y sala
        correo = cliente_socket.recv(1024).decode('utf-8')
        username = obtener_nombre_por_correo(correo)
        cliente_socket.send(str(username).encode('utf-8'))  

        cliente_socket.send("Sala: ".encode('utf-8'))
        sala = cliente_socket.recv(1024).decode('utf-8')

        # Crear sala si no existe
        
        if sala not in salas:
            salas[sala] = []
        salas[sala].append((cliente_socket, username))

        # Notificar a la sala que el usuario entró
        broadcast(sala, f"[{username} se ha unido a la sala]", cliente_socket)

        # Bucle de recepción de mensajes
        while True:
            mensaje = cliente_socket.recv(1024).decode('utf-8')
            if mensaje.lower() == "/salir":
                break
            broadcast(sala, f"{username}: {mensaje}", cliente_socket)

    except Exception as e:
        print(f"Error en chat ejecutivo: {e}")

    finally:
        # Quitar usuario de la sala
        for sala_actual in list(salas):
            salas[sala_actual] = [(sock, user) for sock, user in salas[sala_actual] if sock != cliente_socket]
            if not salas[sala_actual]:
                del salas[sala_actual]
        cliente_socket.close()

def enviar_mensaje_cliente(cliente_socket):
    try:

        # Recibir username
        correo = cliente_socket.recv(1024).decode('utf-8')
        username = obtener_nombre_por_correo(correo)   
        sala = str(obtener_sala())
        cliente_socket.send(str(sala).encode('utf-8'))
        cliente_socket.send(str(username).encode('utf-8'))
        
        # Crear sala si no existe
        
        if sala not in salas:
            salas[sala] = []
        salas[sala].append((cliente_socket, username))

        # Notificar a la sala que el usuario entró
        broadcast(sala, f"[{username} se ha unido a la sala]", cliente_socket)

        # Bucle de recepción de mensajes
        while True:
            mensaje = cliente_socket.recv(1024).decode('utf-8')
            if mensaje.lower() == "/salir":
                break
            broadcast(sala, f"{username}: {mensaje}", cliente_socket)

    except Exception as e:
        print(f"Error en chat ejecutivo: {e}")

    finally:
        # Quitar usuario de la sala
        for sala_actual in list(salas):
            salas[sala_actual] = [(sock, user) for sock, user in salas[sala_actual] if sock != cliente_socket]
            if not salas[sala_actual]:
                del salas[sala_actual]
        cliente_socket.close()





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
                respuesta = enviar_mensaje_cliente(conn)
            
            elif accion == "7":  # Ver histórico de chats
                pass
            
            
            elif accion == "terminar_chat":  # Terminar un chat activo
                pass

            conn.send(respuesta.encode('utf-8'))
            
        except Exception as e:
            conn.send(f"Error al procesar solicitud: {e}".encode('utf-8'))
            break

def manejar_ejecutivo(conn, correo):   
    while True:
        try:
            # Primero, recibir el primer mensaje para ver si es un "modo chat"
            data = conn.recv(1024).decode('utf-8')
            
            if not data:
                return

            # Intentamos decodificar el mensaje JSON
            try:
                msg = json.loads(data)

            except json.JSONDecodeError:
                msg = {}

        # Si es un socket de chat, lo mandamos directo a la función de chat

            if msg.get("modo") == "chat":
                enviar_mensaje_ejecutivo(conn)  # Tu función del chat (ya la tienes)
                return

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

            #elif comando == ":chats":
                #mensaje = msg.get("mensaje")
                #respuesta = enviar_mensaje_ejecutivo(conn)

            
            elif comando == ":active_chats":
                chats_activos_ejecutivo = {k: v for k, v in salas.items() if v["correo_ejecutivo"] == correo}
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
        # Primero, recibir el primer mensaje para ver si es un "modo chat"
        data = conn.recv(1024).decode('utf-8')
        if not data:
            return

        # Intentamos decodificar el mensaje JSON
        try:
            mensaje = json.loads(data)

        except json.JSONDecodeError:
            mensaje = {}

        # Si es un socket de chat, lo mandamos directo a la función de chat

        if mensaje.get("modo") == "chat":
            enviar_mensaje_cliente(conn)  # Tu función del chat (ya la tienes)
            return
        if mensaje.get("modo") == "chat-ejecutivo":
            enviar_mensaje_ejecutivo(conn)
            return

        # ----------- Lo que ya tenías (MENÚ NORMAL) ----------------
        accion = mensaje.get("accion")

        if accion == "registro":
            exito = manejar_registro(conn, mensaje)
            if exito:
                print(f"[SERVIDOR] Nuevo cliente registrado desde {addr}")
            return

        tipo = mensaje.get("tipo")

        if not autenticar(mensaje, tipo):
            conn.send("Credenciales inválidas.".encode('utf-8'))
            return

        if tipo == "cliente":
            correo = mensaje.get("correo")
            conn.send(f"Bienvenido, cliente {correo}".encode('utf-8'))
            clientes_conectados[conn] = correo
            manejar_cliente_regular(conn, correo)

        elif tipo == "ejecutivo":
            correo = mensaje.get("correo")
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