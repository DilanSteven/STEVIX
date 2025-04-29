# db.py
import pyodbc

# Datos de conexión
server = 'DESKTOP-VA8T8I5\\SQLEXPRESS'  # Recuerda escapar las barras invertidas con doble \
database = 'STEVIX'

# Función para obtener la conexión a la base de datos
def get_db_connection():
    conn = pyodbc.connect(
        f'DRIVER={{ODBC Driver 17 for SQL Server}};'
        f'SERVER={server};'
        f'DATABASE={database};'
        'Trusted_Connection=yes;'
    )
    return conn
