import pytest
from app import app, init_db

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client

def test_pagina_inicio(client):
    """Verifica que la página principal cargue correctamente."""
    respuesta = client.get("/")
    assert respuesta.status_code == 200
    assert b"NASA EARTH GUARDIAN" in respuesta.data

def test_registro_y_login(client):
    """Prueba el registro de un usuario y su posterior inicio de sesión."""
    # 1. Registrar nuevo usuario
    res_registro = client.post("/registro", data={
        "nombre": "Usuario Prueba",
        "correo": "prueba@nasa.com",
        "password": "password123",
        "rol": "admin"
    }, follow_redirects=True)
    assert res_registro.status_code == 200

    # 2. Iniciar sesión con ese usuario
    res_login = client.post("/login", data={
        "correo": "prueba@nasa.com",
        "password": "password123"
    }, follow_redirects=True)
    assert res_login.status_code == 200
    assert b"Panel de Monitoreo Ambiental" in res_login.data

def test_crear_alerta_crud(client):
    """Prueba la creación de una alerta ambiental en SQLite."""
    # Iniciar sesión primero con el admin por defecto
    client.post("/login", data={
        "correo": "admin@nasa.com",
        "password": "admin1234"
    })

    # Crear alerta
    res_crear = client.post("/crear_alerta", data={
        "titulo": "Alerta de Prueba Automatizada",
        "ubicacion": "Zona Norte",
        "categoria": "Incendio Forestal",
        "gravedad": "Alta",
        "descripcion": "Prueba con pytest"
    }, follow_redirects=True)

    assert res_crear.status_code == 200
    assert b"Alerta de Prueba Automatizada" in res_crear.data
