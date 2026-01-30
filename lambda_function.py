import json
import base64
import datetime
import decimal
import logging
from ConexionBD import conectar, get_Drivers
import os

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

def menu(event, context):
    if os.path.exists("/opt/etc/odbcinst.ini"):   

        os.environ["ODBCSYSINI"] = "/opt/etc"  # ubicación base del archivo
        os.environ["ODBCINSTINI"] = "odbcinst.ini"
        os.environ["LD_LIBRARY_PATH"] = "/opt/lib:" + os.environ.get("LD_LIBRARY_PATH", "")

        os.environ["TDSDUMP"] = "/tmp/tds.log"
        os.environ["TDSDUMPLEVEL"] = "10"
        logger.info("Variables de entorno para ODBC configuradas.")

    drivers = get_Drivers()
    
    logger.info("Drivers ODBC disponibles: %s", drivers)
    print("Drivers ODBC disponibles P:", drivers)

    # Obtenemos el evento
    path = (
        event.get("rawPath")
        or event.get("requestContext", {}).get("http", {}).get("path")
        or "/"
    )
    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")

    #Preparación para token o autenticación si es necesario
    headers = event.get("headers", {}) or {}

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
        if api_key != f'{os.getenv("api_key")}':#"6C445EE74E342785F8027BFCC0A1170C":
            logger.warning("Acceso no autorizado: API Key invalida")
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
        logger.warning("Ruta no encontrada: %s", path)
        return {
            "statusCode": 404,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": f"Ruta no encontrada: {path}"})
        }
    
def lambda_handler(event, context):
    return menu(event, context)

