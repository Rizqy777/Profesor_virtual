import mysql.connector
import psycopg2
import json


def obtenerDatosBD(conexion):
    cursor = conn.cursor()
    cursor.execute("""
               SELECT a.nombre AS nombre_alumno,
               a.apellidos AS apellidos_alumno
               FROM alumno a
               """)

    columnas = [desc[0] for desc in cursor.description]
    datos = [dict(zip(columnas,fila)) for fila in cursor.fetchall()]
    return datos

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    port=3306,
    database="profesor_virtual_mysql"
)

alumnosMysql = obtenerDatosBD(conn)

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    port=3307,
    database="profesor_virtual_mariadb"
)

alumnosMariaDB = obtenerDatosBD(conn)

conn = psycopg2.connect(
    host="localhost",
    user="root",
    password="1234",
    dbname="profesor_virtual_postgres",
    port=5432
)

alumnosPostgres = obtenerDatosBD(conn)

listaDefinitiva = []

listaDefinitiva.extend(alumnosMysql)
listaDefinitiva.extend(alumnosMariaDB)
listaDefinitiva.extend(alumnosPostgres)

with open("analisis_mix.json","w",encoding="utf-8") as f:
    json.dump(listaDefinitiva,f,indent=4,ensure_ascii=False)

conn.close()

print("Consulta realizada con exito")