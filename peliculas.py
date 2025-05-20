from conexion import get_db_connection
from flask import request,redirect,render_template,url_for,flash
import base64

#LISTADO DE PELICULAS
def listado_peliculas():
    conn = get_db_connection()
    cursor = conn.cursor()

    search_term = request.args.get('search', '')

    if search_term:
        cursor.execute('''
            SELECT id, titulo, descripcion, fecha_estreno, duracion, portada, link
            FROM Pelicula
            WHERE titulo ILIKE %s 
            ORDER BY titulo ASC
        ''', (f'%{search_term}%',))
    else:
        cursor.execute('''
            SELECT id, titulo, descripcion, fecha_estreno, duracion, portada, link
            FROM Pelicula
            ORDER BY titulo ASC
        ''')

    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]
    peliculas = []

    for row in rows:
        pelicula = dict(zip(columns, row))

        if pelicula['portada']:
            portada_base64 = base64.b64encode(pelicula['portada']).decode('utf-8')
            pelicula['portada_uri'] = f"data:image/jpeg;base64,{portada_base64}"
        else:
            pelicula['portada_uri'] = "https://via.placeholder.com/150x200?text=Sin+Imagen"

        if pelicula['fecha_estreno']:
            pelicula['fecha_estreno'] = pelicula['fecha_estreno'].strftime('%Y-%m-%d')
        else:
            pelicula['fecha_estreno'] = "Desconocida"

        peliculas.append(pelicula)

    cursor.close()
    conn.close()

    return peliculas, search_term 

#CREAR PELICULA

def crear_pelicula():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        fecha_estreno = request.form['fecha_estreno']
        duracion = request.form['duracion']
        link = request.form['link']
        anime_id = request.form.get('anime_id')
        portada = request.files['portada'].read() if 'portada' in request.files else None

        cursor.execute('''
            INSERT INTO Pelicula (titulo, descripcion, fecha_estreno, duracion, link, portada, anime_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (titulo, descripcion, fecha_estreno or None, duracion, link, portada, anime_id))

        conn.commit()
        cursor.close()
        conn.close()
        flash("Película creada exitosamente", "success")
        return redirect(url_for('ver_peliculas'))

    # Obtener lista de animes para el boxlista
    cursor.execute('SELECT id, titulo FROM Anime ORDER BY titulo ASC')
    animes = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('admin/crear_pelicula.html', animes=animes)
    

#EDITAR PELICULA
def editar_pelicula(pelicula_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        # Leer datos del formulario
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        fecha_estreno = request.form['fecha_estreno']
        duracion = request.form['duracion']
        link = request.form['link']
        anime_id = request.form['anime_id']
        portada_file = request.files.get('portada')

        # Leer archivo portada si se subió
        portada = portada_file.read() if portada_file and portada_file.filename else None

        # Actualizar en la base
        if portada:
            cursor.execute('''
                UPDATE Pelicula
                SET titulo=%s, descripcion=%s, fecha_estreno=%s, duracion=%s, portada=%s, link=%s, anime_id=%s
                WHERE id=%s
            ''', (titulo, descripcion, fecha_estreno, duracion, portada, link, anime_id, pelicula_id))
        else:
            cursor.execute('''
                UPDATE Pelicula
                SET titulo=%s, descripcion=%s, fecha_estreno=%s, duracion=%s, link=%s, anime_id=%s
                WHERE id=%s
            ''', (titulo, descripcion, fecha_estreno, duracion, link, anime_id, pelicula_id))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('ver_peliculas'))

    # Si es GET, obtener datos actuales de la película
    cursor.execute("SELECT * FROM Pelicula WHERE id = %s", (pelicula_id,))
    fila = cursor.fetchone()
    if not fila:
        cursor.close()
        conn.close()
        return "Película no encontrada", 404

    # Convertir fila a diccionario con nombres de columnas
    columnas = [desc[0] for desc in cursor.description]
    pelicula = dict(zip(columnas, fila))

    # Codificar portada para mostrarla (si tiene)
    if pelicula['portada']:
        portada_base64 = base64.b64encode(pelicula['portada']).decode('utf-8')
        pelicula['portada_uri'] = f"data:image/jpeg;base64,{portada_base64}"
    else:
        pelicula['portada_uri'] = None

    # Obtener lista de animes para el select
    cursor.execute("SELECT id, titulo FROM Anime ORDER BY titulo ASC")
    animes = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('admin/editar_pelicula.html', pelicula=pelicula, animes=animes)