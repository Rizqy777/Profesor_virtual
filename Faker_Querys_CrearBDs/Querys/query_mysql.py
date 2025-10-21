
import mysql.connector
import json
from datetime import date, datetime

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    port=3306,
    database="profesor_virtual_mysql"
)

# Consulta para obtener alumnos y sus calificaciones para una determinada
# unidad en un determinado examen calificado por un determinado profesor
# en una determinada fecha


cursor = conn.cursor()

cursor.execute("""
               SELECT a.nombre AS nombre_alumno,
               a.apellidos AS apellidos_alumno,
               asig.nombre AS asignatura,
               p.nombre AS nombre_profesor,
               p.apellidos AS apellidos_profesor,
               c.calificacion AS calificacion,
               c.fecha AS fecha_calificacion,
               c.unidad AS unidad
               FROM calificacion_examen c
               JOIN alumno a ON c.id_alumno = a.id_alumno
               JOIN profesor p ON c.id_profesor = p.id_profesor
               JOIN asignatura asig ON c.id_asignatura = asig.id_asignatura;
               """)

columnas = [desc[0] for desc in cursor.description]
datos = [dict(zip(columnas,fila)) for fila in cursor.fetchall()]

for fila in datos:
    if isinstance(fila["fecha_calificacion"], (date, datetime)):
        fila["fecha_calificacion"] = fila["fecha_calificacion"].isoformat()


with open("analisis_mysql.json","w",encoding="utf-8") as f:
    json.dump(datos,f,indent=4,ensure_ascii=False)

conn.close()

print("Consulta realizada con exito")