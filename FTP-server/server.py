import json
import struct
import os
import socket
import sys
import threading
import logging

logging.basicConfig(level=logging.DEBUG,format='(%(threadName)-10s) %(message)s',)


def enviarArchivo(sock: socket.socket, nombreArchivo):
    # Obtener el tamaño del archivo a enviar.
    tamanioArchivo= os.path.getsize(nombreArchivo)
    # Informar primero al servidor la cantidad
    # de bytes que serán enviados.
    sock.sendall(struct.pack("<Q", tamanioArchivo))
    # Enviar el archivo en bloques de 1024 bytes.
    with open(nombreArchivo, "rb") as f:
        while bytesLeidos := f.read(buffer_size):
            sock.sendall(bytesLeidos)

def recibirTamanioArchivo(sock: socket.socket):
    # Esta función se asegura de que se reciban los bytes
    # que indican el tamaño del archivo que será enviado,
    # que es codificado por el cliente vía struct.pack(),
    # función la cual genera una secuencia de bytes que
    # representan el tamaño del archivo.
    formato = "<Q"
    bytesEsperados = struct.calcsize(formato)
    bytesRecibidos = 0
    actualesBytes = bytes()
    while bytesRecibidos < bytesEsperados:
        pedazosBytes = sock.recv(bytesEsperados - bytesRecibidos)
        actualesBytes += pedazosBytes
        bytesRecibidos += len(pedazosBytes)
    tamanioArchivo = struct.unpack(formato, actualesBytes)[0]
    return tamanioArchivo

def recibirArchivo(sock: socket.socket, nombreArchivo):
    # Leer primero del socket la cantidad de
    # bytes que se recibirán del archivo.
    tamanioArchivo = recibirTamanioArchivo(sock)
    # Abrir un nuevo archivo en donde guardar
    # los datos recibidos.
    with open(nombreArchivo, "wb") as f:
        bytesRecibidos = 0
        # Recibir los datos del archivo en bloques de
        # 1024 bytes hasta llegar a la cantidad de
        # bytes total informada por el cliente.
        while bytesRecibidos < tamanioArchivo:
            pedazosBytes = sock.recv(buffer_size)
            if pedazosBytes:
                f.write(pedazosBytes)
                bytesRecibidos += len(pedazosBytes)

def usersValidation(clienteUsuario,clientePassword):
    global directory
    validation = False

    with open("usuarios.json") as file:
        archivoJson = json.load(file)
        for usuario in archivoJson["users"]:
            if (clienteUsuario == usuario["USER"] and clientePassword == usuario["PASS"]):
                validation = True
                username=usuario["USER"]
                directory = usuario["DIRECTORY"]
                #print(f'directorio de {usuario["USER"]}: {directory} ')
                validationUserDirectory = str(validation)+"*"+username+"*"+directory
                break
            else:
                validationUserDirectory=str(validation)+"*"+"none"+"*"+"none"

    return validationUserDirectory

def mostrarListaArchivos(files):
    i = 0
    for file in files:
        print(f"{i+1}.- {file}")
        i=+1

def servirPorSiempre(socket_control, listaconexiones,semaforo):
    try:
        while True:
            control_conn, control_addr = socket_control.accept()
            listaconexiones.append(control_conn)
            thread_read = threading.Thread(target=recibir_datos, args=[control_conn, control_addr,semaforo])
            thread_read.start()
            gestion_conexiones(listaconexiones)
    except Exception as e:
        print(e)

def gestion_conexiones(listaconexiones):
    for conn in listaconexiones:
        if conn.fileno() == -1:
            listaconexiones.remove(conn)
    #print("hilos activos:", threading.active_count())
    #print("enum", threading.enumerate())
    #print("conexiones: ", len(listaconexiones))
    #print(listaconexiones)

def recibir_datos(control_conn, control_addr,semaforo):
    try:
        while True:
            print("Conexión control establecida ", "a ", control_addr, " port", port_control)
            print('Servidor 220: Servicio listo para nuevo usuario')

            userRecibir = control_conn.recv(buffer_size)
            userRecibirDecode = userRecibir.decode("utf-8")
            userPass= userRecibirDecode.split("*")
            user_cliente = userPass[0]
            password_cliente =userPass[1]

            valueUserDirectory=usersValidation(user_cliente, password_cliente)
            validationUserDirectory= valueUserDirectory.split("*")
            validationUser = validationUserDirectory[0]
            username=validationUserDirectory[1]
            directory = validationUserDirectory[2]

            if validationUser=="True":
                print("Servidor 331: Usuario OK, necesita contraseña")
                print("Servidor: Contraseña correcta")
                control_conn.send("clientOn*passOn".encode("utf-8"))
                value_users = True

            else:
                control_conn.send("clientOff*passOff".encode("utf-8"))
                value_users = False

            if (value_users):
                print("Servidor: Credenciales correctas")
                print("Servidor 230: Usuario conectado correctamente, continue...")

                control_conn.send(("credencialesOn"+"*"+username+"*"+directory).encode("utf-8"))
                portArchivo=control_conn.recv(buffer_size)
                portArchivoDecode=portArchivo.decode("utf-8")
                localPortNombreArchivo=portArchivoDecode.split("*")
                localPortStr=localPortNombreArchivo[0]
                nombreArchivo=localPortNombreArchivo[1]
                localPort=int(localPortStr)
                rutaFinal = directory + nombreArchivo
                print("Servidor 150: Estado de archivo correcto; a punto de abrir la conexión de datos")
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_conexion:
                    socket_conexion.connect((host_control,localPort))
                    print("Servidor 125: Conexión de datos ya abierta; transferencia de inicio")
                    logging.debug("Candado adquirido")
                    semaforo.acquire()
                    enviarArchivo(socket_conexion,rutaFinal)
                    semaforo.release()
                    logging.debug("Candado liberado")
                    print("Servidor 226: Cerrando la conexión de datos. La acción de archivo solicitada se realizó correctamente")
            else:
                print("Servidor: Credenciales incorrectas")
                print("Servidor 332: Necesita una cuenta para entrar en el sistema.")
                print("Servidor 425: No se puede abrir la conexión de datos.")
                print("Servidor: intentelo de nuevo")
                control_conn.send(("credencialesOff"+"*"+username+"*"+directory).encode("utf-8"))
                continue
            # Recibimos bytes, convertimos en str
            QUIT = control_conn.recv(buffer_size)
            # Verificamos que hemos recibido datos

            if QUIT.decode("utf-8") == "s":
                break
        print("Servidor 221: Conexión de control de cierre del servicio.")
    finally:
        control_conn.close()
# Creamos un objeto socket tipo TCP
listaConexiones = []
host_control = "127.0.0.1"
port_control = 8080
buffer_size = 1024  # Usamos un número pequeño para tener una respuesta rápida
'''Los objetos socket soportan el context manager type
así que podemos usarlo con una sentencia with, no hay necesidad
de llamar a socket_close()
'''
directory =""
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_control:
    socket_control.bind((host_control, port_control))
    socket_control.listen(5)  # Esperamos la conexión del cliente
    print("El servidor FTP está disponible y en espera de solicitudes")
    semaforo = threading.Semaphore(1)
    servirPorSiempre(socket_control, listaConexiones, semaforo)

