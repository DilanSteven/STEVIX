# anime.py
import base64
from flask import request
from db import get_db_connection 
from flask import Blueprint, render_template, request, redirect, url_for
#Obtener Listado de Animes
def obtener_animes():
    conn = get_db_connection()
    cursor = conn.cursor()

    search_term = request.args.get('search', '')

    if search_term:
        cursor.execute('''
            SELECT id, titulo, descripcion, genero, estado, fecha_estreno, portada
            FROM Anime
            WHERE titulo LIKE ? OR genero LIKE ?
            ORDER BY titulo ASC
        ''', (f'%{search_term}%', f'%{search_term}%'))
    else:
        cursor.execute('''
            SELECT id, titulo, descripcion, genero, estado, fecha_estreno, portada
            FROM Anime
            ORDER BY titulo ASC
        ''')

    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]
    animes = []

    for row in rows:
        anime = dict(zip(columns, row))

        # Imagen en base64
        if anime['portada']:
            portada_base64 = base64.b64encode(anime['portada']).decode('utf-8')
            anime['portada_uri'] = f"data:image/jpeg;base64,{portada_base64}"
        else:
            anime['portada_uri'] = "https://via.placeholder.com/150x200?text=Sin+Imagen"

        # Fecha
        if anime['fecha_estreno']:
            anime['fecha_estreno'] = anime['fecha_estreno'].strftime('%Y-%m-%d')
        else:
            anime['fecha_estreno'] = "Desconocida"

        animes.append(anime)

    cursor.close()
    conn.close()

    return animes, search_term

def crear_anime():
    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        genero = request.form['genero']
        fecha_estreno = request.form['fecha_estreno']
        estado = request.form['estado']
        portada = request.files['portada']
        imagen_presentacion = request.files['imagen_presentacion']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(''' 
            INSERT INTO Anime (titulo, descripcion, genero, fecha_estreno, estado, portada, imagen_presentacion) 
            VALUES (?, ?, ?, ?, ?, ?, ?) 
        ''', (
            titulo,
            descripcion,
            genero,
            fecha_estreno,
            estado,
            portada.read() if portada else None,
            imagen_presentacion.read() if imagen_presentacion else None
        ))
        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('ver_animes'))

    return render_template('admin/crear_anime.html')

def editar_anime(anime_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Manejo de método POST para actualización de los datos
    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        genero = request.form['genero']
        fecha_estreno = request.form['fecha_estreno']
        estado = request.form['estado']
        portada = request.files['portada']
        imagen_presentacion = request.files['imagen_presentacion']

        # Si se sube una portada nueva
        if portada and portada.filename:
            portada_data = portada.read()
        else:
            portada_data = None

        # Si se sube una imagen de presentación nueva
        if imagen_presentacion and imagen_presentacion.filename:
            imagen_presentacion_data = imagen_presentacion.read()
        else:
            imagen_presentacion_data = None

        # Realizar la actualización con los nuevos datos
        cursor.execute('''
            UPDATE Anime SET titulo=?, descripcion=?, genero=?, fecha_estreno=?, estado=?, portada=?, imagen_presentacion=? 
            WHERE id=?
        ''', (
            titulo, descripcion, genero, fecha_estreno, estado,
            portada_data,
            imagen_presentacion_data,
            anime_id
        ))

        conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for('ver_animes'))

    # Manejo de método GET para obtener los datos del anime a editar
    cursor.execute('SELECT * FROM Anime WHERE id = ?', (anime_id,))
    row = cursor.fetchone()

    if not row:
        cursor.close()
        conn.close()
        return "Anime no encontrado", 404

    # Obtener los nombres de las columnas para convertir la fila en un diccionario
    col_names = [col[0] for col in cursor.description]
    temporada = dict(zip(col_names, row))

    # Preparar la URI para la portada, en caso de que no haya, se asigna una imagen predeterminada
    portada_uri = (
        f"data:image/jpeg;base64,{base64.b64encode(temporada['portada']).decode('utf-8')}"
        if temporada['portada'] else
        "https://via.placeholder.com/200x300?text=No+Imagen"
    )

    # Obtener lista de animes
    cursor.execute('SELECT id, titulo FROM Anime ORDER BY titulo')
    animes = cursor.fetchall()
    col_names = [col[0] for col in cursor.description]
    animes = [dict(zip(col_names, a)) for a in animes]

    cursor.close()
    conn.close()

    return render_template('admin/editar_anime.html', temporada=temporada, animes=animes, portada_uri=portada_uri)
