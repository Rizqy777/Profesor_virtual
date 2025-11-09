import redis
import random
import mysql.connector
from datetime import datetime, timedelta
from redis.commands.json.path import Path

conexionRedis = redis.ConnectionPool(host='localhost', port=6379, db=0,decode_responses=True)
r = redis.Redis(connection_pool=conexionRedis)


# Funcion que crea una fecha aleatoria entre dos rangos de fecha inicial y final obteniendo los segundos entre ambas fechas y transformandolo en una fecha
def fecha_aleatoria():
    # Fecha inicial y final
    inicio = datetime(2025, 9, 1)
    fin = datetime(2025, 11, 30, 23, 59)
    # Diferencia en segundos
    delta_segundos = int((fin - inicio).total_seconds())
    # Generar un número aleatorio de segundos
    segundos_aleatorios = random.randint(0, delta_segundos)
    return inicio + timedelta(seconds=segundos_aleatorios)

# Funciona para obtener una cantidad de segundos aleatorios que simbolizan el tiempo que duro la sesion de un usuario, para ello se utiliza random.
def duracion_sesion_aleatorio():
    segundos_aleatorios = random.randint(1000, 100000)
    return segundos_aleatorios



# 21 - Obtén datos de alguna de las bases de datos de la tarea anterior  mediante una sql e incluyelos en Redis(1 punto)

# Establezco conexion con la BD de MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    port=3306,
    database="profesor_virtual_mysql"
)
cursor = conn.cursor()
# Obtengo datos de la tabla profesor de la BD
cursor.execute("SELECT id_profesor,nombre,edad from profesor")
profesores = cursor.fetchall()

# Recorro cada dato obtenido y lo almaceno en un nuevo registro json de redis con el metodo set() asigando como clave el patron "profesor:+id_base_de_datos" y genero fechas y duraciones de sesion aleatorias
for profesor in profesores:
    clave = f"profesor:{profesor[0]}"
    r.json().set(clave,Path.root_path(),{
        "id":profesor[0],
        "nombre":profesor[1],
        "edad":profesor[2],
        "fecha_conexion":fecha_aleatoria().isoformat(),
        "duracion_sesion":duracion_sesion_aleatorio()
    })
    print(profesor[1])


# 22 - Obtén datos de la base de datos de Redis e incluyelos en de alguna de las bases de datos de la tarea anterior (1 puntos)
# Obtengo todos las claves con el patron "profesor:"

clavesProfesor = r.keys("profesor:*")
# Recorro cada clave, obtengo el tipo de clave para confirmar si es json o hash ya que cada tipo tiene un metodo de obtencion diferente
for clave in clavesProfesor:
    tipo = r.type(clave)
    if isinstance(r.type(clave), bytes):
        tipo = tipo.decode()
    
    if tipo == "hash":
        profesor = r.hgetall(clave)
    else:
        profesor = r.json().get(clave)
 # Una vez obtenido el dato, extraigo el id de la clave, la duracion de la sesion y la fecha. Si la fecha es nula , genero una aleatoria
    id_usuario = int(clave.split(":")[1])
    duracion_sesion = int(profesor.get("duracion_sesion", 0))
    fecha_conexion = profesor.get("fecha_conexion")
    if fecha_conexion is None:
        fecha_conexion = fecha_aleatoria().isoformat()
    fecha_mysql = fecha_conexion.replace("T", " ")
# Genera sentencia sql para insertar en la tabla log previamente creada en mysql y posteriormente ejecuto la consulta
    sql = """
    INSERT INTO log (id_usuario, tipo_usuario, duracion_sesion, fecha_conexion)
    VALUES (%s, %s, %s, %s )
    """
    cursor.execute(sql,(id_usuario,"profesor",duracion_sesion,fecha_conexion))
    print(f"{id_usuario}, {duracion_sesion}, {fecha_conexion}")

conn.commit()

# Mismo procedimiento que antes pero esta vez para alumnos.
clavesAlumno = r.keys("alumno:*")

for clave in clavesAlumno:
    tipo = r.type(clave)
    if isinstance(r.type(clave), bytes):
        tipo = tipo.decode()
    
    if tipo == "hash":
        alumno = r.hgetall(clave)
    else:
        alumno = r.json().get(clave)

    id_usuario = int(clave.split(":")[1])
    duracion_sesion = int(alumno.get("duracion_sesion", 0))
    fecha_conexion = alumno.get("fecha_conexion")
    if fecha_conexion is None:
        fecha_conexion = fecha_aleatoria().isoformat()
    fecha_mysql = fecha_conexion.replace("T", " ")
    sql = """
    INSERT INTO log (id_usuario, tipo_usuario, duracion_sesion, fecha_conexion)
    VALUES (%s, %s, %s, %s )
    """
    cursor.execute(sql,(id_usuario,"alumno",duracion_sesion,fecha_conexion))
    print(f"{id_usuario}, {duracion_sesion}, {fecha_conexion}")

conn.commit()