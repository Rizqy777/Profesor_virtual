import os
from dotenv import load_dotenv
load_dotenv()
import botocore
import boto3
import pymysql
from faker import Faker

## ESTABLECER CONEXION CON AWS
session = boto3.session.Session(
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
    region_name=os.getenv("AWS_REGION", "us-east-1")
)

## SELECCIONAR CLIENTE RDS
rds = session.client('rds')

## CREAR INSTANCIA DE BD
try:
    rds.create_db_instance(
        DBInstanceIdentifier="profesor-virtual-RDS",
        AllocatedStorage=20,
        DBInstanceClass="db.t4g.micro",
        Engine="mysql",
        MasterUsername=os.getenv("DB_USER"),
        MasterUserPassword=os.getenv("DB_PASS"),
        PubliclyAccessible=True
    )
    waiter = rds.get_waiter('db_instance_available')
    waiter.wait(DBInstanceIdentifier="profesor-virtual-RDS")
    info = rds.describe_db_instances(DBInstanceIdentifier="profesor-virtual-RDS")
    endpoint = info['DBInstances'][0]['Endpoint']['Address']
    print("Endpoint:", endpoint)
except botocore.exceptions.ClientError as e:
    print("Error de cliente AWS:", e)
except Exception as e:
    print("Error inesperado:", e) 

## CONECTARSE A BD MYSQL
config = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS"),
    "host": "profesor-virtual-rds.cp8q2ae2y0j6.us-east-1.rds.amazonaws.com"
}
DB_NAME = "profesor_virtual_RDS"
cnx = pymysql.connect(**config)
cursor = cnx.cursor()
cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")

cursor.execute(f"USE {DB_NAME}")

## CREAR TABLA PROFESOR
cursor.execute(
    """
    CREATE TABLE profesor(
    id_profesor INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(50),
    apellidos VARCHAR(50),
    edad INT,
    email VARCHAR(50),
    telefono VARCHAR(20)
    );
    """
    
)
## CREAR TABLA ALUMNO
cursor.execute(
    """
    CREATE TABLE alumno(
    id_alumno INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(50),
    apellidos VARCHAR(50),
    edad INT,
    email VARCHAR(50),
    telefono VARCHAR(20)
    );

    """
    
)
## CREAR TABLA ASIGNATURA
cursor.execute(
    """
    CREATE TABLE asignatura(
    id_asignatura INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(50),
    id_profesor INT,
    curso VARCHAR(10),
    FOREIGN KEY (id_profesor) REFERENCES profesor(id_profesor)
    );
    """
    
)
## CREAR TABLA ALUMNO_ASIGNATURA (LAS ASIGNATURAS DONDE ESTA MATRICULADO)
cursor.execute(
    """
    CREATE TABLE alumno_asignatura (
    id_alumno INT,
    id_asignatura INT,
    PRIMARY KEY (id_alumno, id_asignatura),
    FOREIGN KEY (id_alumno) REFERENCES alumno(id_alumno),
    FOREIGN KEY (id_asignatura) REFERENCES asignatura(id_asignatura)
    );
    """
    
)
## CREAR TABLA INFORME
cursor.execute(
    """
    CREATE TABLE informe(
    id_informe INT PRIMARY KEY AUTO_INCREMENT,
    id_profesor INT,
    id_alumno INT,
    descripcion TEXT,
    fecha DATE,
    Foreign Key (id_profesor) REFERENCES profesor(id_profesor),
    Foreign Key (id_alumno) REFERENCES alumno(id_alumno)
    );
    """
    
)
## CREAR TABLA CONDUCTA
cursor.execute(
    """
    CREATE TABLE conducta(
    id_conducta int PRIMARY KEY AUTO_INCREMENT,
    id_alumno int,
    id_profesor int,
    id_asignatura int,
    descripcion TEXT,
    fecha DATE,
    Foreign Key (id_profesor) REFERENCES profesor(id_profesor),
    Foreign Key (id_alumno) REFERENCES alumno(id_alumno)
    );
    """
    
)
## CREAR TABLA CALIFICACION_EXAMEN
cursor.execute(
    """
    CREATE Table calificacion_examen(
    id_calificacion INT PRIMARY KEY AUTO_INCREMENT,
    id_asignatura INT,
    id_profesor INT,
    id_alumno INT,
    calificacion DOUBLE,
    unidad VARCHAR(50),
    fecha DATE,
    Foreign Key (id_profesor) REFERENCES profesor(id_profesor),
    Foreign Key (id_alumno) REFERENCES alumno(id_alumno)
    );
    """
    
)
## CREAR TABLA CALIFICACION_PRACTICA
cursor.execute(
    """
    CREATE Table calificacion_practica(
    id_calificacion INT PRIMARY KEY AUTO_INCREMENT,
    id_asignatura INT,
    id_profesor INT,
    id_alumno INT,
    calificacion DOUBLE,
    unidad VARCHAR(50),
    fecha DATE,
    Foreign Key (id_profesor) REFERENCES profesor(id_profesor),
    Foreign Key (id_alumno) REFERENCES alumno(id_alumno)
    );
    """
    
)
## CREAR TABLA INTERES
cursor.execute(
    """
    CREATE TABLE interes(
    id_interes INT PRIMARY KEY AUTO_INCREMENT,
    id_alumno INT,
    resumen VARCHAR(255),
    Foreign Key (id_alumno) REFERENCES alumno(id_alumno)
    );

    """
    
)
## CREAR TABLA ALUMNO_INTERES (INTERES DE CADA ALUMNO)
cursor.execute(
    """
    CREATE TABLE alumno_interes (
    id_alumno INT,
    id_interes INT,
    PRIMARY KEY (id_alumno, id_interes),
    FOREIGN KEY (id_alumno) REFERENCES alumno(id_alumno),
    FOREIGN KEY (id_interes) REFERENCES interes(id_interes)
    );

    """
    
)

## CREAR TABLA EJERCICIO

cursor.execute(
    """
    CREATE TABLE ejercicio(
    id_ejercicio INT PRIMARY KEY AUTO_INCREMENT,
    id_asignatura INT,
    id_interes int,
    id_alumno INT,
    contenido TEXT,
    dificultad VARCHAR(10),
    unidad VARCHAR(50),
    Foreign Key (id_alumno) REFERENCES alumno(id_alumno),
    Foreign Key (id_asignatura) REFERENCES asignatura(id_asignatura),
    Foreign Key (id_interes) REFERENCES interes(id_interes)
    );
    """
    
)
## CREAR TABLA EJERCICIO_INTERES (EJERCICIO GENERADO APARTIR DE UN INTERES)
 
cursor.execute(
    """
    CREATE TABLE ejercicio_interes (
    id_ejercicio INT,
    id_interes INT,
    PRIMARY KEY (id_ejercicio, id_interes),
    FOREIGN KEY (id_ejercicio) REFERENCES ejercicio(id_ejercicio),
    FOREIGN KEY (id_interes) REFERENCES interes(id_interes)
    );
    """
    
)

## CREAR TABLA PROGRESO

cursor.execute(
    """
    CREATE Table progreso(
    id_progreso INT PRIMARY KEY AUTO_INCREMENT,
    id_asignatura INT,
    id_alumno INT,
    unidad VARCHAR(50),
    evolucion VARCHAR(255),
    nota_media DOUBLE,
    fecha DATE,
    Foreign Key (id_asignatura) REFERENCES asignatura(id_asignatura),
    Foreign Key (id_alumno) REFERENCES alumno(id_alumno)
    );

    """
    
)
## GUARDAR CAMBIOS
cnx.commit()
print("Base datos creada con exito")


## RELLENAR BD CON FAKER
fake = Faker('es_ES')


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
    


cnx.commit()
print("Completado sin errores")

## CONSULTAS

# CONSULTA EN TABLA ALUMNO
cursor.execute("SELECT * FROM alumno")
alumnos = cursor.fetchall()
for alumno in alumnos:
    print(alumno)

# CONSULTA EN TABLA PROFESOR
cursor.execute("SELECT * FROM profesor")
profesores = cursor.fetchall()
for profesor in profesores:
    print(profesor)

# CONSULTA EN TABLA CALIFICACIONES
cursor.execute("SELECT a.nombre,c.calificacion,asig.nombre FROM alumno a " \
"JOIN calificacion_examen c on a.id_alumno = c.id_alumno " \
"JOIN asignatura asig on c.id_asignatura = asig.id_asignatura")
calificaciones = cursor.fetchall()
for calificacion in calificaciones:
    print(calificacion)