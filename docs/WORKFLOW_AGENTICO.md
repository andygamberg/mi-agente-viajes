# 🤖 Workflow Agéntico - Mi Agente Viajes

**Versión:** 1.0  
**Fecha:** 12 Diciembre 2025

---

## 📊 Arquitectura de Tres Capas

```
┌─────────────────────────────────────────────────────────────┐
│                      ANDY (Humano)                          │
│  • Visión de producto    • Prioridades    • Validación      │
│  • Decisiones UX         • Git/Deploy     • Testing final   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   CLAUDE.AI (Arquitecto)                    │
│  • Planificación          • Diseño de soluciones            │
│  • Análisis de trade-offs • Documentación                   │
│  • Contexto del proyecto  • Prepara instrucciones           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 CLAUDE CODE (Ejecutor)                      │
│  • Edición de archivos    • Implementación                  │
│  • Verificaciones         • Refactors                       │
│  • UN archivo a la vez    • Propone, no decide              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Setup Inicial (Una vez)

### 1. Conectar GitHub a Claude.ai

```
Claude.ai → Settings → Connectors → GitHub → Conectar
```

### 2. Agregar repo a Project Knowledge

```
Proyecto → Files → Add → GitHub → Seleccionar repo
```

### 3. Crear archivos de configuración

En el repo, crear:
- `CLAUDE.md` (raíz) - Manifiesto operativo
- `.claude/settings.json` - Permisos

### 4. Abrir GitHub Codespaces

```
github.com/[user]/[repo] → Code → Codespaces → Create
```

---

## 📋 Flujo de Trabajo Diario

### Inicio de Sesión

```markdown
Proyecto: Mi Agente Viajes
Conversación: Mis Viajes XX
Objetivo: [Qué queremos lograr]

Por favor revisá CLAUDE.md, METODOLOGIA_TRABAJO.md y ROADMAP.md.
```

### Ciclo de Desarrollo

```
1. DEFINIR: Andy describe qué necesita
2. PLANEAR: Claude.ai propone solución
3. APROBAR: Andy valida enfoque
4. EJECUTAR: Claude Code edita archivos (uno a uno)
5. VERIFICAR: Andy revisa con git diff
6. COMMIT: Andy ejecuta git add/commit/push
7. DEPLOY: Andy ejecuta gcloud deploy
8. TEST: Smoke tests
9. SYNC: Actualizar Project Knowledge (🔄)
```

### Cierre de Sesión

Antes de cerrar, verificar:
- [ ] ¿Commits hechos?
- [ ] ¿Deploy exitoso?
- [ ] ¿Smoke tests pasaron?
- [ ] ¿Documentación actualizada?
- [ ] ¿Próximo paso claro?

---

## ⚠️ Reglas Críticas

### HACER ✅

| Acción | Responsable |
|--------|-------------|
| Editar archivos | Claude Code |
| Ver contenido (cat, tail) | Claude Code |
| Proponer soluciones | Claude Code |
| Git operations | Andy |
| Deploy | Andy |
| Decisiones de producto | Andy |

### NO HACER ❌

| Acción | Por qué |
|--------|---------|
| Múltiples archivos a la vez | Causa "incompatible messages" |
| Claude Code ejecuta git | No tiene permisos |
| Claude Code ejecuta gcloud | No tiene permisos |
| Regenerar archivos >200 líneas | Riesgo de truncamiento |
| Saltar verificaciones | Causa errores en deploy |

---

## 🛠️ Troubleshooting

### "Incompatible messages"

**Causa:** Se intentaron crear múltiples archivos simultáneamente.  
**Solución:** Cerrar sidebar, reabrir, hacer UN archivo a la vez.

### Archivo truncado

**Síntoma:** `TemplateSyntaxError: unexpected end of template`  
**Solución:**
```bash
git log --oneline -5
git checkout <commit_hash> -- ruta/archivo
git add . && git commit -m "Rollback" && git push
```

### Deploy falla

**Verificar:**
```bash
gcloud builds list --limit 5
gcloud logging read "resource.type=cloud_run_revision..." --limit 30
```

### Contexto perdido

**Síntoma:** Claude no recuerda decisiones previas.  
**Solución:** Nueva conversación con template de inicio + sync Project Knowledge.

---

## 📚 Archivos del Sistema

| Archivo | Ubicación | Propósito |
|---------|-----------|-----------|
| `CLAUDE.md` | Raíz | Manifiesto para Claude Code |
| `.claude/settings.json` | `.claude/` | Permisos y config |
| `METODOLOGIA_TRABAJO.md` | Raíz | Workflow detallado |
| `ROADMAP.md` | Raíz | Estado del proyecto |
| `docs/APRENDIZAJES.md` | `docs/` | Lecciones aprendidas |
| `docs/WORKFLOW_AGENTICO.md` | `docs/` | Este documento |

---

## 🔄 Cuándo Crear Nueva Sesión

| Señal | Acción |
|-------|--------|
| ~50 intercambios | Sugerir corte |
| MVP completado | Buen momento para cerrar |
| Respuestas lentas | Contexto saturado |
| Cambio de tema grande | Nueva sesión |

### Nomenclatura

```
Mis Viajes 18  →  Mis Viajes 19  →  ...
Meta 1  →  Meta 2  →  ...  (para meta-proyecto)
```

---

## 💡 Tips de Productividad

1. **Screenshots** para mostrar UI/errores
2. **Copy-paste de terminal** para output exacto
3. **Links clickeables** en lugar de URLs
4. **Chunks pequeños** para validar incrementalmente
5. **git diff** antes de commit para verificar cambios

---

*Documento vivo - actualizar cuando surjan nuevos aprendizajes*
