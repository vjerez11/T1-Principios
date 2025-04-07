import socket
import json
import sys
import getpass

HOST = '127.0.0.1'
PORT = 8889

def enviar_mensaje(sock, mensaje):
    sock.send(json.dumps(mensaje).encode('utf-8'))
    respuesta = sock.recv(1024).decode('utf-8')
    return respuesta

def registro():
    print("\n=== Registro de Cliente ===")
    # Eliminada la solicitud de tipo, ahora es solo "cliente"
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

def cliente_menu(sock, correo):
    while True:
        print("\n=== Menú Cliente ===")
        print("1. Cambio de Contraseña")
        print("2. Ver historial")
        print("3. Catálogo de productos / Comprar productos")
        print("4. Solicitar devolución")
        print("5. Confirmar envío")
        print("6. Contactar ejecutivo")
        print("7. Salir")
        
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
            mensaje_texto = input("Mensaje para el ejecutivo: ")
            mensaje = {"accion": "6", "mensaje": mensaje_texto}
            respuesta = enviar_mensaje(sock, mensaje)
            print(respuesta)
        
        elif opcion == "7":
            print("Sesión finalizada.")
            break
        
        else:
            print("Opción no válida.")

def ejecutivo_menu(sock, correo):
    while True:
        print("\n=== Menú Ejecutivo ===")
        print("1. :status - Ver estado del sistema")
        print("2. :details - Ver clientes conectados")
        print("3. :history - Ver historial de un cliente")
        print("4. :catalogue - Mostrar catálogo")
        print("5. :buy - Comprarle a un cliente")
        print("6. :publish - Publicar nueva carta")
        print("7. :disconnect - Terminar conexión")

        
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
        
        elif opcion == "4":
            mensaje = {"comando": ":catalogue"}
            respuesta = enviar_mensaje(sock, mensaje)
            print(respuesta)
        
        elif opcion == "5":
            correo_cliente = input("Ingrese correo del cliente: ")
            id_carta = input("Ingrese ID de carta a comprar: ")
            mensaje = {"comando": ":buy", "correo_cliente": correo_cliente, "id_carta": int(id_carta)}
            respuesta = enviar_mensaje(sock, mensaje)
            print(respuesta)
        
        elif opcion == "6":
            nombre = input("Nombre de la carta: ")
            precio = input("Precio de la carta: ")
            mensaje = {"comando": ":publish", "nombre": nombre, "precio": float(precio)}
            respuesta = enviar_mensaje(sock, mensaje)
            print(respuesta)
        
        elif opcion == "7":
            comando = ":disconnect"
            mensaje = {"comando": comando}
            respuesta = enviar_mensaje(sock, mensaje)
            print(respuesta)
            break
        
        else:
            print("Opción no válida.")

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