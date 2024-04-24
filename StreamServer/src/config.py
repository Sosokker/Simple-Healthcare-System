"""
This file is used to store the configuration of the project.

Attributes:
    DB_HOST: The host of the MySQL database
    DB_USER: The username of the MySQL database
    DB_PASSWD: The password of the MySQL database
    DB_NAME: The name of the MySQL database
    MINIO_ENDPOINT: The endpoint of the MinIO storage
    MINIO_ACCESS_KEY: The access key of the MinIO storage
    MINIO_SECRET_KEY: The secret key of the MinIO storage
"""

from decouple import Config

config = Config('.env')

DB_HOST = config.get('DB_HOST', default='localhost')
DB_USER = config.get('DB_USER', default='root')
DB_PASSWD = config.get('DB_PASSWD', default='root')
DB_NAME = config.get('DB_NAME')
MINIO_ENDPOINT = config.get('MINIO_ENDPOINT', default='localhost:9000')
MINIO_ACCESS_KEY = config.get('MINIO_ACCESS_KEY')
MINIO_SECRET_KEY = config.get('MINIO_SECRET_KEY')