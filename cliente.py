import socket
import json
import sys
import getpass
import time
import threading
import time

HOST = '127.0.0.1'
PORT = 8889

def enviar_mensaje(sock, mensaje):
    try:
        sock.send(json.dumps(mensaje).encode('utf-8'))
        respuesta = sock.recv(4096).decode('utf-8')  # Aumentado buffer para mensajes más grandes
        return respuesta
    except Exception as e:
        print(f"Error al enviar mensaje: {e}")
        return "Error de comunicación con el servidor"
    

def enviar_mensajes_chat(sock):
    while True:
        mensaje = input()
        sock.send(mensaje.encode('utf-8'))
        if mensaje.lower() == "/salir":
            break

def recibir_mensajes_chat(sock):
    while True:
        try:
            mensaje = sock.recv(1024).decode('utf-8')
            if mensaje:
                print(mensaje)
            else:
                break
        except:
            break

def iniciar_chat_ejecutivo(sock, correo):

    # Recibir y responder preguntas del servidor
    time.sleep(0.2)
    sock.send(correo.encode('utf-8'))
    username = sock.recv(1024).decode('utf-8')

    mensaje = sock.recv(1024).decode('utf-8')
    sala = input(mensaje)
    sock.send(sala.encode('utf-8'))

    print(f"Conectado como {username} en la sala '{sala}' — escribe '/salir' para salir.\n")

    threading.Thread(target=recibir_mensajes_chat, args=(sock,)).start()
    enviar_mensajes_chat(sock)
    sock.close()



def registro():
    print("\n=== Registro de Cliente ===")
    tipo = "cliente"
    
    nombre = input("Nombre completo: ")
    correo = input("Correo electrónico: ")
    clave = getpass.getpass("Contraseña: ")
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
            mensaje = {
                "accion": "registro",
                "tipo": tipo,
                "datos": {
                    "nombre": nombre,
                    "correo": correo,
                    "clave": clave
                }
            }
            respuesta = enviar_mensaje(s, mensaje)
            print(respuesta)
        except Exception as e:
            print(f"Error: {e}")

def login():
    print("\n=== Iniciar Sesión ===")
    tipo = input("Tipo (cliente/ejecutivo): ").lower()
    
    if tipo not in ["cliente", "ejecutivo"]:
        print("Tipo no válido. Debe ser 'cliente' o 'ejecutivo'.")
        return
    
    correo = input("Correo electrónico: ")
    clave = getpass.getpass("Contraseña: ")
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
            mensaje = {
                "tipo": tipo,
                "correo": correo,
                "clave": clave
            }
            s.send(json.dumps(mensaje).encode('utf-8'))
            respuesta = s.recv(1024).decode('utf-8')
            print(respuesta)
            
            if "Bienvenido" in respuesta:
                if tipo == "cliente":
                    cliente_menu(s, correo)
                else:
                    ejecutivo_menu(s, correo)
            
        except Exception as e:
            print(f"Error: {e}")



def iniciar_chat(sock, correo):

    time.sleep(0.2) #delay para asegurar que el socket esté listo
    sock.send(correo.encode('utf-8'))
    sala = sock.recv(1024).decode('utf-8')
    username = sock.recv(1024).decode('utf-8')
    print(f"Conectado como {username} en la sala {sala} — escribe '/salir' para salir.\n")

    threading.Thread(target=recibir_mensajes_chat, args=(sock,)).start()
    enviar_mensajes_chat(sock)
    sock.close()


def cliente_menu(sock, correo):
    chat_activo = None
    correo_ejecutivo = None
    
    while True:
        print("\n=== Menú Cliente ===")
        print("1. Cambio de Contraseña")
        print("2. Ver historial")
        print("3. Catálogo de productos / Comprar productos")
        print("4. Solicitar devolución")
        print("5. Confirmar envío")
        print("6. Contactar ejecutivo")
        print("7. Ver chat activo") # Nueva opción
        print("8. Ver histórico de chats") # Nueva opción
        print("9. Salir")
        
        opcion = input("\nSeleccione una opción: ")
        
        if opcion == "1":
            contraseña = getpass.getpass("Ingrese nueva contraseña: ")
            mensaje = {"accion": "1", "contraseña": contraseña}
            respuesta = enviar_mensaje(sock, mensaje)
            print(respuesta)

        elif opcion == "2":
            mensaje = {"accion": "2"}
            respuesta = enviar_mensaje(sock, mensaje)
            print(respuesta)
            input("\nPresione Enter para continuar...")
        
        elif opcion == "3":
            # Primero obtenemos el catálogo
            mensaje = {"accion": "3"}
            respuesta = enviar_mensaje(sock, mensaje)
            print("\n=== Catálogo de Cartas ===")
            print(respuesta)
            
            # Luego preguntamos si quiere comprar
            id_carta = input("\nIngrese ID de carta para comprar (o 0 para cancelar): ")
            if id_carta != "0":
                try:
                    mensaje = {"accion": "comprar", "id_carta": int(id_carta)}
                    respuesta = enviar_mensaje(sock, mensaje)
                    print(respuesta)
                except ValueError:
                    print("ID de carta debe ser un número.")
        
        elif opcion == "4":
            # Listar compras para devolución
            mensaje = {"accion": "4"}
            respuesta = enviar_mensaje(sock, mensaje)
            print("\n=== Sus Compras ===")
            print(respuesta)
            
            id_compra = input("\nIngrese ID de compra para devolver (o 0 para cancelar): ")
            if id_compra != "0":
                try:
                    mensaje = {"accion": "devolver", "id_compra": int(id_compra)}
                    respuesta = enviar_mensaje(sock, mensaje)
                    print(respuesta)
                except ValueError:
                    print("ID de compra debe ser un número.")

        elif opcion == "5":
            # Mostrar compras pendientes de envío
            mensaje = {"accion": "5"}
            respuesta = enviar_mensaje(sock, mensaje)
            print("\n=== Sus Compras Pendientes ===")
            print(respuesta)
            
            id_compra = input("\nIngrese ID de compra para confirmar envío (o 0 para cancelar): ")
            if id_compra != "0":
                try:
                    mensaje = {"accion": "confirmar_envio", "id_compra": int(id_compra)}
                    respuesta = enviar_mensaje(sock, mensaje)
                    print(respuesta)
                except ValueError:
                    print("ID de compra debe ser un número.")
        
        elif opcion == "6":
            try:
                # Crear NUEVO socket para el chat
                chat_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                chat_sock.connect((HOST, PORT))

                # Enviar mensaje inicial para indicar que es un chat
                mensaje_inicio_chat = {
                    "modo": "chat"
                }
                chat_sock.send(json.dumps(mensaje_inicio_chat).encode('utf-8'))

                print("\nConectando al chat con el ejecutivo...")
                iniciar_chat(chat_sock,correo)  # Tu función iniciar_chat() ya está lista

            except Exception as e:
                print(f"Error al iniciar el chat: {e}")
        
        elif opcion == "7":
            pass
        
        elif opcion == "8":
            pass
        
        elif opcion == "9":
            print("Sesión finalizada.")
            break
        
        else:
            print("Opción no válida.")
        
        # Verificar notificaciones (simulado - en una app real se usarían hilos)
        # Este código simula la recepción de notificaciones como aceptación de chat
        try:
            mensaje = {"accion": "check_notificaciones"}
            respuesta = enviar_mensaje(sock, mensaje)
            notif = json.loads(respuesta)
            if notif.get("tipo") == "notificacion":
                if notif.get("subtipo") == "chat_aceptado":
                    print(f"\n*** {notif.get('mensaje')} ***")
                    correo_ejecutivo = notif.get("correo_ejecutivo")
                    chat_activo = True
        except:
            pass

def ejecutivo_menu(sock, correo):
    while True:
        print("\n=== Menú Ejecutivo ===")
        print("1. :status - Ver estado del sistema")
        print("2. :details - Ver clientes conectados")
        print("3. :history - Ver historial de un cliente")
        print("4. :catalogue - Mostrar catálogo")
        print("5. :buy - Comprarle a un cliente")
        print("6. :publish - Publicar nueva carta")
        print("7. :chats - Conectarse a un chat")  # Nueva opción
        print("8. :disconnect - Terminar conexión")

        
        opcion = input("\nSeleccione una opción: ")
        
        if opcion == "1":
            mensaje = {"comando": ":status"}
            respuesta = enviar_mensaje(sock, mensaje)
            print(respuesta)
        
        elif opcion == "2":
            mensaje = {"comando": ":details"}
            respuesta = enviar_mensaje(sock, mensaje)
            print(respuesta)

        elif opcion == "3":
            correo_cliente = input("Ingrese correo del cliente: ")
            mensaje = {"comando": ":history", "correo_cliente": correo_cliente}
            respuesta = enviar_mensaje(sock, mensaje)
            print(respuesta)
            input("\nPresione Enter para continuar...")
        
        elif opcion == "4":
            mensaje = {"comando": ":catalogue"}
            respuesta = enviar_mensaje(sock, mensaje)
            print(respuesta)
        
        elif opcion == "5":
            correo_cliente = input("Ingrese correo del cliente: ")
            id_carta = input("Ingrese ID de carta a comprar: ")
            try:
                mensaje = {"comando": ":buy", "correo_cliente": correo_cliente, "id_carta": int(id_carta)}
                respuesta = enviar_mensaje(sock, mensaje)
                print(respuesta)
            except ValueError:
                print("ID de carta debe ser un número.")
        
        elif opcion == "6":
            nombre = input("Nombre de la carta: ")
            precio = input("Precio de la carta: ")
            try:
                mensaje = {"comando": ":publish", "nombre": nombre, "precio": float(precio)}
                respuesta = enviar_mensaje(sock, mensaje)
                print(respuesta)
            except ValueError:
                print("El precio debe ser un número válido.")
        
        elif opcion == "7":
            try:
                # Crear NUEVO socket para el chat
                chat_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                chat_sock.connect((HOST, PORT))

                # Enviar mensaje inicial para indicar que es un chat
                mensaje_inicio_chat = {
                    "modo": "chat-ejecutivo"
                }
                chat_sock.send(json.dumps(mensaje_inicio_chat).encode('utf-8'))

                print("\nConectando al chat con el ejecutivo...")
                iniciar_chat_ejecutivo(chat_sock,correo)  # Tu función iniciar_chat() ya está lista

            except Exception as e:
                print(f"Error al conectarse al chat: {e}")
        
        elif opcion == "8":
            comando = ":disconnect"
            mensaje = {"comando": comando}
            respuesta = enviar_mensaje(sock, mensaje)
            print(respuesta)
            break
        
        else:
            print("Opción no válida.")
            
        # Verificar notificaciones (simulado - en app real usar hilos)
        try:
            mensaje = {"comando": ":check_notifications"}
            respuesta = enviar_mensaje(sock, mensaje)
            notif = json.loads(respuesta)
            if notif.get("tipo") == "notificacion" and notif.get("subtipo") == "solicitud_chat":
                print(f"\n*** NUEVA SOLICITUD DE CHAT: {notif.get('mensaje')} ***")
        except:
            pass

if __name__ == "__main__":
    while True:
        print("\n=== Sistema de Cartas ===")
        print("1. Registrarse como Cliente")
        print("2. Iniciar sesión")
        print("3. Salir")
        
        opcion = input("\nSeleccione una opción: ")
        
        if opcion == "1":
            registro()
        elif opcion == "2":
            login()
        elif opcion == "3":
            print("¡Hasta pronto!")
            sys.exit(0)
        else:
            print("Opción no válida. Intente nuevamente.")
