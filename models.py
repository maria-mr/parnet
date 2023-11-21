from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Administrador(db.Model):
    id_admin = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario = db.Column(db.String(255), nullable=False)
    contraseña = db.Column(db.String(255), nullable=False)
    mail = db.Column(db.String(255), nullable=False)

class TipoProducto(db.Model):
    id_tipo = db.Column(db.Integer, primary_key=True)
    tipoProducto = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.String(255), nullable=False)

class CatalogoServicios(db.Model):
    id_servicio = db.Column(db.Integer, primary_key=True)
    tipoServicio = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.String(255), nullable=False)

class Producto(db.Model):
    id_producto = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_producto = db.Column(db.String(255))
    descripcion_producto = db.Column(db.String(255))
    precio = db.Column(db.String(255))
    imagen = db.Column(db.LargeBinary)
    estatus = db.Column(db.String(255))
    id_tipo = db.Column(db.Integer, db.ForeignKey('tipo_producto.id_tipo'))
    tipo = db.relationship('TipoProducto', backref='productos')

class Servicio(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_servicio = db.Column(db.String(255))
    descripcion = db.Column(db.String(255))
    id_servicio = db.Column(db.Integer, db.ForeignKey('catalogo_servicios.id_servicio'))
    correo = db.Column(db.String(255))
    catalogo_servicio = db.relationship('CatalogoServicios', backref='servicios')

class Sugerencias(db.Model):
    id_sugerencia = db.Column(db.Integer, primary_key=True, autoincrement=True)
    mensaje = db.Column(db.String(255))
