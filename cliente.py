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
                    cliente_menu(s)
                else:
                    ejecutivo_menu(s)
            
        except Exception as e:
            print(f"Error: {e}")

def cliente_menu(sock):
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
            #Da aviso de lo que se hace 
            mensaje = {"accion": "1"}
            respuesta = enviar_mensaje(sock, mensaje)
            print(respuesta)
            #Se programa lo que debe hacer 

        elif opcion == "2":
            mensaje = {"accion": "2"}
            respuesta = enviar_mensaje(sock, mensaje)
            print(respuesta)
            #Se programa lo que debe hacer 
        
        elif opcion == "3":
            #Da aviso a lo que se hace
            mensaje = {"accion": "3"}
            respuesta = enviar_mensaje(sock, mensaje)
            print(respuesta)
            
            #Se programa lo que debe hacer 
            id_carta = input("Ingrese ID de carta para comprar (o 0 para cancelar): ")
            if id_carta != "0":
                mensaje = {"accion": "2", "id_carta": int(id_carta)}
                respuesta = enviar_mensaje(sock, mensaje)
                print(respuesta)
        
        elif opcion == "4":
            # Listar compras para devolución
            mensaje = {"accion": "4"}
            respuesta = enviar_mensaje(sock, mensaje)
            print(respuesta)
            
            #Se programa lo que debe hacer 
            id_compra = input("Ingrese ID de compra para devolver (o 0 para cancelar): ")
            if id_compra != "0":
                mensaje = {"accion": "3", "id_compra": int(id_compra)}
                respuesta = enviar_mensaje(sock, mensaje)
                print(respuesta)

        elif opcion == "5":
            mensaje = {"accion": "5"}
            respuesta = enviar_mensaje(sock, mensaje)
            print(respuesta)
            #Se programa lo que debe hacer 
        
        elif opcion == "6":
            mensaje = input("Mensaje para el ejecutivo: ")
            mensaje_obj = {"accion": "6", "mensaje": mensaje}
            respuesta = enviar_mensaje(sock, mensaje_obj)
            print(respuesta)
        
        elif opcion == "7":
            print("Sesión finalizada.")
            break
        
        else:
            print("Opción no válida.")
            break

def ejecutivo_menu(sock):
    while True:
        print("\n=== Menú Ejecutivo ===")
        print("1. :status - Ver estado")
        print("2. :details - Clientes Conectados")
        print("3. :history - Ver al Cliente")
        print("4. :catalogue - Mostrar Catálogo")
        print("5. :buy - Comprarle al Cliente")
        print("6. :publish - Publicar carta")
        print("7. :disconnect - Terminar conexión")
        print("8. :exit - Desconectarse")
        
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
            mensaje = {"comando": ":history"}
            respuesta = enviar_mensaje(sock, mensaje)
            print(respuesta)
        
        elif opcion == "4":
            mensaje = {"comando": ":catalogue"}
            respuesta = enviar_mensaje(sock, mensaje)
            print(respuesta)
        
        elif opcion == "5":
            mensaje = {"comando": ":buy"}
            respuesta = enviar_mensaje(sock, mensaje)
            print(respuesta)
        
        elif opcion == "6":
            mensaje = {"comando": ":publish"}
            respuesta = enviar_mensaje(sock, mensaje)
            print(respuesta)
        
        elif opcion == "7":
            mensaje = {"comando": ":disconnect"}
            respuesta = enviar_mensaje(sock, mensaje)
            print(respuesta)
            break

        elif opcion == "8":
            mensaje = {"comando": ":exit"}
            respuesta = enviar_mensaje(sock, mensaje)
            print(respuesta)
        
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