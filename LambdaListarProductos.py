import boto3
import json

def lambda_handler(event, context):
    print(event)
    # Entrada (json)
    body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
    tenant_id = body.get('tenant_id')
    
    if not tenant_id:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'tenant_id es requerido'})
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

    # Proceso - Listar productos por tenant_id
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('t_productos')
    
    try:
        # Consultar la tabla usando tenant_id como clave de partición
        query_response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('tenant_id').eq(tenant_id)
        )
        
        productos = query_response.get('Items', [])
        
        # Salida (json)
        return {
            'statusCode': 200,
            'body': json.dumps({
                'productos': productos,
                'count': len(productos)
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
