# Casos de Uso - Mi Agente Viajes

**Última actualización:** 14 Diciembre 2025

## Cómo usar este documento
- ✅ = Implementado y testeado
- 🔄 = Implementado parcialmente
- ❌ = Pendiente
- 🐛 = Bug conocido

**Actualizar:** Después de cada feature/fix.

---

## 1. Entrada de Reservas

| ID | Caso | Actor | Resultado Esperado | Status |
|----|------|-------|-------------------|--------|
| E1 | Reenvío email a misviajes@ | Usuario | Reserva aparece en app | ✅ |
| E2 | Gmail OAuth detecta email | Sistema | Reserva aparece automáticamente | ✅ |
| E3 | Microsoft OAuth detecta email | Sistema | Reserva aparece automáticamente | ✅ |
| E4 | Carga manual form (/agregar) | Usuario | Reserva creada con datos ingresados | ✅ |
| E5 | Carga rápida PDF | Usuario | Reserva extraída por Claude | ✅ |

---

## 2. Visibilidad (quién ve qué)

| ID | Caso | Actor | Resultado Esperado | Status |
|----|------|-------|-------------------|--------|
| V1 | Owner ve su reserva | Owner | Aparece en "Mis Viajes" | ✅ |
| V2 | Pasajero ve vuelo donde está | Pasajero | Aparece en su app | ✅ |
| V3 | Pasajero ve hotel donde es huésped | Pasajero | Aparece en su app | ❌ BUG-PASSENGER-MATCH |
| V4 | Pasajero ve crucero donde está | Pasajero | Aparece en su app | ❌ BUG-PASSENGER-MATCH |
| V5 | Pasajero ve actividad donde participa | Pasajero | Aparece en su app | ❌ BUG-PASSENGER-MATCH |
| V6 | Actualización de reserva se propaga | Sistema | Todos los que ven la reserva ven el cambio | ✅ |

---

## 3. Edición

| ID | Caso | Actor | Resultado Esperado | Status |
|----|------|-------|-------------------|--------|
| ED1 | Editar reserva simple | Owner | Datos actualizados, redirect a home | ✅ |
| ED2 | Editar vuelo combinado | Owner | Menú muestra opciones por código reserva | ✅ |
| ED3 | Cambiar tipo de reserva | Owner | Campos del form se adaptan | ✅ |
| ED4 | Editar nombre de viaje | Owner | Nombre actualizado en grupo | ✅ |
| ED5 | Editar reserva con datos legacy (int) | Owner | Form maneja datos sin error | ✅ |

---

## 4. Eliminación

| ID | Caso | Actor | Resultado Esperado | Status |
|----|------|-------|-------------------|--------|
| D1 | Eliminar viaje completo | Owner | Todo el grupo borrado | ✅ |
| D2 | Eliminar segmento individual | Owner | Solo ese segmento borrado | ❌ UX-DELETE |
| D3 | Desagrupar viaje | Owner | Segmentos quedan separados | ✅ |
| D4 | Eliminar reserva que otros ven | Owner | ¿Qué pasa con otros usuarios? | ❌ UX-DELETE-SHARED |

---

## 5. Agrupación

| ID | Caso | Actor | Resultado Esperado | Status |
|----|------|-------|-------------------|--------|
| G1 | Agrupar viajes manualmente | Owner | Viajes combinados bajo mismo nombre | ✅ |
| G2 | Auto-agrupar por código reserva | Sistema | Misma reserva = mismo grupo | ✅ |
| G3 | Desagrupar viaje | Owner | Cada segmento independiente | ✅ |

---

## 6. Compartir (MVP-SHARE - futuro)

| ID | Caso | Actor | Resultado Esperado | Status |
|----|------|-------|-------------------|--------|
| S1 | Compartir viaje completo | Owner | Link para ver todo el viaje | ❌ |
| S2 | Compartir segmento individual | Owner | Link a reserva específica | ❌ |
| S3 | Ver viaje compartido | Invitado | Acceso read-only | ❌ |
| S4 | Dejar de compartir | Owner | Acceso revocado | ❌ |
| S5 | Editar viaje compartido | ¿Quién? | Definir permisos | ❌ |

---

## 7. Calendario

| ID | Caso | Actor | Resultado Esperado | Status |
|----|------|-------|-------------------|--------|
| C1 | Suscribir webcal en Apple Calendar | Usuario | Eventos sincronizados | ✅ |
| C2 | Suscribir en Google Calendar | Usuario | Eventos sincronizados | ✅ |
| C3 | Hotel aparece como all-day | Sistema | Sin hora específica | ✅ |
| C4 | Vuelo aparece con hora | Sistema | Hora exacta de salida | ✅ |
| C5 | Precio oculto en calendario | Sistema | No visible por privacidad | ✅ |
| C6 | Vuelo combinado en calendario | Sistema | Pasajeros agrupados por reserva | ✅ |

---

## 8. Notificaciones (MVP13b - futuro)

| ID | Caso | Actor | Resultado Esperado | Status |
|----|------|-------|-------------------|--------|
| N1 | Notificar cambio de vuelo (FR24) | Sistema | Email al owner | ❌ |
| N2 | Notificar delay | Sistema | Email con nueva hora | ❌ |
| N3 | Notificar cancelación | Sistema | Email de alerta | ❌ |
| N4 | Preferencias de notificación | Usuario | Toggle on/off por tipo | 🔄 (UI ✅, envío ❌) |

---

## 9. Autenticación y Perfil

| ID | Caso | Actor | Resultado Esperado | Status |
|----|------|-------|-------------------|--------|
| A1 | Registro nuevo usuario | Visitante | Cuenta creada, redirect a bienvenida | ✅ |
| A2 | Login | Usuario | Acceso a app | ✅ |
| A3 | Recuperar contraseña | Usuario | Email con link seguro | ✅ |
| A4 | Conectar Gmail OAuth | Usuario | Emails detectados automáticamente | ✅ |
| A5 | Conectar Microsoft OAuth | Usuario | Emails detectados automáticamente | ✅ |
| A6 | Desconectar cuenta email | Usuario | Deja de escanear esa cuenta | ✅ |
| A7 | Configurar nombre pasajero | Usuario | Matching funciona correctamente | ✅ |

---

## Historial de Cambios

| Fecha | Cambio |
|-------|--------|
| 14 Dic 2025 | Documento creado - Sesión 24 |
