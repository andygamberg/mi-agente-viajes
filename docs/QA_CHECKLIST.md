# QA Checklist - Mi Agente Viajes

**Última actualización:** 14 Diciembre 2025

---

## Pre-Deploy (OBLIGATORIO)
```bash
./smoke_tests.sh
```

**Resultado esperado:** 10/10 tests passing

Si falla alguno, NO deployar hasta resolver.

---

## Review Manual - Features Pequeños

Tiempo: ~5 minutos

### Core
- [ ] Home carga sin errores
- [ ] Login/logout funciona
- [ ] Perfil accesible

### Feature Específico
- [ ] El cambio funciona como se espera
- [ ] No rompió nada existente (revisar home)

---

## Review Manual - Features Grandes (MVPs)

Tiempo: ~15-20 minutos

### Funcionalidad Core
- [ ] Login/logout
- [ ] Home con viajes
- [ ] Home sin viajes (empty state)
- [ ] Perfil

### Crear Reservas
- [ ] /agregar carga correctamente
- [ ] Selector de tipo funciona
- [ ] Form se adapta al tipo
- [ ] Guardar crea reserva
- [ ] Carga rápida (PDF) funciona

### Ver Reservas
- [ ] Cards se expanden/colapsan
- [ ] Vuelo simple muestra datos completos
- [ ] Vuelo combinado muestra pasajeros agrupados
- [ ] Otros tipos (hotel, crucero, etc.) renderizan bien

### Editar Reservas
- [ ] Menú kebab aparece
- [ ] Click abre dropdown
- [ ] "Editar reserva" lleva al form
- [ ] Form pre-poblado con datos
- [ ] Guardar actualiza correctamente
- [ ] Vuelo combinado: múltiples opciones en menú

### Acciones de Grupo
- [ ] Editar nombre de viaje
- [ ] Agrupar viajes
- [ ] Desagrupar viaje

### Por Tipo de Reserva (spot check, no todos)
- [ ] Vuelo
- [ ] Hotel
- [ ] Crucero/Ferry
- [ ] Al menos 1 tipo más

---

## Review Mobile

Tiempo: ~5 minutos

### Legibilidad
- [ ] Textos >= 13px
- [ ] Cards legibles
- [ ] Botones tocables (min 44px)

### Interacción
- [ ] Menú hamburguesa funciona
- [ ] Cards se expanden
- [ ] Menú kebab funciona (no requiere hover)
- [ ] Forms usables

---

## Auditoría UX (cada 5 MVPs o cambio visual grande)

Tiempo: ~30 minutos

### Design System
- [ ] Comparar UI actual con DESIGN_SYSTEM.md
- [ ] Sin emojis en UI (solo en datos/calendario)
- [ ] Iconos monocromáticos (Heroicons)
- [ ] Tipografía consistente

### Consistencia
- [ ] Cards siguen misma estructura
- [ ] Botones mismo estilo
- [ ] Colores según paleta

### Empty States
- [ ] Home sin viajes: educativo
- [ ] Perfil sin emails: call to action

### Feedback
- [ ] Acciones muestran confirmación (flash messages)
- [ ] Errores son claros
- [ ] Loading states donde corresponde

### Actualizar Docs
- [ ] DESIGN_SYSTEM.md refleja cambios
- [ ] UX_UI_ROADMAP.md actualizado

---

## Casos Especiales a Testear

Estos casos han causado bugs en el pasado:

### Datos Legacy
- [ ] Viaje con pasajeros como int (no array)
- [ ] Viaje con campos vacíos/null
- [ ] Código reserva muy largo (>250 chars)

### Vuelos Combinados
- [ ] 2 reservas mismo vuelo
- [ ] 3+ reservas mismo vuelo
- [ ] Orden correcto en card y menú

### OAuth
- [ ] Token expirado → refresh funciona
- [ ] Reconectar cuenta
- [ ] Múltiples cuentas mismo usuario

---

## Post-Deploy Verification

Después de deploy exitoso:
```bash
# Verificar que responde
curl -s -o /dev/null -w "%{http_code}" https://mi-agente-viajes-454542398872.us-east1.run.app/

# Debería retornar 200 o 302
```

- [ ] App accesible
- [ ] Login funciona
- [ ] No hay errores en logs recientes

---

## Historial de Cambios

| Fecha | Cambio |
|-------|--------|
| 14 Dic 2025 | Documento creado - Sesión 24 |
