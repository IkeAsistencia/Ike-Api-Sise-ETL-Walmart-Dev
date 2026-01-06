import pyodbc
import os

def conectar():
    
    conexion=(
        #'DRIVER={SQL Server};'
        'DRIVER={FreeTDS};'
        #'DRIVER={ODBC Driver 17 for SQL Server};'
        #'DRIVER={Microsoft ODBC Driver 18 for SQL Server};'
        #f'SERVER={os.getenv("MX_DB_SERVER")},{os.getenv("MX_DB_PORT")};'
        f'SERVER={os.getenv("MX_DB_SERVER")};'
        f'PORT={os.getenv("MX_DB_PORT")};'
        f'DATABASE={os.getenv("MX_DB_NAME")};'
        f'UID={os.getenv("MX_DB_USER")};'
        f'PWD={os.getenv("MX_DB_PASSWORD")};'
        'TDS_Version=7.3;'
        'ClientCharset=UTF-8;'
        #"Encrypt=no;"
        #"TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conexion,timeout=300)

#comprobar la conexion
'''''
conexion_BD=conectar()
cursor=conexion_BD.cursor()

cursor.execute("SELECT 1")

for row in cursor.fetchall():
    print(row)

cursor.close()
conexion_BD.close()
'''''