import json
import base64

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
        datos = [
            {"id": 1, "nombre": "Ricardo", "rol": "Admin"},
            {"id": 2, "nombre": "Laura", "rol": "Usuario"},
        ]
        print ("Datos a exportar:", datos)
        # Generamos titulos y filas
        muestraData = "id,nombre,rol\n"
        for d in datos:
            muestraData += f"{d['id']},{d['nombre']},{d['rol']}\n"

        # Codificamos el CSV en Base64 para que AWS no lo rompa
        csv_b64 = base64.b64encode(muestraData.encode("utf-8")).decode("utf-8")

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                #"Content-Type": "text/csv",
                #"Content-Disposition": "attachment; filename=consulta.csv"
            },
            #"body": muestraData
            "body": json.dumps({
               "data": datos

            })
        }

    # Ruta no encontrada
    else:
        return {
            "statusCode": 404,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": f"Ruta no encontrada: {path}"})
        }