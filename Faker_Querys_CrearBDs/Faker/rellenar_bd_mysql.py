# ----------------------------------------------------
# Script para rellenar la base de datos profesor_virtual_mysql con Faker
# Providers usados:
# 1. first_name()                  -> nombre de profesor y alumno
# 2. last_name()                   -> apellidos de profesor y alumno
# 3. random_int()                  -> edad de profesor y alumno
# 4. word()                        -> nombre de asignatura
# 5. sentence(nb_words=2)          -> nombre corto o curso
# 6. text(max_nb_chars=100)        -> descripción o contenido
# 7. random_element([...])         -> curso o dificultad
# 8. pyfloat(left_digits=1, right_digits=2, positive=True, min_value=0, max_value=10) -> nota_media
# 9. date_this_decade()            -> fecha de informe o evaluación
# 10. email()                      -> email de profesor o alumno
# 11. phone_number()               -> telefono de profesor o alumno
# ----------------------------------------------------

from faker import Faker
import mysql.connector
import random

fake = Faker('es_ES')

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    database="profesor_virtual_mysql",
    port=3306
)

cursor = conn.cursor()


#Profesores

for _ in range(5):
    cursor.execute("""
                   INSERT INTO profesor (nombre,apellidos,edad,email,telefono)
                   VALUES (%s, %s, %s, %s, %s)
                   """,(fake.first_name(),fake.last_name(),fake.random_int(min=20,max=65),fake.email(),fake.phone_number()))

#Alumnos

for _ in range(20):
    cursor.execute("""
                   INSERT INTO alumno (nombre,apellidos,edad,email,telefono)
                   VALUES (%s, %s, %s, %s, %s)
                   """,(fake.first_name(),fake.last_name(),fake.random_int(min=12,max=17),fake.email(),fake.phone_number()))


#Asignaturas

cursor.execute("SELECT id_profesor FROM profesor")
asignaturas = ["Matematicas","Fisica","Lengua","Frances","Sociales"]
profesores = [row[0] for row in cursor.fetchall()]

for _ in range(5):
    cursor.execute("""
                   INSERT INTO asignatura (nombre,id_profesor,curso)
                   VALUES (%s, %s, %s)
                   """,(fake.random_element(asignaturas),fake.random_element(profesores),fake.random_element(["1A","1B","2A","2B","3A","3B","4A","4B"])))
    
#Alumno_asignatura

cursor.execute("SELECT id_alumno FROM alumno")
alumnos = [row[0] for row in cursor.fetchall()]

cursor.execute("SELECT id_asignatura FROM asignatura")
asignaturas = [row[0] for row in cursor.fetchall()]

relaciones_alumno_asignatura = set()
for _ in range(20):
    alumno = fake.random_element(alumnos)
    asignatura = fake.random_element(asignaturas)
    relaciones_alumno_asignatura.add((alumno, asignatura))

for alumno, asignatura in relaciones_alumno_asignatura:
    cursor.execute("""
        INSERT INTO alumno_asignatura (id_alumno, id_asignatura)
        VALUES (%s, %s)
    """, (alumno, asignatura))




#Interes

for alumno_id in alumnos:
    cursor.execute("""
                   INSERT INTO interes (id_alumno,resumen)
                   VALUES (%s, %s)
                   """,(alumno_id,fake.sentence(nb_words=6)))
    

#Alumno_interes

cursor.execute("SELECT id_interes FROM interes")
intereses = [row[0] for row in cursor.fetchall()]

relaciones_alumno_interes = set()

for _ in range(20):
    alumno = fake.random_element(alumnos)
    interes = fake.random_element(intereses)
    relaciones_alumno_interes.add((alumno,interes))

for alumno,interes in relaciones_alumno_interes:
    cursor.execute("""
                   INSERT INTO alumno_interes (id_alumno,id_interes) 
                   VALUES (%s, %s)
                   """, (alumno,interes))

#Informes

for _ in range(10):
    cursor.execute("""
                   INSERT INTO informe (id_profesor, id_alumno, descripcion, fecha)
                   VALUES (%s, %s, %s, %s)
                   """,(fake.random_element(profesores),fake.random_element(alumnos),fake.text(max_nb_chars=100),fake.date_this_decade()))
    

#Conducta

cursor.execute("SELECT id_asignatura FROM asignatura")
asignaturas = [row[0] for row in cursor.fetchall()]

for _ in range(15):
    cursor.execute("""
                   INSERT INTO conducta (id_alumno, id_profesor, id_asignatura, descripcion, fecha)
                   VALUES (%s, %s, %s, %s, %s) 
                   """,(fake.random_element(alumnos),fake.random_element(profesores),fake.random_element(asignaturas),fake.text(max_nb_chars=100),fake.date_this_decade()))
    
#Calificaciones
unidades = [fake.word() for _ in range(15)]

for _ in range(20):
    cursor.execute("""
                   INSERT INTO calificacion_examen (id_asignatura,id_profesor, id_alumno, calificacion, unidad, fecha )
                   VALUES (%s, %s, %s, %s, %s, %s) 
                   """, (fake.random_element(asignaturas),fake.random_element(profesores),fake.random_element(alumnos),fake.pyfloat(left_digits=1, right_digits=2,min_value=0, max_value=10),fake.random_element(unidades),fake.date_this_decade()))
    cursor.execute("""
                   INSERT INTO calificacion_practica (id_asignatura,id_profesor, id_alumno, calificacion, unidad, fecha )
                   VALUES (%s, %s, %s, %s, %s, %s) 
                   """,  (fake.random_element(asignaturas),fake.random_element(profesores),fake.random_element(alumnos),fake.pyfloat(left_digits=1, right_digits=2,min_value=0, max_value=10),fake.random_element(unidades),fake.date_this_decade()))
    
#Ejercicios

for _ in range(20):
    cursor.execute("""
                   INSERT INTO ejercicio (id_asignatura,id_interes,id_alumno, contenido, dificultad, unidad)
                   VALUES (%s, %s, %s, %s, %s, %s)
                   """, (fake.random_element(asignaturas),fake.random_element(intereses),fake.random_element(alumnos),fake.text(max_nb_chars=100),fake.random_element(["baja","media","alta"]),fake.random_element(unidades)))

#Ejercicio_interes

cursor.execute("SELECT id_ejercicio FROM ejercicio")
ejercicios = [row[0] for row in cursor.fetchall()]

relaciones_ejercicio_interes = set()
for _ in range(30):
    ejercicio = fake.random_element(ejercicios)
    interes = fake.random_element(intereses)
    relaciones_ejercicio_interes.add((ejercicio, interes))

for ejercicio, interes in relaciones_ejercicio_interes:
    cursor.execute("""
        INSERT INTO ejercicio_interes (id_ejercicio, id_interes)
        VALUES (%s, %s)
    """, (ejercicio, interes))




#Progreso
for _ in range(20):
    cursor.execute("""INSERT INTO progreso (id_asignatura, id_alumno, unidad, evolucion, nota_media, fecha)
                   VALUES (%s, %s, %s, %s, %s, %s)
                   """, (fake.random_element(asignaturas),fake.random_element(alumnos),fake.random_element(unidades),fake.sentence(nb_words=6),fake.pyfloat(left_digits=1, right_digits=2,min_value=0, max_value=10),fake.date_this_decade()))
    


conn.commit()
conn.close()

print("Completado sin errores")