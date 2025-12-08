"""
Modelos de base de datos - Mi Agente Viajes
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """Modelo de usuario para autenticación"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    creado = db.Column(db.DateTime, default=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True)
    
    # Relación con viajes
    viajes = db.relationship('Viaje', backref='owner', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.email}>'


class Viaje(db.Model):
    """Modelo de viaje/vuelo"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Relación con usuario
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # nullable=True para migración
    
    # Campos existentes
    tipo = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.String(200), nullable=False)
    origen = db.Column(db.String(100))
    destino = db.Column(db.String(100))
    fecha_salida = db.Column(db.DateTime, nullable=False)
    fecha_llegada = db.Column(db.DateTime)
    hora_salida = db.Column(db.String(10))
    hora_llegada = db.Column(db.String(10))
    aerolinea = db.Column(db.String(100))
    numero_vuelo = db.Column(db.String(50))
    codigo_reserva = db.Column(db.String(50))
    terminal = db.Column(db.String(50))
    puerta = db.Column(db.String(20))
    asiento = db.Column(db.String(20))
    nombre_hotel = db.Column(db.String(200))
    direccion_hotel = db.Column(db.String(300))
    notas = db.Column(db.Text)
    pasajeros = db.Column(db.Text)  # JSON con lista de pasajeros
    equipaje_facturado = db.Column(db.String(200))
    equipaje_mano = db.Column(db.String(200))
    grupo_viaje = db.Column(db.String(50))
    nombre_viaje = db.Column(db.String(200))
    creado = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Campos para monitoreo FR24
    ultima_actualizacion_fr24 = db.Column(db.DateTime)
    status_fr24 = db.Column(db.String(50))
    delay_minutos = db.Column(db.Integer)
    datetime_takeoff_actual = db.Column(db.DateTime)
    datetime_landed_actual = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Viaje {self.origen}->{self.destino} {self.fecha_salida}>'


class UserEmail(db.Model):
    """Emails adicionales asociados a un usuario"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    verificado = db.Column(db.Boolean, default=False)
    es_principal = db.Column(db.Boolean, default=False)
    creado = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('emails_adicionales', lazy='dynamic'))
    
    def __repr__(self):
        return f'<UserEmail {self.email}>'
