import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

def conectar():
    conexion=(
        'DRIVER={SQL Server};'
        f'SERVER={os.getenv("MX_DB_SERVER")};'
        f'DATABASE={os.getenv("MX_DB_NAME")};'
        f'UID={os.getenv("MX_DB_USER")};'
        f'PWD={os.getenv("MX_DB_PASSWORD")};'
        'CHARSET=UTF8MB4;'  
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