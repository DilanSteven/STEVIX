from flask import Flask, render_template
import pyodbc

app = Flask(__name__)

# Datos de conexión
server = 'tu_servidor'  # Ejemplo: 'localhost' o la IP del servidor
database = 'tu_base_de_datos'  # El nombre de tu base de datos
username = 'tu_usuario'  # El usuario de tu base de datos
password = 'tu_contraseña'  # La contraseña de tu base de datos

# Función para obtener la conexión a la base de datos
def get_db_connection():
    conn = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};'
                          f'SERVER={server};'
                          f'DATABASE={database};'
                          f'UID={username};'
                          f'PWD={password}')
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Realiza una consulta a la base de datos
    cursor.execute('SELECT * FROM peliculas')
    peliculas = cursor.fetchall()  # Obtener todos los resultados
    
    cursor.close()
    conn.close()
    
    # Renderiza una plantilla HTML (puedes crearla en templates/index.html)
    return render_template('index.html', peliculas=peliculas)

if __name__ == '__main__':
    app.run(debug=True)
