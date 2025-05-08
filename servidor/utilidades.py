import json
import os
from datetime import datetime

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

def listar_compras_cliente(correo):
    compras = cargar_json("compras.json")
    compras_cliente = [c for c in compras if c.get("correo_cliente") == correo]
    return json.dumps(compras_cliente, indent=4)


