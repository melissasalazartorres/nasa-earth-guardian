import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "nasa_earth_guardian_clave_secreta"
DB_NAME = "guardian.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            correo TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT NOT NULL DEFAULT 'usuario'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            ubicacion TEXT NOT NULL,
            categoria TEXT NOT NULL,
            gravedad TEXT NOT NULL,
            descripcion TEXT
        )
    ''')
    
    # Crear usuario Admin por defecto si no existe
    cursor.execute("SELECT * FROM usuarios WHERE correo = ?", ("admin@nasa.com",))
    if not cursor.fetchone():
        clave_admin = generate_password_hash("admin1234")
        cursor.execute(
            "INSERT INTO usuarios (nombre, correo, password, rol) VALUES (?, ?, ?, ?)",
            ("Administrador NASA", "admin@nasa.com", clave_admin, "admin")
        )
    
    # Crear alerta de ejemplo si la tabla está vacía
    cursor.execute("SELECT COUNT(*) FROM alertas")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO alertas (titulo, ubicacion, categoria, gravedad, descripcion) VALUES (?, ?, ?, ?, ?)",
            ("Foco de calor detectado", "Reserva Natural Sur", "Incendio Forestal", "Alta", "Monitoreo satelital activo")
        )
    
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def index():
    conn = get_db()
    total_alertas = conn.execute("SELECT COUNT(*) FROM alertas").fetchone()[0]
    total_usuarios = conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
    total_criticas = conn.execute("SELECT COUNT(*) FROM alertas WHERE gravedad = 'Alta'").fetchone()[0]
    conn.close()
    
    return render_template(
        "index.html",
        total_alertas=total_alertas,
        total_usuarios=total_usuarios,
        total_criticas=total_criticas
    )

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        correo = request.form.get("correo")
        password = request.form.get("password")
        rol = request.form.get("rol", "usuario")

        conn = get_db()
        try:
            clave_segura = generate_password_hash(password)
            conn.execute(
                "INSERT INTO usuarios (nombre, correo, password, rol) VALUES (?, ?, ?, ?)",
                (nombre, correo, clave_segura, rol)
            )
            conn.commit()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Este correo ya está registrado.")
            return redirect(url_for("registro"))
        finally:
            conn.close()

    return render_template("registro")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form.get("correo")
        password = request.form.get("password")

        conn = get_db()
        usuario = conn.execute("SELECT * FROM usuarios WHERE correo = ?", (correo,)).fetchone()
        conn.close()

        if usuario and check_password_hash(usuario["password"], password):
            session["usuario_id"] = usuario["id"]
            session["usuario_nombre"] = usuario["nombre"]
            session["usuario_rol"] = usuario["rol"]
            return redirect(url_for("dashboard"))

        flash("Correo o contraseña incorrectos.")
        return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/dashboard")
def dashboard():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    alertas = conn.execute("SELECT * FROM alertas ORDER BY id DESC").fetchall()
    total_criticas = conn.execute("SELECT COUNT(*) FROM alertas WHERE gravedad = 'Alta'").fetchone()[0]
    conn.close()

    return render_template(
        "dashboard.html",
        alertas=alertas,
        total_criticas=total_criticas
    )

@app.route("/crear_alerta", methods=["POST"])
def crear_alerta():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    titulo = request.form.get("titulo")
    ubicacion = request.form.get("ubicacion")
    categoria = request.form.get("categoria")
    gravedad = request.form.get("gravedad")
    descripcion = request.form.get("descripcion")

    conn = get_db()
    conn.execute(
        "INSERT INTO alertas (titulo, ubicacion, categoria, gravedad, descripcion) VALUES (?, ?, ?, ?, ?)",
        (titulo, ubicacion, categoria, gravedad, descripcion)
    )
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))

@app.route("/editar_alerta/<int:id>", methods=["GET", "POST"])
def editar_alerta(id):
    if "usuario_id" not in session:
        return redirect(url_for("login"))
    
    if session.get("usuario_rol") != "admin":
        flash("Solo los administradores pueden editar alertas.")
        return redirect(url_for("dashboard"))

    conn = get_db()
    if request.method == "POST":
        titulo = request.form.get("titulo")
        ubicacion = request.form.get("ubicacion")
        categoria = request.form.get("categoria")
        gravedad = request.form.get("gravedad")
        descripcion = request.form.get("descripcion")

        conn.execute('''
            UPDATE alertas 
            SET titulo = ?, ubicacion = ?, categoria = ?, gravedad = ?, descripcion = ?
            WHERE id = ?
        ''', (titulo, ubicacion, categoria, gravedad, descripcion, id))
        conn.commit()
        conn.close()
        return redirect(url_for("dashboard"))

    alerta = conn.execute("SELECT * FROM alertas WHERE id = ?", (id,)).fetchone()
    conn.close()
    
    if not alerta:
        return redirect(url_for("dashboard"))
        
    return render_template("editar_alerta.html", alerta=alerta)

@app.route("/eliminar_alerta/<int:id>")
def eliminar_alerta(id):
    if "usuario_id" not in session:
        return redirect(url_for("login"))
        
    if session.get("usuario_rol") != "admin":
        flash("Solo los administradores pueden eliminar alertas.")
        return redirect(url_for("dashboard"))

    conn = get_db()
    conn.execute("DELETE FROM alertas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True)
