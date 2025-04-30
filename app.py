from flask import Flask 
from flask import render_template , request, redirect, url_for,jsonify,flash,session
from functools import wraps
import pyodbc
import base64
import os
import random
import hashlib
#importacion de Anime
from anime import obtener_animes,crear_anime,editar_anime
#Conexion de base de datos
from db import get_db_connection
import psycopg2



app=Flask(__name__)
app.secret_key = 'tu_clave_super_secreta'

# Datos de conexión
#server = 'DESKTOP-VA8T8I5\SQLEXPRESS'  # Tu servidor SQL Server
#database = 'STEVIX'  # El nombre de tu base de datos

# Función para obtener la conexión a la base de datos (autenticación de Windows)
#def get_db_connection():
#    conn = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};'
#                          f'SERVER={server};'
#                          f'DATABASE={database};'
#                          'Trusted_Connection=yes;')  # Utiliza la autenticación de Windows
#    return conn

# Datos de conexión para PostgreSQL en Render
def get_db_connection():
    conn = psycopg2.connect(
        host='dpg-d08n0s95pdvs739mi980-a.oregon-postgres.render.com',
        port=5432,
        database='stevix',
        user='stevix',
        password='eCiIdjZOFn3M2h4vcabGY5DJa607Lbl0'
    )
    return conn

#Listado de 
    #Anime
# Vista para ver animes
@app.route('/admin/animes', methods=['GET', 'POST'])
def ver_animes():
    animes, search_term = obtener_animes()
    return render_template('admin/lista_animes.html', animes=animes, search_term=search_term)
#Crear Anime
@app.route('/admin/crear_anime', methods=['GET', 'POST'])
def crear_anime_route():
    return crear_anime()
#Editar Anime
@app.route('/admin/editar_anime/<int:anime_id>', methods=['GET', 'POST'])
def editar_anime_route(anime_id):
    return editar_anime(anime_id)

#inicio de session
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('login'))  # Redirige si no hay sesión
        return f(*args, **kwargs)
    return decorated_function

@app.route('/peliculas')
def peliculas():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Realiza una consulta a la base de datos para obtener las películas
    cursor.execute('SELECT id, titulo, descripcion, portada FROM pelicula')  # Ajusta según tu base de datos
    peliculas = cursor.fetchall()  # Obtener todos los resultados
    
    # Convierte las portadas en binario a una cadena base64
    peliculas_con_imagen = []
    for pelicula in peliculas:
        id_pelicula, titulo, descripcion, portada_bin = pelicula
        
        # Convertir la portada binaria a base64 para usarla en el HTML
        if portada_bin:
            portada_base64 = base64.b64encode(portada_bin).decode('utf-8')
            portada_data_uri = f"data:image/jpeg;base64,{portada_base64}"
        else:
            portada_data_uri = "https://via.placeholder.com/300x400?text=No+Imagen"  # Imagen por defecto si no hay portada
        
        peliculas_con_imagen.append({
            'id': id_pelicula,
            'titulo': titulo,
            'descripcion': descripcion,
            'portada': portada_data_uri
        })
    
    cursor.close()
    conn.close()
    
    # Renderiza la plantilla HTML, pasando las películas con sus portadas como contexto
    return render_template('sitio/peliculas.html', peliculas=peliculas_con_imagen)

    #return render_template('sitio/peliculas.html')

#llamar lista de Id para formulario de Peliculas
@app.route('/NewPeli', methods=['GET', 'POST'])
def NewPeli():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'GET':
        cursor.execute('SELECT id, titulo FROM anime')
        anime_ids = cursor.fetchall()  # Traemos todos los ids de anime
        print("IDs de Anime: ", anime_ids)
        cursor.close()
        conn.close()

        return render_template('admin/NewPeli.html', anime_ids=anime_ids)

    if request.method == 'POST':
        anime_id = request.form['anime_id']
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        fecha_estreno = request.form['fecha_estreno']
        duracion = request.form['duracion']
        
        # Guardamos la imagen de portada
        portada = request.files['portada']
        if portada:
            # Definir la ruta de destino de la imagen
            image_folder = os.path.join('static', 'images')
            
            # Verificar si el directorio existe, si no, crearlo
            if not os.path.exists(image_folder):
                os.makedirs(image_folder)
            
            # Guardar la imagen en la ruta especificada
            portada_path = os.path.join(image_folder, portada.filename)
            portada.save(portada_path)

            # Abrir la imagen como datos binarios
            with open(portada_path, 'rb') as f:
                portada_data = f.read()  # Esto convierte la imagen a datos binarios

            # Insertamos los datos binarios en la base de datos
            cursor.execute('''
                INSERT INTO pelicula (anime_id, titulo, descripcion, fecha_estreno, duracion, portada)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (anime_id, titulo, descripcion, fecha_estreno, duracion, portada_data))

            conn.commit()
        else:
            # Si no se sube una imagen, puedes dejar la columna de portada como NULL
            cursor.execute('''
                INSERT INTO pelicula (anime_id, titulo, descripcion, fecha_estreno, duracion, portada)
                VALUES (?, ?, ?, ?, ?, NULL)
            ''', (anime_id, titulo, descripcion, fecha_estreno, duracion))
            conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for('NewPeli'))  # Redirigir después de insertar
#Mostrar Pelicula
@app.route('/pelicula/<int:id>')
def ViewPeli(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Consultar por ID de la película seleccionada
    cursor.execute('SELECT p.id, p.titulo, p.descripcion, p.fecha_estreno, p.duracion, p.portada, p.link, a.portada FROM pelicula p JOIN Anime a ON p.anime_id = a.id WHERE p.id = ?', (id,))

    pelicula = cursor.fetchone()

    if pelicula:
        id_pelicula, titulo, descripcion, fecha_estreno, duracion, portada_bin, link , portada_bin1= pelicula

        # Convertir portada binaria a base64 (o poner imagen por defecto)
        if portada_bin:
            portada_base64 = base64.b64encode(portada_bin).decode('utf-8')
            portada_data_uri = f"data:image/jpeg;base64,{portada_base64}"
        else:
            portada_data_uri = "https://via.placeholder.com/300x400?text=No+Imagen"
        #Convertir segunda imagen de portada
        if portada_bin1:
            portada_base641 = base64.b64encode(portada_bin1).decode('utf-8')
            portada_data_uri1 = f"data:image/jpeg;base64,{portada_base641}"
        else:
            portada_data_uri1 = "https://via.placeholder.com/300x400?text=No+Imagen"
        # Obtener la portada de la primera película para la sección de inicio
        cursor.execute('SELECT TOP 1 portada FROM pelicula')  # Corregido para SQL Server
        primera_pelicula = cursor.fetchone()
        if primera_pelicula:
            portada_inicio_bin = primera_pelicula[0]
            if portada_inicio_bin:
                portada_inicio_base64 = base64.b64encode(portada_inicio_bin).decode('utf-8')
                portada_inicio_data_uri = f"data:image/jpeg;base64,{portada_inicio_base64}"
            else:
                
                portada_inicio_data_uri = "https://via.placeholder.com/1200x600?text=Imagen+de+inicio"
        else:
            portada_inicio_data_uri = "https://via.placeholder.com/1200x600?text=Imagen+de+inicio"  # Imagen por defecto

        # Datos de la película seleccionada
        datos_pelicula = {
            'id': id_pelicula,
            'titulo': titulo,
            'descripcion': descripcion,
            'fecha_estreno': fecha_estreno,
            'duracion': duracion,
            'portada': portada_data_uri,
            'link': link,
            'portada_inicio': portada_bin  # Pasamos la portada de la primera película
        }
        portada_inicio_data_uri = portada_data_uri1

        cursor.close()
        conn.close()

        # Renderizamos la vista, pasando tanto los datos de la película como la portada de inicio
        return render_template('sitio/ViewPeli.html', pelicula=datos_pelicula, portada_inicio=portada_inicio_data_uri,random=random)
    else:
        cursor.close()
        conn.close()
        return "Película no encontrada", 404

@app.route('/EditPeli/<int:id>', methods=['GET', 'POST'])
def EditPeli(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'GET':
        # Obtener datos de la película
        cursor.execute('SELECT * FROM pelicula WHERE id = ?', id)
        pelicula = cursor.fetchone()

        if not pelicula:
            return "Película no encontrada", 404

        # Obtener animes para el dropdown
        cursor.execute('SELECT id, titulo FROM anime')
        anime_ids = cursor.fetchall()

        # Convertir portada a base64
        portada = base64.b64encode(pelicula.portada).decode('utf-8') if pelicula.portada else None
        portada_uri = f"data:image/jpeg;base64,{portada}" if portada else "https://via.placeholder.com/200x300?text=No+Imagen"

        datos_pelicula = {
            'id': pelicula.id,
            'anime_id': pelicula.anime_id,
            'titulo': pelicula.titulo,
            'descripcion': pelicula.descripcion,
            'fecha_estreno': str(pelicula.fecha_estreno),
            'duracion': pelicula.duracion,
            'link': pelicula.link,
            'portada': portada_uri
        }

        cursor.close()
        conn.close()
        return render_template('admin/EditPeli.html', pelicula=datos_pelicula, anime_ids=anime_ids)

    # POST - guardar cambios
    if request.method == 'POST':
        anime_id = request.form['anime_id']
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        fecha_estreno = request.form['fecha_estreno']
        duracion = request.form['duracion']
        link = request.form['link']
        portada = request.files['portada']

        try:
            if portada and portada.filename:
                portada_data = portada.read()
                cursor.execute('''
                    UPDATE pelicula SET anime_id=?, titulo=?, descripcion=?, fecha_estreno=?, duracion=?, link=?, portada=?
                    WHERE id=?
                ''', (anime_id, titulo, descripcion, fecha_estreno, duracion, link, portada_data, id))
            else:
                cursor.execute('''
                    UPDATE pelicula SET anime_id=?, titulo=?, descripcion=?, fecha_estreno=?, duracion=?, link=?
                    WHERE id=?
                ''', (anime_id, titulo, descripcion, fecha_estreno, duracion, link, id))

            conn.commit()
            mensaje = "Película actualizada correctamente."
        except Exception as e:
            print("Error al actualizar:", e)
            mensaje = "Hubo un error al actualizar la película."

        cursor.close()
        conn.close()
        return redirect(url_for('peliculas'))  # o puedes redirigir a /pelicula/id

@app.route('/EditAnime/<int:id>', methods=['GET', 'POST'])
def EditAnime(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'GET':
        cursor.execute('SELECT * FROM anime WHERE id = ?', (id,))
        anime = cursor.fetchone()

        if not anime:
            cursor.close()
            conn.close()
            return "Anime no encontrado", 404

        # Convertir a diccionario para acceder con nombres
        columns = [column[0] for column in cursor.description]
        anime = dict(zip(columns, anime))

        portada = base64.b64encode(anime['portada']).decode('utf-8') if anime['portada'] else None
        portada_uri = f"data:image/jpeg;base64,{portada}" if portada else "https://via.placeholder.com/200x300?text=No+Imagen"

        datos_anime = {
            'id': anime['id'],
            'titulo': anime['titulo'],
            'descripcion': anime['descripcion'],
            'genero': anime['genero'],
            'fecha_estreno': str(anime['fecha_estreno']),
            'estado': anime['estado'],
            'portada': portada_uri
        }

        cursor.close()
        conn.close()
        return render_template('admin/EditAnime.html', anime=datos_anime)

    # POST - Guardar cambios
    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        genero = request.form['genero']
        fecha_estreno = request.form['fecha_estreno']
        estado = request.form['estado']
        portada = request.files['portada']

        try:
            if portada and portada.filename:
                portada_data = portada.read()
                cursor.execute('''
                    UPDATE anime SET titulo=?, descripcion=?, genero=?, fecha_estreno=?, estado=?, portada=?
                    WHERE id=?
                ''', (titulo, descripcion, genero, fecha_estreno, estado, portada_data, id))
            else:
                cursor.execute('''
                    UPDATE anime SET titulo=?, descripcion=?, genero=?, fecha_estreno=?, estado=?
                    WHERE id=?
                ''', (titulo, descripcion, genero, fecha_estreno, estado, id))

            conn.commit()
            print("Anime actualizado correctamente.")
        except Exception as e:
            print("Error al actualizar:", e)

        cursor.close()
        conn.close()
        return redirect(url_for('peliculas'))  # o donde quieras redirigir

#Buscador
@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT a.id, a.titulo, a.descripcion, a.portada
        FROM Anime a
        JOIN temporada t ON a.id = t.anime_id
        WHERE YEAR(t.fecha_estreno) = 2024
    """)
    resultados = cursor.fetchall()

    animes2025 = []
    for fila in resultados:
        id_anime, titulo, descripcion, portada_bin = fila
        portada = (
            f"data:image/jpeg;base64,{base64.b64encode(portada_bin).decode('utf-8')}"
            if portada_bin else
            "https://via.placeholder.com/300x400?text=No+Imagen"
        )
        animes2025.append({
            'id': id_anime,
            'titulo': titulo,
            'descripcion': descripcion,
            'portada': portada
        })

    cursor.close()
    conn.close()

    return render_template('sitio/index.html', animes=animes2025)



@app.route('/api/buscar-animes')
def api_buscar_animes():
    titulo = request.args.get('titulo', '').strip()
    if not titulo:
        return jsonify([])

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        resultados = []

        # Buscar animes con portada de su PRIMERA temporada
        cursor.execute("""
            SELECT a.id, a.titulo, a.descripcion, t.portada, 'anime' AS tipo
            FROM Anime a
            JOIN temporada t ON a.id = t.anime_id
            WHERE a.titulo LIKE ?
            AND t.id = (
                SELECT TOP 1 t2.id FROM temporada t2 WHERE t2.anime_id = a.id ORDER BY t2.fecha_estreno
            )
        """, (f'%{titulo}%',))
        animes = cursor.fetchall()

        # Buscar películas (usando portada propia)
        cursor.execute("""
            SELECT p.id, p.titulo, p.descripcion, p.portada, 'pelicula' AS tipo
            FROM pelicula p
            WHERE p.titulo LIKE ?
        """, (f'%{titulo}%',))
        peliculas = cursor.fetchall()

        # Unificar resultados
        resultados = animes + peliculas

        data = []
        for fila in resultados:
            id_, titulo, descripcion, portada_bin, tipo = fila
            portada = (
                f"data:image/jpeg;base64,{base64.b64encode(portada_bin).decode('utf-8')}"
                if portada_bin else
                "https://via.placeholder.com/300x400?text=No+Imagen"
            )
            data.append({
                'id': id_,
                'titulo': titulo,
                'descripcion': descripcion,
                'portada': portada,
                'tipo': tipo
            })

        return jsonify(data)

    except Exception as e:
        print("❌ Error:", e)
        return jsonify({"error": "Error interno del servidor"}), 500

    finally:
        cursor.close()
        conn.close()


#ver captuloo
#ver captuloo
@app.route('/anime/<int:id>/ver_capitulos')
def ver_capitulos_anime(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Obtener anime
    cursor.execute('SELECT titulo, descripcion, portada FROM anime WHERE id = ?', (id,))
    anime_data = cursor.fetchone()

    if not anime_data:
        return "Anime no encontrado", 404

    titulo, descripcion, portada_bin = anime_data
    portada = (
        f"data:image/jpeg;base64,{base64.b64encode(portada_bin).decode('utf-8')}"
        if portada_bin else
        "https://via.placeholder.com/300x400?text=No+Imagen"
    )

    # Obtener temporadas y sus capítulos
    cursor.execute("SELECT id, titulo, portada FROM temporada WHERE anime_id = ? ORDER BY fecha_estreno", (id,))
    temporadas_raw = cursor.fetchall()

    temporadas = []
    for temp_id, temp_titulo, temp_portada_bin in temporadas_raw:
        temp_portada = (
            f"data:image/jpeg;base64,{base64.b64encode(temp_portada_bin).decode('utf-8')}"
            if temp_portada_bin else
            "https://via.placeholder.com/50x50?text=No+Imagen"
        )
        
        # Obtener capítulos para la temporada actual
        cursor.execute("""
            SELECT id, numero_capitulo, titulo, link
            FROM capitulo
            WHERE temporada_id = ?
            ORDER BY numero_capitulo
        """, (temp_id,))
        caps = cursor.fetchall()
        capitulos = [{
            'id': c[0],
            'numero': c[1],
            'titulo': c[2],
            'link': c[3]
        } for c in caps]

        temporadas.append({
            'id': temp_id,
            'titulo': temp_titulo,
            'portada': temp_portada,  # Añadir portada de temporada
            'capitulos': capitulos
        })

    cursor.close()
    conn.close()

    return render_template('sitio/ver_capitulos_anime.html', anime={
        'id': id,
        'titulo': titulo,
        'descripcion': descripcion,
        'portada': portada,
        'temporadas': temporadas
    })




#CREAR CAPITULO
@app.route('/admin/capitulo/nuevo', methods=['GET', 'POST'])
def crear_capitulo():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Obtener lista de temporadas con el nombre del anime
    cursor.execute("""
        SELECT t.id, a.titulo, t.titulo
        FROM temporada t
        JOIN Anime a ON t.anime_id = a.id
        ORDER BY a.titulo ASC, t.titulo ASC
    """)
    temporadas = cursor.fetchall()

    if request.method == 'POST':
        temporada_id = request.form['temporada_id']
        numero_capitulo = request.form['numero_capitulo']
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        fecha_emision = request.form['fecha_emision']
        duracion = request.form['duracion']
        link = request.form['link']

        cursor.execute("""
            INSERT INTO capitulo (temporada_id, numero_capitulo, titulo, descripcion, fecha_emision, duracion, link)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (temporada_id, numero_capitulo, titulo, descripcion, fecha_emision, duracion, link))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('crear_capitulo'))

    cursor.close()
    conn.close()
    return render_template('admin/crear_capitulo.html', temporadas=temporadas)

#EDITAR CAPITULO
@app.route('/admin/capitulo/editar/<int:id>', methods=['GET', 'POST'])
def editar_capitulo(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Obtener capítulo actual
    cursor.execute("SELECT * FROM capitulo WHERE id = ?", (id,))
    capitulo = cursor.fetchone()

    # Obtener temporadas para el select
    cursor.execute("""
        SELECT t.id, a.titulo, t.titulo
        FROM temporada t
        JOIN Anime a ON t.anime_id = a.id
        ORDER BY a.titulo ASC, t.titulo ASC
    """)
    temporadas = cursor.fetchall()

    if request.method == 'POST':
        temporada_id = request.form['temporada_id']
        numero_capitulo = request.form['numero_capitulo']
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        fecha_emision = request.form['fecha_emision']
        duracion = request.form['duracion']
        link = request.form['link']

        cursor.execute("""
            UPDATE capitulo
            SET temporada_id = ?, numero_capitulo = ?, titulo = ?, descripcion = ?, fecha_emision = ?, duracion = ?, link = ?
            WHERE id = ?
        """, (temporada_id, numero_capitulo, titulo, descripcion, fecha_emision, duracion, link, id))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('editar_capitulo', id=id))

    cursor.close()
    conn.close()
    return render_template('admin/editar_capitulo.html', capitulo=capitulo, temporadas=temporadas)

#CREAR TEMPORADA
@app.route('/admin/crear_temporada', methods=['GET', 'POST'])
def crear_temporada():
    if request.method == 'POST':
        # Lógica para crear temporada
        anime_id = request.form['anime_id']
        numero_temporada = request.form['numero_temporada']
        titulo = request.form['titulo']
        fecha_estreno = request.form['fecha_estreno']
        portada = request.files['portada']

        # Guardar los datos en la base de datos (suponiendo que tengas la lógica correcta para esto)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO temporada (anime_id, numero_temporada, titulo, fecha_estreno, portada)
            VALUES (?, ?, ?, ?, ?)
        ''', (anime_id, numero_temporada, titulo, fecha_estreno, portada.read()))
        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('ver_temporadas'))  # Redirige a la vista de lista de temporadas

    # Obtener la lista de animes para el formulario
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, titulo FROM Anime ORDER BY titulo ASC')
    animes = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('admin/crear_temporada.html', animes=animes)


#EDITAR TEMPORADA
@app.route('/admin/temporada/editar/<int:id>', methods=['GET', 'POST'])
def editar_temporada(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        anime_id = request.form['anime_id']
        numero_temporada = request.form['numero_temporada']
        titulo = request.form['titulo']
        fecha_estreno = request.form['fecha_estreno']

        portada_file = request.files['portada']
        if portada_file and portada_file.filename != '':
            portada_data = portada_file.read()
            cursor.execute('''
                UPDATE temporada
                SET anime_id = ?, numero_temporada = ?, titulo = ?, fecha_estreno = ?, portada = ?
                WHERE id = ?
            ''', (anime_id, numero_temporada, titulo, fecha_estreno, portada_data, id))
        else:
            cursor.execute('''
                UPDATE temporada
                SET anime_id = ?, numero_temporada = ?, titulo = ?, fecha_estreno = ?
                WHERE id = ?
            ''', (anime_id, numero_temporada, titulo, fecha_estreno, id))

        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('ver_temporadas'))

    # GET: datos de temporada
    cursor.execute('SELECT * FROM temporada WHERE id = ?', (id,))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        return "Temporada no encontrada", 404

    col_names = [col[0] for col in cursor.description]
    temporada = dict(zip(col_names, row))

    portada_uri = (
        f"data:image/jpeg;base64,{base64.b64encode(temporada['portada']).decode('utf-8')}"
        if temporada['portada'] else
        "https://via.placeholder.com/200x300?text=No+Imagen"
    )

    cursor.execute('SELECT id, titulo FROM Anime ORDER BY titulo')
    animes = cursor.fetchall()
    col_names = [col[0] for col in cursor.description]
    animes = [dict(zip(col_names, a)) for a in animes]

    cursor.close()
    conn.close()
    return render_template('admin/editar_temporada.html', temporada=temporada, animes=animes, portada_uri=portada_uri)

#VER TEMPORADAS
@app.route('/admin/temporadas', methods=['GET', 'POST'])
def ver_temporadas():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Obtener el término de búsqueda de la URL (si existe)
    search_term = request.args.get('search', '')

    # Si hay un término de búsqueda, filtrar por título de anime o temporada
    if search_term:
        query = '''
            SELECT t.id, t.numero_temporada, t.titulo AS titulo_temporada, 
                   t.fecha_estreno, t.portada, a.titulo AS titulo_anime
            FROM temporada t
            JOIN Anime a ON t.anime_id = a.id
            WHERE a.titulo LIKE ? OR t.titulo LIKE ?
            ORDER BY a.titulo, t.numero_temporada
        '''
        cursor.execute(query, (f'%{search_term}%', f'%{search_term}%'))
    else:
        # Si no hay búsqueda, simplemente traer todas las temporadas
        cursor.execute('''
            SELECT t.id, t.numero_temporada, t.titulo AS titulo_temporada, 
                   t.fecha_estreno, t.portada, a.titulo AS titulo_anime
            FROM temporada t
            JOIN Anime a ON t.anime_id = a.id
            ORDER BY a.titulo, t.numero_temporada
        ''')

    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]
    temporadas = []

    for row in rows:
        temp = dict(zip(columns, row))
        
        # Convertir la fecha a string en formato YYYY-MM-DD
        if temp['fecha_estreno']:
            temp['fecha_estreno_formateada'] = temp['fecha_estreno'].strftime('%Y-%m-%d')
        else:
            temp['fecha_estreno_formateada'] = "Fecha no disponible"
        
        if temp['portada']:
            portada_base64 = base64.b64encode(temp['portada']).decode('utf-8')
            temp['portada_uri'] = f"data:image/jpeg;base64,{portada_base64}"
        else:
            temp['portada_uri'] = "https://via.placeholder.com/150x200?text=No+Imagen"
        
        temporadas.append(temp)

    cursor.close()
    conn.close()

    return render_template('admin/lista_temporadas.html', temporadas=temporadas, search_term=search_term)



#login y usuarios

# Función para encriptar contraseñas
def encriptar_contraseña(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']

        # Encriptar contraseña ingresada
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id_usuario, tipo_perfil FROM Usuario WHERE usuario = ? AND contraseña = ?', (usuario, hashed_password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session['usuario_id'] = user[0]
            session['tipo_perfil'] = user[1]
            session['usuario'] = usuario
            return redirect(url_for('presentacion_admin'))  # Redirige a la página de inicio o donde quieras
        else:
            return "Credenciales incorrectas", 401

    return render_template('admin/login.html')  # tu formulario de login

# Ver lista de usuarios
@app.route('/usuarios')
def lista_usuarios():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_usuario, tipo_perfil, usuario FROM Usuario")
    usuarios = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin/usuarios.html', usuarios=usuarios)

# Editar usuario
@app.route('/usuarios/<int:id>/editar', methods=['GET', 'POST'])
def editar_usuario(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        tipo_perfil = request.form['tipo_perfil']
        usuario = request.form['usuario']
        nueva_contraseña = request.form['contraseña']

        if nueva_contraseña:
            contraseña_hash = encriptar_contraseña(nueva_contraseña)
            cursor.execute("""
                UPDATE Usuario SET tipo_perfil = ?, usuario = ?, contraseña = ?
                WHERE id_usuario = ?
            """, (tipo_perfil, usuario, contraseña_hash, id))
        else:
            cursor.execute("""
                UPDATE Usuario SET tipo_perfil = ?, usuario = ?
                WHERE id_usuario = ?
            """, (tipo_perfil, usuario, id))

        conn.commit()
        cursor.close()
        conn.close()
        flash("Usuario actualizado con éxito", "success")
        return redirect(url_for('lista_usuarios'))

    cursor.execute("SELECT id_usuario, tipo_perfil, usuario FROM Usuario WHERE id_usuario = ?", (id,))
    usuario_data = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('admin/editar_usuario.html', usuario=usuario_data)

@app.route('/admin/presentacion')
@login_required
def presentacion_admin():
    return render_template('admin/presentacion.html')

@app.route('/admin/capitulos', methods=['GET'])
def ver_capitulos():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Obtener parámetro de búsqueda (si existe)
    search_term = request.args.get('search', '')

    if search_term:
        cursor.execute('''
            SELECT c.id, c.numero_capitulo, c.titulo AS titulo_capitulo, c.descripcion,
                   c.fecha_emision, c.duracion, c.link,
                   t.titulo AS titulo_temporada, a.titulo AS titulo_anime
            FROM capitulo c
            JOIN temporada t ON c.temporada_id = t.id
            JOIN Anime a ON t.anime_id = a.id
            WHERE c.titulo LIKE ? OR t.titulo LIKE ? OR a.titulo LIKE ?
            ORDER BY a.titulo, t.titulo, c.numero_capitulo
        ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
    else:
        cursor.execute('''
            SELECT c.id, c.numero_capitulo, c.titulo AS titulo_capitulo, c.descripcion,
                   c.fecha_emision, c.duracion, c.link,
                   t.titulo AS titulo_temporada, a.titulo AS titulo_anime
            FROM capitulo c
            JOIN temporada t ON c.temporada_id = t.id
            JOIN Anime a ON t.anime_id = a.id
            ORDER BY a.titulo, t.titulo, c.numero_capitulo
        ''')

    # Obtener resultados
    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]

    capitulos = []
    for row in rows:
        cap = dict(zip(columns, row))

        # Formatear la fecha
        if cap['fecha_emision']:
            cap['fecha_emision'] = cap['fecha_emision'].strftime('%Y-%m-%d')
        else:
            cap['fecha_emision'] = 'Sin fecha'

        capitulos.append(cap)

    cursor.close()
    conn.close()

    return render_template('admin/lista_capitulos.html', capitulos=capitulos, search_term=search_term)

@app.route('/cerrar_sesion')
def cerrar_sesion():
    session.clear()  # Elimina todos los datos de la sesión
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('login'))  # Redirige al login (ajusta el nombre si tu vista tiene otro nombre)

if __name__ =='__main__':
    app.run(debug=True)
    