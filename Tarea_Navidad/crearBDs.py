import mysql.connector
import redis
import json
from pymongo import MongoClient
from datetime import datetime, timedelta

try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='1234'
    )
    cursor = conn.cursor()
    print("Conexión exitosa a MySQL")

    # Crear bds
    cursor.execute("DROP DATABASE IF EXISTS trivial_mysql")
    cursor.execute("CREATE DATABASE trivial_mysql")
    cursor.execute("USE trivial_mysql")

    # Crear tablas
    cursor.execute("""
        CREATE TABLE preguntas (
            id INT PRIMARY KEY AUTO_INCREMENT,
            texto VARCHAR(500) NOT NULL,
            nivel ENUM('fácil', 'medio', 'difícil') NOT NULL,
            fecha_registro DATE NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE opciones (
            id INT PRIMARY KEY AUTO_INCREMENT,
            pregunta_id INT NOT NULL,
            texto_opcion VARCHAR(200) NOT NULL,
            es_correcta BOOLEAN NOT NULL,
            FOREIGN KEY (pregunta_id) REFERENCES preguntas(id)
        )
    """)

    # Insertar datos - Geografía (25 preguntas)
    preguntas = [
        ("¿Cuál es la capital de Francia?", "fácil"),
        ("¿Cuál es el río más largo del mundo?", "medio"),
        ("¿Cuál es la montaña más alta del mundo?", "fácil"),
        ("¿En qué continente se encuentra Egipto?", "fácil"),
        ("¿Cuál es la capital de Japón?", "fácil"),
        ("¿Cuál es el océano más grande?", "medio"),
        ("¿En qué país se encuentra la Torre Eiffel?", "fácil"),
        ("¿Cuál es la capital de Australia?", "medio"),
        ("¿Cuántos países hay en Europa?", "difícil"),
        ("¿Cuál es el desierto más grande del mundo?", "medio"),
        ("¿En qué país está Machu Picchu?", "medio"),
        ("¿Cuál es la capital de Canadá?", "fácil"),
        ("¿Cuál es el mar más salado del mundo?", "difícil"),
        ("¿En qué país se encuentra la Estatua de la Libertad?", "fácil"),
        ("¿Cuál es la capital de Brasil?", "fácil"),
        ("¿Cuántas islas tiene Grecia?", "difícil"),
        ("¿En qué continente está Nueva Zelanda?", "medio"),
        ("¿Cuál es el río más caudaloso del mundo?", "medio"),
        ("¿En qué país se encuentra el Big Ben?", "fácil"),
        ("¿Cuál es la capital de Tailandia?", "medio"),
        ("¿Cuántos países hay en América del Sur?", "medio"),
        ("¿En qué país está la Gran Muralla China?", "fácil"),
        ("¿Cuál es el lago más grande del mundo?", "difícil"),
        ("¿En qué país se encuentra Stonehenge?", "medio"),
        ("¿Cuál es la capital de Sudáfrica?", "difícil"),
    ]
    # Insertar preguntas de Geografía
    fecha = datetime.now().date()
    # Insertar respuestas - geografia
    opciones = {
        1:  (["París", "Londres", "Berlín", "Madrid"], "París"),
        2:  (["Nilo", "Amazonas", "Yangtsé", "Misisipi"], "Nilo"),
        3:  (["Kilimanjaro", "Everest", "Elbrus", "McKinley"], "Everest"),
        4:  (["Asia", "Europa", "África", "América"], "África"),
        5:  (["Tokio", "Kioto", "Osaka", "Nagoya"], "Tokio"),
        6:  (["Atlántico", "Pacífico", "Índico", "Ártico"], "Pacífico"),
        7:  (["Francia", "Italia", "España", "Alemania"], "Francia"),
        8:  (["Canberra", "Sídney", "Melbourne", "Brisbane"], "Canberra"),
        9:  (["44", "50", "27", "36"], "44"),
        10: (["Sahara", "Gobi", "Kalahari", "Antártico"], "Sahara"),
        11: (["Perú", "México", "Chile", "Argentina"], "Perú"),
        12: (["Ottawa", "Toronto", "Montreal", "Vancouver"], "Ottawa"),
        13: (["Mar Muerto", "Mar Rojo", "Mar Caribe", "Mar Negro"], "Mar Muerto"),
        14: (["EE. UU.", "Canadá", "Reino Unido", "Francia"], "EE. UU."),
        15: (["Brasilia", "Río de Janeiro", "São Paulo", "Buenos Aires"], "Brasilia"),
        16: (["1400", "3000", "6000", "1500"], "1400"),
        17: (["Oceanía", "Asia", "Europa", "América"], "Oceanía"),
        18: (["Amazonas", "Nilo", "Yangtsé", "Misisipi"], "Amazonas"),
        19: (["Reino Unido", "Estados Unidos", "Francia", "Alemania"], "Reino Unido"),
        20: (["Bangkok", "Chiang Mai", "Pattaya", "Phuket"], "Bangkok"),
        21: (["10", "12", "14", "13"], "12"),
        22: (["China", "Japón", "Corea del Sur", "Vietnam"], "China"),
        23: (["Superior", "Victoria", "Titicaca", "Huron"], "Superior"),
        24: (["Inglaterra", "Escocia", "Irlanda", "Gales"], "Inglaterra"),
        25: (["Pretoria", "Ciudad del Cabo", "Bloemfontein", "Johannesburgo"], "Pretoria"),
        }
    
    for i, (texto, nivel) in enumerate(preguntas, 1):
        cursor.execute(
            "INSERT INTO preguntas (texto, nivel, fecha_registro) VALUES (%s, %s, %s)",
            (texto, nivel, fecha)
        )
        pregunta_id = cursor.lastrowid
        
        # Insertar 4 opciones por pregunta (solo una correcta)
        

        
        # Obtenemos las opciones de la pregunta
        opts, respuesta_correcta = opciones[i]
        
        for j, opcion in enumerate(opts):
            es_correcta = 1 if opcion == respuesta_correcta else 0
            cursor.execute(
                "INSERT INTO opciones (pregunta_id, texto_opcion, es_correcta) VALUES (%s, %s, %s)",
                (pregunta_id, opcion, es_correcta)
            )
    
        
    # Deportes (25 preguntas)
    preguntas = [
        ("¿Cuántos jugadores hay en un equipo de fútbol?", "fácil"),
        ("¿Cuántos sets gana un tenista para ganar un partido?", "medio"),
        ("¿En qué deporte se utiliza un disco frisbee?", "medio"),
        ("¿Cuántos puntos vale un touchdown en fútbol americano?", "medio"),
        ("¿Cuántos jugadores hay en un equipo de baloncesto?", "fácil"),
        ("¿Cuál es la distancia de una maratón?", "fácil"),
        ("¿En qué deporte se usa un guante especial?", "fácil"),
        ("¿Cuántos juegos hay en el tenis de mesa?", "difícil"),
        ("¿Cuál es el tiempo de duración de un partido de rugby?", "medio"),
        ("¿Cuántos jugadores hay en un equipo de voleibol?", "fácil"),
        ("¿En qué deporte se utiliza un bate de madera?", "fácil"),
        ("¿Cuántos hoyos tiene un campo de golf?", "fácil"),
        ("¿En qué deporte se practica el triple axel?", "medio"),
        ("¿Cuánto pesa una pelota de fútbol?", "difícil"),
        ("¿En qué deporte se usa un arco y flechas?", "fácil"),
        ("¿Cuál es la velocidad máxima en natación de estilos?", "difícil"),
        ("¿Cuántos puntos vale un gol en hockey?", "fácil"),
        ("¿En qué deporte se practica el salto triple?", "medio"),
        ("¿Cuántos períodos tiene un partido de béisbol?", "fácil"),
        ("¿En qué deporte se utiliza un balonmano?", "fácil"),
        ("¿Cuál es la altura de la red en voleibol?", "medio"),
        ("¿En qué deporte se practica el servicio directo?", "medio"),
        ("¿Cuántos juadores se necesitan para un partido de tenis?", "fácil"),
        ("¿En qué deporte se usa un caballo?", "fácil"),
        ("¿Cuál es el peso de un disco en lanzamiento?", "difícil"),
    ]


        # Insertar respuestas - deporte
    # Respuesta deporte
    opciones = {
    1:  (["11", "10", "9", "12"], "11"),
    2:  (["2 sets", "3 sets", "5 sets", "7 sets"], "3 sets"),
    3:  (["Fútbol", "Disco Frisbee", "Baloncesto", "Tenis"], "Disco Frisbee"),
    4:  (["3 puntos", "6 puntos", "7 puntos", "1 punto"], "6 puntos"),
    5:  (["5", "6", "7", "4"], "5"),
    6:  (["21 km", "42 km", "10 km", "50 km"], "42 km"),
    7:  (["Boxeo", "Béisbol", "Baloncesto", "Natación"], "Boxeo"),
    8:  (["5", "7", "11", "3"], "11"),
    9:  (["40 min", "60 min", "80 min", "90 min"], "80 min"),
    10: (["6", "7", "5", "4"], "6"),
    11: (["Béisbol", "Golf", "Hockey", "Bateball"], "Béisbol"),
    12: (["9", "12", "18", "36"], "18"),
    13: (["Patinaje artístico", "Gimnasia", "Natación", "Esquí"], "Patinaje artístico"),
    14: (["410-450 g", "350-390 g", "400-450 g", "300-350 g"], "410-450 g"),
    15: (["Tiro con arco", "Esgrima", "Pentatlón", "Hockey"], "Tiro con arco"),
    16: (["1.5 m/s", "2 m/s", "2.5 m/s", "3 m/s"], "2.5 m/s"),
    17: (["1 punto", "2 puntos", "3 puntos", "5 puntos"], "1 punto"),
    18: (["Salto de altura", "Salto triple", "Salto con pértiga", "Longitud"], "Salto triple"),
    19: (["3", "7", "9", "5"], "9"),
    20: (["Balonmano", "Fútbol", "Voleibol", "Rugby"], "Balonmano"),
    21: (["2.43 m", "2.24 m", "2.50 m", "2.10 m"], "2.43 m"),
    22: (["Tenis", "Fútbol", "Baloncesto", "Bádminton"], "Tenis"),
    23: (["1", "2", "4", "6"], "2"),
    24: (["Individual", "Dúo", "Dobles", "Solo"], "Individual"),
    25: (["2 kg", "1 kg", "1.5 kg", "3 kg"], "2 kg"),
    }

    # Insertar preguntas de Deportes
    for i, (texto, nivel) in enumerate(preguntas, 1):
        cursor.execute(
            "INSERT INTO preguntas (texto, nivel, fecha_registro) VALUES (%s, %s, %s)",
            (texto, nivel, fecha)
        )
        pregunta_id = cursor.lastrowid
        
        
        # Obtenemos las opciones de la pregunta
        opts, respuesta_correcta = opciones[i]
        
        for j, opcion in enumerate(opts):
            es_correcta = 1 if opcion == respuesta_correcta else 0
            cursor.execute(
                "INSERT INTO opciones (pregunta_id, texto_opcion, es_correcta) VALUES (%s, %s, %s)",
                (pregunta_id, opcion, es_correcta)
            )
    
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ MySQL: Base de datos 'trivia_mysql' creada con 50 preguntas")

except Exception as e:
    print("Error en MySQL:", e)



# Redis
try:
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    
    # Prueba de conexión
    r.ping()
    
    # Limpiar datos anteriores
    r.flushdb()
    # Lista de 50 preguntas de Ciencias
    preguntas_ciencias = [
        {"txt": "¿Cuál es el elemento más abundante en el universo?",
        "opts": ["Oxígeno", "Hidrógeno", "Carbono", "Helio"], "ans_idx": 1, "diff": 2, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Cuántos planetas hay en el sistema solar?",
        "opts": ["7", "8", "9", "10"], "ans_idx": 1, "diff": 1, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Cuál es la velocidad de la luz en el vacío?",
        "opts": ["100,000 km/s", "200,000 km/s", "300,000 km/s", "400,000 km/s"], "ans_idx": 2, "diff": 2, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Cuántos átomos de hidrógeno hay en una molécula de agua?",
        "opts": ["1", "2", "3", "4"], "ans_idx": 1, "diff": 2, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Cuál es el gas más abundante en la atmósfera terrestre?",
        "opts": ["Oxígeno", "Nitrógeno", "Dióxido de carbono", "Argón"], "ans_idx": 1, "diff": 2, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Qué planeta es conocido como el planeta rojo?",
        "opts": ["Mercurio", "Venus", "Marte", "Júpiter"], "ans_idx": 2, "diff": 1, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Cuál es la fuerza que mantiene a los planetas en órbita?",
        "opts": ["Magnetismo", "Gravedad", "Fricción", "Electromagnetismo"], "ans_idx": 1, "diff": 1, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Qué tipo de sangre es considerado donante universal?",
        "opts": ["A", "B", "AB", "O"], "ans_idx": 3, "diff": 2, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Qué órgano produce insulina en el cuerpo humano?",
        "opts": ["Hígado", "Páncreas", "Riñón", "Estómago"], "ans_idx": 1, "diff": 2, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Cuál es la unidad básica de la vida?",
        "opts": ["Célula", "Tejido", "Órgano", "Sistema"], "ans_idx": 0, "diff": 1, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Qué planeta tiene los anillos más visibles?",
        "opts": ["Saturno", "Urano", "Júpiter", "Neptuno"], "ans_idx": 0, "diff": 1, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Cuál es el metal más abundante en la corteza terrestre?",
        "opts": ["Hierro", "Aluminio", "Cobre", "Oro"], "ans_idx": 1, "diff": 2, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Qué gas es esencial para la respiración de los humanos?",
        "opts": ["Nitrógeno", "Oxígeno", "Dióxido de carbono", "Hidrógeno"], "ans_idx": 1, "diff": 1, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Qué planeta es el más grande del sistema solar?",
        "opts": ["Júpiter", "Saturno", "Neptuno", "Urano"], "ans_idx": 0, "diff": 1, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Qué órgano filtra la sangre eliminando desechos?",
        "opts": ["Corazón", "Hígado", "Riñón", "Pulmón"], "ans_idx": 2, "diff": 1, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Qué molécula transporta oxígeno en la sangre?",
        "opts": ["Glucosa", "Hemoglobina", "Colágeno", "Insulina"], "ans_idx": 1, "diff": 2, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Cuál es la principal fuente de energía de la Tierra?",
        "opts": ["Luz de la luna", "Energía solar", "Energía nuclear", "Viento"], "ans_idx": 1, "diff": 1, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Qué científico formuló la teoría de la relatividad?",
        "opts": ["Newton", "Einstein", "Galileo", "Curie"], "ans_idx": 1, "diff": 2, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Qué sustancia forma los huesos humanos?",
        "opts": ["Colágeno", "Calcio", "Hierro", "Fósforo"], "ans_idx": 1, "diff": 1, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Qué órgano bombea la sangre a todo el cuerpo?",
        "opts": ["Pulmón", "Corazón", "Hígado", "Riñón"], "ans_idx": 1, "diff": 1, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Qué tipo de energía genera un panel solar?",
        "opts": ["Térmica", "Nuclear", "Luminosa", "Eléctrica"], "ans_idx": 3, "diff": 1, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Cuál es la capa más externa de la Tierra?",
        "opts": ["Núcleo", "Manto", "Corteza", "Atmósfera"], "ans_idx": 2, "diff": 1, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Qué partícula tiene carga negativa?",
        "opts": ["Protón", "Neutrón", "Electrón", "Positrón"], "ans_idx": 2, "diff": 1, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Cuál es el planeta más cercano al Sol?",
        "opts": ["Mercurio", "Venus", "Tierra", "Marte"], "ans_idx": 0, "diff": 1, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Qué sustancia se libera durante la fotosíntesis?",
        "opts": ["CO2", "O2", "H2O", "N2"], "ans_idx": 1, "diff": 1, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Cuál es la principal molécula de energía en las células?",
        "opts": ["ADN", "ATP", "ARN", "Glucosa"], "ans_idx": 1, "diff": 1, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Qué fenómeno causa los eclipses?",
        "opts": ["Reflexión", "Rotación", "Interposición", "Refracción"], "ans_idx": 2, "diff": 1, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Cuál es la principal función de las raíces de una planta?",
        "opts": ["Fotosíntesis", "Absorber agua", "Producir flores", "Sostener hojas"], "ans_idx": 1, "diff": 1, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Qué órgano produce la bilis?",
        "opts": ["Hígado", "Páncreas", "Riñón", "Estómago"], "ans_idx": 0, "diff": 2, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Qué tipo de animal es un delfín?",
        "opts": ["Pez", "Mamífero", "Anfibio", "Reptil"], "ans_idx": 1, "diff": 1, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Qué planeta es conocido por sus tormentas gigantes?",
        "opts": ["Júpiter", "Saturno", "Urano", "Neptuno"], "ans_idx": 0, "diff": 2, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Qué partícula tiene carga positiva?",
        "opts": ["Electrón", "Protón", "Neutrón", "Quark"], "ans_idx": 1, "diff": 1, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Qué tipo de energía usa un generador eólico?",
        "opts": ["Solar", "Eólica", "Nuclear", "Geotérmica"], "ans_idx": 1, "diff": 1, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Qué planeta es conocido por su color azul intenso?",
        "opts": ["Urano", "Neptuno", "Tierra", "Saturno"], "ans_idx": 1, "diff": 1, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Qué gas es liberado por la respiración de los seres vivos?",
        "opts": ["O2", "CO2", "N2", "H2"], "ans_idx": 1, "diff": 1, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Qué órgano produce glóbulos rojos?",
        "opts": ["Hígado", "Médula ósea", "Bazo", "Riñón"], "ans_idx": 1, "diff": 2, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Qué tipo de energía se obtiene al quemar gasolina?",
        "opts": ["Térmica", "Química", "Eléctrica", "Nuclear"], "ans_idx": 1, "diff": 1, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Qué planeta tiene mayor densidad?",
        "opts": ["Tierra", "Mercurio", "Júpiter", "Saturno"], "ans_idx": 0, "diff": 2, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Qué órgano ayuda a mantener el equilibrio?",
        "opts": ["Oído interno", "Cerebro", "Corazón", "Pulmón"], "ans_idx": 0, "diff": 2, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Qué tipo de onda es la luz?",
        "opts": ["Longitudinal", "Transversal", "Mecánica", "Sonora"], "ans_idx": 1, "diff": 2, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Qué gas es usado en los globos aerostáticos?",
        "opts": ["Helio", "Nitrógeno", "Oxígeno", "Argón"], "ans_idx": 0, "diff": 1, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Qué órgano ayuda a digerir las grasas?",
        "opts": ["Hígado", "Estómago", "Páncreas", "Intestino delgado"], "ans_idx": 0, "diff": 2, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Cuál es la distancia promedio entre la Tierra y el Sol?",
        "opts": ["149 millones km", "100 millones km", "200 millones km", "300 millones km"], "ans_idx": 0, "diff": 2, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Qué tipo de sangre puede recibir cualquier otro tipo?",
        "opts": ["A", "B", "AB", "O"], "ans_idx": 2, "diff": 2, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Cuál es la molécula que almacena información genética?",
        "opts": ["ADN", "ARN", "Proteína", "Glucosa"], "ans_idx": 0, "diff": 1, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Qué planeta es conocido como el planeta gigante gaseoso?",
        "opts": ["Júpiter", "Saturno", "Urano", "Neptuno"], "ans_idx": 0, "diff": 1, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Qué órgano es responsable de filtrar toxinas químicas?",
        "opts": ["Riñón", "Hígado", "Pulmón", "Corazón"], "ans_idx": 1, "diff": 2, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Qué tipo de energía producen las baterías?",
        "opts": ["Eléctrica", "Térmica", "Nuclear", "Luminosa"], "ans_idx": 0, "diff": 1, "tstamp": datetime.now().isoformat()},
        {"txt": "¿Qué elemento químico se usa para hacer vidrio?",
        "opts": ["Sodio", "Silicio", "Hierro", "Cobre"], "ans_idx": 1, "diff": 2, "tstamp": datetime.now().isoformat()},
    ]

    # Insertar 50 preguntas en Redis
    for i in range(1, 51):
        if i <= len(preguntas_ciencias):
            pregunta = preguntas_ciencias[i - 1]
        else:
            pregunta = {
                "txt": f"Pregunta de Ciencias #{i}",
                "opts": ["Opción A", "Opción B", "Opción C", "Opción D"],
                "ans_idx": 0,
                "diff": 2,
                "tstamp": datetime.now().isoformat()
            }
        
        clave = f"trivial:game:{i}"
        r.set(clave, json.dumps(pregunta, ensure_ascii=False))
    
    print("✅ Redis: 50 preguntas de Ciencias almacenadas")
    
except Exception as e:
    print(f"❌ Error en Redis: {e}")


# Mongo DB

try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['trivial_mongodb']
    
    # Eliminar colección anterior
    if 'questions' in db.list_collection_names():
        db['questions'].drop()
    
    # Preguntas de Arte
    preguntas_arte = [
    ("¿En qué año pintó Da Vinci la Mona Lisa?", ["1503", "1515", "1525", "1535"], "1503", "Media"),
    ("¿Cuál es el cuadro más famoso de Picasso?", ["Las Meninas", "El Grito", "Guernica", "Noche Estrellada"], "Guernica", "Media"),
    ("¿Cuál es el museo más visitado del mundo?", ["British Museum", "Louvre", "Metropolitan", "Uffizi"], "Louvre", "Alta"),
    ("¿Quién pintó la Capilla Sixtina?", ["Miguel Ángel", "Raphael", "Leonardo Da Vinci", "Donatello"], "Miguel Ángel", "Alta"),
    ("¿Qué movimiento artístico pertenece a Van Gogh?", ["Impresionismo", "Postimpresionismo", "Cubismo", "Renacimiento"], "Postimpresionismo", "Media"),
    ("¿Cuál es la obra más famosa de Botticelli?", ["El nacimiento de Venus", "La Primavera", "La Última Cena", "Guernica"], "El nacimiento de Venus", "Alta"),
    ("¿Qué artista es famoso por los retratos de Campbell's Soup?", ["Andy Warhol", "Roy Lichtenstein", "Jackson Pollock", "Salvador Dalí"], "Andy Warhol", "Media"),
    ("¿Qué corriente artística representa Dalí?", ["Surrealismo", "Expresionismo", "Cubismo", "Realismo"], "Surrealismo", "Alta"),
    ("¿Qué museo se encuentra en París y tiene la Gioconda?", ["Louvre", "Orsay", "Pompidou", "Rodin"], "Louvre", "Media"),
    ("¿Qué estilo de arquitectura es la Sagrada Familia?", ["Gótico", "Barroco", "Modernista", "Renacentista"], "Modernista", "Media"),
    ("¿Quién pintó 'La noche estrellada'?", ["Van Gogh", "Monet", "Rembrandt", "Picasso"], "Van Gogh", "Media"),
    ("¿Qué movimiento artístico fundó Picasso con Braque?", ["Cubismo", "Futurismo", "Expresionismo", "Impresionismo"], "Cubismo", "Alta"),
    ("¿Qué pintor es famoso por sus 'Nenúfares'?", ["Monet", "Renoir", "Cézanne", "Degas"], "Monet", "Media"),
    ("¿Quién pintó 'Las Meninas'?", ["Velázquez", "Goya", "El Bosco", "Murillo"], "Velázquez", "Alta"),
    ("¿Qué estilo caracteriza a Gaudí?", ["Modernismo", "Barroco", "Neoclásico", "Renacimiento"], "Modernismo", "Media"),
    ("¿Qué escultor creó 'El David'?", ["Miguel Ángel", "Donatello", "Rodin", "Bernini"], "Miguel Ángel", "Alta"),
    ("¿Qué artista es conocido por sus cuadros de relojes derretidos?", ["Dalí", "Magritte", "Klimt", "Warhol"], "Dalí", "Media"),
    ("¿Qué pintor es famoso por la serie de 'Bailarinas'?", ["Degas", "Renoir", "Monet", "Van Gogh"], "Degas", "Media"),
    ("¿Qué país es famoso por la cerámica de Delft?", ["Países Bajos", "Italia", "España", "Francia"], "Países Bajos", "Media"),
    ("¿Qué técnica utiliza Jackson Pollock?", ["Action Painting", "Fresco", "Óleo sobre lienzo", "Acuarela"], "Action Painting", "Alta"),
    ("¿Quién pintó 'La Primavera'?", ["Botticelli", "Da Vinci", "Raphael", "Michelangelo"], "Botticelli", "Alta"),
    ("¿Qué corriente artística representa Andy Warhol?", ["Pop Art", "Surrealismo", "Cubismo", "Expresionismo"], "Pop Art", "Media"),
    ("¿Qué museo está en Nueva York y tiene obras de Van Gogh?", ["Metropolitan", "MoMA", "Whitney", "Guggenheim"], "Metropolitan", "Media"),
    ("¿Quién pintó 'La persistencia de la memoria'?", ["Dalí", "Picasso", "Kandinsky", "Magritte"], "Dalí", "Alta"),
    ("¿Qué movimiento artístico pertenece a Klimt?", ["Modernismo", "Renacimiento", "Barroco", "Cubismo"], "Modernismo", "Media"),
    ("¿Qué pintor holandés es famoso por 'La ronda de noche'?", ["Rembrandt", "Vermeer", "Van Gogh", "Mondrian"], "Rembrandt", "Alta"),
    ("¿Quién es el autor de 'El jardín de las delicias'?", ["El Bosco", "Goya", "Velázquez", "Bruegel"], "El Bosco", "Alta"),
    ("¿Qué estilo arquitectónico es el Partenón?", ["Clásico", "Gótico", "Renacentista", "Barroco"], "Clásico", "Media"),
    ("¿Qué pintor francés es famoso por los nenúfares y su jardín?", ["Monet", "Renoir", "Cézanne", "Degas"], "Monet", "Media"),
    ("¿Quién pintó 'El grito'?", ["Munch", "Picasso", "Van Gogh", "Dalí"], "Munch", "Media"),
    ("¿Qué artista es conocido por esculturas gigantes de globos?", ["Koons", "Dalí", "Rodin", "Brâncuși"], "Koons", "Alta"),
    ("¿Qué pintor barroco español pintó 'La rendición de Breda'?", ["Velázquez", "Murillo", "Goya", "El Greco"], "Velázquez", "Alta"),
    ("¿Qué pintor americano es famoso por 'Número 5'?", ["Pollock", "Rothko", "Warhol", "Hopper"], "Pollock", "Media"),
    ("¿Qué arquitecto diseñó el Guggenheim de Nueva York?", ["Wright", "Le Corbusier", "Gaudí", "Frank Lloyd Wright"], "Frank Lloyd Wright", "Alta"),
    ("¿Qué pintor surrealista creó 'El Elefante Celestial'? ", ["Dalí", "Magritte", "Kahlo", "Ernst"], "Dalí", "Media"),
    ("¿Quién pintó 'Las bodas de Caná'?", ["Veronese", "Tintoretto", "Rubens", "Rafael"], "Veronese", "Alta"),
    ("¿Qué pintor renacentista pintó 'La última cena'?", ["Da Vinci", "Raphael", "Michelangelo", "Botticelli"], "Da Vinci", "Alta"),
    ("¿Qué pintor mexicano es famoso por sus murales?", ["Rivera", "Orozco", "Kahlo", "Siqueiros"], "Rivera", "Media"),
    ("¿Qué escultor francés creó 'El Pensador'?", ["Rodin", "Bernini", "Michelangelo", "Donatello"], "Rodin", "Alta"),
    ("¿Qué técnica usa Andy Warhol en sus obras?", ["Serigrafía", "Óleo", "Acuarela", "Fresco"], "Serigrafía", "Media"),
    ("¿Qué museo se encuentra en Florencia y es famoso por arte renacentista?", ["Uffizi", "Louvre", "Metropolitan", "Hermitage"], "Uffizi", "Alta"),
    ("¿Quién pintó 'El Beso'?", ["Klimt", "Mucha", "Picasso", "Matisse"], "Klimt", "Media"),
    ("¿Qué pintor francés pintó 'El almuerzo sobre la hierba'?", ["Manet", "Renoir", "Monet", "Cézanne"], "Manet", "Media"),
    ("¿Qué movimiento artístico pertenece a Cézanne?", ["Impresionismo", "Postimpresionismo", "Cubismo", "Renacimiento"], "Postimpresionismo", "Media"),
    ("¿Qué artista creó 'El grito del caballo'?", ["Munch", "Picasso", "Goya", "Dalí"], "Munch", "Alta"),
    ("¿Quién pintó 'La escuela de Atenas'?", ["Raphael", "Da Vinci", "Michelangelo", "Botticelli"], "Raphael", "Alta"),
    ("¿Qué pintor expresionista alemán pintó 'Autorretrato con chaqueta de cuero'?", ["Kandinsky", "Munch", "Beckmann", "Hodler"], "Beckmann", "Media"),
    ("¿Qué escultor moderno es famoso por 'Bird in Space'?", ["Brâncuși", "Rodin", "Michelangelo", "Koons"], "Brâncuși", "Alta"),
    ("¿Qué pintor surrealista belga creó 'La Trahison des images'?", ["Magritte", "Dalí", "Kahlo", "Ernst"], "Magritte", "Media"),
    ("¿Qué pintor italiano pintó 'El Bautismo de Cristo'?", ["Verrocchio", "Da Vinci", "Raphael", "Michelangelo"], "Da Vinci", "Alta"),
    ("¿Qué artista barroco flamenco pintó 'El Descanso en la Huida a Egipto'?", ["Rubens", "Van Dyck", "El Bosco", "Bruegel"], "Rubens", "Alta"),
]
    
    # Insertar 50 documentos en MongoDB
    documentos = []
    for i in range(1, 51):
        if i <= len(preguntas_arte):
            t = preguntas_arte[i - 1]
            doc = {
                "difficulty": t[3],
                "createdAt": datetime.now().isoformat(),
                "localizations": [
                    {
                        "language": "es",
                        "text": t[0],
                        "items": t[1],
                        "ok_item": t[2]
                    }
                ]
            }
        else:
            doc = {
                "difficulty": "Media",
                "createdAt": datetime.now().isoformat(),
                "localizations": [
                    {
                        "language": "es",
                        "text": f"Pregunta de Arte #{i}",
                        "items": ["Opción A", "Opción B", "Opción C", "Opción D"],
                        "ok_item": "Opción A"
                    }
                ]
            }
        documentos.append(doc)
    
    db['questions'].insert_many(documentos)
    print("✅ MongoDB: 50 preguntas de Arte almacenadas")
    
except Exception as e:
    print(f"❌ Error en MongoDB: {e}")


# PostgreSQL

try:
    import psycopg2
    
    # Conectar a PostgreSQL (usuario por defecto: postgres)
    conn = psycopg2.connect(
        host='localhost',
        user='root',
        password='1234', 
        database='postgres'
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Crear base de datos
    cursor.execute("DROP DATABASE IF EXISTS trivial_postgres")
    cursor.execute("CREATE DATABASE trivial_postgres")
    cursor.close()
    conn.close()
    
    # Conectar a la nueva BD
    conn = psycopg2.connect(
        host='localhost',
        user='root',
        password='1234',
        database='trivial_postgres'
    )
    cursor = conn.cursor()
    
    # Crear tabla (formato: Pregunta|Dificultad|Fecha|Opción1|Opción2|Opción3|Opción4|RespuestaCorrecta)
    cursor.execute("""
        CREATE TABLE trivial (
            id SERIAL PRIMARY KEY,
            pregunta_datos TEXT NOT NULL
        )
    """)
    
    # Insertar 50 preguntas de Espectáculo
    preguntas_espectaculo = [
    "¿Cuál es la película más taquillera de todos los tiempos?|Media|2024-01-01|Avatar|Titanic|Avengers|Inception|Avatar",
    "¿Quién ganó el Óscar a Mejor Actor en 2023?|Media|2024-02-10|Tom Cruise|Cillian Murphy|Leonardo DiCaprio|Jake Gyllenhaal|Cillian Murphy",
    "¿Cuál es la serie más vista en Netflix?|Media|2024-01-15|Breaking Bad|Stranger Things|The Crown|Squid Game|Squid Game",
    "¿Quién es el cantante más escuchado en Spotify?|Baja|2024-02-01|The Weeknd|Bad Bunny|Drake|Taylor Swift|The Weeknd",
    "¿En qué año se estrenó Game of Thrones?|Media|2024-01-20|2009|2010|2011|2012|2011",
    "¿Quién ganó el Óscar a Mejor Película en 2023?|Alta|2024-03-01|Everything Everywhere|Avatar|Top Gun|Elvis|Everything Everywhere",
    "¿Qué cantante lanzó el álbum '30' en 2021?|Media|2024-01-05|Adele|Beyoncé|Taylor Swift|Dua Lipa|Adele",
    "¿Cuál es la película más premiada de la historia?|Alta|2024-01-10|Titanic|Ben-Hur|Lord of the Rings|Avatar|Ben-Hur",
    "¿Quién ganó el Grammy a Mejor Álbum del Año 2023?|Media|2024-02-05|Harry Styles|Beyoncé|Taylor Swift|Bad Bunny|Harry Styles",
    "¿Cuál es la serie más larga de Disney Channel?|Media|2024-01-12|Hannah Montana|High School Musical|Violetta|Lizzie McGuire|Hannah Montana",
    "¿Qué película ganó el León de Oro en Venecia 2023?|Alta|2024-03-02|All the Beauty|Avatar|Elvis|Top Gun|All the Beauty",
    "¿Quién interpreta a Spider-Man en las películas recientes?|Baja|2024-02-07|Tom Holland|Andrew Garfield|Tobey Maguire|Jake Johnson|Tom Holland",
    "¿Cuál fue la película más vista en 2023?|Media|2024-01-25|Avatar|Top Gun|Barbie|Oppenheimer|Barbie",
    "¿Qué cantante es conocido como 'The King of Pop'?|Baja|2024-01-30|Michael Jackson|Prince|Elvis Presley|Justin Timberlake|Michael Jackson",
    "¿Qué serie ganó el Emmy a Mejor Drama 2023?|Alta|2024-02-15|Succession|Better Call Saul|The Crown|House of the Dragon|Succession",
    "¿Quién interpreta a Wonder Woman en las películas recientes?|Media|2024-01-28|Gal Gadot|Charlize Theron|Margot Robbie|Emma Stone|Gal Gadot",
    "¿Cuál es la película más vista de Marvel?|Media|2024-02-01|Avengers|Black Panther|Iron Man|Thor|Avengers",
    "¿Qué cantante lanzó el álbum 'Midnights'?|Baja|2024-01-18|Taylor Swift|Adele|Dua Lipa|Beyoncé|Taylor Swift",
    "¿Cuál fue la película más nominada al Óscar 2023?|Alta|2024-02-20|Everything Everywhere|Avatar|Top Gun|Elvis|Everything Everywhere",
    "¿Quién es la estrella de la serie 'Stranger Things'?|Media|2024-01-22|Millie Bobby Brown|Sadie Sink|Finn Wolfhard|Noah Schnapp|Millie Bobby Brown",
    "¿Qué película animada ganó el Óscar en 2023?|Media|2024-02-10|Encanto|Paw Patrol|Spider-Man|Luca|Encanto",
    "¿Quién ganó el premio a Mejor Director en 2023?|Alta|2024-03-05|Daniel Kwan|Steven Spielberg|James Cameron|Christopher Nolan|Daniel Kwan",
    "¿Cuál es la canción más reproducida en Spotify 2023?|Baja|2024-02-12|As It Was|Blinding Lights|Bad Habit|Flowers|As It Was",
    "¿Qué película ganó la Palma de Oro en Cannes 2023?|Alta|2024-03-08|Anatomy of a Fall|Elvis|Avatar|Barbie|Anatomy of a Fall",
    "¿Quién interpreta a Harry Potter en las películas originales?|Media|2024-01-15|Daniel Radcliffe|Rupert Grint|Tom Felton|Robert Pattinson|Daniel Radcliffe",
    "¿Cuál es la serie más popular de HBO?|Media|2024-01-19|Game of Thrones|Succession|The Last of Us|Westworld|Game of Thrones",
    "¿Qué cantante es conocido como 'La Reina del Pop'?|Baja|2024-01-23|Madonna|Adele|Beyoncé|Lady Gaga|Madonna",
    "¿Cuál fue la película más taquillera de Marvel 2023?|Media|2024-01-27|Avengers|Spider-Man|Black Panther|Thor|Avengers",
    "¿Quién ganó el Globo de Oro a Mejor Actor 2023?|Alta|2024-02-02|Austin Butler|Brad Pitt|Leonardo DiCaprio|Cillian Murphy|Austin Butler",
    "¿Qué película ganó el BAFTA 2023?|Alta|2024-02-08|Everything Everywhere|Elvis|Avatar|Top Gun|Everything Everywhere",
    "¿Quién lanzó la canción 'Anti-Hero'?|Baja|2024-01-29|Taylor Swift|Dua Lipa|Adele|Billie Eilish|Taylor Swift",
    "¿Qué serie ganó el Emmy a Mejor Comedia 2023?|Media|2024-02-11|Ted Lasso|Only Murders|Abbott Elementary|The Bear|Ted Lasso",
    "¿Cuál es la película más premiada de Disney?|Alta|2024-03-01|Frozen|Encanto|Ratatouille|Moana|Frozen",
    "¿Quién es la estrella de 'Barbie'?|Media|2024-01-21|Margot Robbie|Emma Watson|Anne Hathaway|Scarlett Johansson|Margot Robbie",
    "¿Qué película ganó el Óscar a Mejor Animación 2023?|Media|2024-02-14|Puss in Boots|Encanto|Luca|Soul|Encanto",
    "¿Quién interpreta a Batman en las películas recientes?|Media|2024-01-26|Robert Pattinson|Christian Bale|Ben Affleck|Michael Keaton|Robert Pattinson",
    "¿Qué cantante lanzó el álbum 'Renaissance'?|Baja|2024-01-31|Beyoncé|Taylor Swift|Adele|Dua Lipa|Beyoncé",
    "¿Cuál es la serie más vista en Disney+?|Media|2024-01-17|The Mandalorian|WandaVision|Loki|Ms. Marvel|The Mandalorian",
    "¿Quién ganó el Óscar a Mejor Actriz 2023?|Alta|2024-02-18|Cate Blanchett|Michelle Yeoh|Viola Davis|Margot Robbie|Cate Blanchett",
    "¿Qué película fue dirigida por Christopher Nolan en 2023?|Media|2024-01-24|Oppenheimer|Tenet|Dunkirk|Interstellar|Oppenheimer",
    "¿Quién es el cantante más joven en ganar un Grammy?|Baja|2024-01-16|Billie Eilish|Olivia Rodrigo|Lorde|Dua Lipa|Billie Eilish",
    "¿Cuál es la serie más comentada en Twitter 2023?|Media|2024-02-03|Stranger Things|The Crown|Succession|The Last of Us|Stranger Things",
    "¿Qué película ganó la Mostra de Venecia 2023?|Alta|2024-03-04|All the Beauty|Avatar|Elvis|Top Gun|All the Beauty",
    "¿Quién es la actriz principal de 'Euphoria'?|Media|2024-01-18|Zendaya|Hunter Schafer|Sydney Sweeney|Alexa Demie|Zendaya",
    "¿Qué cantante ganó el premio Billboard 2023?|Baja|2024-02-06|Bad Bunny|Taylor Swift|Drake|The Weeknd|Bad Bunny",
    "¿Cuál es la película más vista en Amazon Prime 2023?|Media|2024-01-22|The Lord of the Rings|Top Gun|Avatar|Elvis|The Lord of the Rings",
    "¿Quién interpretó a Jack Sparrow?|Media|2024-01-20|Johnny Depp|Orlando Bloom|Geoffrey Rush|Ian McShane|Johnny Depp",
    "¿Qué serie ganó el Emmy a Mejor Miniserie 2023?|Alta|2024-02-09|The White Lotus|The Crown|Mare of Easttown|Dopesick|The White Lotus",
    "¿Quién es la estrella de 'Stranger Things'?|Media|2024-01-14|Millie Bobby Brown|Sadie Sink|Finn Wolfhard|Noah Schnapp|Millie Bobby Brown",
    "¿Cuál es la película más vista de Pixar?|Media|2024-01-21|Toy Story 4|Soul|Luca|Turning Red|Toy Story 4",
    "¿Quién ganó el Óscar a Mejor Director de Animación 2023?|Alta|2024-02-17|Enrico Casarosa|Pete Docter|Lee Unkrich|Brad Bird|Enrico Casarosa"
    ]

    
    for i in range(1, 51):
        if i <= len(preguntas_espectaculo):
            datos = preguntas_espectaculo[i - 1]
        else:
            datos = f"Pregunta Espectáculo #{i}|Media|2024-01-01|Opción A|Opción B|Opción C|Opción D|Opción A"
        
        cursor.execute(
            "INSERT INTO trivial (pregunta_datos) VALUES (%s)",
            (datos,)
        )
    
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ PostgreSQL: Base de datos 'trivia_postgres' creada con 50 preguntas")
    
except Exception as e:
    print(f"❌ Error en PostgreSQL: {e}")
