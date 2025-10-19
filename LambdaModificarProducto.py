import boto3
import json

def lambda_handler(event, context):
    print(event)
    # Entrada (json)
    body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
    tenant_id = body.get('tenant_id')
    producto_id = body.get('producto_id')
    datos_modificar = body.get('datos_modificar')
    
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
        
    if not datos_modificar or not isinstance(datos_modificar, dict):
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'datos_modificar es requerido y debe ser un objeto'})
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

    # Proceso - Modificar producto específico por tenant_id y producto_id
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
        
        # Construir la expresión de actualización
        update_expression = "SET "
        expression_attribute_values = {}
        expression_attribute_names = {}
        
        for key, value in datos_modificar.items():
            # No permitir modificar producto_id ni tenant_id por seguridad
            if key in ['producto_id', 'tenant_id']:
                continue
                
            # Usar nombres de atributos para evitar conflictos con palabras reservadas
            attribute_name = f"#{key}"
            attribute_value = f":{key}"
            
            update_expression += f"{attribute_name} = {attribute_value}, "
            expression_attribute_names[attribute_name] = key
            expression_attribute_values[attribute_value] = value
        
        # Remover la última coma y espacio
        update_expression = update_expression.rstrip(", ")
        
        if not expression_attribute_values:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No hay datos válidos para modificar'})
            }
        
        # Realizar la actualización usando clave compuesta
        update_response = table.update_item(
            Key={
                'tenant_id': tenant_id,
                'producto_id': producto_id
            },
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues='ALL_NEW'
        )
        
        producto_modificado = update_response['Attributes']
        
        # Salida (json)
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Producto modificado exitosamente',
                'producto': producto_modificado
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
