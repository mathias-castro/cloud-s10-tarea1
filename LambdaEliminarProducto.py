import boto3
import json

def lambda_handler(event, context):
    print(event)
    # Entrada (json)
    body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
    tenant_id = body.get('tenant_id')
    producto_id = body.get('producto_id')
    
    if not tenant_id:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'tenant_id es requerido'})
        }
        
    if not producto_id:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'producto_id es requerido'})
        }
    
    # Inicio - Proteger el Lambda
    token = event['headers']['Authorization']
    lambda_client = boto3.client('lambda')    
    payload_string = '{ "token": "' + token +  '" }'
    invoke_response = lambda_client.invoke(FunctionName="ValidarTokenAcceso",
                                           InvocationType='RequestResponse',
                                           Payload = payload_string)
    response = json.loads(invoke_response['Payload'].read())
    print(response)
    if response['statusCode'] == 403:
        return {
            'statusCode' : 403,
            'status' : 'Forbidden - Acceso No Autorizado'
        }
    # Fin - Proteger el Lambda        

    # Proceso - Eliminar producto específico por tenant_id y producto_id
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('t_productos')
    
    try:
        # Primero verificar que el producto existe usando clave compuesta
        get_response = table.get_item(
            Key={
                'tenant_id': tenant_id,
                'producto_id': producto_id
            }
        )
        
        if 'Item' not in get_response:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Producto no encontrado'})
            }
        
        producto_actual = get_response['Item']
        
        # Como ya usamos tenant_id en la clave, no necesitamos verificar nuevamente
        
        # Eliminar el producto usando clave compuesta
        delete_response = table.delete_item(
            Key={
                'tenant_id': tenant_id,
                'producto_id': producto_id
            },
            ReturnValues='ALL_OLD'
        )
        
        producto_eliminado = delete_response.get('Attributes')
        
        # Salida (json)
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Producto eliminado exitosamente',
                'producto_eliminado': producto_eliminado
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
