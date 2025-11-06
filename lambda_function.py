import json

def lambda_handler(event, context):
    # Obtenemos el evento
    path = event.get("rawPath", "/")
    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")

    # ruta raiz con get
    if path == "/" and method == "GET":
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"mensaje": "API Lambda activa"})
        }

    # ruta consulta_csv con get
    elif path == "/consulta_csv" and method == "GET":
        datos = [
            {"id": 1, "nombre": "Ricardo", "rol": "Admin"},
            {"id": 2, "nombre": "Laura", "rol": "Usuario"},
        ]

        # Generamos un CSV en memoria
        muestraData = "id,nombre,rol\n"
        for d in datos:
            muestraData += f"{d['id']},{d['nombre']},{d['rol']}\n"

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "text/csv",
                "Content-Disposition": "attachment; filename=consulta.csv"
            },
            "body": muestraData
        }

    # Ruta no encontrada
    else:
        return {
            "statusCode": 404,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": f"Ruta no encontrada: {path}"})
        }