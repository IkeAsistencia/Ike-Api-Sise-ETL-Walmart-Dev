import json
import base64
import datetime
import decimal
import logging
from ConexionBD import conectar
import shutil
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

def lambda_handler(event, context):   
    if os.path.exists("/opt/etc/odbcinst.ini"):
        shutil.copy("/opt/etc/odbcinst.ini", "/tmp/odbcinst.ini")

        # 2. Exportar variables para que unixODBC lea el archivo desde /tmp
        os.environ["ODBCINSTINI"] = "/tmp/odbcinst.ini"
        os.environ["ODBCSYSINI"] = "/tmp"  # ubicación base del archivo
        os.environ["LD_LIBRARY_PATH"] = "/opt/lib:" + os.environ.get("LD_LIBRARY_PATH", "")

    import pyodbc
    drivers = pyodbc.drivers()
    
    logger.info("Drivers ODBC disponibles: %s", drivers)
    print("Drivers ODBC disponibles P:", drivers)

    logger.info("Existe /opt/etc/odbcinst.ini: %s", os.path.exists("/opt/etc/odbcinst.ini"))
    logger.info("Existe libmsodbcsql en /opt/lib: %s", any('libmsodbcsql' in f for f in os.listdir('/opt/lib')))
    logger.info("LD_LIBRARY_PATH: %s", os.environ.get('LD_LIBRARY_PATH'))
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
                "statusCode": 403,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Acceso no autorizado: API Key invalida"})
            }

        # conexion a la base de datos y obtencion de datos 
        
        try:
            conexion = conectar()
        except Exception as e:
            logger.error("Error de conexion a la base de datos: %s", str(e))
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": f"Error de conexion a la base de datos {drivers}"})
            }
        cursor = conexion.cursor()
        #cursor.execute("SELECT * FROM DBO.CAFILIADOWBP")
        cursor.execute("EXEC [sp_MigraVentas_WM_API] ?",
                        (2,))
        resultados = cursor.fetchall()
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