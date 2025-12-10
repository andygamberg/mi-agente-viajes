"""
Modelos de base de datos - Mi Agente Viajes
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

db = SQLAlchemy()


def generate_calendar_token():
    """Genera token único para calendar feed"""
    return str(uuid.uuid4())


class User(UserMixin, db.Model):
    """Modelo de usuario para autenticación"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    nombre_pax = db.Column(db.String(50))  # Nombre para match en reservas
    apellido_pax = db.Column(db.String(50))  # Apellido para match en reservas
    calendar_token = db.Column(db.String(36), unique=True, default=generate_calendar_token)  # MVP9: Token único para calendar feed
    combinar_vuelos = db.Column(db.Boolean, default=True)  # MVP11: Deduplicar vuelos idénticos

    # MVP13: Preferencias de notificaciones
    notif_email_master = db.Column(db.Boolean, default=True)
    notif_delay = db.Column(db.Boolean, default=True)
    notif_cancelacion = db.Column(db.Boolean, default=True)
    notif_gate = db.Column(db.Boolean, default=True)
    
    # MVP14: Whitelist personal de remitentes (JSON array)
    # Ejemplo: ["marta@miagentedeviajes.com", "@agenciaturismo.com.ar"]
    custom_senders = db.Column(db.Text)

    creado = db.Column(db.DateTime, default=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True)
    
    # Relación con viajes
    viajes = db.relationship('Viaje', backref='owner', lazy='dynamic')
    
    # MVP14: Relación con conexiones de email
    email_connections = db.relationship('EmailConnection', backref='owner', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def regenerate_calendar_token(self):
        """Regenera el token del calendario (si el usuario lo compartió por error)"""
        self.calendar_token = generate_calendar_token()
    
    def get_custom_senders(self):
        """Retorna lista de remitentes custom del usuario"""
        if not self.custom_senders:
            return []
        try:
            import json
            return json.loads(self.custom_senders)
        except:
            return []
    
    def set_custom_senders(self, senders_list):
        """Guarda lista de remitentes custom"""
        import json
        self.custom_senders = json.dumps(senders_list)
    
    def add_custom_sender(self, sender):
        """Agrega un remitente a la whitelist"""
        senders = self.get_custom_senders()
        sender = sender.strip().lower()
        if sender and sender not in senders:
            senders.append(sender)
            self.set_custom_senders(senders)
            return True
        return False
    
    def remove_custom_sender(self, sender):
        """Quita un remitente de la whitelist"""
        senders = self.get_custom_senders()
        sender = sender.strip().lower()
        if sender in senders:
            senders.remove(sender)
            self.set_custom_senders(senders)
            return True
        return False
    
    def __repr__(self):
        return f'<User {self.email}>'


class EmailConnection(db.Model):
    """
    MVP14: Conexiones OAuth a proveedores de email
    Soporta múltiples providers: gmail, outlook, apple (futuro)
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Provider: 'gmail', 'outlook', 'apple'
    provider = db.Column(db.String(20), nullable=False)
    
    # Email de la cuenta conectada
    email = db.Column(db.String(120), nullable=False)
    
    # OAuth tokens (encriptados en producción idealmente)
    access_token = db.Column(db.Text)
    refresh_token = db.Column(db.Text)
    token_expiry = db.Column(db.DateTime)
    
    # Estado y tracking
    is_active = db.Column(db.Boolean, default=True)
    last_scan = db.Column(db.DateTime)
    last_error = db.Column(db.Text)
    emails_processed = db.Column(db.Integer, default=0)
    
    # Timestamps
    connected_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def is_token_expired(self):
        """Verifica si el token expiró"""
        if not self.token_expiry:
            return True
        return datetime.utcnow() > self.token_expiry
    
    def __repr__(self):
        return f'<EmailConnection {self.provider}:{self.email}>'


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
    """Emails adicionales asociados a un usuario (para matching de pasajeros)"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    verificado = db.Column(db.Boolean, default=False)
    es_principal = db.Column(db.Boolean, default=False)
    creado = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('emails_adicionales', lazy='dynamic'))
    
    def __repr__(self):
        return f'<UserEmail {self.email}>'
