# 📘 APRENDIZAJES - Mi Agente Viajes

> Lecciones aprendidas durante el desarrollo.  
> Transferibles a otros proyectos.
> 
> **Última actualización:** 12 Diciembre 2025  
> **Sesiones revisadas:** Mis Viajes 1-18 + Meta 1

---

## 🔴 Errores críticos evitados

### 1. Buscar antes de pedir al humano
**Problema:** Claude pide información que podría obtener de otras fuentes  
**Síntoma:** El humano pierde tiempo respondiendo lo que Claude ya tiene  
**Solución:** Agotar fuentes automatizadas antes de preguntar:
1. Project Knowledge (archivos del repo)
2. `conversation_search` (conversaciones pasadas)
3. Terminal (`cat`, `ls`, `grep`)
4. Recién entonces preguntar al humano

**Principio:** Andy es la última opción, no la primera.  
**Sesión:** Meta 1  
**Aplicable a:** Todo workflow con asistencia IA

---

### 2. Archivos grandes traban Claude.ai
**Problema:** Al generar múltiples archivos grandes (>200 líneas), Claude.ai se traba con "incompatible messages"  
**Síntoma:** La interfaz se congela, hay que abrir nueva conversación  
**Solución:** Crear archivos de a UNO con confirmación de Andy entre cada uno  
**Sesiones afectadas:** Mis Viajes 8, 9, 10, 13  
**Aplicable a:** Cualquier proyecto con Claude.ai que genere código

---

### 3. Código después de `if __name__`
**Problema:** Nuevos endpoints en Flask no se registran si están después del bloque main  
**Síntoma:** 404 en endpoints que deberían existir  
**Solución:** Siempre verificar ubicación del código nuevo, debe estar ANTES de `if __name__ == '__main__'`  
**Sesión:** Mis Viajes 3  
**Aplicable a:** Proyectos Flask

---

### 4. Secrets montados en `/app`
**Problema:** Montar secrets de GCP en /app sobreescribe el código de la aplicación  
**Síntoma:** App no arranca, archivos desaparecen  
**Solución:** Usar `/secrets/` u otra ruta separada para secrets  
**Sesión:** Mis Viajes 4  
**Aplicable a:** Google Cloud Run con secrets

---

### 5. Archivos truncados/corruptos
**Problema:** Archivos grandes a veces se generan incompletos  
**Síntoma:** Internal Server Error, `TemplateSyntaxError: unexpected end of template`  
**Solución:** Verificar integridad antes de deploy con `tail -20 archivo`, tener rollback listo: `git checkout HEAD -- archivo`  
**Sesión:** Mis Viajes 14  
**Aplicable a:** Cualquier proyecto con generación de código

---

### 6. GitHub secret scanning bloquea commits
**Problema:** Credenciales hardcodeadas en código bloquean el push  
**Síntoma:** `git push` rechazado por GitHub  
**Solución:** SIEMPRE usar variables de entorno para credenciales desde el inicio  
**Sesión:** Mis Viajes 17  
**Aplicable a:** Cualquier proyecto con OAuth o API keys

---

### 7. OAuth scope validation estricta
**Problema:** Google OAuth falla al conectar múltiples cuentas por validación de scopes  
**Síntoma:** Error de autenticación en segunda cuenta  
**Solución:** Bypassear strict scope validation en el flow de auth  
**Sesión:** Mis Viajes 17  
**Aplicable a:** Proyectos con Google OAuth multi-cuenta

---

## 🟢 Patterns exitosos

### 1. Smoke tests obligatorios
**Qué:** Script `smoke_tests.sh` que verifica endpoints críticos post-deploy  
**Implementación:** curl a cada endpoint, verificar status codes esperados  
**Por qué funciona:** Detecta roturas inmediatamente, da confianza para deployar seguido  
**Sesión implementado:** Mis Viajes 2  
**Aplicable a:** Cualquier web app

---

### 2. Design System documentado
**Qué:** UX_UI_ROADMAP.md con principios, colores, componentes  
**Por qué funciona:** Consistencia visual sin repensar cada decisión  
**Aplicable a:** Cualquier producto con UI

---

### 3. Documentación como código
**Qué:** ROADMAP.md, METODOLOGIA.md versionados en git  
**Por qué funciona:** Historia de decisiones, onboarding de nuevos contextos (sesiones de Claude)  
**Aplicable a:** Cualquier proyecto

---

### 4. Screenshots > Descripciones
**Qué:** Compartir screenshots en lugar de describir problemas  
**Por qué funciona:** Claude ve exactamente el estado de la UI, errores, o comportamiento  
**Aplicable a:** Debugging de UI

---

### 5. Validar antes de implementar
**Qué:** Discutir opciones primero, elegir enfoque, LUEGO implementar  
**Por qué funciona:** Evita retrabajo en features complejas  
**Aplicable a:** Features con múltiples enfoques posibles

---

## 🛠️ Herramientas descubiertas

### Claude Code en VS Code/Codespaces
**Qué:** CLI que ejecuta comandos, edita archivos  
**Descubierto:** 10 Dic 2025  
**Documentación:** https://docs.anthropic.com/claude-code  
**Configuración:** `.claude/settings.json` para permisos

---

### Project Knowledge sync
**Qué:** Claude.ai puede leer repo de GitHub si está en Project Knowledge  
**Limitación:** Sync manual, puede tener delay  
**Workaround:** Recordar hacer sync después de cada push, usar `cat` para ver actual

---

## 💡 Insights de producto

### Usuarios piensan en "viajes", no en "vuelos"
**Contexto:** Un viaje = vuelo + hotel + restaurantes + actividades  
**Implicación:** Arquitectura debe soportar múltiples tipos de eventos agrupados  
**Decisión:** Modelo híbrido Evento + DetalleVuelo/Hotel/etc

---

### Duplicación de UI confunde
**Contexto:** Emails aparecían en Perfil Y en Preferencias  
**Implicación:** Un concepto = un lugar en la UI  
**Decisión:** Unificar en "Mis emails" con toggle de OAuth

---

## 🚫 Anti-patrones

| Anti-patrón | Por qué es malo | Alternativa |
|-------------|-----------------|-------------|
| Pedir info sin buscar | Fricción innecesaria | Agotar fuentes automatizadas |
| Regenerar archivos largos | Truncamiento | str_replace |
| Múltiples archivos a la vez | Bloqueo | Uno por uno |
| Deploy sin verificar | Rollbacks | git diff primero |
| Sesiones infinitas | Degradación | Cortar a ~50 intercambios |
| Saltar sync | Contexto desactualizado | 🔄 después de push |

---

## 📅 Changelog de aprendizajes

| Fecha | Categoría | Resumen | Sesión |
|-------|-----------|---------|--------|
| 12 Dic | Workflow | Buscar antes de pedir al humano | Meta 1 |
| 11 Dic | Workflow | Sistema de agentes Claude.ai + Claude Code | 18 |
| 11 Dic | UX | Unificar conceptos duplicados | 18 |
| 11 Dic | Producto | Estrategia email por tiers | 18 |
| 10 Dic | Proceso | Archivos de a uno para evitar trabas | 15 |
| 10 Dic | UX | Empty states > modals de onboarding | 15 |
| 10 Dic | UX | Heroicons SVG, no emojis | 15 |
| 9 Dic | Infra | Refactor a blueprints | 11 |
| 9 Dic | Feature | Calendar feed privado por token | 9 |
| 8 Dic | Auth | Multi-usuario con Flask-Login | 5-6 |
| 7 Dic | UX | Header unificado mobile/desktop | 7 |
| 6 Dic | Infra | Secrets no en /app | 4 |
| 6 Dic | Flask | Código antes de if __name__ | 3 |
| 5 Dic | Infra | Cloud Run + PostgreSQL setup | 2 |
| 5 Dic | Core | MVP inicial funcionando | 1 |

---

## 🔄 Proceso de actualización

### Cuándo agregar a este archivo
- Cuando algo salga mal que no debería haber pasado
- Cuando descubramos un pattern que funciona bien
- Cuando encontremos una herramienta útil
- Cuando tengamos un insight de producto o colaboración

### Formato de entrada
```markdown
### Título descriptivo
**Problema/Qué:** [Descripción]
**Solución/Por qué funciona:** [Explicación]
**Sesión:** Mis Viajes XX
**Aplicable a:** [Contextos donde aplica]
```

### Revisión periódica
Cada 5 sesiones, revisar si hay aprendizajes no documentados.

---

## 🔮 Pendientes de validar

- [ ] ¿Claude Code con `settings.json` mejora autonomía?
- [ ] ¿CLAUDE.md reduce errores de contexto?
- [ ] ¿Modelo híbrido de eventos escala bien?

---

**Este archivo es portable. Copialo a nuevos proyectos y adaptalo.**
