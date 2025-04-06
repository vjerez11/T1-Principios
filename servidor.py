import socket
import threading
import json
import os
from datetime import datetime

HOST = '127.0.0.1'
PORT = 8889

clientes_conectados = []
ejecutivos_conectados = []
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

def manejar_cliente_regular(conn, correo):
    # Implementación opcional
    pass

def manejar_ejecutivo(conn, correo):
    while True:
        try:
            data = conn.recv(1024)
            if not data:
                break

            msg = json.loads(data.decode('utf-8'))
            comando = msg.get("comando")

            if comando == ":create_user":
                respuesta = "Esta funcionalidad ha sido deshabilitada. Los usuarios ahora deben registrarse directamente como clientes."
                conn.send(respuesta.encode('utf-8'))
            # Otros comandos aquí...

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
            clientes_conectados.append(conn)
            manejar_cliente_regular(conn, correo)
        elif tipo == "ejecutivo":
            conn.send(f"Bienvenido, ejecutivo {correo}".encode('utf-8'))
            ejecutivos_conectados.append(conn)
            manejar_ejecutivo(conn, correo)
        else:
            conn.send("Tipo no reconocido.".encode('utf-8'))

    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        conn.close()
        if conn in clientes_conectados: clientes_conectados.remove(conn)
        if conn in ejecutivos_conectados: ejecutivos_conectados.remove(conn)
        print(f"[SERVIDOR] Conexión cerrada con {addr}")

def main():
    global cartas_disponibles
    cartas_disponibles = cargar_json("cartas.json")

    for archivo in ["usuarios.json", "ejecutivos.json", "historial.json", "compras.json", "devoluciones.json"]:
        if not os.path.exists(archivo):
            guardar_json(archivo, [])

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
