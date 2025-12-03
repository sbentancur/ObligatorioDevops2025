# ============================
# IMPORTS
# ============================
import boto3
import os
from botocore.exceptions import ClientError

# ============================
# VARIABLES GLOBALES
# ============================
AMI = 'ami-06b21ccaeff8cd686'
SECURITY_GROUP_NAME = 'secgrpEC2'

NOMBRE_SG_BD = 'rrhh-db-sg'
ID_SG_BD = None

# RDS Settings
db_instance_identifier = 'rds-obl-devops-25'
db_instance_class = 'db.t3.medium'
master_username = 'admin'
master_user_password = open("./password.txt", 'r').read().strip()
name_db = "demo_db"
allocated_storage = int(os.environ.get('RDS_ALLOCATED_STORAGE', 20))
publicly_accessible = True

# ============================
# CLIENTES
# ============================
ec2 = boto3.client('ec2')
rds_client = boto3.client('rds')

# ============================
# CREACIÓN DE SECURITY GROUP WEB
# ============================
try:
    response = ec2.create_security_group(
        GroupName=SECURITY_GROUP_NAME,
        Description='scgrpEC2'
    )
    sg_id = response['GroupId']
    print(f"✔ SG Web creado: {sg_id}")

    # Abrir puerto 80
    ec2.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[
            {
                'IpProtocol': 'tcp',
                'FromPort': 80,
                'ToPort': 80,
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            }
        ]
    )
    print("✔ Ingress HTTP habilitado")

except ClientError as e:
    if e.response['Error']['Code'] == 'InvalidGroup.Duplicate':
        print("ℹ SG Web ya existe, buscando ID...")
        existentes = ec2.describe_security_groups(GroupNames=[SECURITY_GROUP_NAME])
        sg_id = existentes['SecurityGroups'][0]['GroupId']
        print(f"✔ SG Web existente: {sg_id}")
    else:
        raise e

# ============================
# S3 – CREAR BUCKET Y SUBIR APP
# ============================
BUCKET_NAME = "rrhh-app-bucket-obl-devops25"
LOCAL_WEBAPP_PATH = "/home/admin/obli/python/ObligatorioDevops2025/python/webapp"

s3 = boto3.client("s3")

# Crear bucket si no existe
try:
    s3.create_bucket(Bucket=BUCKET_NAME)
    print(f"✔ Bucket creado: {BUCKET_NAME}")
except ClientError as e:
    if e.response["Error"]["Code"] == "BucketAlreadyOwnedByYou":
        print(f"ℹ Bucket ya existe: {BUCKET_NAME}")
    else:
        raise e


# Subir webapp recursivamente
def upload_folder_to_s3(folder_path, bucket, prefix=""):
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            full_path = os.path.join(root, file)
            relative_path = os.path.relpath(full_path, folder_path)
            s3_key = f"{prefix}{relative_path}"
            s3.upload_file(full_path, bucket, s3_key)
            print(f"📤 Subido: {s3_key}")


print("\n➡ Subiendo carpeta webapp/")
upload_folder_to_s3(LOCAL_WEBAPP_PATH, BUCKET_NAME, prefix="webapp/")

print("\n✔ Archivos cargados en S3 correctamente.\n")

# ============================
# CREACIÓN SECURITY GROUP BD
# ============================
try:
    respuesta = ec2.create_security_group(
        GroupName=NOMBRE_SG_BD,
        Description='SG para base de datos RRHH'
    )
    ID_SG_BD = respuesta['GroupId']
    print(f"✔ SG BD creado: {ID_SG_BD}")

    # Access from EC2 SG
    ec2.authorize_security_group_ingress(
        GroupId=ID_SG_BD,
        IpPermissions=[
            {
                'IpProtocol': 'tcp',
                'FromPort': 3306,
                'ToPort': 3306,
                'UserIdGroupPairs': [{'GroupId': sg_id}]
            }
        ]
    )
    print("✔ Ingress MySQL permitido desde SG Web")

except ClientError as e:
    if e.response['Error']['Code'] == 'InvalidGroup.Duplicate':
        print("ℹ SG BD ya existe, buscando ID...")
        existentes = ec2.describe_security_groups(GroupNames=[NOMBRE_SG_BD])
        ID_SG_BD = existentes['SecurityGroups'][0]['GroupId']
        print(f"✔ SG BD existente: {ID_SG_BD}")
    else:
        raise e

# ============================
# CREAR INSTANCIA RDS
# ============================
try:
    response = rds_client.create_db_instance(
        DBInstanceIdentifier=db_instance_identifier,
        DBInstanceClass=db_instance_class,
        Engine = 'mysql',
        MasterUsername=master_username,
        MasterUserPassword=master_user_password,
        DBName='demo_db',
        AllocatedStorage=allocated_storage,
        VpcSecurityGroupIds=[ID_SG_BD],
        PubliclyAccessible=False
    )
    print(f"✔ Creando instancia RDS: {db_instance_identifier}")

except ClientError as e:
    if "DBInstanceAlreadyExists" in str(e):
        print("ℹ Instancia RDS ya existe. Continuando...")
    else:
        raise e

print("⏳ Esperando a que RDS esté disponible...")

waiter = rds_client.get_waiter("db_instance_available")
waiter.wait(DBInstanceIdentifier=db_instance_identifier)

db_info = rds_client.describe_db_instances(DBInstanceIdentifier=db_instance_identifier)

ENDPOINT_RDS = db_info["DBInstances"][0]["Endpoint"]["Address"]

print(f"✔ Endpoint RDS: {ENDPOINT_RDS}")

# ============================
# VARIABLES PARA USER DATA
# ============================
USUARIO_APP = "admin"
CONTRASENA_APP = "admin123"

NOMBRE_BUCKET = BUCKET_NAME
NOMBRE_BD = 'demo_db'
USUARIO_BD = master_username 
CONTRASENA_BD = master_user_password

# ==============
# USER DATA 
# ==============
USER_DATA = f"""#!/bin/bash
yum update -y
yum install -y httpd php php-cli php-fpm php-common php-mysqlnd mariadb105 awscli -y

systemctl enable --now httpd
systemctl enable --now php-fpm

echo '<FilesMatch \\.php$>
  SetHandler "proxy:unix:/run/php-fpm/www.sock|fcgi://localhost/"
</FilesMatch>' | tee /etc/httpd/conf.d/php-fpm.conf

rm -rf /var/www/html/*
aws s3 sync s3://{NOMBRE_BUCKET}/webapp/ /var/www/html/

if [ -f /var/www/html/init_db.sql ]; then
  cp /var/www/html/init_db.sql /var/www/
fi

if [ ! -f /var/www/.env ]; then
cat > /var/www/.env << 'EOT'
DB_HOST={ENDPOINT_RDS}
DB_NAME={NOMBRE_BD}
DB_USER={USUARIO_BD}
DB_PASS={CONTRASENA_BD}

APP_USER={USUARIO_APP}
APP_PASS={CONTRASENA_APP}
EOT
fi

chown apache:apache /var/www/.env
chmod 600 /var/www/.env

chown -R apache:apache /var/www/html
chmod -R 755 /var/www/html

if [ -f /var/www/init_db.sql ]; then
  mysql -h {ENDPOINT_RDS} -u {USUARIO_BD} -p{CONTRASENA_BD} {NOMBRE_BD} < /var/www/init_db.sql
fi

systemctl restart httpd php-fpm
"""

# ============================
# CREACIÓN INSTANCIA EC2
# ============================
instance = ec2.run_instances(
    ImageId=AMI,
    InstanceType='t2.micro',
    SecurityGroupIds=[sg_id],
    MinCount=1,
    MaxCount=1,
    UserData=USER_DATA,
    IamInstanceProfile={
        'Name': 'LabInstanceProfile'
    }
)

instance_id = instance["Instances"][0]["InstanceId"]
print(f"✔ Instancia EC2 creada: {instance_id}")

# Tags
ec2.create_tags(
    Resources=[instance_id],
    Tags=[
        {'Key': 'Name', 'Value': 'app-rrhh'},
        {'Key': 'Application', 'Value': 'RRHH'},
        {'Key': 'DataClassification', 'Value': 'Confidential'}
    ]
)

waiter_ec2 = ec2.get_waiter("instance_running")
waiter_ec2.wait(InstanceIds=[instance_id])

print("\nObteniendo IP pública...")
inf_instance = ec2.describe_instances(InstanceIds=[instance_id])
IP_PUBLICA = inf_instance['Reservations'][0]['Instances'][0].get('PublicIpAddress')

print(f"IP pública: {IP_PUBLICA}")
print("====================================")
