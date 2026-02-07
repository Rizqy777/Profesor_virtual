import boto3
import time
import os
import json
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()


# ==================== GESTOR DE CONFIGURACIÓN ====================

class ConfigManager:
    """
    Clase para gestionar la configuración persistente entre ejecuciones.
    Guarda y carga los IDs de recursos en un archivo JSON.
    """
    
    CONFIG_FILE = "aws_config.json"
    
    # Configuración por defecto
    DEFAULT_CONFIG = {
        "vpc_id": None,
        "sg_id": None,
        "subnet_id": None,
        "instance_id": None,
        "efs_id": None,
        "volume_id": None,
        "key_pairs_name": None,
        "availability_zone": None,
        "mount_target_id": None,
        "s3_bucket": None
    }
    
    @staticmethod
    def cargar_config():
        """
        Carga la configuración desde el archivo JSON.
        Si no existe, crea uno nuevo con valores por defecto.
        """
        if os.path.exists(ConfigManager.CONFIG_FILE):
            try:
                with open(ConfigManager.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    print(f"✓ Configuración cargada desde {ConfigManager.CONFIG_FILE}")
                    return config
            except Exception as e:
                print(f"⚠ Error al cargar configuración: {str(e)}")
                return ConfigManager.DEFAULT_CONFIG.copy()
        else:
            print(f"ℹ Archivo de configuración no encontrado, creando nuevo...")
            ConfigManager.guardar_config(ConfigManager.DEFAULT_CONFIG)
            return ConfigManager.DEFAULT_CONFIG.copy()
    
    @staticmethod
    def guardar_config(config):
        """
        Guarda la configuración en el archivo JSON.
        """
        try:
            with open(ConfigManager.CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
            print(f"✓ Configuración guardada en {ConfigManager.CONFIG_FILE}")
        except Exception as e:
            print(f"✗ Error al guardar configuración: {str(e)}")
    
    @staticmethod
    def actualizar(key, value):
        """
        Actualiza un valor específico en la configuración.
        """
        config = ConfigManager.cargar_config()
        config[key] = value
        ConfigManager.guardar_config(config)
    
    @staticmethod
    def obtener(key, default=None):
        """
        Obtiene un valor específico de la configuración.
        """
        config = ConfigManager.cargar_config()
        return config.get(key, default)
    
    @staticmethod
    def mostrar():
        """
        Muestra toda la configuración actual.
        """
        config = ConfigManager.cargar_config()
        print("\n" + "=" * 80)
        print("CONFIGURACIÓN ACTUAL (aws_config.json)")
        print("=" * 80)
        for key, value in config.items():
            if value:
                print(f"  {key}: {value}")
            else:
                print(f"  {key}: (no configurado)")
        print("=" * 80)
    
    @staticmethod
    def limpiar():
        """
        Limpia toda la configuración (la resetea a valores por defecto).
        """
        ConfigManager.guardar_config(ConfigManager.DEFAULT_CONFIG.copy())
        print("✓ Configuración limpiada")

# ==================== GESTOR DE ALMACENAMIENTO ====================

class StorageManager:
    def __init__(self, region="us-east-1"):
        """
        Inicializa los clientes de AWS

        Args:
            region (str): Región de AWS donde crear los recursos (opcional, por defecto us-west-2)
        """
        self.region = region
        self.ec2_client = boto3.client("ec2", region_name=region)
        self.ec2_resource = boto3.resource("ec2", region_name=region)
        self.efs_client = boto3.client("efs", region_name=region)
        self.s3_client = boto3.client("s3", region_name=region)
        self.s3_resource = boto3.resource("s3", region_name=region)
        self.athena_client = boto3.client("athena", region_name=region)

    def crear_bucket_s3(self, bucket_name, acl="private", encryption=False):
        """
        CREAR BUCKET S3 (Amazon Simple Storage Service)

        Parámetros OBLIGATORIOS:
            - bucket_name (str): Nombre único del bucket (debe ser único globalmente)
                - Solo minúsculas, números, guiones
                - Máximo 63 caracteres
                - No puede empezar ni terminar con número

        Parámetros OPCIONALES:
            - acl (str): Control de acceso (private, public-read, public-read-write)
                - 'private': Solo el propietario puede acceder (RECOMENDADO)
                - 'public-read': Cualquiera puede leer
                - 'public-read-write': Cualquiera puede leer y escribir
            - encryption (bool): Encriptación en reposo (por defecto False)

        Almacena: Contenedor para almacenar objetos (archivos, datos, etc.)
        Casos de uso: Almacenar imágenes, backups, datos, logs, etc.
        """
        try:
            bucket_name = bucket_name.lower()
            print(f"\n[S3] Creando bucket: {bucket_name}...")
            print(f"  ACL: {acl}")
            print(f"  Encriptación: {encryption}")

            # Parámetros obligatorios
            params = {
                "Bucket": bucket_name,  # OBLIGATORIO: Nombre del bucket
                "ACL": acl,  # OPCIONAL: Control de acceso
            }

            # Crear bucket
            response = self.s3_client.create_bucket(
                Bucket=bucket_name,
                ACL=acl,
                CreateBucketConfiguration={"LocationConstraint": self.region}
                if self.region != "us-east-1"
                else {},
            )

            print(f"✓ Bucket creado: {bucket_name}")

            # Agregar etiquetas al bucket
            self.s3_client.put_bucket_tagging(
                Bucket=bucket_name,
                Tagging={"TagSet": [{"Key": "Nombre", "Value": bucket_name}]},
            )

            return bucket_name

        except Exception as e:
            if "BucketAlreadyOwnedByYou" in str(e):
                print(f"⚠ Bucket '{bucket_name}' ya existe y te pertenece")
                return bucket_name
            elif "BucketAlreadyExists" in str(e):
                print(f"✗ Error: Bucket '{bucket_name}' ya existe (pertenece a otro usuario)")
                return None
            print(f"✗ Error al crear bucket: {str(e)}")
            return None


    def crear_carpeta_s3(self, bucket_name, folder_name):
        """
        CREAR CARPETA EN S3 (Simular carpeta usando prefijo)

        Parámetros OBLIGATORIOS:
            - bucket_name (str): Nombre del bucket
            - folder_name (str): Nombre de la carpeta (ej: "datos", "backup/2024")

        NOTA: En S3, las "carpetas" no existen realmente, son prefijos de objetos
              Para crear una carpeta, subimos un objeto vacío con "/" al final

        Almacena: Prefijo para organizar objetos en el bucket
        """
        try:
            print(f"\n[S3] Creando carpeta: {bucket_name}/{folder_name}/")

            # Crear un objeto vacío para simular la carpeta
            self.s3_client.put_object(
                Bucket=bucket_name,
                Key=f"{folder_name}/",  # OBLIGATORIO: Clave del objeto (carpeta)
                Body=b"",  # Objeto vacío
            )

            print(f"✓ Carpeta creada: {folder_name}/")
            return True

        except Exception as e:
            print(f"✗ Error al crear carpeta: {str(e)}")
            return False

    def subir_archivo_s3(self, bucket_name, file_path, s3_key):
        """
        SUBIR ARCHIVO A S3

        Parámetros OBLIGATORIOS:
            - bucket_name (str): Nombre del bucket
            - file_path (str): Ruta local del archivo
            - s3_key (str): Ruta en S3 (ej: "datos/archivo.csv")

        Parámetros OPCIONALES:
            - ExtraArgs: Metadatos, ACL, etc.
            - Callback: Función para monitorear progreso

        Almacena: Archivos en el bucket S3
        Casos de uso: Subir datos, imágenes, backups, etc.
        """
        try:
            print(f"\n[S3] Subiendo archivo a S3...")
            print(f"  Bucket: {bucket_name}")
            print(f"  Archivo local: {file_path}")
            print(f"  Ruta en S3: {s3_key}")

            # Verificar que el archivo existe
            if not os.path.exists(file_path):
                print(f"✗ Error: Archivo no encontrado: {file_path}")
                return False

            # Subir archivo
            self.s3_client.upload_file(
                file_path,
                bucket_name,
                s3_key,
            )

            print(f"✓ Archivo subido exitosamente")
            return True

        except Exception as e:
            print(f"✗ Error al subir archivo: {str(e)}")
            return False

    def subir_contenido_s3(self, bucket_name, contenido, s3_key, content_type="text/plain"):
        """
        SUBIR CONTENIDO DIRECTO A S3 (sin archivo local)

        Parámetros OBLIGATORIOS:
            - bucket_name (str): Nombre del bucket
            - contenido (str o bytes): Contenido a subir
            - s3_key (str): Ruta en S3 (ej: "datos/archivo.csv")
            - content_type (str): Tipo MIME (text/plain, text/csv, application/json, etc.)

        Almacena: Contenido directo en S3 sin necesidad de archivo local
        Casos de uso: Crear archivos dinámicamente, datos generados
        """
        try:
            print(f"\n[S3] Subiendo contenido a S3...")
            print(f"  Bucket: {bucket_name}")
            print(f"  Ruta en S3: {s3_key}")
            print(f"  Tipo: {content_type}")

            # Convertir contenido a bytes si es string
            if isinstance(contenido, str):
                contenido = contenido.encode("utf-8")

            # Subir contenido
            self.s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,  # OBLIGATORIO: Ruta del objeto
                Body=contenido,  # OBLIGATORIO: Contenido
                ContentType=content_type,  # OPCIONAL: Tipo MIME
            )

            print(f"✓ Contenido subido exitosamente")
            return True

        except Exception as e:
            print(f"✗ Error al subir contenido: {str(e)}")
            return False

    def subir_contenido_s3_con_storage_class(self, bucket_name, contenido, s3_key, 
                                         storage_class="STANDARD", content_type="text/plain"):
        """
        SUBIR CONTENIDO A S3 CON STORAGE CLASS ESPECÍFICA
        
        Parámetros OBLIGATORIOS:
            - bucket_name (str): Nombre del bucket
            - contenido (str o bytes): Contenido a subir
            - s3_key (str): Ruta en S3
            - storage_class (str): Clase de almacenamiento:
                - 'STANDARD': Acceso frecuente (defecto, costo normal)
                - 'STANDARD_IA': Acceso infrecuente (más barato, 30 días mínimo)
                - 'INTELLIGENT_TIERING': Automático según acceso (variable)
                - 'GLACIER': Archivo a largo plazo (muy barato, recuperación en horas)
                - 'DEEP_ARCHIVE': Compliance/Backup (baratísimo, recuperación en 12+ horas)
                - 'ONEZONE_IA': Una sola zona (más barato que STANDARD_IA)
        
        Almacena: Contenido con clase de almacenamiento específica
        Casos de uso: Optimizar costos según patrón de acceso
        """
        try:
            print(f"\n[S3] Subiendo contenido con Storage Class: {storage_class}...")
            print(f"  Bucket: {bucket_name}")
            print(f"  Ruta: {s3_key}")
            print(f"  Storage Class: {storage_class}")
            
            if isinstance(contenido, str):
                contenido = contenido.encode("utf-8")
            
            self.s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=contenido,
                ContentType=content_type,
                StorageClass=storage_class  # CLAVE: Define la clase de almacenamiento
            )
            
            print(f"✓ Contenido subido exitosamente con {storage_class}")
            return True
            
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return False

    def subir_archivo_s3_con_storage_class(self, bucket_name, file_path, s3_key, 
                                        storage_class="STANDARD"):
        """
        SUBIR ARCHIVO A S3 CON STORAGE CLASS ESPECÍFICA
        
        Parámetros OBLIGATORIOS:
            - bucket_name (str): Nombre del bucket
            - file_path (str): Ruta local del archivo
            - s3_key (str): Ruta en S3
            - storage_class (str): Clase de almacenamiento (ver arriba)
        
        Casos de uso: Subir backups a Glacier, datos históricos a Deep Archive
        """
        try:
            print(f"\n[S3] Subiendo archivo con Storage Class: {storage_class}...")
            print(f"  Archivo local: {file_path}")
            print(f"  Ruta en S3: {s3_key}")
            
            if not os.path.exists(file_path):
                print(f"✗ Archivo no encontrado: {file_path}")
                return False
            
            # Usar ExtraArgs para especificar StorageClass
            self.s3_client.upload_file(
                file_path,
                bucket_name,
                s3_key,
                ExtraArgs={'StorageClass': storage_class}
            )
            
            print(f"✓ Archivo subido con {storage_class}")
            return True
            
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return False

    
    def listar_objetos_s3(self, bucket_name, prefix=""):
        """
        LISTAR OBJETOS EN S3

        Parámetros OBLIGATORIOS:
            - bucket_name (str): Nombre del bucket

        Parámetros OPCIONALES:
            - prefix (str): Filtrar por prefijo (ej: "datos/" para listar solo esa carpeta)

        Retorna: Lista de objetos en el bucket
        """
        try:
            print(f"\n[S3] Listando objetos en {bucket_name}...")

            response = self.s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix,  # OPCIONAL: Filtrar por prefijo
            )

            if "Contents" not in response:
                print("  No hay objetos en el bucket")
                return []

            objetos = []
            for obj in response["Contents"]:
                tamaño = obj["Size"]
                fecha = obj["LastModified"]
                clave = obj["Key"]

                # No mostrar carpetas vacías (terminan en /)
                if not clave.endswith("/"):
                    print(f"  - {clave} ({tamaño} bytes, {fecha})")
                    objetos.append(clave)
                else:
                    print(f"  📁 {clave}")

            return objetos

        except Exception as e:
            print(f"✗ Error al listar objetos: {str(e)}")
            return []
        
    def descargar_objeto_s3(self, bucket_name, s3_key, file_path=None):
        """
        DESCARGAR OBJETO DESDE S3

        Parámetros OBLIGATORIOS:
            - bucket_name (str): Nombre del bucket
            - s3_key (str): Ruta del objeto en S3 (ej: "datos/archivo.csv")

        Parámetros OPCIONALES:
            - file_path (str): Ruta local donde guardar (por defecto usa el nombre del objeto)

        Retorna: Ruta donde se guardó el archivo
        """
        try:
            print(f"\n[S3] Descargando objeto desde S3...")
            print(f"  Bucket: {bucket_name}")
            print(f"  Objeto: {s3_key}")

            # Si no especifica ruta, usar el nombre del objeto
            if not file_path:
                file_path = os.path.basename(s3_key)

            # Crear carpetas si no existen
            os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)

            # Descargar archivo
            self.s3_client.download_file(bucket_name, s3_key, file_path)

            print(f"✓ Archivo descargado: {file_path}")
            return file_path

        except Exception as e:
            print(f"✗ Error al descargar objeto: {str(e)}")
            return None

    def obtener_contenido_s3(self, bucket_name, s3_key):
        """
        OBTENER CONTENIDO DE UN OBJETO S3 (sin descargar archivo)

        Parámetros OBLIGATORIOS:
            - bucket_name (str): Nombre del bucket
            - s3_key (str): Ruta del objeto (ej: "datos/archivo.csv")

        Retorna: Contenido del objeto como bytes
        """
        try:
            print(f"\n[S3] Obteniendo contenido desde S3...")
            print(f"  Bucket: {bucket_name}")
            print(f"  Objeto: {s3_key}")

            response = self.s3_client.get_object(
                Bucket=bucket_name,
                Key=s3_key,  # OBLIGATORIO: Clave del objeto
            )

            # Leer contenido
            contenido = response["Body"].read()

            print(f"✓ Contenido obtenido ({len(contenido)} bytes)")
            return contenido

        except Exception as e:
            print(f"✗ Error al obtener contenido: {str(e)}")
            return None

    def obtener_contenido_s3_como_texto(self, bucket_name, s3_key):
        """
        OBTENER CONTENIDO DE UN OBJETO S3 COMO TEXTO

        Parámetros OBLIGATORIOS:
            - bucket_name (str): Nombre del bucket
            - s3_key (str): Ruta del objeto (ej: "datos/archivo.csv")

        Retorna: Contenido como string
        """
        try:
            contenido_bytes = self.obtener_contenido_s3(bucket_name, s3_key)
            if contenido_bytes:
                return contenido_bytes.decode("utf-8")
            return None
        except Exception as e:
            print(f"✗ Error al decodificar contenido: {str(e)}")
            return None

    def eliminar_objeto_s3(self, bucket_name, s3_key):
        """
        ELIMINAR OBJETO DE S3

        Parámetros OBLIGATORIOS:
            - bucket_name (str): Nombre del bucket
            - s3_key (str): Ruta del objeto a eliminar

        ADVERTENCIA: Esta acción es irreversible
        """
        try:
            print(f"\n[S3] Eliminando objeto: {s3_key}")

            self.s3_client.delete_object(
                Bucket=bucket_name,
                Key=s3_key,  # OBLIGATORIO: Clave del objeto
            )

            print(f"✓ Objeto eliminado")
            return True

        except Exception as e:
            print(f"✗ Error al eliminar objeto: {str(e)}")
            return False

    def eliminar_bucket_s3(self, bucket_name):
        """
        ELIMINAR BUCKET S3 (vacío)

        Parámetro OBLIGATORIO:
            - bucket_name (str): Nombre del bucket

        NOTA: El bucket DEBE estar vacío para poder eliminarlo
        ADVERTENCIA: Esta acción es irreversible
        """
        try:
            print(f"\n[S3] Eliminando bucket: {bucket_name}")

            # Primero, eliminar todos los objetos
            print(f"  Limpiando objetos...")
            objetos = self.listar_objetos_s3(bucket_name)
            for obj in objetos:
                self.eliminar_objeto_s3(bucket_name, obj)

            # Eliminar el bucket
            self.s3_client.delete_bucket(Bucket=bucket_name)

            print(f"✓ Bucket eliminado")
            return True

        except Exception as e:
            print(f"✗ Error al eliminar bucket: {str(e)}")
            return False
    
    def habilitar_versionado_s3(self, bucket_name):
        """
        HABILITAR VERSIONADO EN S3
        
        Permite guardar múltiples versiones de un objeto
        
        Parámetros:
            - bucket_name: Nombre del bucket
        """
        try:
            print(f"\n[S3] Habilitando versionado en {bucket_name}...")
            
            self.s3_client.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            
            print(f"✓ Versionado habilitado")
            return True
        
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return False

    def obtener_versiones_objeto(self, bucket_name, s3_key):
        """
        OBTENER TODAS LAS VERSIONES DE UN OBJETO
        
        Retorna lista de versiones con sus IDs
        """
        try:
            print(f"\n[S3] Listando versiones de {s3_key}...")
            
            response = self.s3_client.list_object_versions(
                Bucket=bucket_name,
                Prefix=s3_key
            )
            
            versiones = []
            if 'Versions' in response:
                for version in response['Versions']:
                    versiones.append({
                        'VersionId': version['VersionId'],
                        'LastModified': version['LastModified'],
                        'Size': version['Size'],
                        'IsLatest': version['IsLatest']
                    })
                    
                    print(f"\n  Versión: {version['VersionId']}")
                    print(f"    Última: {version['IsLatest']}")
                    print(f"    Fecha: {version['LastModified']}")
                    print(f"    Tamaño: {version['Size']} bytes")
            
            return versiones
            
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return []

    def obtener_version_especifica(self, bucket_name, s3_key, version_id):
        """
        OBTENER UNA VERSION ESPECIFICA DE UN OBJETO
        """
        try:
            print(f"\n[S3] Obteniendo versión {version_id[:8]}... del objeto {s3_key}")
            
            response = self.s3_client.get_object(
                Bucket=bucket_name,
                Key=s3_key,
                VersionId=version_id
            )
            
            contenido = response['Body'].read()
            print(f"✓ Contenido obtenido ({len(contenido)} bytes)")
            
            return contenido
            
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return None    
        
    # ==================== ATHENA ====================

    def crear_tabla_athena_csv(self, database_name, table_name, bucket_name, 
                          csv_path, columns):
        """
        CREAR TABLA ATHENA DESDE CSV EN S3
        
        Parámetros:
            - database_name: Nombre de la base de datos
            - table_name: Nombre de la tabla
            - bucket_name: Bucket S3 donde están los datos
            - csv_path: Ruta en S3 de los archivos (ej: "datos/")
            - columns: Lista de tuplas (nombre, tipo)
                    Ej: [("id", "int"), ("nombre", "string")]
        """
        try:
            print(f"\n[ATHENA] Creando tabla {table_name}...")
            
            # Construir definición de columnas
            cols_def = ", ".join([f"{col} {tipo}" for col, tipo in columns])
            
            # SQL para crear tabla
            sql = f"""
                    CREATE EXTERNAL TABLE IF NOT EXISTS {database_name}.{table_name} (
                        {cols_def}
                    )
                    ROW FORMAT DELIMITED
                    FIELDS TERMINATED BY ','
                    STORED AS TEXTFILE
                    LOCATION 's3://{bucket_name}/{csv_path}'
                    """
            
            print(f"SQL:\n{sql}")
            
            # Ejecutar query
            response = self.athena_client.start_query_execution(
                QueryString=sql,
                QueryExecutionContext={'Database': database_name},
                ResultConfiguration={'OutputLocation': f's3://{bucket_name}/athena-results/'}
            )
            
            query_id = response['QueryExecutionId']
            print(f"✓ Tabla creada con QueryID: {query_id}")
            
            return query_id
        
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return None

    def ejecutar_query_athena(self, database_name, sql, bucket_name):
        """
        EJECUTAR QUERY EN ATHENA
        
        Parámetros:
            - database_name: Base de datos
            - sql: Consulta SQL
            - bucket_name: Bucket para resultados
        """
        try:
            print(f"\n[ATHENA] Ejecutando query...")
            print(f"SQL: {sql}\n")
            
            response = self.athena_client.start_query_execution(
                QueryString=sql,
                QueryExecutionContext={'Database': database_name},
                ResultConfiguration={'OutputLocation': f's3://{bucket_name}/athena-results/'}
            )
            
            query_id = response['QueryExecutionId']
            print(f"✓ Query ejecutado. ID: {query_id}")
            
            # Esperar a que termine
            import time
            max_attempts = 30
            for i in range(max_attempts):
                response = self.athena_client.get_query_execution(QueryExecutionId=query_id)
                status = response['QueryExecution']['Status']['State']
                
                if status == 'SUCCEEDED':
                    print(f"✓ Query completado")
                    break
                elif status == 'FAILED':
                    print(f"✗ Query falló: {response['QueryExecution']['Status']['StateChangeReason']}")
                    return None
                
                time.sleep(1)
            
            # Obtener resultados
            results = self.athena_client.get_query_results(QueryExecutionId=query_id)
            
            # Mostrar resultados
            print(f"\n[RESULTADOS]")
            for row in results['ResultSet']['Rows']:
                valores = [col.get('VarCharValue', '') for col in row['Data']]
                print(f"  {valores}")
            
            return results
            
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return None

    def crear_tabla_athena_json(self, database_name, table_name, bucket_name, 
                            json_path, columns):
        """
        CREAR TABLA ATHENA DESDE JSON EN S3
        """
        try:
            print(f"\n[ATHENA] Creando tabla JSON {table_name}...")
            
            cols_def = ", ".join([f"{col} {tipo}" for col, tipo in columns])
            
            sql = f"""
            CREATE EXTERNAL TABLE IF NOT EXISTS {database_name}.{table_name} (
                {cols_def}
            )
            ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
            STORED AS TEXTFILE
            LOCATION 's3://{bucket_name}/{json_path}'
            """
            
            print(f"SQL:\n{sql}")
            
            response = self.athena_client.start_query_execution(
                QueryString=sql,
                QueryExecutionContext={'Database': database_name},
                ResultConfiguration={'OutputLocation': f's3://{bucket_name}/athena-results/'}
            )
            
            query_id = response['QueryExecutionId']
            print(f"✓ Tabla JSON creada: {query_id}")
            return query_id
            
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return None
        
    def crear_tabla_particionada_athena(self, database_name, table_name, 
                                    bucket_name, columns):
        """
        CREAR TABLA PARTICIONADA EN ATHENA
        
        Las particiones aceleran las queries filtrando por columna
        """
        try:
            print(f"\n[ATHENA] Creando tabla particionada {table_name}...")
            
            cols_def = ", ".join([f"{col} {tipo}" for col, tipo in columns[:-1]])
            partition_col, partition_type = columns[-1]
            
            sql = f"""
            CREATE EXTERNAL TABLE IF NOT EXISTS {database_name}.{table_name} (
                {cols_def}
            )
            PARTITIONED BY (
                {partition_col} {partition_type}
            )
            ROW FORMAT DELIMITED
            FIELDS TERMINATED BY ','
            STORED AS TEXTFILE
            LOCATION 's3://{bucket_name}/datos_particionados/'
            """
            
            print(f"SQL:\n{sql}")
            
            response = self.athena_client.start_query_execution(
                QueryString=sql,
                QueryExecutionContext={'Database': database_name},
                ResultConfiguration={'OutputLocation': f's3://{bucket_name}/athena-results/'}
            )
            
            print(f"✓ Tabla particionada creada")
            return response['QueryExecutionId']
            
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return None

    def agregar_particion_athena(self, database_name, table_name, 
                                partition_value, bucket_name, path):
        """
        AGREGAR PARTICIÓN A TABLA
        """
        try:
            print(f"\n[ATHENA] Agregando partición...")
            
            sql = f"""
            ALTER TABLE {database_name}.{table_name}
            ADD IF NOT EXISTS PARTITION (year='{partition_value}')
            LOCATION 's3://{bucket_name}/{path}'
            """
            
            response = self.athena_client.start_query_execution(
                QueryString=sql,
                QueryExecutionContext={'Database': database_name},
                ResultConfiguration={'OutputLocation': f's3://{bucket_name}/athena-results/'}
            )
            
            print(f"✓ Partición agregada")
            return response['QueryExecutionId']
            
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            return None
    
    # ==================== VPC/NETWORK MANAGEMENT ====================

    def obtener_vpc_predeterminada(self):
        """
        Obtiene la VPC por defecto de la región
        """
        try:
            response = self.ec2_client.describe_vpcs(
                Filters=[{"Name": "isDefault", "Values": ["true"]}]
            )
            if response["Vpcs"]:
                vpc_id = response["Vpcs"][0]["VpcId"]
                print(f"[VPC] VPC por defecto encontrada: {vpc_id}")
                return vpc_id
            else:
                print("[VPC] No se encontró VPC por defecto")
                return None
        except Exception as e:
            print(f"✗ Error al obtener VPC: {str(e)}")
            return None

    def obtener_subnet_predeterminada(self, vpc_id=None):
        """
        Obtiene una subred de la VPC (por defecto usa la VPC por defecto)
        Las subredes YA EXISTEN en tu VPC, no necesitan crearse
        """
        try:
            filters = []
            if vpc_id:
                filters.append({"Name": "vpc-id", "Values": [vpc_id]})

            response = self.ec2_client.describe_subnets(Filters=filters)
            if response["Subnets"]:
                subnet_id = response["Subnets"][0]["SubnetId"]
                availability_zone = response["Subnets"][0]["AvailabilityZone"]
                print(f"[SUBNET] Subred encontrada: {subnet_id} ({availability_zone})")
                return subnet_id, availability_zone
            else:
                print("[SUBNET] No se encontraron subredes")
                return None, None
        except Exception as e:
            print(f"✗ Error al obtener subred: {str(e)}")
            return None, None

    def crear_security_group(self, sg_name, sg_description, vpc_id=None):
        """
        CREAR SECURITY GROUP NUEVO

        Parámetros OBLIGATORIOS:
            - sg_name (str): Nombre del security group
            - sg_description (str): Descripción del SG

        Parámetros OPCIONALES:
            - vpc_id (str): ID de la VPC (por defecto crea en VPC por defecto)

        Retorna: ID del security group creado
        """
        try:
            print(f"\n[SG] Creando Security Group: {sg_name}...")

            # Si no especifica VPC, usa la por defecto
            if not vpc_id:
                vpc_id = self.obtener_vpc_predeterminada()
                if not vpc_id:
                    print("✗ No se pudo obtener VPC por defecto")
                    return None

            params = {
                "GroupName": sg_name,
                "Description": sg_description,
                "VpcId": vpc_id,
            }

            response = self.ec2_client.create_security_group(**params)
            sg_id = response["GroupId"]

            print(f"✓ Security Group creado: {sg_id}")

            return sg_id

        except Exception as e:
            if "InvalidGroup.Duplicate" in str(e):
                print(f"⚠ Security Group '{sg_name}' ya existe")
                # Obtener su ID
                response = self.ec2_client.describe_security_groups(
                    Filters=[{"Name": "group-name", "Values": [sg_name]}]
                )
                if response["SecurityGroups"]:
                    return response["SecurityGroups"][0]["GroupId"]
            print(f"✗ Error al crear Security Group: {str(e)}")
            return None

    def agregar_regla_ingress_sg(
        self, sg_id, protocol, from_port, to_port, cidr="0.0.0.0/0"
    ):
        """
        AGREGAR REGLA INGRESS (ENTRADA) AL SECURITY GROUP

        Parámetros OBLIGATORIOS:
            - sg_id (str): ID del security group
            - protocol (str): Protocolo ('tcp', 'udp', 'icmp', '-1' para todos)
            - from_port (int): Puerto inicial
            - to_port (int): Puerto final
            - cidr (str): CIDR que puede acceder (por defecto 0.0.0.0/0 = todos)

        Ejemplos:
            - SSH: protocol='tcp', from_port=22, to_port=22
            - HTTP: protocol='tcp', from_port=80, to_port=80
            - HTTPS: protocol='tcp', from_port=443, to_port=443
            - Todos: protocol='-1', from_port=-1, to_port=-1
        """
        try:
            print(
                f"\n[SG] Agregando regla INGRESS: {protocol}:{from_port}-{to_port} desde {cidr}"
            )

            self.ec2_client.authorize_security_group_ingress(
                GroupId=sg_id,
                IpPermissions=[
                    {
                        "IpProtocol": protocol,
                        "FromPort": from_port,
                        "ToPort": to_port,
                        "IpRanges": [
                            {"CidrIp": cidr, "Description": "Acceso permitido"}
                        ],
                    }
                ],
            )

            print(f"✓ Regla ingress agregada")
            return True

        except Exception as e:
            if "InvalidPermission.Duplicate" in str(e):
                print(f"⚠ Regla ya existe")
                return True
            print(f"✗ Error al agregar regla: {str(e)}")
            return False

    def agregar_regla_egress_sg(
        self, sg_id, protocol, from_port, to_port, cidr="0.0.0.0/0"
    ):
        """
        AGREGAR REGLA EGRESS (SALIDA) AL SECURITY GROUP
        Similar a ingress pero para tráfico de salida
        """
        try:
            print(
                f"\n[SG] Agregando regla EGRESS: {protocol}:{from_port}-{to_port} hacia {cidr}"
            )

            self.ec2_client.authorize_security_group_egress(
                GroupId=sg_id,
                IpPermissions=[
                    {
                        "IpProtocol": protocol,
                        "FromPort": from_port,
                        "ToPort": to_port,
                        "IpRanges": [
                            {"CidrIp": cidr, "Description": "Acceso permitido"}
                        ],
                    }
                ],
            )

            print(f"✓ Regla egress agregada")
            return True

        except Exception as e:
            print(f"✗ Error al agregar regla egress: {str(e)}")
            return False

    def crear_key_pair(self, key_name):
        """
        CREAR O VERIFICAR KEY PAIR PARA SSH

        Parámetro OBLIGATORIO:
            - key_name (str): Nombre de la key pair

        Retorna: Nombre de la key pair
        """
        try:
            # Verificar si existe
            response = self.ec2_client.describe_key_pairs(KeyNames=[key_name])
            print(f"✓ Key Pair ya existe: {key_name}")
            return key_name
        except:
            # Crear si no existe
            try:
                print(f"\n[KeyPair] Creando Key Pair: {key_name}...")
                response = self.ec2_client.create_key_pair(KeyName=key_name)
                print(f"✓ Key Pair creado: {key_name}")
                print(f"⚠ Guarda el contenido abajo en un archivo .pem para SSH:")
                print(response["KeyMaterial"][:100] + "...")
                return key_name
            except Exception as e:
                print(f"✗ Error al crear Key Pair: {str(e)}")
                return None

    # ==================== EC2 MANAGEMENT ====================
    # Almacenamiento: Instancias de máquinas virtuales completas en la nube
    # Caso de uso: Ejecutar servidores web, aplicaciones, bases de datos

    def crear_ec2(
        self,
        instance_name,
        subnet_id,
        ami_id="ami-0ecb62995f68bb549",
        instance_type="t2.micro",
        security_group_name="sg-076af812ec93aff17",
        key_name="clave_casa",
        user_data=None
    ):
        """
        CREAR INSTANCIA EC2

        Parámetros OBLIGATORIOS:
            - ami_id (str): ID de la imagen AMI (ej: ami-0ecb62995f68bb549 para Ubuntu en us-east-1)
            - instance_type (str): Tipo de instancia (t2.micro, t2.small, t3.medium, etc.)

        Parámetros OPCIONALES:
            - instance_name (str): Nombre para etiquetar la instancia
            - security_group_name (str): Grupo de seguridad a usar
            - key_name (str): Par de claves para SSH
            - user_data (str): Script bash a ejecutar al iniciar la instancia
            - MaxCount, MinCount: Cantidad de instancias (por defecto 1)

        Almacena: Máquina virtual con SO (Linux/Windows) lista para usar
        """
        try:
            print(f"\n[EC2] Creando instancia: {instance_name}...")

            # Parámetros obligatorios
            params = {
                "ImageId": ami_id,  # OBLIGATORIO: ID de la imagen
                "MinCount": 1,  # OBLIGATORIO: Mínimo de instancias
                "MaxCount": 1,  # OBLIGATORIO: Máximo de instancias
                "InstanceType": instance_type,  # OBLIGATORIO: Tipo de máquina
                "SecurityGroupIds": security_group_name,  # OPCIONAL
                "SubnetId":subnet_id,
                "KeyName": key_name,  # OPCIONAL
            }

            # Parámetros opcionales
            if security_group_name:
                params["SecurityGroupIds"] = [security_group_name]
            if key_name:
                params["KeyName"] = key_name
            if user_data:
                params["UserData"] = user_data  # Script a ejecutar al iniciar

            # Crear la instancia
            response = self.ec2_client.run_instances(**params)
            instance_id = response["Instances"][0]["InstanceId"]

            # Etiquetar la instancia (opcional pero útil)
            self.ec2_resource.create_tags(
                Resources=[instance_id], Tags=[{"Key": "Name", "Value": instance_name}]
            )

            print(f"✓ Instancia creada exitosamente: {instance_id}")
            print(f"  Estado: {response['Instances'][0]['State']['Name']}")

            return instance_id

        except Exception as e:
            print(f"✗ Error al crear instancia EC2: {str(e)}")
            return None

    def ejecutar_ec2(self, instance_id):
        """
        EJECUTAR (INICIAR) INSTANCIA EC2

        Parámetro OBLIGATORIO:
            - instance_id (str): ID de la instancia a iniciar

        Parámetros OPCIONALES:
            - DryRun (bool): Simular la operación sin ejecutar
        """
        try:
            print(f"\n[EC2] Iniciando instancia: {instance_id}...")

            self.ec2_client.start_instances(InstanceIds=[instance_id])

            # Esperar a que inicie
            waiter = self.ec2_client.get_waiter("instance_running")
            waiter.wait(InstanceIds=[instance_id])

            print(f"✓ Instancia iniciada: {instance_id}")

        except Exception as e:
            print(f"✗ Error al iniciar instancia: {str(e)}")

    def parar_ec2(self, instance_id):
        """
        PARAR INSTANCIA EC2

        Parámetro OBLIGATORIO:
            - instance_id (str): ID de la instancia a parar

        Parámetros OPCIONALES:
            - Force (bool): Forzar parada
            - Hibernate (bool): Hibernar en lugar de parar

        Nota: Los datos en EBS persisten cuando se para
        """
        try:
            print(f"\n[EC2] Parando instancia: {instance_id}...")

            self.ec2_client.stop_instances(InstanceIds=[instance_id])

            # Esperar a que se pare
            waiter = self.ec2_client.get_waiter("instance_stopped")
            waiter.wait(InstanceIds=[instance_id])

            print(f"✓ Instancia parada: {instance_id}")

        except Exception as e:
            print(f"✗ Error al parar instancia: {str(e)}")

    def eliminar_ec2(self, instance_id):
        """
        ELIMINAR (TERMINAR) INSTANCIA EC2

        Parámetro OBLIGATORIO:
            - instance_id (str): ID de la instancia a eliminar

        Parámetros OPCIONALES:
            - Force (bool): Forzar terminación

        ADVERTENCIA: Esta acción es irreversible. Los volúmenes EBS
                     con DeleteOnTermination=True también se eliminarán
        """
        try:
            print(f"\n[EC2] Eliminando instancia: {instance_id}...")

            self.ec2_client.terminate_instances(InstanceIds=[instance_id])

            # Esperar a que se termine
            waiter = self.ec2_client.get_waiter("instance_terminated")
            waiter.wait(InstanceIds=[instance_id])

            print(f"✓ Instancia eliminada: {instance_id}")

        except Exception as e:
            print(f"✗ Error al eliminar instancia: {str(e)}")

    def obtener_estado_ec2(self, instance_id):
        """
        Obtener estado actual de una instancia EC2
        """
        try:
            response = self.ec2_client.describe_instances(InstanceIds=[instance_id])
            state = response["Reservations"][0]["Instances"][0]["State"]["Name"]
            print(f"[EC2] Estado de {instance_id}: {state}")
            return state
        except Exception as e:
            print(f"✗ Error al obtener estado: {str(e)}")
            return None

    # ==================== EBS MANAGEMENT ====================
    # Almacenamiento: Almacenamiento en bloque persistente y de alto rendimiento
    # Caso de uso: Discos duros virtuales para bases de datos, archivos críticos

    def crear_ebs(
        self, volume_name, size=20, availability_zone=None, volume_type="gp3"
    ):
        """
        CREAR VOLUMEN EBS (Elastic Block Store)

        Parámetros OBLIGATORIOS:
            - Size (int): Tamaño en GB (1-16384)
            - AvailabilityZone (str): Zona de disponibilidad (ej: us-west-2a)

        Parámetros OPCIONALES:
            - volume_name (str): Nombre para etiquetar el volumen
            - VolumeType (str): Tipo de volumen (gp2, gp3, io1, io2, st1, sc1)
                - gp3: Propósito general, mejor relación precio/rendimiento
                - io1/io2: IOPS provisionadas, muy alto rendimiento
                - st1: Optimizado para rendimiento
                - sc1: Optimizado para cold storage
            - Encrypted (bool): Encriptación (por defecto False)
            - Iops (int): IOPS provisionadas (solo para io1, io2, gp3)
            - Throughput (int): Rendimiento en MB/s (solo para gp3)
            - TagSpecifications: Etiquetas

        Almacena: Volumen de almacenamiento en bloque persistente
        Nota: DEBE estar en la MISMA zona de disponibilidad que el EC2
        """
        try:
            # Obtener zona de disponibilidad por defecto si no se proporciona
            if not availability_zone:
                response = self.ec2_client.describe_availability_zones()
                availability_zone = response["AvailabilityZones"][0]["ZoneName"]

            print(f"\n[EBS] Creando volumen EBS: {volume_name}...")
            print(f"  Tamaño: {size} GB")
            print(f"  Tipo: {volume_type}")
            print(f"  Zona: {availability_zone}")

            # Parámetros obligatorios
            params = {
                "Size": size,  # OBLIGATORIO: Tamaño en GB
                "AvailabilityZone": availability_zone,  # OBLIGATORIO: Zona
                "VolumeType": volume_type,  # OBLIGATORIO: Tipo de volumen
            }

            # Parámetros opcionales según tipo
            if volume_type in ["gp3", "io1", "io2"]:
                params["Iops"] = 3000  # IOPS mínimas para gp3
            if volume_type == "gp3":
                params["Throughput"] = 125  # Rendimiento en MB/s

            params["Encrypted"] = False  # Opcional: activar encriptación

            response = self.ec2_client.create_volume(**params)
            volume_id = response["VolumeId"]

            # Etiquetar el volumen
            self.ec2_resource.create_tags(
                Resources=[volume_id], Tags=[{"Key": "Name", "Value": volume_name}]
            )

            print(f"✓ Volumen EBS creado: {volume_id}")

            return volume_id

        except Exception as e:
            print(f"✗ Error al crear volumen EBS: {str(e)}")
            return None

    def asociar_ebs_a_ec2(self, volume_id, instance_id, device="/dev/sdf"):
        """
        ASOCIAR VOLUMEN EBS A INSTANCIA EC2

        Parámetros OBLIGATORIOS:
            - volume_id (str): ID del volumen EBS
            - instance_id (str): ID de la instancia EC2
            - device (str): Nombre del dispositivo (ej: /dev/sdf, /dev/sdg)

        Parámetros OPCIONALES:
            - DeleteOnTermination (bool): Eliminar volumen al terminar EC2

        Nota: La instancia DEBE estar en RUNNING o STOPPED
        """
        try:
            print(f"\n[EBS] Asociando volumen {volume_id} a instancia {instance_id}...")

            self.ec2_client.attach_volume(
                VolumeId=volume_id, InstanceId=instance_id, Device=device
            )

            # Esperar a que se asocie
            time.sleep(2)

            print(f"✓ Volumen asociado en dispositivo {device}")

            return True

        except Exception as e:
            print(f"✗ Error al asociar volumen: {str(e)}")
            return False

    def generar_user_data_montaje_ebs(
        self, device="/dev/sdf", mount_point="/mnt/datos"
    ):
        """
        GENERAR SCRIPT USER_DATA PARA MONTAR EBS AUTOMÁTICAMENTE

        Este script se ejecuta automáticamente cuando inicia la instancia EC2

        Parámetros:
            - device (str): Dispositivo EBS asociado (ej: /dev/sdf)
            - mount_point (str): Ruta donde montar el EBS

        Retorna: Script bash para montar el EBS
        """
        user_data_script = f"""#!/bin/bash
# Script de montaje automático de EBS

echo "Esperando a que el dispositivo {device} esté disponible..."
sleep 10

# Verificar si el dispositivo existe
if [ ! -e {device} ]; then
    echo "Error: Dispositivo {device} no encontrado"
    exit 1
fi

echo "Dispositivo encontrado: {device}"

# Verificar si tiene particiones
if ! sudo fdisk -l {device} | grep -q "Units="; then
    echo "Inicializando y formateando dispositivo {device}..."
    
    # Crear partición
    sudo parted {device} mklabel gpt
    sudo parted {device} mkpart primary ext4 1 100%
    
    # Esperar a que se cree la partición
    sleep 5
    
    # Formatear
    sudo mkfs.ext4 {device}1
fi

# Crear punto de montaje
sudo mkdir -p {mount_point}

# Montar el volumen
sudo mount {device}1 {mount_point}

# Cambiar permisos
sudo chown ec2-user:ec2-user {mount_point}
chmod 755 {mount_point}

# Agregar a fstab para montaje automático en reinicios
if ! grep -q "{device}" /etc/fstab; then
    echo "{device}1 {mount_point} ext4 defaults,nofail 0 2" | sudo tee -a /etc/fstab
fi

echo "EBS montado en {mount_point}"
df -h {mount_point}
"""
        return user_data_script

    def agregar_archivo_ebs(self, instance_id, archivo_path, contenido):
        """
        AGREGAR ARCHIVO AL VOLUMEN EBS (via SSH)

        NOTA: Requiere SSH accesible y credenciales de clave privada
        Para simplificar la demostración, usaremos user_data en EC2

        Parámetros:
            - instance_id: ID de la instancia
            - archivo_path: Ruta donde crear el archivo
            - contenido: Contenido del archivo
        """
        print(f"\n[EBS] Para agregar archivos al EBS, usa SSH o configurar user_data")
        print(f"      Archivo que se guardaría: {archivo_path}")
        print(f"      Contenido: {contenido[:50]}...")

    # ==================== EFS MANAGEMENT ====================
    # Almacenamiento: Sistema de archivos elástico y compartido
    # Caso de uso: Almacenamiento compartido entre múltiples EC2, aplicaciones web

    def crear_efs(
        self,
        fs_name,
        performance_mode="generalPurpose",
        throughput_mode="bursting",
        encrypted=False,
    ):
        """
        CREAR EFS (Elastic File System)

        Parámetros OBLIGATORIOS:
            - Ninguno (todos tienen valores por defecto)

        Parámetros OPCIONALES:
            - fs_name (str): Nombre del sistema de archivos
            - PerformanceMode (str): Tipo de rendimiento
                - 'generalPurpose': Latencia baja, propósito general (RECOMENDADO)
                - 'maxIO': Máximo rendimiento, mayor latencia
            - ThroughputMode (str): Modo de rendimiento
                - 'bursting': Rendimiento variable (por defecto, sin costo adicional)
                - 'provisioned': Rendimiento garantizado (costo adicional)
            - ProvisionedThroughputInMibps (int): Rendimiento si ThroughputMode=provisioned
            - Encrypted (bool): Encriptación en reposo (por defecto False)
            - KmsKeyId (str): Clave KMS para encriptación

        Almacena: Sistema de archivos NFS compartido entre múltiples EC2
        Ventaja: Sincronización automática, escalable, persistente
        """
        try:
            print(f"\n[EFS] Creando EFS: {fs_name}...")

            # Parámetros obligatorios
            params = {
                "PerformanceMode": performance_mode,  # OBLIGATORIO
                "ThroughputMode": throughput_mode,  # OBLIGATORIO
                "Encrypted": encrypted,  # OPCIONAL: Encriptación
            }

            response = self.efs_client.create_file_system(**params)
            fs_id = response["FileSystemId"]

            # Etiquetar el EFS
            self.efs_client.create_tags(
                FileSystemId=fs_id, Tags=[{"Key": "Name", "Value": fs_name}]
            )

            print(f"✓ EFS creado: {fs_id}")
            print(f"  Performance Mode: {performance_mode}")
            print(f"  Throughput Mode: {throughput_mode}")

            return fs_id

        except Exception as e:
            print(f"✗ Error al crear EFS: {str(e)}")
            return None

    def crear_mount_target(self, fs_id, subnet_id, security_group_ids=None):
        """
        CREAR MOUNT TARGET PARA EFS

        Parámetros OBLIGATORIOS:
            - fs_id (str): ID del sistema de archivos EFS
            - subnet_id (str): ID de la subred donde montar

        Parámetros OPCIONALES:
            - security_group_ids (list): IDs de grupos de seguridad

        NOTA: Necesitas una VPC y subred preexistente
        """
        try:
            print(f"\n[EFS] Creando Mount Target para EFS {fs_id}...")

            params = {
                "FileSystemId": fs_id,  # OBLIGATORIO
                "SubnetId": subnet_id,  # OBLIGATORIO
            }

            if security_group_ids:
                params["SecurityGroups"] = security_group_ids

            response = self.efs_client.create_mount_target(**params)
            mount_target_id = response["MountTargetId"]

            print(f"✓ Mount Target creado: {mount_target_id}")

            return mount_target_id

        except Exception as e:
            print(f"✗ Error al crear Mount Target: {str(e)}")
            return None

    def listar_efs(self):
        """
        Listar todos los EFS disponibles
        """
        try:
            print(f"\n[EFS] Listando sistemas de archivos...")
            response = self.efs_client.describe_file_systems()

            if not response["FileSystems"]:
                print("  No hay EFS disponibles")
                return []

            for fs in response["FileSystems"]:
                print(
                    f"  - {fs['FileSystemId']}: {fs['Name']} ({fs['LifeCycleState']})"
                )

            return response["FileSystems"]

        except Exception as e:
            print(f"✗ Error al listar EFS: {str(e)}")
            return []

# ==================== PROGRAMA Security_Group_SUBNET_KeyPair ====================

def main_security_group_subnet_keypairs():

    # Crear instancia
    manager = StorageManager(region="us-east-1")

    # ========== PASO 0: CREAR INFRAESTRUCTURA DE RED ==========
    print("\n\n>>> PASO 0: CREAR SECURITY GROUP <<<")
    vpc_id = manager.obtener_vpc_predeterminada()

    sg_id = manager.crear_security_group(
        sg_name="almacenamiento-aws",
        sg_description="Security Group para EC2, EBS y EFS",
        vpc_id=vpc_id,
    )

    if sg_id:
        # Agregar reglas de acceso
        print("\n[SG] Agregando reglas de seguridad...")
        manager.agregar_regla_ingress_sg(sg_id, "tcp", 22, 22, "0.0.0.0/0")  # SSH
        manager.agregar_regla_ingress_sg(sg_id, "tcp", 80, 80, "0.0.0.0/0")  # HTTP
        manager.agregar_regla_ingress_sg(sg_id, "tcp", 443, 443, "0.0.0.0/0")  # HTTPS
        manager.agregar_regla_ingress_sg(
            sg_id, "-1", -1, -1, "0.0.0.0/0"
        )  # Todos (para NFS/EFS)
    else:
        print("✗ No se pudo crear el security group")
        return

    # Obtener subred (YA EXISTE, no se crea)
    print("\n\n>>> PASO 0B: OBTENER SUBRED <<<")
    subnet_id, availability_zone = manager.obtener_subnet_predeterminada(vpc_id)

    if not subnet_id:
        print("✗ No se encontró subred disponible")
        return

    # ========== PASO 0C: CREAR/VERIFICAR KEY PAIR ==========
    print("\n\n>>> PASO 0C: CREAR/VERIFICAR KEY PAIR <<<")
    key_name = manager.crear_key_pair("clave_casa")

    if not key_name:
        print("✗ No se pudo crear/verificar la key pair")
        return

    # Guardar en archivo de configuración
    ConfigManager.actualizar("sg_id", sg_id)
    ConfigManager.actualizar("subnet_id", subnet_id)
    ConfigManager.actualizar("key_pairs_name", key_name)
    ConfigManager.actualizar("availability_zone", availability_zone)
    
    print("\n✓ Infraestructura guardada en aws_config.json")

# ==================== PROGRAMA EC2_EFS_EBS ====================

def main_ec2_efs_ebs():
    
    print("=" * 80)
    print("GESTOR DE ALMACENAMIENTO AWS (EC2, EBS, EFS)")
    print("=" * 80)

    # Crear instancia
    manager = StorageManager(region="us-east-1")

    # Cargar configuración guardada
    key_name = ConfigManager.obtener("key_pairs_name")
    sg_id = ConfigManager.obtener("sg_id")
    subnet_id = ConfigManager.obtener("subnet_id")
    availability_zone = ConfigManager.obtener("availability_zone")
    
    if not all([key_name, sg_id, subnet_id]):
        print("✗ Error: Debes ejecutar MAIN 1 primero para crear la infraestructura")
        return
    
    print(f"\n[CONFIG] Usando datos guardados:")
    print(f"  SG: {sg_id}")
    print(f"  Subnet: {subnet_id}")
    print(f"  Key: {key_name}")

    # # ========== PASO 1: CREAR Y GESTIONAR EC2 ==========
    print("\n\n>>> PASO 1: CREAR INSTANCIA EC2 <<<")

    # Generar script para montar el EBS automáticamente
    user_data = manager.generar_user_data_montaje_ebs(
        device="/dev/sdf", mount_point="/mnt/datos"
    )

    instance_id = manager.crear_ec2(
        instance_name="mi-servidor-web",
        ami_id="ami-0ecb62995f68bb549",
        instance_type="t2.micro",
        subnet_id=ConfigManager.obtener("subnet_id"),
        key_name=key_name,
        security_group_name=sg_id,
        user_data=user_data,
    )

    if not instance_id:
        print("✗ Error: No se pudo crear la instancia EC2")
        return

    if instance_id:
        manager.ec2_client.get_waiter("instance_running").wait(
            InstanceIds=[instance_id]
        )

    if instance_id:
        # Esperar a que la instancia esté disponible
        time.sleep(5)

        print("\n>>> PASO 2: VERIFICAR ESTADO DE EC2 <<<")
        manager.obtener_estado_ec2(instance_id)

        print("\n>>> PASO 3: PARAR EC2 <<<")
        manager.parar_ec2(instance_id)

        time.sleep(3)

        print("\n>>> PASO 4: EJECUTAR EC2 <<<")
        manager.ejecutar_ec2(instance_id)

        time.sleep(3)

    ConfigManager.actualizar("instance_id", instance_id)

    # ========== PASO 5: CREAR Y ASOCIAR EBS ==========
    print("\n\n>>> PASO 5: CREAR VOLUMEN EBS <<<")

    volume_id = manager.crear_ebs(
        volume_name="mi-volumen-datos",
        size=20,
        volume_type="gp3",
        availability_zone=availability_zone,
    )

    if volume_id:
        time.sleep(3)

        print("\n>>> PASO 6: ASOCIAR EBS A EC2 <<<")
        manager.asociar_ebs_a_ec2(volume_id, instance_id, device="/dev/sdf")

        print("\n>>> PASO 7: AGREGAR ARCHIVO A EBS <<<")

    ConfigManager.actualizar("volume_id", volume_id)

    # ========== PASO 8: CREAR EFS ==========
    print("\n\n>>> PASO 8: CREAR EFS (SISTEMA DE ARCHIVOS COMPARTIDO) <<<")
    efs_id = manager.crear_efs(
        fs_name="mi-efs-compartido",
        performance_mode="generalPurpose",
        throughput_mode="bursting",
        encrypted=False,
    )

    if not efs_id:
        print("✗ Error: No se pudo crear EFS")
        return

    ConfigManager.actualizar("efs_id", efs_id)

    while True:
        estado = manager.efs_client.describe_file_systems(FileSystemId=efs_id)[
            "FileSystems"
        ][0]["LifeCycleState"]
        if estado == "available":
            break
        print(f"EFS aún en estado {estado}, esperando...")
        time.sleep(3)

    if efs_id:
        time.sleep(2)

        # ========== PASO 9: CREAR MOUNT TARGET PARA EFS ==========
        print("\n\n>>> PASO 9: CREAR MOUNT TARGET PARA EFS <<<")

        if subnet_id:
            mount_target_id = manager.crear_mount_target(
                fs_id=efs_id,
                subnet_id=subnet_id,
                security_group_ids=[sg_id],
            )
        else:
            print("No se pudo obtener el subnet_id, no se creará el Mount Target.")
            mount_target_id = None

        if mount_target_id:
            ConfigManager.actualizar("mount_target_id", mount_target_id)
            time.sleep(2)

            # ========== PASO 10: LISTAR EFS DISPONIBLES ===
            print("\n\n>>> PASO 10: LISTAR EFS DISPONIBLES <<<")
            manager.listar_efs()

    print("\n✓ EC2, EBS y EFS guardados en aws_config.json")

# ==================== PROGRAMA S3_STANDARD ====================

def main_s3_STANDARD():
    """
    MAIN 3: S3 - Crear bucket, carpetas y archivos CSV
    
    Pasos:
    1. Crear bucket S3 estándar
    2. Crear carpetas dentro del bucket
    3. Crear archivos CSV con datos
    4. Listar objetos
    5. Descargar/Obtener objetos
    """
    
    print("=" * 80)
    print("PARTE 3: S3 (SIMPLE STORAGE SERVICE)")
    print("=" * 80)
    
    # Crear instancia de manager
    manager = StorageManager(region="us-east-1")
    
    # PASO 1: Crear bucket S3
    print("\n\n>>> PASO 1: CREAR BUCKET S3 <<<")
    bucket_name = "mi-bucket-datos-" + str(int(time.time()))  # Nombre único
    
    bucket_creado = manager.crear_bucket_s3(
        bucket_name=bucket_name,
        acl="private",
        encryption=False  # OPCIONAL: Encriptación
    )
    
    if not bucket_creado:
        print("✗ Error: No se pudo crear el bucket")
        return
    
    ConfigManager.actualizar("s3_bucket", bucket_name)
    
    # PASO 2: Crear carpetas en S3
    print("\n\n>>> PASO 2: CREAR CARPETAS EN S3 <<<")
    
    carpetas = ["ventas", "clientes", "productos", "reportes"]
    
    for carpeta in carpetas:
        manager.crear_carpeta_s3(bucket_name, carpeta)
    
    # PASO 3: Crear archivos CSV y subirlos
    print("\n\n>>> PASO 3: CREAR Y SUBIR ARCHIVOS CSV <<<")
    
    # CSV 1: Datos de ventas
    print("\n[CSV] Creando CSV de VENTAS...")
    csv_ventas = """id,fecha,producto,cantidad,precio,total
1,2024-01-01,Laptop,5,1200.00,6000.00
2,2024-01-02,Mouse,50,25.00,1250.00
3,2024-01-03,Teclado,30,75.00,2250.00
4,2024-01-04,Monitor,10,300.00,3000.00
5,2024-01-05,Auriculares,25,80.00,2000.00
6,2024-01-06,Webcam,15,120.00,1800.00
7,2024-01-07,SSD,8,450.00,3600.00
8,2024-01-08,RAM,20,100.00,2000.00
9,2024-01-09,Procesador,5,550.00,2750.00
10,2024-01-10,Fuente,12,200.00,2400.00"""
    
    manager.subir_contenido_s3(
        bucket_name=bucket_name,
        contenido=csv_ventas,
        s3_key="ventas/ventas_enero_2024.csv",  # Ruta con carpeta
        content_type="text/csv"
    )
    
    # CSV 2: Datos de clientes
    print("\n[CSV] Creando CSV de CLIENTES...")
    csv_clientes = """id,nombre,email,telefono,ciudad,activo
101,Juan García,juan@example.com,555-0001,Madrid,true
102,María López,maria@example.com,555-0002,Barcelona,true
103,Carlos Rodríguez,carlos@example.com,555-0003,Valencia,false
104,Ana Martínez,ana@example.com,555-0004,Sevilla,true
105,Luis Fernández,luis@example.com,555-0005,Bilbao,true
106,Elena Jiménez,elena@example.com,555-0006,Malaga,true
107,David Pérez,david@example.com,555-0007,Murcia,false
108,Sofia Gómez,sofia@example.com,555-0008,Palma,true
109,Miguel Sánchez,miguel@example.com,555-0009,Las Palmas,true
110,Isabel Ruiz,isabel@example.com,555-0010,Alicante,false"""
    
    manager.subir_contenido_s3(
        bucket_name=bucket_name,
        contenido=csv_clientes,
        s3_key="clientes/clientes_activos.csv",
        content_type="text/csv"
    )
    
    # CSV 3: Datos de productos
    print("\n[CSV] Creando CSV de PRODUCTOS...")
    csv_productos = """id,nombre,categoria,precio,stock,proveedor
1001,Laptop Dell XPS,Computadoras,1200.00,15,Dell Inc
1002,Mouse Logitech,Periféricos,25.00,100,Logitech
1003,Teclado Mecánico,Periféricos,75.00,45,Keychron
1004,Monitor LG 27,Pantallas,300.00,8,LG
1005,Auriculares Sony,Audio,80.00,60,Sony
1006,Webcam HD,Accesorios,120.00,25,Logitech
1007,SSD Samsung 1TB,Almacenamiento,450.00,20,Samsung
1008,RAM DDR4 16GB,Componentes,100.00,50,Corsair
1009,Procesador Intel,Componentes,550.00,12,Intel
1010,Fuente 750W,Componentes,200.00,18,EVGA"""
    
    manager.subir_contenido_s3(
        bucket_name=bucket_name,
        contenido=csv_productos,
        s3_key="productos/inventario.csv",
        content_type="text/csv"
    )
    
    # CSV 4: Reportes
    print("\n[CSV] Creando CSV de REPORTES...")
    csv_reportes = """mes,ingresos,gastos,ganancia,margen
Enero,15100.00,8500.00,6600.00,0.437
Febrero,18200.00,9100.00,9100.00,0.500
Marzo,21500.00,10200.00,11300.00,0.525
Abril,19800.00,9800.00,10000.00,0.505
Mayo,23100.00,11000.00,12100.00,0.524
Junio,25600.00,12000.00,13600.00,0.531"""
    
    manager.subir_contenido_s3(
        bucket_name=bucket_name,
        contenido=csv_reportes,
        s3_key="reportes/resumen_financiero.csv",
        content_type="text/csv"
    )
    
    # PASO 4: Listar objetos en el bucket
    print("\n\n>>> PASO 4: LISTAR TODOS LOS OBJETOS <<<")
    todos_los_objetos = manager.listar_objetos_s3(bucket_name)
    
    # PASO 5: Listar objetos por carpeta
    print("\n\n>>> PASO 5: LISTAR OBJETOS POR CARPETA <<<")
    
    print("\n[S3] Objetos en carpeta 'ventas':")
    manager.listar_objetos_s3(bucket_name, prefix="ventas/")
    
    print("\n[S3] Objetos en carpeta 'clientes':")
    manager.listar_objetos_s3(bucket_name, prefix="clientes/")
    
    # PASO 6: Obtener contenido de un objeto (sin descargar)
    print("\n\n>>> PASO 6: OBTENER CONTENIDO DE OBJETO (EN MEMORIA) <<<")
    
    print("\n[S3] Obteniendo contenido de 'ventas/ventas_enero_2024.csv'...")
    contenido_ventas = manager.obtener_contenido_s3_como_texto(
        bucket_name=bucket_name,
        s3_key="ventas/ventas_enero_2024.csv"
    )
    
    if contenido_ventas:
        print(f"\n[CONTENIDO] Primeras líneas del archivo:")
        lineas = contenido_ventas.split("\n")[:5]
        for linea in lineas:
            print(f"  {linea}")
        print(f"  ... ({len(contenido_ventas.split(chr(10)))} filas totales)")
    
    # PASO 7: Descargar objeto a archivo local
    print("\n\n>>> PASO 7: DESCARGAR OBJETO A ARCHIVO LOCAL <<<")
    
    archivo_descargado = manager.descargar_objeto_s3(
        bucket_name=bucket_name,
        s3_key="clientes/clientes_activos.csv",
        file_path="clientes_descargados.csv"
    )
    
    # PASO 8: Obtener información de objetos específicos
    print("\n\n>>> PASO 8: OBTENER INFORMACIÓN DE OBJETOS <<<")
    
    objetos_info = {
        "ventas/ventas_enero_2024.csv": "Datos de ventas de enero",
        "clientes/clientes_activos.csv": "Lista de clientes activos",
        "productos/inventario.csv": "Inventario de productos",
        "reportes/resumen_financiero.csv": "Resumen financiero del semestre"
    }
    
    for obj_key, descripcion in objetos_info.items():
        try:
            metadata = manager.s3_client.head_object(
                Bucket=bucket_name,
                Key=obj_key
            )
            tamaño = metadata["ContentLength"]
            print(f"\n[OBJETO] {obj_key}")
            print(f"  Descripción: {descripcion}")
            print(f"  Tamaño: {tamaño} bytes")
            print(f"  Última modificación: {metadata['LastModified']}")
        except Exception as e:
            print(f"Error: {str(e)}")
    
    # Guardar info del bucket en archivo de configuración
    ConfigManager.actualizar("s3_bucket", bucket_name)
    
    print("\n" + "=" * 80)
    print("✓ S3 completado exitosamente")
    print("=" * 80)
    print(f"\nInformación del bucket:")
    print(f"  Nombre: {bucket_name}")
    print(f"  Región: us-east-1")
    print(f"  Objetos creados: {len(todos_los_objetos)}")
    
# ==================== PROGRAMA S3_STANDARD_IA ====================

def main_s3_STANDARD_IA():
    """
    MAIN 3: S3 - Crear bucket, carpetas y archivos CSV
    
    Pasos:
    1. Crear bucket S3 estándar
    2. Crear carpetas dentro del bucket
    3. Crear archivos CSV con datos
    4. Listar objetos
    5. Descargar/Obtener objetos
    """
    
    print("=" * 80)
    print("PARTE 3: S3 (SIMPLE STORAGE SERVICE)")
    print("=" * 80)
    
    # Crear instancia de manager
    manager = StorageManager(region="us-east-1")
    
    # PASO 1: Crear bucket S3
    print("\n\n>>> PASO 1: CREAR BUCKET S3 <<<")
    bucket_name = "mi-bucket-datos-standard-ia" + str(int(time.time()))  # Nombre único
    
    bucket_creado = manager.crear_bucket_s3(
        bucket_name=bucket_name,
        acl="private",
        encryption=False  # OPCIONAL: Encriptación
    )
    
    if not bucket_creado:
        print("✗ Error: No se pudo crear el bucket")
        return
    
    ConfigManager.actualizar("s3_bucket", bucket_name)
    
    # PASO 2: Crear carpetas en S3
    print("\n\n>>> PASO 2: CREAR CARPETAS EN S3 <<<")
    
    carpetas = ["ventas", "clientes", "productos", "reportes"]
    
    for carpeta in carpetas:
        manager.crear_carpeta_s3(bucket_name, carpeta)
    
    # PASO 3: Crear archivos CSV y subirlos
    print("\n\n>>> PASO 3: CREAR Y SUBIR ARCHIVOS CSV <<<")
    
    # CSV 1: Datos de ventas
    print("\n[CSV] Creando CSV de VENTAS...")
    csv_ventas = """id,fecha,producto,cantidad,precio,total
1,2024-01-01,Laptop,5,1200.00,6000.00
2,2024-01-02,Mouse,50,25.00,1250.00
3,2024-01-03,Teclado,30,75.00,2250.00
4,2024-01-04,Monitor,10,300.00,3000.00
5,2024-01-05,Auriculares,25,80.00,2000.00
6,2024-01-06,Webcam,15,120.00,1800.00
7,2024-01-07,SSD,8,450.00,3600.00
8,2024-01-08,RAM,20,100.00,2000.00
9,2024-01-09,Procesador,5,550.00,2750.00
10,2024-01-10,Fuente,12,200.00,2400.00"""
    
    manager.subir_contenido_s3_con_storage_class(
        bucket_name=bucket_name,
        contenido=csv_ventas,
        s3_key="ventas/ventas_enero_2024.csv",  # Ruta con carpeta
        content_type="text/csv",
        storage_class="STANDARD_IA"
    )
    
    # CSV 2: Datos de clientes
    print("\n[CSV] Creando CSV de CLIENTES...")
    csv_clientes = """id,nombre,email,telefono,ciudad,activo
101,Juan García,juan@example.com,555-0001,Madrid,true
102,María López,maria@example.com,555-0002,Barcelona,true
103,Carlos Rodríguez,carlos@example.com,555-0003,Valencia,false
104,Ana Martínez,ana@example.com,555-0004,Sevilla,true
105,Luis Fernández,luis@example.com,555-0005,Bilbao,true
106,Elena Jiménez,elena@example.com,555-0006,Malaga,true
107,David Pérez,david@example.com,555-0007,Murcia,false
108,Sofia Gómez,sofia@example.com,555-0008,Palma,true
109,Miguel Sánchez,miguel@example.com,555-0009,Las Palmas,true
110,Isabel Ruiz,isabel@example.com,555-0010,Alicante,false"""
    
    manager.subir_contenido_s3_con_storage_class(
        bucket_name=bucket_name,
        contenido=csv_clientes,
        s3_key="clientes/clientes_activos.csv",
        content_type="text/csv",
        storage_class="STANDARD_IA"
    )
    
    # CSV 3: Datos de productos
    print("\n[CSV] Creando CSV de PRODUCTOS...")
    csv_productos = """id,nombre,categoria,precio,stock,proveedor
1001,Laptop Dell XPS,Computadoras,1200.00,15,Dell Inc
1002,Mouse Logitech,Periféricos,25.00,100,Logitech
1003,Teclado Mecánico,Periféricos,75.00,45,Keychron
1004,Monitor LG 27,Pantallas,300.00,8,LG
1005,Auriculares Sony,Audio,80.00,60,Sony
1006,Webcam HD,Accesorios,120.00,25,Logitech
1007,SSD Samsung 1TB,Almacenamiento,450.00,20,Samsung
1008,RAM DDR4 16GB,Componentes,100.00,50,Corsair
1009,Procesador Intel,Componentes,550.00,12,Intel
1010,Fuente 750W,Componentes,200.00,18,EVGA"""
    
    manager.subir_contenido_s3_con_storage_class(
        bucket_name=bucket_name,
        contenido=csv_productos,
        s3_key="productos/inventario.csv",
        content_type="text/csv",
        storage_class="STANDARD_IA"
    )
    
    # CSV 4: Reportes
    print("\n[CSV] Creando CSV de REPORTES...")
    csv_reportes = """mes,ingresos,gastos,ganancia,margen
Enero,15100.00,8500.00,6600.00,0.437
Febrero,18200.00,9100.00,9100.00,0.500
Marzo,21500.00,10200.00,11300.00,0.525
Abril,19800.00,9800.00,10000.00,0.505
Mayo,23100.00,11000.00,12100.00,0.524
Junio,25600.00,12000.00,13600.00,0.531"""
    
    manager.subir_contenido_s3_con_storage_class(
        bucket_name=bucket_name,
        contenido=csv_reportes,
        s3_key="reportes/resumen_financiero.csv",
        content_type="text/csv",
        storage_class="STANDARD_IA"
    )
    
    # PASO 4: Listar objetos en el bucket
    print("\n\n>>> PASO 4: LISTAR TODOS LOS OBJETOS <<<")
    todos_los_objetos = manager.listar_objetos_s3(bucket_name)
    
    # PASO 5: Listar objetos por carpeta
    print("\n\n>>> PASO 5: LISTAR OBJETOS POR CARPETA <<<")
    
    print("\n[S3] Objetos en carpeta 'ventas':")
    manager.listar_objetos_s3(bucket_name, prefix="ventas/")
    
    print("\n[S3] Objetos en carpeta 'clientes':")
    manager.listar_objetos_s3(bucket_name, prefix="clientes/")
    
    # PASO 6: Obtener contenido de un objeto (sin descargar)
    print("\n\n>>> PASO 6: OBTENER CONTENIDO DE OBJETO (EN MEMORIA) <<<")
    
    print("\n[S3] Obteniendo contenido de 'ventas/ventas_enero_2024.csv'...")
    contenido_ventas = manager.obtener_contenido_s3_como_texto(
        bucket_name=bucket_name,
        s3_key="ventas/ventas_enero_2024.csv"
    )
    
    if contenido_ventas:
        print(f"\n[CONTENIDO] Primeras líneas del archivo:")
        lineas = contenido_ventas.split("\n")[:5]
        for linea in lineas:
            print(f"  {linea}")
        print(f"  ... ({len(contenido_ventas.split(chr(10)))} filas totales)")
    
    # PASO 7: Descargar objeto a archivo local
    print("\n\n>>> PASO 7: DESCARGAR OBJETO A ARCHIVO LOCAL <<<")
    
    archivo_descargado = manager.descargar_objeto_s3(
        bucket_name=bucket_name,
        s3_key="clientes/clientes_activos.csv",
        file_path="clientes_descargados.csv"
    )
    
    # PASO 8: Obtener información de objetos específicos
    print("\n\n>>> PASO 8: OBTENER INFORMACIÓN DE OBJETOS <<<")
    
    objetos_info = {
        "ventas/ventas_enero_2024.csv": "Datos de ventas de enero",
        "clientes/clientes_activos.csv": "Lista de clientes activos",
        "productos/inventario.csv": "Inventario de productos",
        "reportes/resumen_financiero.csv": "Resumen financiero del semestre"
    }
    
    for obj_key, descripcion in objetos_info.items():
        try:
            metadata = manager.s3_client.head_object(
                Bucket=bucket_name,
                Key=obj_key
            )
            tamaño = metadata["ContentLength"]
            print(f"\n[OBJETO] {obj_key}")
            print(f"  Descripción: {descripcion}")
            print(f"  Tamaño: {tamaño} bytes")
            print(f"  Última modificación: {metadata['LastModified']}")
        except Exception as e:
            print(f"Error: {str(e)}")
    
    # Guardar info del bucket en archivo de configuración
    ConfigManager.actualizar("s3_bucket", bucket_name)
    
    print("\n" + "=" * 80)
    print("✓ S3 completado exitosamente")
    print("=" * 80)
    print(f"\nInformación del bucket:")
    print(f"  Nombre: {bucket_name}")
    print(f"  Región: us-east-1")
    print(f"  Objetos creados: {len(todos_los_objetos)}")

# ==================== PROGRAMA S3_INTELLIGENT_TIERING ====================    

def main_s3_INTELLIGENT_TIERING():
    """
    MAIN 3: S3 - Crear bucket, carpetas y archivos CSV
    
    Pasos:
    1. Crear bucket S3 estándar
    2. Crear carpetas dentro del bucket
    3. Crear archivos CSV con datos
    4. Listar objetos
    5. Descargar/Obtener objetos
    """
    
    print("=" * 80)
    print("PARTE 3: S3 (SIMPLE STORAGE SERVICE)")
    print("=" * 80)
    
    # Crear instancia de manager
    manager = StorageManager(region="us-east-1")
    
    # PASO 1: Crear bucket S3
    print("\n\n>>> PASO 1: CREAR BUCKET S3 <<<")
    bucket_name = "mi-bucket-datos-intelligent-tiering" + str(int(time.time()))  # Nombre único
    
    bucket_creado = manager.crear_bucket_s3(
        bucket_name=bucket_name,
        acl="private",
        encryption=False  # OPCIONAL: Encriptación
    )
    
    if not bucket_creado:
        print("✗ Error: No se pudo crear el bucket")
        return
    
    ConfigManager.actualizar("s3_bucket", bucket_name)
    
    # PASO 2: Crear carpetas en S3
    print("\n\n>>> PASO 2: CREAR CARPETAS EN S3 <<<")
    
    carpetas = ["ventas", "clientes", "productos", "reportes"]
    
    for carpeta in carpetas:
        manager.crear_carpeta_s3(bucket_name, carpeta)
    
    # PASO 3: Crear archivos CSV y subirlos
    print("\n\n>>> PASO 3: CREAR Y SUBIR ARCHIVOS CSV <<<")
    
    # CSV 1: Datos de ventas
    print("\n[CSV] Creando CSV de VENTAS...")
    csv_ventas = """id,fecha,producto,cantidad,precio,total
1,2024-01-01,Laptop,5,1200.00,6000.00
2,2024-01-02,Mouse,50,25.00,1250.00
3,2024-01-03,Teclado,30,75.00,2250.00
4,2024-01-04,Monitor,10,300.00,3000.00
5,2024-01-05,Auriculares,25,80.00,2000.00
6,2024-01-06,Webcam,15,120.00,1800.00
7,2024-01-07,SSD,8,450.00,3600.00
8,2024-01-08,RAM,20,100.00,2000.00
9,2024-01-09,Procesador,5,550.00,2750.00
10,2024-01-10,Fuente,12,200.00,2400.00"""
    
    manager.subir_contenido_s3_con_storage_class(
        bucket_name=bucket_name,
        contenido=csv_ventas,
        s3_key="ventas/ventas_enero_2024.csv",  # Ruta con carpeta
        content_type="text/csv",
        storage_class="INTELLIGENT_TIERING"
    )
    
    # CSV 2: Datos de clientes
    print("\n[CSV] Creando CSV de CLIENTES...")
    csv_clientes = """id,nombre,email,telefono,ciudad,activo
101,Juan García,juan@example.com,555-0001,Madrid,true
102,María López,maria@example.com,555-0002,Barcelona,true
103,Carlos Rodríguez,carlos@example.com,555-0003,Valencia,false
104,Ana Martínez,ana@example.com,555-0004,Sevilla,true
105,Luis Fernández,luis@example.com,555-0005,Bilbao,true
106,Elena Jiménez,elena@example.com,555-0006,Malaga,true
107,David Pérez,david@example.com,555-0007,Murcia,false
108,Sofia Gómez,sofia@example.com,555-0008,Palma,true
109,Miguel Sánchez,miguel@example.com,555-0009,Las Palmas,true
110,Isabel Ruiz,isabel@example.com,555-0010,Alicante,false"""
    
    manager.subir_contenido_s3_con_storage_class(
        bucket_name=bucket_name,
        contenido=csv_clientes,
        s3_key="clientes/clientes_activos.csv",
        content_type="text/csv",
        storage_class="INTELLIGENT_TIERING"
    )
    
    # CSV 3: Datos de productos
    print("\n[CSV] Creando CSV de PRODUCTOS...")
    csv_productos = """id,nombre,categoria,precio,stock,proveedor
1001,Laptop Dell XPS,Computadoras,1200.00,15,Dell Inc
1002,Mouse Logitech,Periféricos,25.00,100,Logitech
1003,Teclado Mecánico,Periféricos,75.00,45,Keychron
1004,Monitor LG 27,Pantallas,300.00,8,LG
1005,Auriculares Sony,Audio,80.00,60,Sony
1006,Webcam HD,Accesorios,120.00,25,Logitech
1007,SSD Samsung 1TB,Almacenamiento,450.00,20,Samsung
1008,RAM DDR4 16GB,Componentes,100.00,50,Corsair
1009,Procesador Intel,Componentes,550.00,12,Intel
1010,Fuente 750W,Componentes,200.00,18,EVGA"""
    
    manager.subir_contenido_s3_con_storage_class(
        bucket_name=bucket_name,
        contenido=csv_productos,
        s3_key="productos/inventario.csv",
        content_type="text/csv",
        storage_class="INTELLIGENT_TIERING"
    )
    
    # CSV 4: Reportes
    print("\n[CSV] Creando CSV de REPORTES...")
    csv_reportes = """mes,ingresos,gastos,ganancia,margen
Enero,15100.00,8500.00,6600.00,0.437
Febrero,18200.00,9100.00,9100.00,0.500
Marzo,21500.00,10200.00,11300.00,0.525
Abril,19800.00,9800.00,10000.00,0.505
Mayo,23100.00,11000.00,12100.00,0.524
Junio,25600.00,12000.00,13600.00,0.531"""
    
    manager.subir_contenido_s3_con_storage_class(
        bucket_name=bucket_name,
        contenido=csv_reportes,
        s3_key="reportes/resumen_financiero.csv",
        content_type="text/csv",
        storage_class="INTELLIGENT_TIERING"
    )
    
    # PASO 4: Listar objetos en el bucket
    print("\n\n>>> PASO 4: LISTAR TODOS LOS OBJETOS <<<")
    todos_los_objetos = manager.listar_objetos_s3(bucket_name)
    
    # PASO 5: Listar objetos por carpeta
    print("\n\n>>> PASO 5: LISTAR OBJETOS POR CARPETA <<<")
    
    print("\n[S3] Objetos en carpeta 'ventas':")
    manager.listar_objetos_s3(bucket_name, prefix="ventas/")
    
    print("\n[S3] Objetos en carpeta 'clientes':")
    manager.listar_objetos_s3(bucket_name, prefix="clientes/")
    
    # PASO 6: Obtener contenido de un objeto (sin descargar)
    print("\n\n>>> PASO 6: OBTENER CONTENIDO DE OBJETO (EN MEMORIA) <<<")
    
    print("\n[S3] Obteniendo contenido de 'ventas/ventas_enero_2024.csv'...")
    contenido_ventas = manager.obtener_contenido_s3_como_texto(
        bucket_name=bucket_name,
        s3_key="ventas/ventas_enero_2024.csv"
    )
    
    if contenido_ventas:
        print(f"\n[CONTENIDO] Primeras líneas del archivo:")
        lineas = contenido_ventas.split("\n")[:5]
        for linea in lineas:
            print(f"  {linea}")
        print(f"  ... ({len(contenido_ventas.split(chr(10)))} filas totales)")
    
    # PASO 7: Descargar objeto a archivo local
    print("\n\n>>> PASO 7: DESCARGAR OBJETO A ARCHIVO LOCAL <<<")
    
    archivo_descargado = manager.descargar_objeto_s3(
        bucket_name=bucket_name,
        s3_key="clientes/clientes_activos.csv",
        file_path="clientes_descargados.csv"
    )
    
    # PASO 8: Obtener información de objetos específicos
    print("\n\n>>> PASO 8: OBTENER INFORMACIÓN DE OBJETOS <<<")
    
    objetos_info = {
        "ventas/ventas_enero_2024.csv": "Datos de ventas de enero",
        "clientes/clientes_activos.csv": "Lista de clientes activos",
        "productos/inventario.csv": "Inventario de productos",
        "reportes/resumen_financiero.csv": "Resumen financiero del semestre"
    }
    
    for obj_key, descripcion in objetos_info.items():
        try:
            metadata = manager.s3_client.head_object(
                Bucket=bucket_name,
                Key=obj_key
            )
            tamaño = metadata["ContentLength"]
            print(f"\n[OBJETO] {obj_key}")
            print(f"  Descripción: {descripcion}")
            print(f"  Tamaño: {tamaño} bytes")
            print(f"  Última modificación: {metadata['LastModified']}")
        except Exception as e:
            print(f"Error: {str(e)}")
    
    # Guardar info del bucket en archivo de configuración
    ConfigManager.actualizar("s3_bucket", bucket_name)
    
    print("\n" + "=" * 80)
    print("✓ S3 completado exitosamente")
    print("=" * 80)
    print(f"\nInformación del bucket:")
    print(f"  Nombre: {bucket_name}")
    print(f"  Región: us-east-1")
    print(f"  Objetos creados: {len(todos_los_objetos)}")

# ==================== PROGRAMA S3_GLACIER ====================    

def main_s3_GLACIER():
    """
    MAIN 3: S3 - Crear bucket, carpetas y archivos CSV
    
    Pasos:
    1. Crear bucket S3
    2. Crear carpetas dentro del bucket
    3. Crear archivos CSV con datos
    4. Listar objetos
    5. Descargar/Obtener objetos
    """
    
    print("=" * 80)
    print("PARTE 3: S3 (SIMPLE STORAGE SERVICE)")
    print("=" * 80)
    
    # Crear instancia de manager
    manager = StorageManager(region="us-east-1")
    
    # PASO 1: Crear bucket S3
    print("\n\n>>> PASO 1: CREAR BUCKET S3 <<<")
    bucket_name = "mi-bucket-datos-glacier" + str(int(time.time()))  # Nombre único
    
    bucket_creado = manager.crear_bucket_s3(
        bucket_name=bucket_name,
        acl="private",
        encryption=False  # OPCIONAL: Encriptación
    )
    
    if not bucket_creado:
        print("✗ Error: No se pudo crear el bucket")
        return
    
    ConfigManager.actualizar("s3_bucket", bucket_name)
    
    # PASO 2: Crear carpetas en S3
    print("\n\n>>> PASO 2: CREAR CARPETAS EN S3 <<<")
    
    carpetas = ["ventas", "clientes", "productos", "reportes"]
    
    for carpeta in carpetas:
        manager.crear_carpeta_s3(bucket_name, carpeta)
    
    # PASO 3: Crear archivos CSV y subirlos
    print("\n\n>>> PASO 3: CREAR Y SUBIR ARCHIVOS CSV <<<")
    
    # CSV 1: Datos de ventas
    print("\n[CSV] Creando CSV de VENTAS...")
    csv_ventas = """id,fecha,producto,cantidad,precio,total
1,2024-01-01,Laptop,5,1200.00,6000.00
2,2024-01-02,Mouse,50,25.00,1250.00
3,2024-01-03,Teclado,30,75.00,2250.00
4,2024-01-04,Monitor,10,300.00,3000.00
5,2024-01-05,Auriculares,25,80.00,2000.00
6,2024-01-06,Webcam,15,120.00,1800.00
7,2024-01-07,SSD,8,450.00,3600.00
8,2024-01-08,RAM,20,100.00,2000.00
9,2024-01-09,Procesador,5,550.00,2750.00
10,2024-01-10,Fuente,12,200.00,2400.00"""
    
    manager.subir_contenido_s3_con_storage_class(
        bucket_name=bucket_name,
        contenido=csv_ventas,
        s3_key="ventas/ventas_enero_2024.csv",  # Ruta con carpeta
        content_type="text/csv",
        storage_class="GLACIER"
    )
    
    # CSV 2: Datos de clientes
    print("\n[CSV] Creando CSV de CLIENTES...")
    csv_clientes = """id,nombre,email,telefono,ciudad,activo
101,Juan García,juan@example.com,555-0001,Madrid,true
102,María López,maria@example.com,555-0002,Barcelona,true
103,Carlos Rodríguez,carlos@example.com,555-0003,Valencia,false
104,Ana Martínez,ana@example.com,555-0004,Sevilla,true
105,Luis Fernández,luis@example.com,555-0005,Bilbao,true
106,Elena Jiménez,elena@example.com,555-0006,Malaga,true
107,David Pérez,david@example.com,555-0007,Murcia,false
108,Sofia Gómez,sofia@example.com,555-0008,Palma,true
109,Miguel Sánchez,miguel@example.com,555-0009,Las Palmas,true
110,Isabel Ruiz,isabel@example.com,555-0010,Alicante,false"""
    
    manager.subir_contenido_s3_con_storage_class(
        bucket_name=bucket_name,
        contenido=csv_clientes,
        s3_key="clientes/clientes_activos.csv",
        content_type="text/csv",
        storage_class="GLACIER"
    )
    
    # CSV 3: Datos de productos
    print("\n[CSV] Creando CSV de PRODUCTOS...")
    csv_productos = """id,nombre,categoria,precio,stock,proveedor
1001,Laptop Dell XPS,Computadoras,1200.00,15,Dell Inc
1002,Mouse Logitech,Periféricos,25.00,100,Logitech
1003,Teclado Mecánico,Periféricos,75.00,45,Keychron
1004,Monitor LG 27,Pantallas,300.00,8,LG
1005,Auriculares Sony,Audio,80.00,60,Sony
1006,Webcam HD,Accesorios,120.00,25,Logitech
1007,SSD Samsung 1TB,Almacenamiento,450.00,20,Samsung
1008,RAM DDR4 16GB,Componentes,100.00,50,Corsair
1009,Procesador Intel,Componentes,550.00,12,Intel
1010,Fuente 750W,Componentes,200.00,18,EVGA"""
    
    manager.subir_contenido_s3_con_storage_class(
        bucket_name=bucket_name,
        contenido=csv_productos,
        s3_key="productos/inventario.csv",
        content_type="text/csv",
        storage_class="GLACIER"
    )
    
    # CSV 4: Reportes
    print("\n[CSV] Creando CSV de REPORTES...")
    csv_reportes = """mes,ingresos,gastos,ganancia,margen
Enero,15100.00,8500.00,6600.00,0.437
Febrero,18200.00,9100.00,9100.00,0.500
Marzo,21500.00,10200.00,11300.00,0.525
Abril,19800.00,9800.00,10000.00,0.505
Mayo,23100.00,11000.00,12100.00,0.524
Junio,25600.00,12000.00,13600.00,0.531"""
    
    manager.subir_contenido_s3_con_storage_class(
        bucket_name=bucket_name,
        contenido=csv_reportes,
        s3_key="reportes/resumen_financiero.csv",
        content_type="text/csv",
        storage_class="GLACIER"
    )
    
    # PASO 4: Listar objetos en el bucket
    print("\n\n>>> PASO 4: LISTAR TODOS LOS OBJETOS <<<")
    todos_los_objetos = manager.listar_objetos_s3(bucket_name)
    
    # PASO 5: Listar objetos por carpeta
    print("\n\n>>> PASO 5: LISTAR OBJETOS POR CARPETA <<<")
    
    print("\n[S3] Objetos en carpeta 'ventas':")
    manager.listar_objetos_s3(bucket_name, prefix="ventas/")
    
    print("\n[S3] Objetos en carpeta 'clientes':")
    manager.listar_objetos_s3(bucket_name, prefix="clientes/")
    
    # PASO 6: Obtener contenido de un objeto (sin descargar)
    print("\n\n>>> PASO 6: OBTENER CONTENIDO DE OBJETO (EN MEMORIA) <<<")
    
    print("\n[S3] Obteniendo contenido de 'ventas/ventas_enero_2024.csv'...")
    contenido_ventas = manager.obtener_contenido_s3_como_texto(
        bucket_name=bucket_name,
        s3_key="ventas/ventas_enero_2024.csv"
    )
    
    if contenido_ventas:
        print(f"\n[CONTENIDO] Primeras líneas del archivo:")
        lineas = contenido_ventas.split("\n")[:5]
        for linea in lineas:
            print(f"  {linea}")
        print(f"  ... ({len(contenido_ventas.split(chr(10)))} filas totales)")
    
    # PASO 7: Descargar objeto a archivo local
    print("\n\n>>> PASO 7: DESCARGAR OBJETO A ARCHIVO LOCAL <<<")
    
    archivo_descargado = manager.descargar_objeto_s3(
        bucket_name=bucket_name,
        s3_key="clientes/clientes_activos.csv",
        file_path="clientes_descargados.csv"
    )
    
    # PASO 8: Obtener información de objetos específicos
    print("\n\n>>> PASO 8: OBTENER INFORMACIÓN DE OBJETOS <<<")
    
    objetos_info = {
        "ventas/ventas_enero_2024.csv": "Datos de ventas de enero",
        "clientes/clientes_activos.csv": "Lista de clientes activos",
        "productos/inventario.csv": "Inventario de productos",
        "reportes/resumen_financiero.csv": "Resumen financiero del semestre"
    }
    
    for obj_key, descripcion in objetos_info.items():
        try:
            metadata = manager.s3_client.head_object(
                Bucket=bucket_name,
                Key=obj_key
            )
            tamaño = metadata["ContentLength"]
            print(f"\n[OBJETO] {obj_key}")
            print(f"  Descripción: {descripcion}")
            print(f"  Tamaño: {tamaño} bytes")
            print(f"  Última modificación: {metadata['LastModified']}")
        except Exception as e:
            print(f"Error: {str(e)}")
    
    # Guardar info del bucket en archivo de configuración
    ConfigManager.actualizar("s3_bucket", bucket_name)
    
    print("\n" + "=" * 80)
    print("✓ S3 completado exitosamente")
    print("=" * 80)
    print(f"\nInformación del bucket:")
    print(f"  Nombre: {bucket_name}")
    print(f"  Región: us-east-1")
    print(f"  Objetos creados: {len(todos_los_objetos)}")

# ==================== PROGRAMA S3_DEEP_ARCHIVE ====================    

def main_s3_DEEP_ARCHIVE():
    """
    MAIN 3: S3 - Crear bucket, carpetas y archivos CSV
    
    Pasos:
    1. Crear bucket S3
    2. Crear carpetas dentro del bucket
    3. Crear archivos CSV con datos
    4. Listar objetos
    5. Descargar/Obtener objetos
    """
    
    print("=" * 80)
    print("PARTE 3: S3 (SIMPLE STORAGE SERVICE)")
    print("=" * 80)
    
    # Crear instancia de manager
    manager = StorageManager(region="us-east-1")
    
    # PASO 1: Crear bucket S3
    print("\n\n>>> PASO 1: CREAR BUCKET S3 <<<")
    bucket_name = "mi-bucket-datos-deep-archive" + str(int(time.time()))  # Nombre único
    
    bucket_creado = manager.crear_bucket_s3(
        bucket_name=bucket_name,
        acl="private",
        encryption=False  # OPCIONAL: Encriptación
    )
    
    if not bucket_creado:
        print("✗ Error: No se pudo crear el bucket")
        return
    
    ConfigManager.actualizar("s3_bucket", bucket_name)
    
    # PASO 2: Crear carpetas en S3
    print("\n\n>>> PASO 2: CREAR CARPETAS EN S3 <<<")
    
    carpetas = ["ventas", "clientes", "productos", "reportes"]
    
    for carpeta in carpetas:
        manager.crear_carpeta_s3(bucket_name, carpeta)
    
    # PASO 3: Crear archivos CSV y subirlos
    print("\n\n>>> PASO 3: CREAR Y SUBIR ARCHIVOS CSV <<<")
    
    # CSV 1: Datos de ventas
    print("\n[CSV] Creando CSV de VENTAS...")
    csv_ventas = """id,fecha,producto,cantidad,precio,total
1,2024-01-01,Laptop,5,1200.00,6000.00
2,2024-01-02,Mouse,50,25.00,1250.00
3,2024-01-03,Teclado,30,75.00,2250.00
4,2024-01-04,Monitor,10,300.00,3000.00
5,2024-01-05,Auriculares,25,80.00,2000.00
6,2024-01-06,Webcam,15,120.00,1800.00
7,2024-01-07,SSD,8,450.00,3600.00
8,2024-01-08,RAM,20,100.00,2000.00
9,2024-01-09,Procesador,5,550.00,2750.00
10,2024-01-10,Fuente,12,200.00,2400.00"""
    
    manager.subir_contenido_s3_con_storage_class(
        bucket_name=bucket_name,
        contenido=csv_ventas,
        s3_key="ventas/ventas_enero_2024.csv",  # Ruta con carpeta
        content_type="text/csv",
        storage_class="DEEP_ARCHIVE"
    )
    
    # CSV 2: Datos de clientes
    print("\n[CSV] Creando CSV de CLIENTES...")
    csv_clientes = """id,nombre,email,telefono,ciudad,activo
101,Juan García,juan@example.com,555-0001,Madrid,true
102,María López,maria@example.com,555-0002,Barcelona,true
103,Carlos Rodríguez,carlos@example.com,555-0003,Valencia,false
104,Ana Martínez,ana@example.com,555-0004,Sevilla,true
105,Luis Fernández,luis@example.com,555-0005,Bilbao,true
106,Elena Jiménez,elena@example.com,555-0006,Malaga,true
107,David Pérez,david@example.com,555-0007,Murcia,false
108,Sofia Gómez,sofia@example.com,555-0008,Palma,true
109,Miguel Sánchez,miguel@example.com,555-0009,Las Palmas,true
110,Isabel Ruiz,isabel@example.com,555-0010,Alicante,false"""
    
    manager.subir_contenido_s3_con_storage_class(
        bucket_name=bucket_name,
        contenido=csv_clientes,
        s3_key="clientes/clientes_activos.csv",
        content_type="text/csv",
        storage_class="DEEP_ARCHIVE"
    )
    
    # CSV 3: Datos de productos
    print("\n[CSV] Creando CSV de PRODUCTOS...")
    csv_productos = """id,nombre,categoria,precio,stock,proveedor
1001,Laptop Dell XPS,Computadoras,1200.00,15,Dell Inc
1002,Mouse Logitech,Periféricos,25.00,100,Logitech
1003,Teclado Mecánico,Periféricos,75.00,45,Keychron
1004,Monitor LG 27,Pantallas,300.00,8,LG
1005,Auriculares Sony,Audio,80.00,60,Sony
1006,Webcam HD,Accesorios,120.00,25,Logitech
1007,SSD Samsung 1TB,Almacenamiento,450.00,20,Samsung
1008,RAM DDR4 16GB,Componentes,100.00,50,Corsair
1009,Procesador Intel,Componentes,550.00,12,Intel
1010,Fuente 750W,Componentes,200.00,18,EVGA"""
    
    manager.subir_contenido_s3_con_storage_class(
        bucket_name=bucket_name,
        contenido=csv_productos,
        s3_key="productos/inventario.csv",
        content_type="text/csv",
        storage_class="DEEP_ARCHIVE"
    )
    
    # CSV 4: Reportes
    print("\n[CSV] Creando CSV de REPORTES...")
    csv_reportes = """mes,ingresos,gastos,ganancia,margen
Enero,15100.00,8500.00,6600.00,0.437
Febrero,18200.00,9100.00,9100.00,0.500
Marzo,21500.00,10200.00,11300.00,0.525
Abril,19800.00,9800.00,10000.00,0.505
Mayo,23100.00,11000.00,12100.00,0.524
Junio,25600.00,12000.00,13600.00,0.531"""
    
    manager.subir_contenido_s3_con_storage_class(
        bucket_name=bucket_name,
        contenido=csv_reportes,
        s3_key="reportes/resumen_financiero.csv",
        content_type="text/csv",
        storage_class="DEEP_ARCHIVE"
    )
    
    # PASO 4: Listar objetos en el bucket
    print("\n\n>>> PASO 4: LISTAR TODOS LOS OBJETOS <<<")
    todos_los_objetos = manager.listar_objetos_s3(bucket_name)
    
    # PASO 5: Listar objetos por carpeta
    print("\n\n>>> PASO 5: LISTAR OBJETOS POR CARPETA <<<")
    
    print("\n[S3] Objetos en carpeta 'ventas':")
    manager.listar_objetos_s3(bucket_name, prefix="ventas/")
    
    print("\n[S3] Objetos en carpeta 'clientes':")
    manager.listar_objetos_s3(bucket_name, prefix="clientes/")
    
    # PASO 6: Obtener contenido de un objeto (sin descargar)
    print("\n\n>>> PASO 6: OBTENER CONTENIDO DE OBJETO (EN MEMORIA) <<<")
    
    print("\n[S3] Obteniendo contenido de 'ventas/ventas_enero_2024.csv'...")
    contenido_ventas = manager.obtener_contenido_s3_como_texto(
        bucket_name=bucket_name,
        s3_key="ventas/ventas_enero_2024.csv"
    )
    
    if contenido_ventas:
        print(f"\n[CONTENIDO] Primeras líneas del archivo:")
        lineas = contenido_ventas.split("\n")[:5]
        for linea in lineas:
            print(f"  {linea}")
        print(f"  ... ({len(contenido_ventas.split(chr(10)))} filas totales)")
    
    # PASO 7: Descargar objeto a archivo local
    print("\n\n>>> PASO 7: DESCARGAR OBJETO A ARCHIVO LOCAL <<<")
    
    archivo_descargado = manager.descargar_objeto_s3(
        bucket_name=bucket_name,
        s3_key="clientes/clientes_activos.csv",
        file_path="clientes_descargados.csv"
    )
    
    # PASO 8: Obtener información de objetos específicos
    print("\n\n>>> PASO 8: OBTENER INFORMACIÓN DE OBJETOS <<<")
    
    objetos_info = {
        "ventas/ventas_enero_2024.csv": "Datos de ventas de enero",
        "clientes/clientes_activos.csv": "Lista de clientes activos",
        "productos/inventario.csv": "Inventario de productos",
        "reportes/resumen_financiero.csv": "Resumen financiero del semestre"
    }
    
    for obj_key, descripcion in objetos_info.items():
        try:
            metadata = manager.s3_client.head_object(
                Bucket=bucket_name,
                Key=obj_key
            )
            tamaño = metadata["ContentLength"]
            print(f"\n[OBJETO] {obj_key}")
            print(f"  Descripción: {descripcion}")
            print(f"  Tamaño: {tamaño} bytes")
            print(f"  Última modificación: {metadata['LastModified']}")
        except Exception as e:
            print(f"Error: {str(e)}")
    
    # Guardar info del bucket en archivo de configuración
    ConfigManager.actualizar("s3_bucket", bucket_name)
    
    print("\n" + "=" * 80)
    print("✓ S3 completado exitosamente")
    print("=" * 80)
    print(f"\nInformación del bucket:")
    print(f"  Nombre: {bucket_name}")
    print(f"  Región: us-east-1")
    print(f"  Objetos creados: {len(todos_los_objetos)}")

# ==================== PROGRAMA USO VERSIONADO ====================    

def main_versionado_s3():
    """Demostración de versionado S3"""
    manager = StorageManager()

    ConfigManager.cargar_config()
    bucket_name = ConfigManager.obtener('s3_bucket')

    # PASO 1: Habilitar versionado
    print("\n>>> PASO 1: HABILITAR VERSIONADO <<<")
    manager.habilitar_versionado_s3(bucket_name)
    
    # PASO 2: Subir versión 1
    print("\n>>> PASO 2: SUBIR VERSIÓN 1 <<<")
    csv_v1 = """id,nombre,edad
                1,Juan,25
                2,María,30"""
    
    manager.subir_contenido_s3(
        bucket_name, csv_v1, "datos/personas.csv"
    )
    time.sleep(1)
    
    # PASO 3: Subir versión 2 (modificado)
    print("\n>>> PASO 3: SUBIR VERSIÓN 2 (MODIFICADO) <<<")
    csv_v2 = """id,nombre,edad,ciudad
                1,Juan,26,Madrid
                2,María,31,Barcelona
                3,Carlos,28,Valencia"""
    
    manager.subir_contenido_s3(
        bucket_name, csv_v2, "datos/personas.csv"
    )
    time.sleep(1)
    
    # PASO 4: Subir versión 3
    print("\n>>> PASO 4: SUBIR VERSIÓN 3 <<<")
    csv_v3 = """id,nombre,edad,ciudad,departamento
                1,Juan,26,Madrid,IT
                2,María,31,Barcelona,RH
                3,Carlos,28,Valencia,Ventas
                4,Ana,29,Sevilla,IT"""
    
    manager.subir_contenido_s3(
        bucket_name, csv_v3, "datos/personas.csv"
    )
    
    # PASO 5: Listar todas las versiones
    print("\n>>> PASO 5: LISTAR TODAS LAS VERSIONES <<<")
    versiones = manager.obtener_versiones_objeto(bucket_name, "datos/personas.csv")
    
    # PASO 6: Comparar versiones
    print("\n>>> PASO 6: COMPARAR VERSIONES <<<")
    if len(versiones) >= 2:
        v1_id = versiones[-1]['VersionId']  # Primera versión
        v2_id = versiones[0]['VersionId']   # Última versión
        
        print(f"\n[VERSIÓN 1] (más antigua)")
        contenido_v1 = manager.obtener_version_especifica(bucket_name, "datos/personas.csv", v1_id)
        if contenido_v1:
            print(contenido_v1.decode('utf-8'))
        
        print(f"\n[VERSIÓN 2] (más reciente)")
        contenido_v2 = manager.obtener_version_especifica(bucket_name, "datos/personas.csv", v2_id)
        if contenido_v2:
            print(contenido_v2.decode('utf-8'))

# ==================== PROGRAMA ATHENA ====================   

def main_athena_csv():
    """Demo de Athena con CSV"""
    manager = StorageManager()
    
    # Cargar info

    ConfigManager.cargar_config()
    bucket_name = ConfigManager.obtener('s3_bucket')

    # PASO 1: Crear base de datos
    print("\n>>> PASO 1: CREAR BASE DE DATOS <<<")
    manager.athena_client.start_query_execution(
        QueryString="CREATE DATABASE IF NOT EXISTS mi_db",
        ResultConfiguration={'OutputLocation': f's3://{bucket_name}/athena-results/'}
    )
    time.sleep(2)
    
    # PASO 2: Crear tabla
    print("\n>>> PASO 2: CREAR TABLA DESDE CSV <<<")
    manager.crear_tabla_athena_csv(
        database_name="mi_db",
        table_name="personas",
        bucket_name=bucket_name,
        csv_path="datos/",
        columns=[
            ("id", "int"),
            ("nombre", "string"),
            ("edad", "int"),
            ("ciudad", "string")
        ]
    )
    time.sleep(2)
    
    # PASO 3: Query 1 - Seleccionar todo
    print("\n>>> PASO 3: QUERY 1 - SELECCIONAR TODO <<<")
    manager.ejecutar_query_athena(
        database_name="mi_db",
        sql="SELECT * FROM personas",
        bucket_name=bucket_name
    )
    
    # PASO 4: Query 2 - Contar por ciudad
    print("\n>>> PASO 4: QUERY 2 - CONTAR POR CIUDAD <<<")
    manager.ejecutar_query_athena(
        database_name="mi_db",
        sql="SELECT ciudad, COUNT(*) as cantidad FROM personas GROUP BY ciudad",
        bucket_name=bucket_name
    )
    
    # PASO 5: Query 3 - Promedio de edad
    print("\n>>> PASO 5: QUERY 3 - PROMEDIO DE EDAD <<<")
    manager.ejecutar_query_athena(
        database_name="mi_db",
        sql="SELECT ciudad, AVG(edad) as edad_promedio FROM personas GROUP BY ciudad",
        bucket_name=bucket_name
    )

# ==================== PROGRAMA ATHENA_JSON ====================   

def main_athena_json():
    """Demo de Athena con JSON"""
    manager = StorageManager()
    
    # Cargar info
    ConfigManager.cargar_config()
    bucket_name = ConfigManager.obtener('s3_bucket')

    # PASO 1: Subir datos JSON
    print("\n>>> PASO 1: SUBIR DATOS JSON <<<")
    json_data = """{"id": 1, "nombre": "Juan", "salario": 3000}
                {"id": 2, "nombre": "María", "salario": 3500}
                {"id": 3, "nombre": "Carlos", "salario": 4000}"""
    
    manager.subir_contenido_s3(
        bucket_name, json_data, "datos_json/empleados.json",
        content_type="application/json"
    )
    time.sleep(2)
    
    # PASO 2: Crear tabla JSON
    print("\n>>> PASO 2: CREAR TABLA JSON <<<")
    manager.crear_tabla_athena_json(
        database_name="mi_db",
        table_name="empleados",
        bucket_name=bucket_name,
        json_path="datos_json/",
        columns=[
            ("id", "int"),
            ("nombre", "string"),
            ("salario", "double")
        ]
    )
    time.sleep(2)
    
    # PASO 3: Query 1 - Todos los empleados
    print("\n>>> PASO 3: QUERY 1 - TODOS LOS EMPLEADOS <<<")
    manager.ejecutar_query_athena(
        database_name="mi_db",
        sql="SELECT * FROM empleados",
        bucket_name=bucket_name
    )
    
    # PASO 4: Query 2 - Salario promedio
    print("\n>>> PASO 4: QUERY 2 - SALARIO PROMEDIO <<<")
    manager.ejecutar_query_athena(
        database_name="mi_db",
        sql="SELECT AVG(salario) as salario_promedio FROM empleados",
        bucket_name=bucket_name
    )
    
    # PASO 5: Query 3 - Empleados con salario > 3500
    print("\n>>> PASO 5: QUERY 3 - SALARIO MAYOR A 3500 <<<")
    manager.ejecutar_query_athena(
        database_name="mi_db",
        sql="SELECT nombre, salario FROM empleados WHERE salario > 3500",
        bucket_name=bucket_name
    )

# ==================== PROGRAMA ATHENA_PARTICION_TABLA ====================  

def main_athena_tabla_particionada():
    """Demo de tabla particionada"""
    manager = StorageManager()
    
    # Cargar info
    ConfigManager.cargar_config()
    bucket_name = ConfigManager.obtener('s3_bucket')

    # PASO 1: Crear datos para 2024
    print("\n>>> PASO 1: SUBIR DATOS AÑO 2024 <<<")
    datos_2024 = """1,Juan,25
                 2,María,30"""
    manager.subir_contenido_s3(
        bucket_name, datos_2024, "datos_particionados/year=2024/datos.csv"
    )
    
    # PASO 2: Crear datos para 2025
    print("\n>>> PASO 2: SUBIR DATOS AÑO 2025 <<<")
    datos_2025 = """3,Carlos,28
                4,Ana,29"""
    manager.subir_contenido_s3(
        bucket_name, datos_2025, "datos_particionados/year=2025/datos.csv"
    )
    time.sleep(1)
    
    # PASO 3: Crear tabla particionada
    print("\n>>> PASO 3: CREAR TABLA PARTICIONADA <<<")
    manager.crear_tabla_particionada_athena(
        database_name="mi_db",
        table_name="ventas_por_anio",
        bucket_name=bucket_name,
        columns=[
            ("id", "int"),
            ("nombre", "string"),
            ("valor", "int"),
            ("year", "string")
        ]
    )
    time.sleep(2)
    
    # PASO 4: Agregar particiones
    print("\n>>> PASO 4: AGREGAR PARTICIONES <<<")
    manager.agregar_particion_athena(
        database_name="mi_db",
        table_name="ventas_por_anio",
        partition_value="2024",
        bucket_name=bucket_name,
        path="datos_particionados/year=2024"
    )
    time.sleep(1)
    
    manager.agregar_particion_athena(
        database_name="mi_db",
        table_name="ventas_por_anio",
        partition_value="2025",
        bucket_name=bucket_name,
        path="datos_particionados/year=2025"
    )
    time.sleep(1)
    
    # PASO 5: Query con partición
    print("\n>>> PASO 5: QUERY USANDO PARTICIÓN <<<")
    manager.ejecutar_query_athena(
        database_name="mi_db",
        sql="SELECT * FROM ventas_por_anio WHERE year='2024'",
        bucket_name=bucket_name
    )

# ==================== PROGRAMA PRINCIPAL ====================

def main_selector():
    """
    Selector interactivo para ejecutar los mains
    """
    while True:
        print("\n" + "=" * 80)
        print("SELECTOR DE PARTES - ALMACENAMIENTO AWS")
        print("=" * 80)
        print("\n1. Crear Infraestructura (VPC, SG, Subnet, KeyPair)")
        print("2. EC2, EBS, EFS")
        print("3. S3_STANDART")
        print("4. S3_STANDARD_IA")
        print("5. S3_INTELLIGENT_TIERING")
        print("6. S3_GLACIER")
        print("7. S3_DEEP_ARCHIVE")
        print("8. Demostracion de versionado S3")
        print("9. Consultas con Athena")
        print("10. Athena con JSON")
        print("11. Athena con tabla particionada")
        print("12. Ver configuración guardada (aws_config.json)")
        print("13. Ejecutar todas las partes en orden")
        print("14. Limpiar configuración")
        print("0. Salir")
        
        opcion = input("\nSelecciona una opción (0-14): ").strip()
        
        if opcion == "1":
            main_security_group_subnet_keypairs()
        elif opcion == "2":
            main_ec2_efs_ebs()
        elif opcion == "3":
            main_s3_STANDARD()
        elif opcion == "4":
            main_s3_STANDARD_IA()
        elif opcion == "5":
            main_s3_INTELLIGENT_TIERING()
        elif opcion == "6":
            main_s3_GLACIER()
        elif opcion == "7":
            main_s3_DEEP_ARCHIVE()
        elif opcion == "8":
            main_versionado_s3()
        elif opcion == "9":
            main_athena_csv()
        elif opcion == "10":
            main_athena_json()
        elif opcion == "11":
            main_athena_tabla_particionada()
        elif opcion == "12":
            ConfigManager.mostrar()
        elif opcion == "13":
            print("\nEjecutando todas las partes en orden...\n")
            main_security_group_subnet_keypairs()
            print("\n" + "=" * 80)
            print("Infraestructura creada. Presiona ENTER para continuar...")
            input()
            
            main_ec2_efs_ebs()
            print("\n" + "=" * 80)
            print("EC2, EBS y EFS creados. Presiona ENTER para continuar...")
            input()
            
            main_s3_STANDARD()
            print("\n" + "=" * 80)
            print("S3 STANDARD creado. Todas las partes completadas.")

            main_s3_STANDARD_IA()
            print("\n" + "=" * 80)
            print("S3 STANDARD IA creado. Todas las partes completadas.")

            main_s3_INTELLIGENT_TIERING()
            print("\n" + "=" * 80)
            print("S3 INTELLIGENT TIERING creado. Todas las partes completadas.")

            main_s3_GLACIER()
            print("\n" + "=" * 80)
            print("S3 GLACIER creado. Todas las partes completadas.")

            main_s3_DEEP_ARCHIVE()
            print("\n" + "=" * 80)
            print("S3 DEEP ARCHIVE creado. Todas las partes completadas.")

            main_versionado_s3()
            print("\n" + "=" * 80)
            print("Versionado completado con exito.")

            main_athena_csv()
            print("\n" + "=" * 80)
            print("Consultas Athena completadas con exito.")

            main_athena_json()
            print("\n" + "=" * 80)
            print("Uso de Athena con JSON completado con exito.")

            main_athena_tabla_particionada()
            print("\n" + "=" * 80)
            print("Particionado de tabla con Athena completado con exito.")

        elif opcion == "14":
            confirmacion = input("\n¿Estás seguro de que deseas limpiar la configuración? (s/n): ").strip().lower()
            if confirmacion == "s":
                ConfigManager.limpiar()
            else:
                print("Operación cancelada")
        elif opcion == "0":
            print("Saliendo...")
            break
        else:
            print("✗ Opción no válida")


if __name__ == '__main__':
    main_selector()

