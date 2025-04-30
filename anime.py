# anime.py
import base64
from flask import request
from db import get_db_connection 
from flask import Blueprint, render_template, request, redirect, url_for
# Obtener Listado de Animes
def obtener_animes():
    conn = get_db_connection()
    cursor = conn.cursor()

    search_term = request.args.get('search', '')

    if search_term:
        cursor.execute('''
            SELECT id, titulo, descripcion, genero, estado, fecha_estreno, portada
            FROM Anime
            WHERE titulo ILIKE %s OR genero ILIKE %s
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


# Crear Anime
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
            VALUES (%s, %s, %s, %s, %s, %s, %s)
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


# Editar Anime
def editar_anime(anime_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        genero = request.form['genero']
        fecha_estreno = request.form['fecha_estreno']
        estado = request.form['estado']
        portada = request.files['portada']
        imagen_presentacion = request.files['imagen_presentacion']

        portada_data = portada.read() if portada and portada.filename else None
        imagen_presentacion_data = imagen_presentacion.read() if imagen_presentacion and imagen_presentacion.filename else None

        cursor.execute('''
            UPDATE Anime 
            SET titulo = %s, descripcion = %s, genero = %s, fecha_estreno = %s, estado = %s, portada = %s, imagen_presentacion = %s 
            WHERE id = %s
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

    # Método GET
    cursor.execute('SELECT * FROM Anime WHERE id = %s', (anime_id,))
    row = cursor.fetchone()

    if not row:
        cursor.close()
        conn.close()
        return "Anime no encontrado", 404

    col_names = [col[0] for col in cursor.description]
    temporada = dict(zip(col_names, row))

    portada_uri = (
        f"data:image/jpeg;base64,{base64.b64encode(temporada['portada']).decode('utf-8')}"
        if temporada['portada'] else
        "https://via.placeholder.com/200x300?text=No+Imagen"
    )

    cursor.execute('SELECT id, titulo FROM Anime ORDER BY titulo')
    animes_raw = cursor.fetchall()
    col_names = [col[0] for col in cursor.description]
    animes = [dict(zip(col_names, a)) for a in animes_raw]

    cursor.close()
    conn.close()

    return render_template('admin/editar_anime.html', temporada=temporada, animes=animes, portada_uri=portada_uri)
