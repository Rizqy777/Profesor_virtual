import os
import botocore
from dotenv import load_dotenv
load_dotenv()
import boto3
from boto3.dynamodb.conditions import Attr
from boto3.dynamodb.conditions import Key

## CONEXION Y CREDENCIALES AWS
session = boto3.session.Session(
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
    region_name=os.getenv("AWS_REGION", "us-east-1")
)

dynamodb = session.client('dynamodb')

## CREAR TABLAS

## CREAR TABLA ALUMNO
tabla_alumnos = dynamodb.create_table(
   TableName='alumno',
   AttributeDefinitions=[
       {'AttributeName': 'id_alumno', 'AttributeType': 'N'},   # Partition Key
       {'AttributeName': 'fecha_conexion', 'AttributeType': 'S'},     # Sort Key
   ],
   KeySchema=[
       {'AttributeName': 'id_alumno', 'KeyType': 'HASH'},  # Partition Key
       {'AttributeName': 'fecha_conexion', 'KeyType': 'RANGE'}   # Sort Key
   ],
   ProvisionedThroughput={
       'ReadCapacityUnits': 5, #Numero de lecturas por segundo
       'WriteCapacityUnits': 5 #Numero de escrituras por segundo
   }
)
## ESPERAR A QUE LA TABLA ESTE DISPONIBLE PARA CONTINUAR
waiter = dynamodb.get_waiter('table_exists')
waiter.wait(TableName='alumno')

## CREAR TABLA PROFESOR
tabla_profesores = dynamodb.create_table(
   TableName='profesor',
   AttributeDefinitions=[
       {'AttributeName': 'id_profesor', 'AttributeType': 'N'},   # Partition Key
       {'AttributeName': 'fecha_conexion', 'AttributeType': 'S'},     # Sort Key
       {'AttributeName': 'duracion_sesion', 'AttributeType': 'N'},
   ],
   KeySchema=[
       {'AttributeName': 'id_profesor', 'KeyType': 'HASH'}, # Partition Key
       {'AttributeName': 'fecha_conexion', 'KeyType': 'RANGE'} # Sort Key tabla principal
   ],
   LocalSecondaryIndexes=[
       {
           'IndexName': 'duracionSesionIndex', # Sort Key LSI
           'KeySchema': [
               {'AttributeName': 'id_profesor', 'KeyType': 'HASH'},
               {'AttributeName': 'duracion_sesion', 'KeyType': 'RANGE'}
           ],
           'Projection': {
               'ProjectionType': 'ALL' # Puede ser ALL, KEYS_ONLY o INCLUDE
           }
       }
   ],
   ProvisionedThroughput={
       'ReadCapacityUnits': 5, #Numero de lecturas por segundo
       'WriteCapacityUnits': 5 #Numero de escrituras por segundo
   }
)
## ESPERAR A QUE LA TABLA ESTE DISPONIBLE PARA CONTINUAR
waiter = dynamodb.get_waiter('table_exists')
waiter.wait(TableName='profesor')

## CREAR TABLA LOG_REGISTRO
tabla_registros = dynamodb.create_table(
   TableName='log_registro',
   AttributeDefinitions=[
       {'AttributeName': 'id_registro', 'AttributeType': 'N'},   # Partition Key
       {'AttributeName': 'fecha_registro', 'AttributeType': 'S'},
       {'AttributeName': 'tipo_usuario', 'AttributeType': 'S'}
   ],
   KeySchema=[
       {'AttributeName': 'id_registro', 'KeyType': 'HASH'}, # Partition Key
       {'AttributeName': 'fecha_registro', 'KeyType': 'RANGE'} # Sort Key tabla principal
   ],
   LocalSecondaryIndexes=[
       {
           'IndexName': 'tipoRegistroIndex', # Sort Key LSI
           'KeySchema': [
               {'AttributeName': 'id_registro', 'KeyType': 'HASH'},
               {'AttributeName': 'tipo_usuario', 'KeyType': 'RANGE'}
           ],
           'Projection': {
               'ProjectionType': 'ALL' # Puede ser ALL, KEYS_ONLY o INCLUDE
           }
       }
   ],
   GlobalSecondaryIndexes=[
        {
            'IndexName': 'fechaRegistroIndex',
            'KeySchema': [
                {'AttributeName': 'fecha_registro', 'KeyType': 'HASH'}
            ],
            'Projection': {
                'ProjectionType': 'ALL'
            },
            'ProvisionedThroughput': {
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        }
    ],
   ProvisionedThroughput={
       'ReadCapacityUnits': 5, #Numero de lecturas por segundo
       'WriteCapacityUnits': 5 #Numero de escrituras por segundo
   }
)
## ESPERAR A QUE LA TABLA ESTE DISPONIBLE PARA CONTINUAR
waiter = dynamodb.get_waiter('table_exists')
waiter.wait(TableName='log_registro')

## CAMBIAR LA HERRAMIENTA DE SESION PARA REALIZAR OPERACIONES
dynamodb_resource = session.resource('dynamodb')

## INSERTAR REGISTRO ALUMNOS
tabla = dynamodb_resource.Table('alumno')
tabla.put_item(
    Item={
        'id_alumno':1,
        'fecha_conexion':'2025-11-28T17:00:00'
    }
)
tabla.put_item(
    Item={
        'id_alumno':2,
        'fecha_conexion':'2025-01-18T12:00:00'
    }
)
tabla.put_item(
    Item={
        'id_alumno':3,
        'fecha_conexion':'2025-09-20T11:00:00'
    }
)
## INSERTAR REGISTRO PROFESORES
tabla = dynamodb_resource.Table('profesor')
tabla.put_item(
    Item={
        'id_profesor':1,
        'fecha_conexion':'2025-11-28T17:00:00',
        'duracion_sesion':3000
    }
)
tabla.put_item(
    Item={
        'id_profesor':2,
        'fecha_conexion':'2025-01-18T12:00:00',
        'duracion_sesion':1000
    }
)
tabla.put_item(
    Item={
        'id_profesor':3,
        'fecha_conexion':'2025-09-20T11:00:00',
        'duracion_sesion':6000
    }
)
## INSERTAR REGISTRO LOG_REGISTRO
tabla = dynamodb_resource.Table('log_registro')
tabla.put_item(
    Item={
        'id_registro':1,
        'fecha_registro':'2025-11-28T17:00:00',
        'tipo_usuario':'profesor'
    }
)
tabla.put_item(
    Item={
        'id_registro':2,
        'fecha_registro':'2025-01-18T12:00:00',
        'tipo_usuario':'alumno'
    }
)
tabla.put_item(
    Item={
        'id_registro':3,
        'fecha_registro':'2025-09-20T11:00:00',
        'tipo_usuario':'alumno'
    }
)


## OBTENER REGISTRO DE TABLA ALUMNO
tabla = dynamodb_resource.Table('alumno')

response = tabla.get_item(
    Key={
        'id_alumno':1,
        'fecha_conexion':'2025-11-28T17:00:00'
    }
)
print(response.get('Item'))
## OBTENER REGISTRO DE TABLA PROFESOR
tabla = dynamodb_resource.Table('profesor')
response = tabla.get_item(
    Key={
        'id_profesor':2,
        'fecha_conexion':'2025-01-18T12:00:00'
    }
)
print(response.get('Item'))
## OBTENER REGISTRO DE TABLA LOG_REGISTRO
tabla = dynamodb_resource.Table('log_registro')
response = tabla.get_item(
    Key={
        'id_registro':3,
        'fecha_registro':'2025-09-20T11:00:00'
    }
)
print(response.get('Item'))


## ACTUALIZAR UN REGISTRO DE ALUMNO
tabla = dynamodb_resource.Table('alumno')
tabla.update_item(
    Key={
        'id_alumno':1,
        'fecha_conexion':'2025-11-28T17:00:00'
    },
    UpdateExpression='SET duracion_sesion = :valor',
    ExpressionAttributeValues={
        ':valor':10000
    }
)
print("Actualizado con exito")
## ACTUALIZAR UN REGISTRO DE PROFESOR
tabla = dynamodb_resource.Table('profesor')
tabla.update_item(
    Key={
        'id_profesor':1,
        'fecha_conexion':'2025-01-18T12:00:00'
    },
    UpdateExpression='SET duracion_sesion = :valor',
    ExpressionAttributeValues={
        ':valor':10000
    }
)
print("Actualizado con exito")
## ACTUALIZAR UN REGISTRO DE LOG_REGISTRO
tabla = dynamodb_resource.Table('log_registro')
tabla.update_item(
    Key={
        'id_registro':3,
        'fecha_registro':'2025-09-20T11:00:00'
    },
    UpdateExpression='SET tipo_usuario = :valor',
    ExpressionAttributeValues={
        ':valor':'profesor'
    }
)
print("Actualizado con exito")

## ELIMINAR UN REGISTRO

tabla = dynamodb_resource.Table('alumno')

tabla.delete_item(
    Key={
        'id_alumno':1,
        'fecha_conexion':'2025-11-28T17:00:00'
    }
)
print("Eliminado con exito")

## ELIMINAR UN REGISTRO DE PROFESOR
tabla = dynamodb_resource.Table('profesor')
tabla.delete_item(
    Key={
        'id_profesor':1,
        'fecha_conexion':'2025-01-18T12:00:00'
    }
)
print("Eliminado con exito")
## ELIMINAR UN REGISTRO DE LOG_REGISTRO
tabla = dynamodb_resource.Table('log_registro')
tabla.delete_item(
    Key={
        'id_registro':3,
        'fecha_registro':'2025-09-20T11:00:00'
    }
)
print("Eliminado con exito")
## OBTENER TODOS LOS REGISTROS TABLA ALUMNO
tabla = dynamodb_resource.Table('alumno')
response = tabla.scan()
items = response['Items']
for item in items:
    print(item)
## OBTENER TODOS LOS REGISTROS TABLA PROFESOR
tabla = dynamodb_resource.Table('profesor')
response = tabla.scan()
items = response['Items']
for item in items:
    print(item)
## OBTENER TODOS LOS REGISTROS TABLA LOG_REGISTRO
tabla = dynamodb_resource.Table('log_registro')
response = tabla.scan()
items = response['Items']
for item in items:
    print(item)


## FILTRADO EN TABLA ALUMNO
tabla = dynamodb_resource.Table('alumno')
response = tabla.scan(
    FilterExpression=Attr('id_alumno').gt(2)
)
items = response['Items']
for item in items:
    print(item)

## FILTRADO EN TABLA PROFESOR (INDICE_LOCAL)
tabla = dynamodb_resource.Table('profesor')
response = tabla.scan(
    IndexName='duracionSesionIndex',
    FilterExpression=Attr('id_profesor').eq(3)
)
items = response['Items']
for item in items:
    print(item)

## FILTRADO EN TABLA PROFESOR (INDICE_GLOBAL)
tabla = dynamodb_resource.Table('log_registro')
response = tabla.scan(
    IndexName='fechaRegistroIndex',
    FilterExpression=Attr('fecha_registro').eq('2025-01-18T12:00:00')
)
items = response['Items']
for item in items:
    print(item)

## ELIMINACION CONDICIONAL EN TABLA ALUMNO

tabla = dynamodb_resource.Table('alumno')

tabla.delete_item(
    Key={
        'id_alumno':2,
        'fecha_conexion':'2025-01-18T12:00:00'
    },
    ConditionExpression=Attr('duracion_sesion').not_exists()
)

print("Eliminado con exito")
## ELIMINACION CONDICIONAL EN TABLA PROFESOR
tabla = dynamodb_resource.Table('profesor')
tabla.delete_item(
    Key={
        'id_profesor':2,
        'fecha_conexion':'2025-01-18T12:00:00'
    },
    ConditionExpression=Attr('duracion_sesion').eq(1000)
)
print("Eliminado con exito")
## ELIMINACION CONDICIONAL EN TABLA LOG_REGISTRO
tabla = dynamodb_resource.Table('log_registro')
tabla.delete_item(
    Key={
        'id_registro':2,
        'fecha_registro':'2025-01-18T12:00:00'
    },
    ConditionExpression=Attr('tipo_usuario').eq('alumno')
)
print("Eliminado con exito")

## FILTRADO CON VARIOS FILTROS EN TABLA ALUMNO
tabla = dynamodb_resource.Table('alumno')
response = tabla.scan(
    FilterExpression=Attr('id_alumno').gt(2) & Attr('fecha_conexion').eq('2025-09-20T11:00:00')
)
items = response['Items']
for item in items:
    print(item)

## FILTRADO CON VARIOS FILTROS EN TABLA PROFESOR (INDICE_LOCAL)
tabla = dynamodb_resource.Table('profesor')
response = tabla.scan(
    IndexName='duracionSesionIndex',
    FilterExpression=Attr('id_profesor').eq(3) & Attr('duracion_sesion').gt(5000)
)
items = response['Items']
for item in items:
    print(item)

## FILTRADO CON VARIOS FILTROS EN TABLA PROFESOR (INDICE_GLOBAL)
tabla = dynamodb_resource.Table('log_registro')
response = tabla.scan(
    IndexName='fechaRegistroIndex',
    FilterExpression=Attr('fecha_registro').eq('2025-11-28T17:00:00') & Attr('tipo_usuario').eq('profesor')
)
items = response['Items']
for item in items:
    print(item)


## CONSULTAS PARTIQL PARA TABLA ALUMNO
response = dynamodb.execute_statement(
    Statement="SELECT * FROM alumno"
)
for item in response['Items']:
    print(item)
## CONSULTAS PARTIQL PARA TABLA PROFESOR
response = dynamodb.execute_statement(
    Statement="SELECT * FROM profesor WHERE id_profesor = 3"
)
print(response['Items'])
## CONSULTAS PARTIQL PARA TABLA LOG_REGISTRO
response = dynamodb.execute_statement(
    Statement="SELECT * FROM log_registro WHERE tipo_usuario = 'profesor'"
)
for item in response['Items']:
    print(item)