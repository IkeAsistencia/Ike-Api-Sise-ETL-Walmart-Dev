import pyodbc
import os


def conectar():
    
    drivers = pyodbc.drivers()
    if "FreeTDS" in drivers:
        driv="FreeTDS"
    elif "ODBC Driver 18 for SQL Server" in drivers:
        driv="ODBC Driver 18 for SQL Server"
        
    conexion=(
        #'DRIVER={SQL Server};'
        f'DRIVER={{{driv}}};'
        f'SERVER={os.getenv("MX_DB_SERVER")},{os.getenv("MX_DB_PORT")};'
        f'DATABASE={os.getenv("MX_DB_NAME")};'
        f'UID={os.getenv("MX_DB_USER")};'
        f'PWD={os.getenv("MX_DB_PASSWORD")};'
    )

    if driv == "FreeTDS":
        conexion += "TDS_Version=7.2;Encrypt=yes;"
    else:
        conexion += "Encrypt=yes;TrustServerCertificate=yes;"
    return pyodbc.connect(conexion,timeout=300)

#comprobar la conexion
'''
from dotenv import load_dotenv

load_dotenv()

conexion_BD=conectar()
cursor=conexion_BD.cursor()

cursor.execute("SELECT 1")

for row in cursor.fetchall():
    print(row)

cursor.close()
conexion_BD.close()
'''