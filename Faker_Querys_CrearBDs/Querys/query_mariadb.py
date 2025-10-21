
import mysql.connector
import json
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    port=3307,
    database="profesor_virtual_mariadb"
)

cursor = conn.cursor()


# Consulta para obtener los ejercicios de una determinada unidad
# de una asignatura de un alumno segun su interes y dificultad 

cursor.execute("""
               SELECT a.nombre AS nombre_alumno,
               a.apellidos AS apellidos_alumno,
               asig.nombre AS asignatura,
               i.resumen AS resumen_interes,
               e.unidad AS unidad,
               e.contenido AS contenido,
               e.dificultad AS dificultad
               FROM ejercicio e
               JOIN alumno a ON e.id_alumno = a.id_alumno
               JOIN asignatura asig ON e.id_asignatura = asig.id_asignatura
               JOIN interes i ON e.id_interes = i.id_interes
               """)

columnas = [desc[0] for desc in cursor.description]
datos = [dict(zip(columnas,fila)) for fila in cursor.fetchall()]

with open("analisis_mariadb.json","w",encoding="utf-8") as f:
    json.dump(datos,f,indent=4,ensure_ascii=False)

conn.close()

print("Consulta realizada con exito")