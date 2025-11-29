import json
import boto3
import pymysql
import os
from boto3.dynamodb.conditions import Attr
from dotenv import load_dotenv
load_dotenv()
import decimal

## FUNCION PARA LA SERIALIZACION DE DECIMALES DE DYNAMO A JSON
def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError

## CONEXION AWS
session = boto3.session.Session(
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
    region_name=os.getenv("AWS_REGION", "us-east-1")
)

rds = session.client('rds')

## CONEXION A BD MYSQL PARA CONSULTA
config = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS"),
    "host": "profesor-virtual-rds.cp8q2ae2y0j6.us-east-1.rds.amazonaws.com"
}
DB_NAME = "profesor_virtual_RDS"
cnx = pymysql.connect(**config)
cursor = cnx.cursor()
cursor.execute(f"USE {DB_NAME}")
## CONSULTA MYSQL PARA OBTENER CALIFICACIONES , NOMBRE DE ALUMNO Y ASIGNATURA
cursor.execute("SELECT a.nombre,c.calificacion,asig.nombre FROM alumno a " \
"JOIN calificacion_examen c on a.id_alumno = c.id_alumno " \
"JOIN asignatura asig on c.id_asignatura = asig.id_asignatura")
calificaciones = cursor.fetchall()


## CONEXION A DYNAMODB PARA CONSULTAS
dynamodb_resource = session.resource('dynamodb')

## CONSULTA FILTRADA A TABLA ALUMNO
tabla = dynamodb_resource.Table('alumno')
response = tabla.scan(
    FilterExpression=Attr('id_alumno').gt(2) & Attr('fecha_conexion').eq('2025-09-20T11:00:00')
)
alumno = response['Items']

## FILTRADO CON VARIOS FILTROS EN TABLA PROFESOR (INDICE_LOCAL)
tabla = dynamodb_resource.Table('profesor')
response = tabla.scan(
    IndexName='duracionSesionIndex',
    FilterExpression=Attr('id_profesor').eq(3) & Attr('duracion_sesion').gt(5000)
)
profesor = response['Items']

## FILTRADO CON VARIOS FILTROS EN TABLA PROFESOR (INDICE_GLOBAL)
tabla = dynamodb_resource.Table('log_registro')
response = tabla.scan(
    IndexName='fechaRegistroIndex',
    FilterExpression=Attr('fecha_registro').eq('2025-11-28T17:00:00') & Attr('tipo_usuario').eq('profesor')
)
log_registro = response['Items']


## GENERAR ESTRUCTURA JSON
data = {
    "dynamo_alumno": alumno,
    "dynamo_profesor": profesor,
    "dynamo_log_registro": log_registro,
    "rds_calificaciones_por_alumno":calificaciones
}
## GENERAR JSON
with open("bd_combinadas.json","w",encoding="utf-8") as f:
    json.dump(data,f,ensure_ascii=False,indent=2,default=decimal_default)
