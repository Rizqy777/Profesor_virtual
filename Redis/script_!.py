import redis
import random
import os
import json
from datetime import datetime, timedelta
from redis.commands.json.path import Path
from redis.commands.search.field import TextField, NumericField
from redis.commands.search.index_definition import IndexDefinition, IndexType
import redis.commands.search.aggregation as aggregations
import redis.commands.search.reducers as reducers


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

# 1 - Crear registros clave-valor(0.25 puntos)

# Con bucles que van de 0 a 5 se crean claves para profesores y alumnos y en cada iteracion se genera una fecha aletaria y duracion aleatoria para cada tipo de usuario, se utiliza hset para crear registros complejos en redis
for id_profesor in range(1,6):
    clave = f"profesor:{id_profesor}"
    r.hset(clave, mapping={
        "fecha_conexion":fecha_aleatoria().isoformat(),
        "duracion_sesion":duracion_sesion_aleatorio()
    })

for id_alumno in range(1,6):
    clave = f"alumno:{id_alumno}"
    r.hset(clave, mapping={
        "fecha_conexion":fecha_aleatoria().isoformat(),
        "duracion_sesion":duracion_sesion_aleatorio()
    })

print("Registros insertados con exito")


# 2 - Obtener y mostrar el número de claves registradas (0.25 puntos)
# Se obtienen todas las claves utilizando la expresion regular * y el metodo keys() y posteriormente se calcula cuantas son con el metodo len()

claves = r.keys("*")
numero_claves = len(claves)
print("El numero de registradas es: ", numero_claves)


# 3 - Obtener y mostrar un registro en base a una clave (0.25 puntos)
# Se usa hgetall() debido a que es un registro tipo hash, se indica la clave y se imprime el resultado

profesor = r.hgetall("profesor:3")
print("Datos profesor: ", profesor)
alumno = r.hgetall("alumno:4")
print("Datos alumno: ", alumno)

# 4 - Actualizar el valor de una clave y mostrar el nuevo valor(0.25 puntos)
# Se vuelve a usar el metodo hset() para insertar o actualizar datos complejos , indiciando en el parametro mapping={} aquello que queremos modificar unicamente, posteriormente se obtiene y se imprime el resultado

r.hset("profesor:1" , mapping={
    "duracion_sesion":0
})
profesor = r.hgetall("profesor:1")
print("Datos profesor: ", profesor)


# 5 - Eliminar una clave-valor y mostrar la clave y el valor eliminado(0.25 puntos)
# Generamos la clave y obtenemos el registro hgetall() para mostrarlo posteriormente y finalmente eliminamos con delete()

clave = "profesor:1"
datos = r.hgetall(clave)
r.delete(clave)

print("Datos eliminador: ", clave, "-> ", datos)


# 6 - Obtener y mostrar todas las claves guardadas (0.25 puntos)
# Obtenemos todas las claves con el metodo keys() y la expresion regular "*"


claves = r.keys("*")
print(claves)

# 7 - Obtener y mostrar todos los valores guardados(0.25 puntos)
# Obtenemos todas las claves con keys(*) y posteriormente con un bucle se recorren asignando cada clave al metodo hgetall() para posteriomrente imprimiar los resultados


claves = r.keys("*")

for clave in claves:
    datos = r.hgetall(clave)
    print(f"{clave}->{datos}")


# 8 - Obtener y mostrar varios registros con una clave con un patrón en común usando * (0.5 puntos)
# Obtenemos todas las claves que cumplen con el patron "alumno:", recorremos cada clave y obtenemos datos asignando las claves al metodo hgetall()


claves = r.keys("alumno:*")

for clave in claves:
    datos = r.hgetall(clave)
    print(f"{clave}->{datos}")


# 9 - Obtener y mostrar varios registros con una clave con un patrón en común usando [] (0.5 puntos)
# Obtenemos todas las claves que cumplen con el rango de claves [1-3], recorremos cada clave y obtenemos datos asignando las claves al metodo hgetall()


claves = r.keys("alumno:[1-3]")

for clave in claves:
    datos = r.hgetall(clave)
    print(f"{clave}->{datos}")



# 10 - Obtener y mostrar varios registros con una clave con un patrón en común usando ? (0.5 puntos)
# Obtenemos todas las claves que cumplen con el patron "profesor:" seguido de cualquier caracter, recorremos cada clave y obtenemos datos asignando las claves al metodo hgetall()


claves = r.keys("profesor:?")

for clave in claves:
    datos = r.hgetall(clave)
    print(f"{clave}->{datos}")



# 11 - Obtener y mostrar varios registros y filtrarlos por un valor en concreto. (0.5 puntos)


# Obtenemos todas las claves que cumplen con el patron "profesor:", recorremos cada clave y obtenemos datos asignando, de los datos extraemos la fecha dandole formato ISO, y de la fecha extraemos el mes,
# si el mes coincide con el del filtro, en este caso el 11, agregamos los pares de clave:datos a la variable coincidencias para posteriomente mostrar
claves = r.keys("profesor:*")
coincidencias = []

mes_filtro = 11

for clave in claves:
    datos = r.hgetall(clave)
    fecha = datetime.fromisoformat(datos["fecha_conexion"])
    if fecha.month == mes_filtro:
        coincidencias.append({clave:datos})
    
print(f"{coincidencias}")


# 12 - Actualizar una serie de registros en base a un filtro (por ejemplo aumentar su valor en 1 )(0.5 puntos)
# Obtenemos todas las claves que cumplen con el patron "profesor:", recorremos cada clave y obtenemos datos asignando, de los datos extraemos la fecha dandole formato ISO, y de la fecha extraemos el mes,
# si el mes coincide con el del filtro, en este caso el 11, actualizamos la duracion de la sesion en 1000segundos guardando con el metodo hset() asignando clave y atributo a actualizar dentro de mapping={}


claves = r.keys("profesor:*")
coincidencias = []

mes_filtro = 11

for clave in claves:
    datos = r.hgetall(clave)
    fecha = datetime.fromisoformat(datos["fecha_conexion"])
    if fecha.month == mes_filtro:
        duracion_sesion_actual = int(datos.get("duracion_sesion"))
        duracion_nueva = duracion_sesion_actual + 1000
        r.hset(clave,mapping={
            "duracion_sesion":duracion_nueva
        })


# 13 - Eliminar una serie de registros en base a un filtro (0.5 puntos)
# Obtenemos todas las claves que cumplen con el patron "profesor:", recorremos cada clave y obtenemos datos asignando, de los datos extraemos la fecha dandole formato ISO, y de la fecha extraemos el mes,
# si el mes coincide con el del filtro, eliminamos el registro con el metodo delete() asignandole la clave de la iteracion actual



claves = r.keys("profesor:*")
coincidencias = []

mes_filtro = 10

for clave in claves:
    datos = r.hgetall(clave)
    fecha = datetime.fromisoformat(datos["fecha_conexion"])
    if fecha.month == mes_filtro:
        r.delete(clave)


# 14 - Crear una estructura en JSON de array de los datos que vayais a almacenar(0.5 puntos)
# Creo una estructura para json compleja con un campo id agregado tanto para alumnos como profesores y guardo con el metodo set y json.dumps() que vuelca estructuras json en redis.
estructura = {
    "profesores":[
        {"id": 7, "fecha_conexion": "2025-09-02T15:48:00", "duracion_sesion": 4500},
        {"id": 6, "fecha_conexion": "2025-10-06T13:28:00", "duracion_sesion": 2500}
    ],
    "alumnos":[
        {"id": 7, "fecha_conexion": "2025-11-02T12:18:00", "duracion_sesion": 6500},
        {"id": 6, "fecha_conexion": "2025-09-06T14:28:00", "duracion_sesion": 3500}
    ]
}

r.set("datos_usuarios",json.dumps(estructura))


# 15 - Realizar un filtro por cada atributo de la estructura JSON anterior (0.5 puntos)
# Obtengo el json previamente almacenado con .get(), extraigo la estructura del json con json.loads(), recorro esa estructura tanto para profesores como para alumnos y si de cada fila obtenida la duracion de sesion o fecha
# de conexion cumple con el filtro, lo imprimo por pantalla al alumno o al profesor para mostrar sus datos.

datos_json = r.get("datos_usuarios")
estructura = json.loads(datos_json)

print("Filtro profesores con duracion de sesion menor o igual a 40000s")
for profesor in estructura["profesores"]:
    if profesor["duracion_sesion"] <= 4000:
        print(profesor)

print("Filtro para alumnos con conexion en el mes de Noviembre")
for alumno in estructura["alumnos"]:
    fecha = alumno["fecha_conexion"]
    mes = int(fecha.split("-")[1])
    if mes == 11:
        print(alumno)


# 16 - Crear una lista en Redis (0.25 puntos)
# Creo una lista, recorro cada fila con el bucle for y almaceno cada registro como un json con el metodo r.push() para que agregue el registro en la ultima posicion de la lista

alumnos = [
    {"nombre":"Alumno_1","duracion_sesion":4500},
    {"nombre":"Alumno_2","duracion_sesion":6500},
    {"nombre":"Alumno_3","duracion_sesion":2000},
    {"nombre":"Alumno_4","duracion_sesion":1500},
    {"nombre":"Alumno_5","duracion_sesion":7500}
]

for alumno in alumnos:
    r.rpush("alumnos",json.dumps(alumno))

# 17 - Obtener elementos de una lista con un filtro en concreto(0.5 puntos)
# Obtengo todos las filas de la lista con lrange() indicando el nombre de la lista, indice inicial y final. Recorro cada elemento de la lista obteniendo sus datos con json.loads()
# Si la duracion de la sesion del valor obtenido es mayor a 4000segundos, imprimo por pantalla

elementos= r.lrange("alumnos",0,-1)

print("Alumnos con duracion de sesion mayor a 5000s")

for elemento in elementos:
    alumno = json.loads(elemento)
    if alumno["duracion_sesion"]>4000:
        print(alumno)

# 18 - Crea datos con índices, definiendo un esquema de al menos tres campos (0.5 puntos)
# Creo datos con indices y 3 campos y posteriomento los almaceno en redis
profesores = [
    {"id": 6, "nombre": "Ana", "edad": 31, "duracion_sesion": 4500},
    {"id": 7, "nombre": "Luis", "edad": 45, "duracion_sesion": 6500},
    {"id": 8, "nombre": "Marta", "edad": 29, "duracion_sesion": 2000},
]
for profesor in profesores:
    r.json().set(f"profesor:{profesor['id']}",Path.root_path(),profesor)

# Creo el esquema indicando los campos que voy a indexar y su tipo
esquema = (
    TextField("$.nombre",as_name="nombre"),
    NumericField("$.edad",as_name="edad"),
    NumericField("$.duracion_sesion",as_name="duracion_sesion")
)
# Creo el indice con el metodo ft() asignandole un nombre en este caso "indice:profesores", le paso como parametro el esquema y en la deficion indico que sera aplicado a los registros que empiecen por profesor: y sean de tipo JSON
indiceCreado = r.ft("indice:profesores").create_index(
    esquema,
    definition=IndexDefinition(
        prefix=["profesor:"],
        index_type=IndexType.JSON
    )
)


# 19 - Realiza una búsqueda con índices en base a un campo(0.5 puntos)
# Obtengo el indice creado y ejecuto una busqueda por el atributo duracion_sesion donde su valor sea 4000 o mayor
resultados = r.ft("indice:profesores").search("@duracion_sesion:[4000 +inf]")

# Recorro resultados en formato docs y lo muestro por pantalla obteneniendo el id y el diccionario de claves y valores
for doc in resultados.docs:
    print(doc.id, doc.__dict__) 

# 20 - Realiza un group  by usando los índices(0.5 puntos)
# Creo consulta de agregacion para todos los documentos donde se agrupan por edad y se cuenta cuantos registros hay por cada edad mostrandolos como total.
groupby = aggregations.AggregateRequest("*").group_by(
    '@edad',
    reducers.count().alias("total")
)
# Obtengo el indice y agrupo por edades
resultado = r.ft("indice:profesores").aggregate(groupby)
# Recorro cada uno y lo muestro
for fila in resultado.rows:
    print(fila)
