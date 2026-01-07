import json
import random
from datetime import datetime
from typing import List, Dict, Optional
import os
import mysql.connector
import redis
import psycopg2
from pymongo import MongoClient

class PreguntaTrivial:
    def __init__(self, fuente_origen: str, pregunta: str, opciones: List[str], 
                 respuesta_correcta: str, dificultad: str, fecha_creacion: str = None):
        self.fuente_origen = fuente_origen
        self.pregunta = self._limpiar(pregunta)
        self.opciones = [self._limpiar(op) for op in opciones]
        self.respuesta_correcta = self._limpiar(respuesta_correcta).upper()
        self.dificultad = self._normalizar_dificultad(dificultad)
        self.fecha_creacion = fecha_creacion or datetime.now().strftime("%Y-%m-%d")
        self.categoria = None
    
    @staticmethod
    def _limpiar(texto: str) -> str:
        """Elimina espacios innecesarios"""
        return " ".join(texto.split())
    
    @staticmethod
    def _normalizar_dificultad(dificultad: str) -> str:
        """Normaliza dificultad a: Baja, Media, Alta"""
        mapeo = {
            'fácil': 'Baja', 'facil': 'Baja', 'easy': 'Baja', 'baja': 'Baja', '1': 'Baja',
            'medio': 'Media', 'medium': 'Media', 'media': 'Media', '2': 'Media',
            'difícil': 'Alta', 'dificil': 'Alta', 'hard': 'Alta', 'alta': 'Alta', '3': 'Alta', 'experto': 'Alta'
        }
        return mapeo.get(dificultad.lower().strip(), 'Media')
    
    def to_dict(self) -> Dict:
        return {
            'fuente_origen': self.fuente_origen,
            'pregunta': self.pregunta,
            'opciones': self.opciones,
            'respuesta_correcta': self.respuesta_correcta,
            'dificultad': self.dificultad,
            'fecha_creacion': self.fecha_creacion,
            'categoria': self.categoria
        }



class ConectorMySQL:
    """Conecta a MySQL y extrae una pregunta"""
    
    @staticmethod
    def extraer_pregunta():
        try:
            conn = mysql.connector.connect(
                host='localhost',
                user='root',
                password='1234',
                database='trivial_mysql'
            )
            cursor = conn.cursor()
            
            # Seleccionar una pregunta aleatoria
            cursor.execute("SELECT id FROM preguntas ORDER BY RAND() LIMIT 1")
            pregunta_id = cursor.fetchone()[0]
            
            # Obtener la pregunta
            cursor.execute("""
                SELECT texto, nivel, fecha_registro 
                FROM preguntas 
                WHERE id = %s
            """, (pregunta_id,))
            
            texto, nivel, fecha = cursor.fetchone()
            
            # Obtener las opciones (JOIN con tabla opciones)
            cursor.execute("""
                SELECT texto_opcion, es_correcta 
                FROM opciones 
                WHERE pregunta_id = %s
                ORDER BY id
            """, (pregunta_id,))
            
            opciones = []
            respuesta_correcta = None
            
            for opcion_texto, es_correcta in cursor.fetchall():
                opciones.append(opcion_texto)
                if es_correcta:
                    respuesta_correcta = opcion_texto
            
            cursor.close()
            conn.close()
            
            if respuesta_correcta is None:
                respuesta_correcta = opciones[0]
            
            return PreguntaTrivial(
                fuente_origen='MySQL',
                pregunta=texto,
                opciones=opciones,
                respuesta_correcta=respuesta_correcta,
                dificultad=nivel,
                fecha_creacion=str(fecha)
            )
        
        except Exception as e:
            print(f"❌ Error en MySQL: {e}")
            return None


class ConectorRedis:
    """Conecta a Redis y extrae una pregunta"""
    
    @staticmethod
    def extraer_pregunta():
        try:
            r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            r.ping()
            
            # Obtener una clave aleatoria
            todas_las_claves = r.keys('trivial:game:*')
            if not todas_las_claves:
                print("❌ No hay preguntas en Redis")
                return None
            
            clave = random.choice(todas_las_claves)
            datos = json.loads(r.get(clave))
            
            return PreguntaTrivial(
                fuente_origen='Redis',
                pregunta=datos['txt'],
                opciones=datos['opts'],
                respuesta_correcta=datos['opts'][datos['ans_idx']],
                dificultad=str(datos['diff']),
                fecha_creacion=datos.get('tstamp', datetime.now().strftime("%Y-%m-%d"))
            )
        
        except Exception as e:
            print(f"❌ Error en Redis: {e}")
            return None


class ConectorPostgreSQL:
    """Conecta a PostgreSQL y extrae una pregunta"""
    
    @staticmethod
    def extraer_pregunta():
        try:
            conn = psycopg2.connect(
                host='localhost',
                user='root',
                password='1234',
                database='trivial_postgres'
            )
            cursor = conn.cursor()
            
            # Seleccionar una pregunta aleatoria
            cursor.execute("SELECT pregunta_datos FROM trivial ORDER BY RANDOM() LIMIT 1")
            datos = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            # Parsear el formato: Pregunta|Dificultad|Fecha|Opción1|Opción2|Opción3|Opción4|RespuestaCorrecta
            partes = datos.split('|')
            
            if len(partes) >= 8:
                pregunta = partes[0]
                dificultad = partes[1]
                fecha = partes[2]
                opciones = partes[3:7]
                respuesta_correcta = partes[7]
                
                return PreguntaTrivial(
                    fuente_origen='PostgreSQL (RDS)',
                    pregunta=pregunta,
                    opciones=opciones,
                    respuesta_correcta=respuesta_correcta,
                    dificultad=dificultad,
                    fecha_creacion=fecha
                )
        
        except Exception as e:
            print(f"❌ Error en PostgreSQL: {e}")
            return None


class ConectorMongoDB:
    """Conecta a MongoDB y extrae una pregunta"""
    
    @staticmethod
    def extraer_pregunta():
        try:
            client = MongoClient('mongodb://localhost:27017/')
            db = client['trivial_mongodb']
            
            # Seleccionar un documento aleatorio
            documentos = list(db['questions'].aggregate([
                {"$sample": {"size": 1}}
            ]))
            
            if not documentos:
                print("❌ No hay preguntas en MongoDB")
                return None
            
            doc = documentos[0]
            
            # Extraer el primer localization en español
            localizacion = None
            for loc in doc.get('localizations', []):
                if loc.get('language') == 'es':
                    localizacion = loc
                    break
            
            if not localizacion:
                print("❌ No hay localización en español en MongoDB")
                return None
            
            return PreguntaTrivial(
                fuente_origen='MongoDB',
                pregunta=localizacion['text'],
                opciones=localizacion['items'],
                respuesta_correcta=localizacion['ok_item'],
                dificultad=doc.get('difficulty', 'Media'),
                fecha_creacion=doc.get('createdAt', datetime.now().strftime("%Y-%m-%d"))[:10]
            )
        
        except Exception as e:
            print(f"❌ Error en MongoDB: {e}")
            return None


import requests
class ClasificadorCategorias:
    def __init__(self, api_token=None):
        self.disponible = False
        try:
            from transformers import pipeline
            print("📥 Cargando modelo de clasificación local (puede tardar la primera vez)...")
            self.classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=-1  # CPU
            )
            self.disponible = True
            print("✅ Modelo cargado correctamente\n")
        except Exception as e:
            print(f"⚠️  Error cargando modelo: {e}\n")
            self.disponible = False
    
    def clasificar(self, pregunta: str) -> str:
        """Clasifica la pregunta en una categoría"""
        if not self.disponible:
            return "Sin clasificar"
        
        try:
            categorias = ['Geografía', 'Deportes', 'Ciencias', 'Historia', 'Espectáculo', 'Arte']
            resultado = self.classifier(pregunta, categorias, multi_class=False)
            return resultado['labels'][0]
        except Exception as e:
            print(f"Error clasificando: {e}")
            return "Sin clasificar"
# ============================================================================
# SCRIPT PRINCIPAL
# ============================================================================

def main():
    print("\n" + "=" * 80)
    print("🎮 TRIVIAL-MULTIPLE: Extractor Unificado de Preguntas")
    print("=" * 80)
    print()
    
    # Token de Hugging Face (cámbialo por el tuyo)
    HF_TOKEN = os.getenv("HF_TOKEN")
    
    # Inicializar clasificador
    print("📚 Inicializando clasificador de categorías...")
    clasificador = ClasificadorCategorias(HF_TOKEN)
    
    # Lista de preguntas extraídas
    preguntas_diarias = []
    
    # Conectores disponibles
    conectores = [
        ('MySQL', ConectorMySQL.extraer_pregunta),
        ('Redis', ConectorRedis.extraer_pregunta),
        ('PostgreSQL', ConectorPostgreSQL.extraer_pregunta),
        ('MongoDB', ConectorMongoDB.extraer_pregunta),
    ]
    
    print("📡 Conectando a las bases de datos y extrayendo preguntas...\n")
    
    for nombre_fuente, extractor in conectores:
        try:
            pregunta = extractor()
            
            if pregunta:
                # Clasificar la pregunta
                print(f"   Clasificando {nombre_fuente}...", end=" ")
                pregunta.categoria = clasificador.clasificar(pregunta.pregunta)
                preguntas_diarias.append(pregunta)
                print(f"✅")
            else:
                print(f"⚠️  {nombre_fuente}: No se pudo extraer pregunta")
        
        except Exception as e:
            print(f"❌ {nombre_fuente}: Error - {str(e)}")
    
    print()
    print("=" * 80)
    print("📋 SET DE PREGUNTAS DEL DÍA (UNIFICADO)")
    print("=" * 80)
    print()
    
    # Mostrar todas las preguntas en formato JSON
    resultado_final = {
        'timestamp': datetime.now().isoformat(),
        'total_preguntas': len(preguntas_diarias),
        'preguntas': [p.to_dict() for p in preguntas_diarias]
    }
    
    print(json.dumps(resultado_final, ensure_ascii=False, indent=2))
    
    # Guardar en archivo JSON
    with open('preguntas_del_dia.json', 'w', encoding='utf-8') as f:
        json.dump(resultado_final, f, ensure_ascii=False, indent=2)
    
    print()
    print("💾 Archivo guardado en: preguntas_del_dia.json")
    print()
    
    # Mostrar resumen
    print("=" * 80)
    print("📊 RESUMEN")
    print("=" * 80)
    for i, p in enumerate(preguntas_diarias, 1):
        print(f"\n{i}. [{p.fuente_origen}]")
        print(f"   Pregunta: {p.pregunta}")
        print(f"   Categoría: {p.categoria}")
        print(f"   Dificultad: {p.dificultad}")
        print(f"   Respuesta correcta: {p.respuesta_correcta}")
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()