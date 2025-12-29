"""
Modelos de base de datos - Mi Agente Viajes
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
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
    formato_hora = db.Column(db.String(4), nullable=True)  # null=auto, '24h', '12h'

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

    # MVP14c: Gmail Push Notifications
    history_id = db.Column(db.String(50))  # Para tracking de cambios
    watch_expiration = db.Column(db.DateTime)  # Cuándo renovar watch

    # Timestamps
    connected_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_expiry_warning = db.Column(db.DateTime)  # Cuándo se envió último aviso de expiración

    def is_token_expired(self):
        """Verifica si el token expiró"""
        if not self.token_expiry:
            return True
        return datetime.utcnow() > self.token_expiry
    
    def __repr__(self):
        return f'<EmailConnection {self.provider}:{self.email}>'


class ProcessedEmail(db.Model):
    """
    Tracking de emails ya procesados para evitar reprocesamiento.
    Reduce llamadas a Claude API significativamente.
    """
    id = db.Column(db.Integer, primary_key=True)
    connection_id = db.Column(db.Integer, db.ForeignKey('email_connection.id'), nullable=False)
    message_id = db.Column(db.String(255), nullable=False)
    processed_at = db.Column(db.DateTime, default=datetime.utcnow)
    had_reservation = db.Column(db.Boolean, default=False)

    __table_args__ = (
        db.UniqueConstraint('connection_id', 'message_id', name='uq_connection_message'),
    )

    def __repr__(self):
        return f'<ProcessedEmail {self.message_id[:20]}...>'


class Viaje(db.Model):
    """Modelo de viaje/vuelo"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Relación con usuario
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # nullable=True para migración
    
    # Campos existentes
    tipo = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.String(200), nullable=False, default='')
    origen = db.Column(db.String(100))
    destino = db.Column(db.String(100))
    fecha_salida = db.Column(db.DateTime, nullable=False)
    fecha_llegada = db.Column(db.DateTime)
    hora_salida = db.Column(db.String(10))
    hora_llegada = db.Column(db.String(10))
    aerolinea = db.Column(db.String(100))
    numero_vuelo = db.Column(db.String(50))
    codigo_reserva = db.Column(db.String(255))  # Aumentado para expediciones/charters
    codigos_alternativos = db.Column(db.Text)  # JSON array con códigos adicionales (ej: código aerolínea)
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

    # Campos nuevos para multi-tipo (14-EXT)
    ubicacion = db.Column(db.String(500))   # dirección/ciudad para lugares fijos
    proveedor = db.Column(db.String(200))   # nombre del hotel/restaurante/empresa/aerolinea
    precio = db.Column(db.String(100))      # "USD 450", "€748", formato libre
    raw_data = db.Column(db.Text)           # JSON completo de Claude como backup
    datos = db.Column(JSONB)                # JSON estructurado con toda la info del tipo (migración JSONB)

    # Control de permisos de edición/borrado
    source = db.Column(db.String(20), default='manual')  # Valores: 'manual', 'gmail', 'microsoft', 'email_forward', 'pdf_upload'

    # Campos para monitoreo FR24
    ultima_actualizacion_fr24 = db.Column(db.DateTime)
    status_fr24 = db.Column(db.String(50))
    delay_minutos = db.Column(db.Integer)
    datetime_takeoff_actual = db.Column(db.DateTime)
    datetime_landed_actual = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Viaje {self.origen}->{self.destino} {self.fecha_salida}>'

    def get_codigos_alternativos(self):
        """Retorna lista de códigos alternativos"""
        if not self.codigos_alternativos:
            return []
        try:
            import json
            return json.loads(self.codigos_alternativos)
        except:
            return []

    def add_codigo_alternativo(self, codigo):
        """Agrega un código alternativo si no existe"""
        import json
        codigos = self.get_codigos_alternativos()
        codigo = codigo.strip().upper()
        if codigo and codigo not in codigos and codigo != self.codigo_reserva:
            codigos.append(codigo)
            self.codigos_alternativos = json.dumps(codigos)
            return True
        return False

    def tiene_codigo(self, codigo):
        """Verifica si tiene un código (principal o alternativo)"""
        codigo = codigo.strip().upper() if codigo else ''
        if not codigo:
            return False
        if self.codigo_reserva and self.codigo_reserva.upper() == codigo:
            return True
        return codigo in self.get_codigos_alternativos()


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


class PushSubscription(db.Model):
    """Suscripciones a Push Notifications (Firebase)"""
    __tablename__ = 'push_subscriptions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.Text, nullable=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('push_subscriptions', lazy='dynamic'))

    __table_args__ = (db.UniqueConstraint('user_id', 'token', name='unique_user_token'),)

    def __repr__(self):
        return f'<PushSubscription user_id={self.user_id}>'
