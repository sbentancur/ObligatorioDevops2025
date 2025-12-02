📘 Obligatorio – Programación para DevOps

Fecha de entrega: 03/12/2025

📌 Descripción General del Proyecto

Este proyecto forma parte del obligatorio de la materia Programación para DevOps.
El escenario define que Banco Riendo inicia una migración hacia un modelo de nube híbrida, y se nos asignan dos tareas principales:

- Automatización de creación de usuarios en Linux mediante un script Bash.
- Despliegue automatizado y seguro de una aplicación de Recursos Humanos en AWS utilizando Python y Boto3.

Este repositorio contiene todo el código, documentación y evidencia del funcionamiento.

🟦 Script en Bash

Crear un script en Bash llamado ej1_crea_usuarios.sh capaz de:
Leer un archivo con usuarios en formato formado por 5 campos separados por ":".
Crear usuarios con:

- Shell por defecto
- Directorio home
- Comentario
- Creación condicionada del home
- Opción -i: mostrar salida detallada.
- Opción -c: asignar contraseña a todos los usuarios.
- Manejo de errores con diferentes códigos de retorno.

📁 Ubicación del código
bash/agregarUsuarios.sh

📄 Formato del archivo de entrada
usuario:comentario:/ruta/home:SI|NO:/bin/bash

Ejemplo:
pepe:Este es mi amigo pepe:/home/jose:SI:/bin/bash
papanatas:Usuario trucho:/trucho:NO:/bin/sh

▶️ Modo de uso
./agregarUsuarios.sh [-i] [-c contraseña] archivo_usuarios.txt

Ejemplos:
./agregarUsuarios.sh usuarios.txt
./agregarUsuarios.sh -i usuarios.txt
./agregarUsuarios.sh -i -c "123456" usuarios.txt

📸 Evidencia del funcionamiento
Se incluye en:
bash/screenshots/

🟦 Script en Python (AWS)

Automatizar el despliegue de una aplicación de Recursos Humanos que maneja datos sensibles:

- Nombres
- Emails
- Salarios

📁 Ubicación del código
python/app.py

Bucket S3 configurados con:
- Versionado.
- Bloqueo de acceso público.
- RDS protegido en subred privada.
- Reglas de SG restrictivas y específicas.

🛠️ Requisitos
Python 3.10+
AWS CLI configurado
Permisos para: S3, EC2, RDS, IAM

▶️ Modo de uso
Dentro de la carpeta python, ejecutar
python3 app.py

📸 Evidencia del despliegue

Guardado en:
python/screenshots/
