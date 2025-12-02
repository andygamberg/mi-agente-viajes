# MVP 4 - Monitoreo de Vuelos con Flightradar24 API

## ✅ DECISIONES TOMADAS

**API Seleccionada:** Flightradar24
- **Plan:** Explorer - $9/mes
- **Créditos:** 60,000/mes (hasta Mayo 2026), luego 30,000/mes
- **API Key generada:** 019ae167-5bdd-7355-acf7-d2db1dc29740|bv9Ox4UD5JrSWbf6gR2fvCp0m1bwXcbmyIWspAdQf4d00f82

## 📊 ENDPOINTS IDENTIFICADOS

### Flight Summary (principal para MVP 4)
- **Light:** Tiempos básicos, origen/destino, aircraft info
- **Full:** Todo lo de Light + delays detallados, gate changes, status updates

**Parámetros de búsqueda:**
- `flight_number`: Número de vuelo (ej: AR1303)
- `flight_datetime_from`: Fecha inicio (YYYY-MM-DD)
- `flight_datetime_to`: Fecha fin (YYYY-MM-DD)

Filtros adicionales:
- registration, call_sign, airline, airport, aircraft_type

## 🔧 PROBLEMAS DETECTADOS

### Error 403 Forbidden
Todas las llamadas a la API retornan 403, probamos:
- `Authorization: Bearer {key}`
- `Authorization: Token {key}`
- `X-API-Key: {key}`
- `api-key: {key}`

**Posibles causas:**
1. API key necesita activación/permisos adicionales en dashboard
2. Endpoint incorrecto (necesitamos verificar docs exactas)
3. Autenticación web requerida primero
4. IP whitelisting o restricciones geográficas

## 📝 PRÓXIMOS PASOS (Post-cena)

### 1. Verificar API Key en Dashboard
- Revisar permisos de la key
- Verificar si necesita activación
- Buscar ejemplos de código en documentación oficial

### 2. Testing con curl
```bash
curl -H "Authorization: Bearer API_KEY" \
  "https://fr24api.flightradar24.com/api/flights/summary/light?flight_number=AR1303&flight_datetime_from=2025-12-02&flight_datetime_to=2025-12-02"
```

### 3. Implementar función de chequeo
```python
def check_flight_status(flight_number, date):
    """
    Chequea estado de un vuelo específico
    Returns: dict con status, delays, gate changes
    """
    # Llamar a FR24 API
    # Parsear respuesta
    # Detectar cambios vs BD local
    # Return structured data
```

### 4. Cloud Scheduler Setup
- Trigger cada 6 horas
- Procesar solo vuelos en próximas 48hs
- Guardar cambios en BD

### 5. Sistema de alertas
- Detectar delays > 30 min
- Detectar cancelaciones
- Detectar gate changes
- Email notifications

## 💰 CÁLCULOS DE USO

**Con 60K créditos/mes:**
- Asumiendo 10 créditos por llamada (peor caso)
- 6,000 chequeos/mes disponibles
- Chequear cada 6 horas = 4 veces/día
- 15 vuelos promedio
- 15 × 4 = 60 llamadas/día = 1,800/mes
- **Sobran 4,200 llamadas/mes!**

## 📚 RECURSOS

- Portal API: https://fr24api.flightradar24.com/
- Documentación: https://fr24api.flightradar24.com/docs/endpoints/flight-summary
- Blog post: https://www.flightradar24.com/blog/b2b/flight-summary-flightradar24-api/

## ⚠️ NOTAS IMPORTANTES

- API key debe guardarse en variable de entorno
- NO commitear API key a GitHub
- Regenerar key si se expone públicamente
- Plan cancelable en cualquier momento

---

**Última actualización:** 2025-12-02 20:45 ART
**Estado:** Investigación completa, pendiente resolver autenticación API
