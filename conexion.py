# conexion.py
import psycopg2

import psycopg2
import os

# Puedes controlar esto con una variable de entorno, por defecto usará "render"
MODO = os.getenv("MODO_BD", "render")  # valores posibles: "render" o "local"

def get_db_connection():
    if MODO == "local":
        # CONEXIÓN LOCAL
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='mi_base_local',    # cambia por tu nombre de base local
            user='postgres',             # tu usuario local de PostgreSQL
            password='1234'              # tu contraseña local
        )
    else:
        # CONEXIÓN RENDER
        conn = psycopg2.connect(
            host='dpg-d08n0s95pdvs739mi980-a.oregon-postgres.render.com',
            port=5432,
            database='stevix',
            user='stevix',
            password='eCiIdjZOFn3M2h4vcabGY5DJa607Lbl0'
        
        )
        print("Conexion render")
    return conn