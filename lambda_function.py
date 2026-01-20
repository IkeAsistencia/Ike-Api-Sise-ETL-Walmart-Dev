import json
import base64
import datetime
import decimal
import logging
from ConexionBD import conectar
import shutil
import os
import ctypes
# Configurar logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# helper para serializar tipos de datos
def serializarDatos(v):
    
    if v is None:
        return None
    if isinstance(v, (str, int, float, bool)):
        return v
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.isoformat()
    if isinstance(v, decimal.Decimal):
        try:
            return float(v)
        except Exception:
            return str(v)
    if isinstance(v, (bytes, bytearray)):
        try:
            return v.decode("utf-8")
        except Exception:
            return str(v)
    return str(v)


def test_tcp_connection():
    import socket
    try:
        sock = socket.create_connection((os.getenv("MX_DB_SERVER"), os.getenv("MX_DB_PORT")), timeout=5)
        sock.close()
        print("OK: Lambda puede alcanzar el host y el puerto.")
        return "OK: Lambda puede alcanzar el host y el puerto."
    except Exception as e:
        print("ERROR: Lambda no puede alcanzar el host y el puerto: ", str(e))
        return f"ERROR: No se puede conectar a {os.getenv("MX_DB_SERVER")}:{os.getenv("MX_DB_PORT")} -> {str(e)}"
def menu(event, context):
    if os.path.exists("/opt/etc/odbcinst.ini"):   
        
        with open("/tmp/freetds.conf", "w") as f:
            f.write("""
        [global]
            tds version = 7.1
            encryption = off
            client charset = UTF-8
            timeout = 30
            connect timeout = 30
        """)

        with open("/tmp/odbc.ini", "w") as f:
            f.write("""
        [SQLSERVER]
            Driver      = FreeTDS
            Server      = 172.21.10.185
            Port        = 21518
            Database    = IKE_QA
            TDS_Version = 7.2
            ClientCharset = UTF-8
            Encrypt     = no
        """)
        os.environ["ODBCSYSINI"] = "/opt/etc"  # ubicación base del archivo
        os.environ["ODBCINSTINI"] = "odbcinst.ini"
        os.environ["ODBCINI"] = "/tmp/odbc.ini"
        os.environ["LD_LIBRARY_PATH"] = "/opt/lib:" + os.environ.get("LD_LIBRARY_PATH", "")
        ctypes.CDLL("/opt/lib/libtdsodbc.so")

        os.environ["TDSDUMP"] = "/tmp/tds.log"
        os.environ["TDSDUMPLEVEL"] = "10"

        os.environ["FREETDSCONF"] = "/tmp/freetds.conf"

    import pyodbc
    drivers = pyodbc.drivers()
    
    logger.info("Drivers ODBC disponibles: %s", drivers)
    print("Drivers ODBC disponibles P:", drivers)

    #import socket
    #s = socket.socket()
    #s.settimeout(5)
    #s.connect((os.getenv("MX_DB_SERVER"), os.getenv("MX_DB_PORT")))
    #print("Conexión TCP OK")

    #logger.info("Existe /opt/etc/odbcinst.ini: %s", os.path.exists("/opt/etc/odbcinst.ini"))
    #logger.info("Existe libmsodbcsql en /opt/lib: %s", any('libmsodbcsql' in f for f in os.listdir('/opt/lib')))
    #logger.info("LD_LIBRARY_PATH: %s", os.environ.get('LD_LIBRARY_PATH'))
    #logger.info("ODBCSYSINI: %s", os.environ.get('ODBCSYSINI'))
    #logger.info("ODBCINSTINI: %s", os.environ.get('ODBCINSTINI'))
    
    # Obtenemos el evento
    path = (
        event.get("rawPath")
        or event.get("requestContext", {}).get("http", {}).get("path")
        or "/"
    )
    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")

    #Preparación para token o autenticación si es necesario
    headers = event.get("headers", {}) or {}
    token = headers.get("Authorization")


    # ruta raiz con get
    if path == "/as" and method == "GET":
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "mensajito": "API Lambda activa",
                "ruta": f"{path}",
                "metodo": f"{method}"
            })
        }

    # ruta consulta_csv con get
    elif path == "/" and method == "GET":
        #Obtener la variable api-key de el header y validarla
        api_key = headers.get("api-key")         
        logger.info("API Key recibida: %s", api_key)
        #'''''
        if api_key != "6C445EE74E342785F8027BFCC0A1170C":
            return {
                "statusCode": 401,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Acceso no autorizado: API Key invalida"})
            }

        # conexion a la base de datos y obtencion de datos 
        logger.info("Inicia conexion a la base de datos")
        try:
            conexion = conectar()
        except Exception as e:
            logger.error("Error de conexion a la base de datos: %s", str(e))
            if os.path.exists("/tmp/tds.log"):
                with open("/tmp/tds.log", "r") as f:
                    print(f.read())
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": f"Error de conexion a la base de datos: {str(e)}", 
                                    "Drivers": f"{drivers}"})
            }
        logger.info("crea cursor y ejecuta consulta")
        cursor = conexion.cursor()
        #cursor.execute("SELECT * FROM DBO.CAFILIADOWBP")
        cursor.execute("EXEC [sp_MigraVentas_WM_API] ?",
                        (2,))
        resultados = cursor.fetchall()
        logger.info("Consulta ejecutada, filas obtenidas: %d", len(resultados))
        # obtener nombres de columnas (si existen) antes de cerrar cursor
        columnas = [c[0] for c in cursor.description] if cursor.description else []
        cursor.close()
        conexion.close()

        # Convertir resultados filas a lista de diccionarios JSON-serializables
        resultados_json = []
        if resultados:
            if columnas:
                for row in resultados:
                    fila = {col: serializarDatos(val) for col, val in zip(columnas, row)}
                    resultados_json.append(fila)
            else:
                for row in resultados:
                    resultados_json.append([serializarDatos(v) for v in row])
        else:
            resultados_json = []
        logger.info("Resultados convertidos a JSON, total registros: %d", len(resultados_json))
        '''''    
        datos = [
            {"id": 1, "nombre": "Ricardo", "rol": "Admin"},
            {"id": 2, "nombre": "Laura", "rol": "Usuario"},
        ]
        #logger.info("Datos de BD: %s", resultados)
        #logger.info("Datos a exportar: %s", datos)
        #logger.info("Datos de BD (convertidos): %s", resultados_json)
        #CSV
        # Generamos titulos y filas        
        muestraData = "id,nombre,rol\n"
        for d in datos:
            muestraData += f"{d['id']},{d['nombre']},{d['rol']}\n"

        # Codificamos el CSV en Base64 para que AWS no lo rompa
        csv_b64 = base64.b64encode(muestraData.encode("utf-8")).decode("utf-8")
        '''
        #respuesta en JSON
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                #"Content-Type": "text/csv",
                #"Content-Disposition": "attachment; filename=consulta.csv"
            },
            "body": json.dumps({
               "data": resultados_json
            }, ensure_ascii=False)
        }

    # Ruta no encontrada
    else:
        return {
            "statusCode": 404,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": f"Ruta no encontrada: {path}"})
        }
    
def lambda_handler(event, context):
    return menu(event, context)