import socket
import os
import struct
# El cliente debe tener las mismas especificaciones del servidor
host_control = "127.0.0.1"
port_control = 8080
buffer_size = 1024



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

def mostrarListaArchivos(files):
    i = 0
    for file in files:
        print(f"{i+1}.- {file}")
        i=+1

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_control:
    socket_control.connect((host_control, port_control))
    # Convertimos str a bytes
    QUIT = ""
    while True:
        USER = input("Nombre de usuario: \n")
        PASS = input("Contraseña: \n")
        users =USER+"*"+PASS
        socket_control.send(users.encode('utf-8'))
        validacion_users= socket_control.recv(buffer_size)
        validacion_usersDecode=validacion_users.decode("utf-8")
        userPass=validacion_usersDecode.split("*")
        validacion_user = userPass[0]
        validacion_password = userPass[1]

        if validacion_user == "clientOn" and validacion_password == "passOn":
            print("Cliente: Nombre de usuario correcto")
            print("Cliente: Contraseña correcta")
            value_users = True
        else:
            value_users = False

        validacion_completa = socket_control.recv(buffer_size)
        validacion_completaDecode=validacion_completa.decode("utf-8")
        validationUserDirectory=validacion_completaDecode.split("*")
        validation = validationUserDirectory[0]
        username = validationUserDirectory[1]
        directory = validationUserDirectory[2]
        if(validation=="credencialesOn"):
            print("Cliente: Credenciales correctas")
            print("Cliente: Acceso aceptado del servidor\n")
            listaArchivos = os.listdir(f"../FTP-server/{directory}")
            print(f"Archivos de {username}: ")
            mostrarListaArchivos(listaArchivos)
            nombreArchivo=input("\nIngrese el nombre completo del archivo que quiere descargar: ")
            localPortInt=12345
            localPort=str(localPortInt)
            portNombreArchivo=localPort+"*"+nombreArchivo
            socket_control.send(portNombreArchivo.encode("utf-8"))
            print("Cliente: apunto de abrir la conexion")

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_conexion:
                socket_conexion.bind((host_control,localPortInt))
                socket_conexion.listen(5)  # Esperamos la conexión del cliente
                conexion_conn, conexion_addr = socket_conexion.accept()  # Establecemos la conexión con el cliente
                with conexion_conn:
                    print("Cliente: Recibiento datos")
                    recibirArchivo(conexion_conn,f"ArchivosDescargados/{nombreArchivo}")
                    print("Cliente: Archivo recibido correctamente. Cerrando conexion de datos")
        else:
            print("Cliente: Credenciales incorrectas ")
            print("Cliente: Acceso denegado del servidor")
            print("Cliente: intentelo de nuevo...")
            continue


        QUIT=input("\nDesea salir de la conexion control? (s/n)\n")
        socket_control.send(QUIT.encode("utf-8"))
        if QUIT == "s":
            break
    print("Cliente: Se cerrara la conexion")