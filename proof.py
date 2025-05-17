import base64
from flask import request
from db import get_db_connection
from flask import Blueprint, render_template, redirect, url_for

def Obtener_Imagen_Portada():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Ejecutar la consulta con ID fijo = 1
        cursor.execute('SELECT imagen_presentacion FROM Anime WHERE id = 1')
        resultado = cursor.fetchone()

        portada_data_uri = None
        portada_base64 = None

        if resultado and resultado[0]:
            portada_bin = resultado[0]  # bytes de la imagen

            # Convertir bytes a base64
            portada_base64 = base64.b64encode(portada_bin).decode('utf-8')

            # Construir Data URI para <img>
            portada_data_uri = f"data:image/jpeg;base64,{portada_base64}"
        else:
            print("No se encontró la portada para ID=1.")

    except Exception as e:
        print(f"Error en la consulta SQL: {e}")

    cursor.close()
    conn.close()

    return render_template('admin/proof.html',
                           portada_text=portada_base64,
                           portada_img=portada_data_uri)