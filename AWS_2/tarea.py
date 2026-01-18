import boto3
import time
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

class StorageManager:
    def __init__(self, region='us-east-1'):
        """
        Inicializa los clientes de AWS
        
        Args:
            region (str): Región de AWS donde crear los recursos (opcional, por defecto us-west-2)
        """
        self.region = region
        self.ec2_client = boto3.client('ec2', region_name=region)
        self.ec2_resource = boto3.resource('ec2', region_name=region)
        self.efs_client = boto3.client('efs', region_name=region)

     
    # ==================== EC2 MANAGEMENT ====================
    # Almacenamiento: Instancias de máquinas virtuales completas en la nube
    # Caso de uso: Ejecutar servidores web, aplicaciones, bases de datos
    
    def crear_ec2(self, instance_name, ami_id='ami-0ecb62995f68bb549', instance_type='t2.micro', 
                  security_group_name='sg-076af812ec93aff17', key_name='clave_casa'):
        """
        CREAR INSTANCIA EC2
        
        Parámetros OBLIGATORIOS:
            - ami_id (str): ID de la imagen AMI (ej: ami-0c55b159cbfafe1f0 para Amazon Linux 2 en us-west-2)
            - instance_type (str): Tipo de instancia (t2.micro, t2.small, t3.medium, etc.)
        
        Parámetros OPCIONALES:
            - instance_name (str): Nombre para etiquetar la instancia
            - security_group_name (str): Grupo de seguridad a usar
            - key_name (str): Par de claves para SSH
            - MaxCount, MinCount: Cantidad de instancias (por defecto 1)
        
        Almacena: Máquina virtual con SO (Linux/Windows) lista para usar
        """
        try:
            print(f"\n[EC2] Creando instancia: {instance_name}...")
            
            # Parámetros obligatorios
            params = {
                'ImageId': ami_id,  # OBLIGATORIO: ID de la imagen
                'MinCount': 1,       # OBLIGATORIO: Mínimo de instancias
                'MaxCount': 1,       # OBLIGATORIO: Máximo de instancias
                'InstanceType': instance_type,  # OBLIGATORIO: Tipo de máquina
                'SecurityGroupIds':security_group_name, #OPCIONAL
                'KeyName':key_name #OPCIONAL
            }
            
            # Parámetros opcionales
            if security_group_name:
                params['SecurityGroupIds'] = [security_group_name]
            if key_name:
                params['KeyName'] = key_name
            
            # Crear la instancia
            response = self.ec2_client.run_instances(**params)
            instance_id = response['Instances'][0]['InstanceId']
            
            # Etiquetar la instancia (opcional pero útil)
            self.ec2_resource.create_tags(
                Resources=[instance_id],
                Tags=[{'Key': 'Name', 'Value': instance_name}]
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
            waiter = self.ec2_client.get_waiter('instance_running')
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
            waiter = self.ec2_client.get_waiter('instance_stopped')
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
            waiter = self.ec2_client.get_waiter('instance_terminated')
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
            state = response['Reservations'][0]['Instances'][0]['State']['Name']
            print(f"[EC2] Estado de {instance_id}: {state}")
            return state
        except Exception as e:
            print(f"✗ Error al obtener estado: {str(e)}")
            return None


    # ==================== EBS MANAGEMENT ====================
    # Almacenamiento: Almacenamiento en bloque persistente y de alto rendimiento
    # Caso de uso: Discos duros virtuales para bases de datos, archivos críticos
    
    def crear_ebs(self, volume_name, size=20, availability_zone='us-east-1c', volume_type='gp3'):
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
                availability_zone = response['AvailabilityZones'][0]['ZoneName']
            
            print(f"\n[EBS] Creando volumen EBS: {volume_name}...")
            print(f"  Tamaño: {size} GB")
            print(f"  Tipo: {volume_type}")
            print(f"  Zona: {availability_zone}")
            
            # Parámetros obligatorios
            params = {
                'Size': size,  # OBLIGATORIO: Tamaño en GB
                'AvailabilityZone': availability_zone,  # OBLIGATORIO: Zona
                'VolumeType': volume_type  # OBLIGATORIO: Tipo de volumen
            }
            
            # Parámetros opcionales según tipo
            if volume_type in ['gp3', 'io1', 'io2']:
                params['Iops'] = 3000  # IOPS mínimas para gp3
            if volume_type == 'gp3':
                params['Throughput'] = 125  # Rendimiento en MB/s
            
            params['Encrypted'] = False  # Opcional: activar encriptación
            
            response = self.ec2_client.create_volume(**params)
            volume_id = response['VolumeId']
            
            # Etiquetar el volumen
            self.ec2_resource.create_tags(
                Resources=[volume_id],
                Tags=[{'Key': 'Name', 'Value': volume_name}]
            )
            
            print(f"✓ Volumen EBS creado: {volume_id}")
            
            return volume_id
            
        except Exception as e:
            print(f"✗ Error al crear volumen EBS: {str(e)}")
            return None
    
    def asociar_ebs_a_ec2(self, volume_id, instance_id, device='/dev/sdf'):
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
                VolumeId=volume_id,
                InstanceId=instance_id,
                Device=device
            )
            
            # Esperar a que se asocie
            time.sleep(2)
            
            print(f"✓ Volumen asociado en dispositivo {device}")
            
            return True
            
        except Exception as e:
            print(f"✗ Error al asociar volumen: {str(e)}")
            return False
    
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
    
    def crear_efs(self, fs_name, performance_mode='generalPurpose', 
                  throughput_mode='bursting', encrypted=False):
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
                'PerformanceMode': performance_mode,  # OBLIGATORIO
                'ThroughputMode': throughput_mode,    # OBLIGATORIO
                'Encrypted': encrypted  # OPCIONAL: Encriptación
            }
            
            response = self.efs_client.create_file_system(**params)
            fs_id = response['FileSystemId']
            
            # Etiquetar el EFS
            self.efs_client.create_tags(
                FileSystemId=fs_id,
                Tags=[{'Key': 'Name', 'Value': fs_name}]
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
                'FileSystemId': fs_id,      # OBLIGATORIO
                'SubnetId': subnet_id       # OBLIGATORIO
            }
            
            if security_group_ids:
                params['SecurityGroups'] = security_group_ids
            
            response = self.efs_client.create_mount_target(**params)
            mount_target_id = response['MountTargetId']
            
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
            
            if not response['FileSystems']:
                print("  No hay EFS disponibles")
                return []
            
            for fs in response['FileSystems']:
                print(f"  - {fs['FileSystemId']}: {fs['Name']} ({fs['LifeCycleState']})")
            
            return response['FileSystems']
            
        except Exception as e:
            print(f"✗ Error al listar EFS: {str(e)}")
            return []


# ==================== PROGRAMA PRINCIPAL ====================
def main():
    
    print("=" * 80)
    print("GESTOR DE ALMACENAMIENTO AWS (EC2, EBS, EFS)")
    print("=" * 80)
    
    # Inicializar manager
    manager = StorageManager(region='us-east-1')
    
    # # ========== PASO 1: CREAR Y GESTIONAR EC2 ==========
    print("\n\n>>> PASO 1: CREAR INSTANCIA EC2 <<<")
    instance_id = manager.crear_ec2(
        instance_name='mi-servidor-web',
        ami_id='ami-0ecb62995f68bb549',  # Amazon Linux 2 en us-west-2
        instance_type='t2.micro',
        key_name='clave_casa',
        security_group_name='sg-076af812ec93aff17'

    )

    manager.ec2_client.get_waiter('instance_running').wait(InstanceIds=[instance_id])

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
        # ========== PASO 5: CREAR Y ASOCIAR EBS ==========
    print("\n\n>>> PASO 5: CREAR VOLUMEN EBS <<<")
    volume_id = manager.crear_ebs(
        volume_name='mi-volumen-datos',
        size=20,
        volume_type='gp3',
        availability_zone='us-east-1c'
    )
    
    if volume_id:
        time.sleep(3)
        
        print("\n>>> PASO 6: ASOCIAR EBS A EC2 <<<")
        manager.asociar_ebs_a_ec2(volume_id, 'i-043f9aa4dd72f474c', device='/dev/sdf')
        
        print("\n>>> PASO 7: AGREGAR ARCHIVO A EBS <<<")
    
        # ========== PASO 8: CREAR EFS ==========

    print("\n\n>>> PASO 8: CREAR EFS (SISTEMA DE ARCHIVOS COMPARTIDO) <<<")
    efs_id = manager.crear_efs(
        fs_name='mi-efs-compartido-final',
        performance_mode='generalPurpose',
        throughput_mode='bursting',
        encrypted=False

    )

    while True:
        estado = manager.efs_client.describe_file_systems(FileSystemId=efs_id)['FileSystems'][0]['LifeCycleState']
        if estado == 'available':
            break
        print(f"EFS aún en estado {estado}, esperando...")
        time.sleep(3)
    
    if efs_id:
        time.sleep(2)
        
        # ========== PASO 9: CREAR MOUNT TARGET PARA EFS ==========

        print("\n\n>>> PASO 9: CREAR MOUNT TARGET PARA EFS <<<")
        # NOTA: Necesitas obtener el subnet_id de tu EC2
        # Puedes obtenerlo con: ec2_client.describe_instances()
        
        subnet_id = 'subnet-0aba27d15cd8000a4'  
        
        mount_target_id = manager.crear_mount_target(
            fs_id=efs_id,
            subnet_id=subnet_id,
            security_group_ids=['sg-076af812ec93aff17']  # OPCIONAL: Mismo SG que EC2
        )
        
        if mount_target_id:
            time.sleep(2)
            
            # ========== PASO 10: LISTAR EFS DISPONIBLES ===
            print("\n\n>>> PASO 10: LISTAR EFS DISPONIBLES <<<")
            manager.listar_efs()
    
    # ========== PASO 10: LIMPIAR RECURSOS ==========
    print("\n\n>>> PASO 10: ELIMINAR INSTANCIA EC2 (LIMPIEZA) <<<")
    manager.eliminar_ec2(instance_id)

main()