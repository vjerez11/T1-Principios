import socket
import threading
from cartas import *
from utilidades import *

HOST = '127.0.0.1'
PORT = 8889

clientes_conectados = {}  # Ahora guarda {socket_conn: correo} para identificar clientes
ejecutivos_conectados = {}  # Ahora guarda {socket_conn: correo} para identificar ejecutivos
cartas_disponibles = []
# Diccionario para mantener las conversaciones activas
salas = {}  # {correo_cliente: {correo_ejecutivo, mensajes: []}}


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
            if mensaje.strip().lower() == ":catalog":
                # Obtener catálogo
                catalogo = obtener_catalogo()
                print(catalogo)
                try:
                    cliente_socket.send(f"[Catálogo disponible]:\n{catalogo}".encode('utf-8'))
                except:
                    cliente_socket.close()
                    break
                continue

            if mensaje.startswith(":buy"):
                try:
                    partes = mensaje.split(" ", 2)
                    nombre_carta = partes[1]
                    precio = float(partes[2])

                    # Crear la carta
                    publicar_carta(nombre_carta, precio)

                    # Buscar cliente en la misma sala
                    for sock, usuario in salas[sala]:
                        if sock != cliente_socket:
                            correo_cliente = None
                            for s, correo in clientes_conectados.items():
                                if s == sock:
                                    correo_cliente = correo
                                    break
                            
                            if correo_cliente:
                                # Buscar la carta recién publicada
                                cartas = cargar_json("cartas.json")
                                carta = next((c for c in cartas if c["nombre"] == nombre_carta and not c["disponible"]), None)

                                if not carta:
                                    carta = next((c for c in cartas if c["nombre"] == nombre_carta and c["disponible"]), None)

                                if carta:
                                    id_carta = carta["id"]
                                    respuesta = comprar_carta(correo_cliente, id_carta)
                                    cliente_socket.send(respuesta.encode('utf-8'))
                                    sock.send(f"Has comprado la carta '{nombre_carta}' por ${precio}".encode('utf-8'))
                                else:
                                    cliente_socket.send("Carta no encontrada para compra.".encode('utf-8'))

                except Exception as e:
                    cliente_socket.send(f"Error al procesar compra: {e}".encode('utf-8'))
                continue
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
        
        data = conn.recv(1024).decode('utf-8')
        
        if not data:
            return

        try:
            mensaje = json.loads(data)

        except json.JSONDecodeError:
            mensaje = {}


        if mensaje.get("modo") == "chat":
            enviar_mensaje_cliente(conn)
            return
        if mensaje.get("modo") == "chat-ejecutivo":
            enviar_mensaje_ejecutivo(conn)
            return

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