
import psycopg2
import json
from datetime import date, datetime

conn = psycopg2.connect(
    host="localhost",
    user="root",
    password="1234",
    port=5432,
    dbname="profesor_virtual_postgres"
)

cursor = conn.cursor()

# Obtener la conducta de un alumno en una determinada asignatura por un determinado profesor
# en una determinada fecha

cursor.execute("""
               SELECT a.nombre AS nombre_alumno,
               a.apellidos AS apellidos_alumno,
               p.nombre AS nombre_profesor,
               p.apellidos AS apellidos_profesor,
               asig.nombre AS asignatura,
               c.descripcion AS descripcion,
               c.fecha AS fecha_conducta
               FROM conducta c
               JOIN alumno a ON c.id_alumno = a.id_alumno
               JOIN asignatura asig ON c.id_asignatura = asig.id_asignatura
               JOIN profesor p ON c.id_profesor = p.id_profesor
               """)

columnas = [desc[0] for desc in cursor.description]
datos = [dict(zip(columnas,fila)) for fila in cursor.fetchall()]

for fila in datos:
    if isinstance(fila["fecha_conducta"], (date, datetime)):
        fila["fecha_conducta"] = fila["fecha_conducta"].isoformat()

with open("analisis_postgres.json","w",encoding="utf-8") as f:
    json.dump(datos,f,indent=4,ensure_ascii=False)

conn.close()

print("Consulta realizada con exito")