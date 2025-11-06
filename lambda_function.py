import json

def lambda_handler(event, context):
    print("Lambda fue invocada.")

    return {
        'statusCode': 200,
        'body': json.dumps('¡Hola desde Lambda!')
    }
