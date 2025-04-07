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
    
    resultado = {
        "acciones": historial_cliente,
        "compras": compras_cliente,
        "devoluciones": devoluciones_cliente
    }
    
    return json.dumps(resultado, indent=4)

def obtener_catalogo():
    cartas = cargar_json("cartas.json")
    catalogo = [carta for carta in cartas if carta.get("disponible", True)]
    return json.dumps(catalogo, indent=4)

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
    # Por ahora solo guardamos en el historial
    historial_entrada = {
        "accion": "mensaje_a_ejecutivo",
        "correo_cliente": correo_cliente,
        "mensaje": mensaje,
        "fecha": datetime.now().isoformat()
    }
    guardar_historial(historial_entrada)
    
    # Notificar a los ejecutivos conectados
    for conn, correo in ejecutivos_conectados.items():
        try:
            notificacion = {
                "tipo": "notificacion",
                "mensaje": f"Mensaje de {correo_cliente}: {mensaje}"
            }
            conn.send(json.dumps(notificacion).encode('utf-8'))
        except:
            pass
    
    return "Mensaje enviado a los ejecutivos disponibles."

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
            
            elif accion == "6":  # Contactar ejecutivo
                mensaje = msg.get("mensaje")
                respuesta = enviar_mensaje_ejecutivo(correo, mensaje)

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
                cliente_correo = input("Correo del cliente: ")  # Debería ser parte del comando
                respuesta = obtener_historial_cliente(cliente_correo)
            
            elif comando == ":catalogue":
                respuesta = obtener_catalogo()
            
            elif comando == ":buy":
                # En una versión real, se solicitaría el correo del cliente y el ID de la carta
                respuesta = "Funcionalidad no implementada: ejecutivo comprando para cliente"
            
            elif comando == ":publish":
                # En una versión real, se solicitarían los detalles de la carta
                nombre = input("Nombre de la carta: ")  # Debería ser parte del comando
                precio = input("Precio de la carta: ")  # Debería ser parte del comando
                respuesta = publicar_carta(nombre, float(precio))
            
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
    for archivo in ["usuarios.json", "ejecutivos.json", "historial.json", "compras.json", "devoluciones.json"]:
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
        print("[SERVIDOR] Ahora solo se permite el registro de clientes")

        while True:
            conn, addr = s.accept()
            thread = threading.Thread(target=manejar_cliente, args=(conn, addr))
            thread.start()
            print(f"[SERVIDOR] Total conexiones activas: {threading.active_count() - 1}")

if __name__ == "__main__":
    main()