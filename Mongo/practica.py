from pymongo import MongoClient
import os
from faker import Faker
import json

user = os.getenv("USER_BD")
password = os.getenv("PASS_BD")
print(user)
print(password)
client = MongoClient(f"mongodb+srv://{user}:{password}@cluster0.f9nrpbf.mongodb.net/")
fake = Faker()


baseDatos = client["TV_StreamDB"]

coleccion = baseDatos["series"]

""" ## Insertar series de TV con todos los campos

for i in range(50):
    generos_reales = [
        "Drama",
        "Comedia",
        "Acción",
        "Aventura",
        "Ciencia Ficción",
        "Fantasía",
        "Terror",
        "Misterio",
        "Romance",
        "Animación",
        "Documental",
        "Crimen",
        "Thriller",
        "Musical",
        "Histórico",
        "Western",
    ]
    serie = {
        "titulo": fake.sentence(nb_words=3),
        "plataforma": fake.company(),
        "temporadas": fake.random_int(min=1, max=10),
        "genero": fake.random_choices(elements=generos_reales, length=2),
        "puntuacion": fake.pyfloat(min_value=1, max_value=10, right_digits=2),
        "finalizada": fake.boolean(),
        "año_estreno": fake.random_int(min=1970, max=2025),
    }
    insercion = coleccion.insert_one(serie)
    print(f"Serie {i} insertada con ID: {insercion.inserted_id}")



## Insertar series de TV sin algunos campos
for i in range(10):
    generos_reales = [
        "Drama",
        "Comedia",
        "Acción",
        "Aventura",
        "Ciencia Ficción",
        "Fantasía",
        "Terror",
        "Misterio",
        "Romance",
        "Animación",
        "Documental",
        "Crimen",
        "Thriller",
        "Musical",
        "Histórico",
        "Western",
    ]
    serie = {
        "titulo": fake.sentence(nb_words=3),
        "plataforma": fake.company(),
        "temporadas": fake.random_int(min=1, max=10),
        "genero": fake.random_choices(elements=generos_reales, length=2),
        "finalizada": fake.boolean(),
        "año_estreno": fake.random_int(min=1970, max=2025),
    }
    insercion = coleccion.insert_one(serie)
    print(
        f"Serie sin algunos campos numero {i} insertada con ID: {insercion.inserted_id}"
    )
 """
## Consultas

## Maratones Largas: Series que tengan más de 5 temporadas y una puntuación superior a 8.0.
miquery = {"temporadas": {"$gt": 5}, "puntuacion": {"$gt": 8.0}}
maratones = list(coleccion.find(miquery))

for s in maratones:
    print(s)

## Joyas Recientes de Comedia: Series del género "Comedia" que hayan sido estrenadas a partir del año 2020.

miquery = {"genero": "Comedia", "año_estreno": {"$gte": 2020}}
comedias = list(coleccion.find(miquery))

for s in comedias:
    print(s)

## Contenido Finalizado: Series que ya hayan marcado su estado finalizada como True.

miquery = {"finalizada": True}
finalizadas = list(coleccion.find(miquery))
for s in finalizadas:
    print(s)
## Series con puntuacion mayor a 7 y genero ciencia ficcion

miquery = {"puntuacion": {"$gte": 5}, "genero": "Ciencia Ficción"}
inventadas = list(coleccion.find(miquery))
for s in inventadas:
    print(s)

## Series estrenadas entre 2010 y 2020 con más de 3 temporadas
miquery = {"año_estreno": {"$gte": 2010, "$lte": 2020}, "temporadas": {"$gt": 3}}
inventadas2 = list(coleccion.find(miquery))
for s in inventadas2:
    print(s)

lista_maratones = []
for doc in maratones:
    doc["_id"] = str(doc["_id"])
    lista_maratones.append(doc)


with open("maratones.json", "w", encoding="utf-8") as f:
    json.dump(lista_maratones, f, ensure_ascii=False, indent=4)

lista_comedias = []
for doc in comedias:
    doc["_id"] = str(doc["_id"])
    lista_comedias.append(doc)


with open("comedias.json", "w", encoding="utf-8") as f:
    json.dump(lista_comedias, f, ensure_ascii=False, indent=4)

lista_finalizadas = []
for doc in finalizadas:
    doc["_id"] = str(doc["_id"])
    lista_finalizadas.append(doc)


with open("finalizadas.json", "w", encoding="utf-8") as f:
    json.dump(lista_finalizadas, f, ensure_ascii=False, indent=4)

lista_inventadas = []
for doc in inventadas:
    doc["_id"] = str(doc["_id"])
    lista_inventadas.append(doc)


with open("inventadas.json", "w", encoding="utf-8") as f:
    json.dump(lista_inventadas, f, ensure_ascii=False, indent=4)

lista_inventadas2 = []
for doc in inventadas2:
    doc["_id"] = str(doc["_id"])
    lista_inventadas2.append(doc)

with open("inventadas2.json", "w", encoding="utf-8") as f:
    json.dump(lista_inventadas2, f, ensure_ascii=False, indent=4)
