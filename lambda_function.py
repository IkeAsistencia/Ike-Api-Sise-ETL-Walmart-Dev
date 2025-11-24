import json
import base64
import datetime
import decimal
from ConexionBD import conectar

# helper para serializar tipos no JSON-serializables
def _serialize_value(v):
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
        print("API Key recibida:", api_key)
        
        if api_key != "6C445EE74E342785F8027BFCC0A1170C":
            return {
                "statusCode": 403,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Acceso no autorizado: API Key invalida"})
            }

        # conexion a la base de datos y obtencion de datos
        conexion = conectar()
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
                    fila = {col: _serialize_value(val) for col, val in zip(columnas, row)}
                    resultados_json.append(fila)
            else:
                for row in resultados:
                    resultados_json.append([_serialize_value(v) for v in row])
        else:
            resultados_json = []
            
        datos = [
            {"id": 1, "nombre": "Ricardo", "rol": "Admin"},
            {"id": 2, "nombre": "Laura", "rol": "Usuario"},
        ]
        #print ("Datos de BD:", resultados)
        #print ("Datos a exportar:", datos)
        #print("Datos de BD (convertidos):", resultados_json)
        #CSV
        '''''
        # Generamos titulos y filas        
        muestraData = "id,nombre,rol\n"
        for d in datos:
            muestraData += f"{d['id']},{d['nombre']},{d['rol']}\n"

        # Codificamos el CSV en Base64 para que AWS no lo rompa
        csv_b64 = base64.b64encode(muestraData.encode("utf-8")).decode("utf-8")
        '''
        #
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                #"Content-Type": "text/csv",
                #"Content-Disposition": "attachment; filename=consulta.csv"
            },
            "body": json.dumps({
               "data": datos
            }, ensure_ascii=False)
        }

    # Ruta no encontrada
    else:
        return {
            "statusCode": 404,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": f"Ruta no encontrada: {path}"})
        }