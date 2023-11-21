from flask import Flask, render_template, request, url_for, flash, redirect, send_file,session, make_response,send_from_directory
from models import db
from flask_sqlalchemy import SQLAlchemy
from flask_mysqldb import MySQL
import binascii
import requests
from flask_session import Session
from flask import flash
from reportlab.pdfgen import canvas
from io import BytesIO
from openpyxl import Workbook
from reportlab.lib.pagesizes import letter
import pandas as pd
from werkzeug.utils import secure_filename
import os
import plotly.express as px
from binascii import hexlify
import smtplib
from email.mime.text import MIMEText
from reportlab.lib import utils
from flask_restful import Resource, Api

def hexlify_filter(value):
    if value is not None and len(value) % 2 == 0:
        try:
            return binascii.unhexlify(value)
        except binascii.Error:
            pass  
    return b''  
 
app = Flask(__name__)
api = Api(app)

app.config['SECRET_KEY'] = 'j\x86\x14\xcc:\x99\xb3\x91\xf8/Bv\r\xaa"\xf1\x8a\xfa(A\xa1\xe2\x85\xd6'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:041002@localhost/parnetdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_TYPE'] = 'filesystem' 
Session(app)
#API
# Clase para la ruta de productos privados
class ProductosPrivadoResource(Resource):
    def get(self):
        cur = mysql.connection.cursor()
        cur.execute("SELECT producto.id_producto, producto.nombre_producto, producto.descripcion_producto, producto.precio, producto.imagen_path, producto.estatus, tipoProducto.tipoProducto FROM producto JOIN tipoProducto ON producto.id_tipo = tipoProducto.id_tipo")
        productos = cur.fetchall()
        cur.close()
        return {'productos': productos}

    def post(self):
        termino_busqueda = request.form['termino_busqueda']
        cur = mysql.connection.cursor()
        cur.execute("SELECT producto.id_producto, producto.nombre_producto, producto.descripcion_producto, producto.precio, producto.imagen_path, producto.estatus, tipoProducto.tipoProducto FROM producto JOIN tipoProducto ON producto.id_tipo = tipoProducto.id_tipo WHERE producto.nombre_producto LIKE %s", ('%' + termino_busqueda + '%',))
        productos = cur.fetchall()
        cur.close()
        return {'productos': productos, 'termino_busqueda': termino_busqueda}


api.add_resource(ProductosPrivadoResource, '/vista_json')
class ConfigManager:
    _instance = None
 
    def __new__(cls, app=None):
        if not cls._instance:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            if app:
                cls._instance.init_app(app)
        return cls._instance
 
    def init_app(self, app):
       
        app.config['MYSQL_HOST'] = 'localhost'
        app.config['MYSQL_USER'] = 'root'
        app.config['MYSQL_PASSWORD'] = 'root123'
        app.config['MYSQL_DB'] = 'parnet'

mysql = ConfigManager(app)
app.config['RECAPTCHA_PUBLIC_KEY'] = '6LdWRxIpAAAAAAPreoOlEMvlK3AzTpfEhrmmBdJh'
app.config['RECAPTCHA_SECRET_KEY'] = '6LdWRxIpAAAAAEr84Vu-zTfndo0yqew9qvNAFoVT'
 
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MYSQL_CURSORCLASS'] = 'DictCursor' 
 
 
mysql = MySQL(app)
db = SQLAlchemy(app)
indice_del_campo_id = 0
 
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
 
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/Quienes_Somos")
def quieness():
    return render_template("quieness.html")

@app.route("/Clientes")
def clientes():
    return render_template("clientes.html")

@app.route('/Servicios', methods=['GET', 'POST'])
def servicios():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_servicio, tipoServicio FROM catalogoServicios")
    catalogo_servicios = cur.fetchall()
    cur.close()

    if request.method == 'POST':
        nombre_servicio = request.form['nombre_servicio']
        descripcion = request.form['descripcion']
        id_servicio_str = request.form['id_servicio']
        correo = request.form['correo']

        if id_servicio_str:
            try:
                id_servicio = int(id_servicio_str)
            except ValueError:
                flash('Error: El tipo de servicio no es un número válido.', 'error')
                return redirect(url_for('servicios'))
        else:
            flash('Error: Debes seleccionar un tipo de servicio.', 'error')
            return redirect(url_for('servicios'))


        flash('Servicio procesado correctamente.', 'success')
        return redirect(url_for('servicios'))
    
    return render_template('servicios.html', catalogo_servicios=catalogo_servicios)

@app.route('/procesar_servicio', methods=['POST'])
def procesar_servicio():
    if request.method == 'POST':
        recaptcha_token = request.form.get('g-recaptcha-response')
        if not recaptcha_token:
            flash('Error: Completa el reCAPTCHA.', 'error')
            return redirect(url_for('servicios'))

        nombre_servicio = request.form['nombre_servicio']
        descripcion = request.form['descripcion']
        id_servicio_str = request.form['id_servicio']
        correo = request.form['correo']

        if id_servicio_str:
            try:
                id_servicio = int(id_servicio_str)
            except ValueError:
                flash('Error: El tipo de servicio no es un número válido.', 'error')
                return redirect(url_for('servicios'))
        else:
            flash('Error: Debes seleccionar un tipo de servicio.', 'error')
            return redirect(url_for('servicios'))

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO servicio (nombre_servicio, descripcion, id_servicio, correo) VALUES (%s, %s, %s, %s)",
                    (nombre_servicio, descripcion, id_servicio, correo))
        mysql.connection.commit()
        cur.close()

        flash('Servicio registrado exitosamente.', 'success')

    return redirect(url_for('servicios'))

@app.route('/productos_privado', methods=['GET', 'POST'])
def productos_privado():
    if request.method == 'POST':
        # Obtén el término de búsqueda desde el formulario
        termino_busqueda = request.form['termino_busqueda']
        
        # Realiza la búsqueda en la base de datos
        cur = mysql.connection.cursor()
        # Ajusta la consulta SQL para buscar productos que coincidan con el término de búsqueda
        cur.execute("SELECT producto.id_producto, producto.nombre_producto, producto.descripcion_producto, producto.precio, producto.imagen_path, producto.estatus, tipoProducto.tipoProducto FROM producto JOIN tipoProducto ON producto.id_tipo = tipoProducto.id_tipo WHERE producto.nombre_producto LIKE %s", ('%' + termino_busqueda + '%',))
        productos = cur.fetchall()
        cur.close()

        # Renderiza la plantilla y pasa los productos como contexto
        return render_template('productos_privado.html', productos=productos, termino_busqueda=termino_busqueda)

    # Si no es una solicitud POST, simplemente muestra todos los productos
    cur = mysql.connection.cursor()
    cur.execute("SELECT producto.id_producto, producto.nombre_producto, producto.descripcion_producto, producto.precio, producto.imagen_path, producto.estatus, tipoProducto.tipoProducto FROM producto JOIN tipoProducto ON producto.id_tipo = tipoProducto.id_tipo")
    productos = cur.fetchall()
    cur.close()

    # Renderiza la plantilla y pasa los productos como contexto
    return render_template('productos_privado.html', productos=productos)



@app.route('/agregar_producto', methods=['GET', 'POST'])
def agregar_producto():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM tipoProducto")
    tipos_productos = cur.fetchall()
    cur.close()

    if request.method == 'POST':
        nombre_producto = request.form['nombre']
        descripcion_producto = request.form['descripcion']
        precio = request.form['precio']
        imagen = request.files['imagen']
        estatus = request.form['estatus']
        id_tipo = request.form['id_tipo']

     
        if imagen and allowed_file(imagen.filename):
            filename = secure_filename(imagen.filename)
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO producto (nombre_producto, descripcion_producto, precio, estatus, id_tipo, imagen_path) VALUES (%s, %s, %s, %s, %s, %s)',
                                    (nombre_producto, descripcion_producto, precio, estatus, id_tipo, f'/static/uploads/{filename}'))

        imagen.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        mysql.connection.commit()
        cur.close()

        flash('Producto agregado correctamente.', 'success')
        return redirect(url_for('productos_privado'))

    return render_template('agregar_productos.html', tipos_productos=tipos_productos)


@app.route('/editar_producto/<int:id_producto>', methods=['GET', 'POST'])
def editar_producto(id_producto):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM tipoProducto")
    tipos_productos = cur.fetchall()
    cur.close()

    if request.method == 'POST':
        nombre_producto = request.form['nombre']
        descripcion_producto = request.form['descripcion']
        precio = request.form['precio']
        estatus = request.form['estatus']
        id_tipo = request.form['id_tipo']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM producto WHERE id_producto = %s", (id_producto,))
        producto = cur.fetchone()
        cur.close()

        nueva_imagen = request.files['imagen']
        if nueva_imagen and allowed_file(nueva_imagen.filename):
            filename = secure_filename(nueva_imagen.filename)
            cur = mysql.connection.cursor()
            cur.execute("UPDATE producto SET nombre_producto = %s, descripcion_producto = %s, precio = %s, estatus = %s, id_tipo = %s, imagen_path = %s WHERE id_producto = %s",
                        (nombre_producto, descripcion_producto, precio, estatus, id_tipo, f'/static/uploads/{filename}', id_producto))
            nueva_imagen.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            mysql.connection.commit()
            cur.close()
        else:
            cur = mysql.connection.cursor()
            cur.execute("UPDATE producto SET nombre_producto = %s, descripcion_producto = %s, precio = %s, estatus = %s, id_tipo = %s WHERE id_producto = %s",
                        (nombre_producto, descripcion_producto, precio, estatus, id_tipo, id_producto))
            mysql.connection.commit()
            cur.close()

        flash('Producto actualizado correctamente.', 'success')
        return redirect(url_for('productos_privado'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM producto WHERE id_producto = %s", (id_producto,))
    producto = cur.fetchone()
    cur.close()

    return render_template('editar_producto.html', producto=producto, tipos_productos=tipos_productos)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/eliminar_producto/<int:id_producto>', methods=['GET', 'POST'])
def eliminar_producto(id_producto):
    # Eliminar el producto de la base de datos
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM producto WHERE id_producto = %s", (id_producto,))
    mysql.connection.commit()
    cur.close()

    flash('Producto eliminado correctamente.', 'success')
    return redirect(url_for('productos_privado'))   
@app.route('/exportar_reporte_productos', methods=['GET', 'POST'])
def exportar_reporte_productos():
    cur = mysql.connection.cursor()
    cur.execute("SELECT nombre_producto, estatus FROM producto")
    productos = cur.fetchall()
    cur.close()

    buffer = BytesIO()
    p = canvas.Canvas(buffer)

    y_encabezados = 780  
    y_datos = 760       
    text_size = 8       
    espacio_entre_columnas = 10  
    encabezados = ['Nombre','Estatus']
    x = 100

    p.setFont("Helvetica", text_size + 2)

    for encabezado in encabezados:
        p.drawString(x, y_encabezados, encabezado)
        x += 150 + espacio_entre_columnas  
    x = 100  

    p.setFont("Helvetica", text_size)

    for producto in productos:
        y_datos -= 10  
        p.drawString(x, y_datos, producto['nombre_producto'])
        
        x += 200 + espacio_entre_columnas 
        p.drawString(x, y_datos, producto['estatus'])
        x += 150 + espacio_entre_columnas  
        x = 100 

    p.save()

    buffer.seek(0)
    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=reporte_productos.pdf'
    return response


@app.route('/Sugerencias', methods=['GET', 'POST'])
def sugerencias():
    confirmacion = None  

    if request.method == 'POST':
        sugerencia = request.form['sugerencia']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO sugerencias (mensaje) VALUES (%s)", (sugerencia,))
        mysql.connection.commit()
        cur.close()

        confirmacion = "Gracias por tu sugerencia."

    return render_template('sugerencias.html', confirmacion=confirmacion)
from flask import render_template

@app.route('/ver_sugerencias')
def ver_sugerencias():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM sugerencias")
    sugerencias = cur.fetchall()
    cur.close()

    print(sugerencias)  
    return render_template('ver_sugerencias.html', sugerencias=sugerencias)
@app.route('/exportar_pdf', methods=['POST'])
def exportar_pdf():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM sugerencias")
    sugerencias = cur.fetchall()
    cur.close()
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.drawString(100, 800, "Sugerencias Registradas")  

    y = 780  
    for sugerencia in sugerencias:
        y -= 12
        p.drawString(100, y, f"ID: {sugerencia['id_sugerencia']}, Mensaje: {sugerencia['mensaje']}")

    p.save()

    buffer.seek(0)

    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=sugerencias.pdf'
    return response

@app.route("/descargar_pdf/<int:producto_id>")
def descargar_pdf(producto_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM producto WHERE id_producto = %s", (producto_id,))
    producto = cur.fetchone()

    if not producto:
        return "Producto no encontrado", 404

    cur.execute("SELECT tipoProducto FROM tipoProducto WHERE id_tipo = %s", (producto['id_tipo'],))
    tipo_producto = cur.fetchone()

    cur.close()

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    text_x = 100
    text_y = 800
    text_size = 12 

 
    image_x = 100
    image_y = text_y - 150  
    image_width = 200
    image_height = 200

    p.setFont("Helvetica", text_size)

    p.drawString(text_x, text_y, "Información del Producto:")
    text_y -= 20
    p.drawString(text_x, text_y, "ID: {}".format(producto['id_producto']))
    text_y -= 20
    p.drawString(text_x, text_y, "Nombre: {}".format(producto['nombre_producto']))
    text_y -= 20
    p.drawString(text_x, text_y, "Descripción: {}".format(producto['descripcion_producto']))
    text_y -= 20
    p.drawString(text_x, text_y, "Precio: {}".format(producto['precio']))
    text_y -= 20
    p.drawString(text_x, text_y, "Estatus: {}".format(producto['estatus']))

    if tipo_producto:
        text_y -= 20
        p.drawString(text_x, text_y, "Tipo de Producto: {}".format(tipo_producto['tipoProducto']))
    else:
        text_y -= 20
        p.drawString(text_x, text_y, "Tipo de Producto no encontrado")

    if producto['imagen_path']:
        text_y -= 20  
        image_path = "static" + producto['imagen_path'][7:]
        image_reader = utils.ImageReader(image_path)
        
        p.drawImage(image_reader, image_x, image_y - image_height, width=image_width, height=image_height)

    p.save()

    buffer.seek(0)

    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=producto_{}.pdf'.format(producto_id)

    return response
@app.route('/exportar_excel', methods=['POST'])
def exportar_excel():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM sugerencias")
    sugerencias = cur.fetchall()
    cur.close()

    wb = Workbook()
    ws = wb.active

    ws.append(['ID', 'Mensaje'])

    for sugerencia in sugerencias:
        ws.append([sugerencia['id_sugerencia'], sugerencia['mensaje']])

    output = BytesIO()

    wb.save(output)

    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = 'attachment; filename=sugerencias.xlsx'

    return response


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        input_usuario = request.form['usuario']
        input_mail = request.form['mail']
        input_contraseña = request.form['contraseña']
        input_recaptcha = request.form['g-recaptcha-response']
 
       
        recaptcha_url = 'https://www.google.com/recaptcha/api/siteverify'
        recaptcha_secret_key = '6LdWRxIpAAAAAEr84Vu-zTfndo0yqew9qvNAFoVT'
        recaptcha_data = {
            'secret': recaptcha_secret_key,
            'response': input_recaptcha
        }
        recaptcha_response = requests.post(recaptcha_url, data=recaptcha_data)
        recaptcha_result = recaptcha_response.json()
 
        if recaptcha_result['success']:
           
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM administrador WHERE usuario = %s AND mail = %s AND contraseña = %s",
                        (input_usuario, input_mail, input_contraseña))
            usuario_db = cur.fetchone()
            cur.close()
 
            if usuario_db:
                flash('Inicio de sesión exitoso', 'success')
               
                session['usuario'] = usuario_db['usuario']
               
                return redirect(url_for('vista'))
            else:
                flash('Nombre de usuario, correo electrónico o contraseña incorrectos', 'error')
        else:
            flash('Validación reCAPTCHA fallida', 'error')
 
    return render_template('login.html')
@app.route('/vista')
def vista():
    if 'usuario' in session:
        return render_template('vista.html')
    else:
        flash('Debes iniciar sesión para acceder a esta página', 'error')
        return redirect(url_for('login'))
@app.route('/Contacto', methods=['GET', 'POST'])
def contacto():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        mensaje = request.form['mensaje']
 
        enviar_correo_contacto(nombre, correo, mensaje)
 
        return render_template('gracias.html', nombre=nombre)
 
    return render_template('contactos.html')
 
def enviar_correo_contacto(nombre, correo, mensaje):
    servidor_smtp = 'smtp.gmail.com'
    puerto_smtp = 587
    usuario_smtp = 'contactoparnetmx@gmail.com'
    contraseña_smtp = 'xsiu yvnt ehgk aenw'
 
    asunto = 'PARNET'
    cuerpo = f'Hola {nombre},\n\nHemos recibido su mensaje de contacto:\n\n{mensaje}'
 
    mensaje = MIMEText(cuerpo)
    mensaje['Subject'] = asunto
    mensaje['From'] = usuario_smtp
    mensaje['To'] = correo
 
    try:
        with smtplib.SMTP(servidor_smtp, puerto_smtp) as servidor:
            servidor.starttls()
            servidor.login(usuario_smtp, contraseña_smtp)
            servidor.sendmail(usuario_smtp, [correo], mensaje.as_string())
    except Exception as e:
        print(f"Error al enviar el correo de contacto: {e}")
@app.route("/productos", methods=['GET', 'POST'])
def productos():
    if request.method == 'POST':
        termino_busqueda = request.form['termino_busqueda']
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT producto.id_producto, producto.nombre_producto, producto.descripcion_producto, producto.precio, producto.imagen_path, producto.estatus, tipoProducto.tipoProducto FROM producto JOIN tipoProducto ON producto.id_tipo = tipoProducto.id_tipo WHERE producto.nombre_producto LIKE %s", ('%' + termino_busqueda + '%',))
        productos = cur.fetchall()
        cur.close()

        return render_template('productos.html', productos=productos, termino_busqueda=termino_busqueda)

    cur = mysql.connection.cursor()
    cur.execute("SELECT producto.id_producto, producto.nombre_producto, producto.descripcion_producto, producto.precio, producto.imagen_path, producto.estatus, tipoProducto.tipoProducto FROM producto JOIN tipoProducto ON producto.id_tipo = tipoProducto.id_tipo")
    productos = cur.fetchall()
    cur.close()

    return render_template('productos.html', productos=productos)
@app.route("/Socios")
def socios():
    return render_template("socios.html")

@app.route("/Certificaciones")
def certificaciones():
    return render_template("template.html")

@app.route("/Telecomunicaciones")
def Telecomunicaciones():
    return render_template("template.html")

@app.route("/Redes-Electricas")
def RedesElec():
    return render_template("template.html")

@app.route("/Circuito-CerradoTV")
def CircuitoCerrado():
    return render_template("template.html")

@app.route("/Corriente-Regulada")
def CorrienteRegulada():
    return render_template("template.html")

@app.route("/Data-Centers")
def DataCenters():
    return render_template("template.html")

@app.route("/FibraOptica")
def FibraOptica():
    return render_template("template.html")

@app.route("/Cables-Estructurados")
def CablesEstructurados():
    return render_template("template.html")

@app.route("/Polizas")
def Polizas():
    return render_template("template.html")

@app.route("/Outsourcing")
def Outsourcing():
    return render_template("template.html")

@app.route("/Administracion")
def Administracion():
    return render_template("template.html")
@app.route('/telecomunicaciones')
def telecomunicaciones():
    return render_template('telecomunicaciones.html')

@app.route('/cctv')
def cctv():
    return render_template('cctv.html')

@app.route('/saladejuntas')
def saladejuntas():
    return render_template('saladejuntas.html')

@app.route('/controlacceso')
def controlacceso():
    return render_template('controlacceso.html')
@app.route('/voceo')
def voceo():
    return render_template('voceo.html')
@app.route('/corrienteregulada')
def corrienteregulada():
    return render_template('corrienteregulada.html')

def create_app():
    return app           
@app.route('/dashboard')
def dashboard():
    cur = mysql.connection.cursor()
    cur.execute("SELECT tipoProducto.tipoProducto, producto.estatus, COUNT(*) as cantidad FROM producto JOIN tipoProducto ON producto.id_tipo = tipoProducto.id_tipo GROUP BY tipoProducto.tipoProducto, producto.estatus")
    data = cur.fetchall()
    cur.close()

    df = pd.DataFrame(data)

    fig = px.bar(df, x='tipoProducto', y='cantidad', color='estatus', barmode='group', title='Cantidad de Productos por Tipo y Disponibilidad')
    fig.update_layout(
        xaxis_title='Tipo de Producto',
        yaxis_title='Cantidad',
        legend_title='Disponibilidad'
    )

    graph_html = fig.to_html(full_html=False)

    return render_template('dashboard_productos.html', graph_html=graph_html)
@app.route('/dashboard_servicios')
def dashboard_servicios():
    cur = mysql.connection.cursor()
    cur.execute("SELECT catalogoServicios.tipoServicio, COUNT(servicio.id_servicio) as cantidad FROM catalogoServicios LEFT JOIN servicio ON catalogoServicios.id_servicio = servicio.id_servicio GROUP BY catalogoServicios.tipoServicio")
    data = cur.fetchall()
    cur.close()

    df = pd.DataFrame(data)

    fig = px.bar(df, x='tipoServicio', y='cantidad', title='Cantidad de Servicios por Tipo')
    fig.update_layout(
        xaxis_title='Tipo de Servicio',
        yaxis_title='Cantidad'
    )

    cursor = mysql.connection.cursor()
    query = "SELECT * FROM servicio"
    cursor.execute(query)
    datos_servicios = cursor.fetchall()
    cursor.close()

    return render_template('dashboard_servicios.html', datos_servicios=datos_servicios, graph_html=fig.to_html(full_html=False))


app.jinja_env.filters['hexlify'] = hexlify_filter

if __name__ == "__main__":
    app.run(debug=True)
