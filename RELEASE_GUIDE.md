# MiauBot Release Guide

## 🚀 Sistema de Versionado y Releases

Este proyecto ahora incluye un sistema completo de versionado y releases automatizados usando GitHub Actions.

## 📋 Resumen del Sistema

### Archivos Nuevos:
- `VERSION` - Archivo centralizado de versión
- `src/version.py` - Utilidad Python para obtener información de versión
- `scripts/version.sh` - Script de gestión de versiones
- `.github/workflows/build.yml` - GitHub Action para builds automáticos
- `.github/workflows/release.yml` - GitHub Action para releases manuales

## 🔧 Gestión de Versiones

### 1. Ver Versión Actual
```bash
# Usando Make
make version-show

# Usando script directamente
./scripts/version.sh show

# Usando Python
uv run python -c "from src.version import get_version_info; print(get_version_info())"
```

### 2. Cambiar Versión
```bash
# Establecer versión específica
make version-set V=1.0.0

# Incrementar versión (patch: 1.0.0 -> 1.0.1)
make version-bump-patch

# Incrementar versión (minor: 1.0.0 -> 1.1.0)
make version-bump-minor

# Incrementar versión (major: 1.0.0 -> 2.0.0)
make version-bump-major
```

## 🏗️ GitHub Actions

### 1. Build Automático (`build.yml`)
**Trigger:** Push a `main` o `develop`, Pull Requests a `main`

**Qué hace:**
- Builds para Linux AMD64 y ARM64
- Genera artifacts con los ejecutables
- Los artifacts se mantienen por 30 días
- Ejecuta tests automáticos

### 2. Release Manual (`release.yml`)
**Trigger:** Manual (workflow_dispatch)

**Parámetros:**
- `version`: Versión del release (ej: 1.0.0)
- `prerelease`: Si es pre-release (checkbox)

**Qué hace:**
1. Valida formato de versión
2. Verifica que la versión no exista
3. Actualiza archivo `VERSION`
4. Hace commit del cambio de versión
5. Builds para todas las plataformas
6. Genera changelog automático
7. Crea tag de Git
8. Crea GitHub Release con ejecutables

## 🎯 Proceso de Release

### Paso 1: Preparar Release
```bash
# 1. Asegúrate de estar en la rama main
git checkout main
git pull origin main

# 2. Opcional: Actualizar versión localmente para verificar
make version-show
# make version-set V=1.0.0  # si quieres cambiarla localmente primero
```

### Paso 2: Ejecutar Release
1. Ve a GitHub → Actions → "Release"
2. Click en "Run workflow"
3. Selecciona branch: `main`
4. Ingresa la versión (ej: `1.0.0`)
5. Marca "pre-release" si aplica
6. Click "Run workflow"

### Paso 3: Verificar Release
El workflow automáticamente:
- ✅ Validará la versión
- ✅ Actualizará `VERSION`
- ✅ Hará commit y push
- ✅ Creará builds
- ✅ Generará changelog
- ✅ Creará GitHub Release

## 📦 Artifacts y Downloads

### Builds Automáticos (Artifacts)
- Se generan en cada push/PR
- Disponibles en GitHub Actions → Build → Artifacts
- Incluyen información de commit en el nombre

### Releases
- Se publican en GitHub Releases
- Incluyen ejecutables comprimidos
- Changelog automático
- Comandos de instalación

## 🔍 Verificación Local

```bash
# Ver información completa de build
make info

# Hacer build local
make build

# Test rápido
make quick-test

# Test completo
make test-build
```

## 🐛 Troubleshooting

### Error: "Version already exists"
- La versión ya existe como tag de Git
- Usa una versión diferente

### Error: "Invalid version format"
- Usa formato semántico: `X.Y.Z` o `X.Y.Z-suffix`
- Ejemplos válidos: `1.0.0`, `1.0.0-beta`, `2.1.3-rc1`

### Builds fallan
- Verifica que Docker esté funcionando
- Revisa los logs en GitHub Actions

## 📝 Changelog Automático

El changelog se genera automáticamente basado en:
- Commits desde el último tag
- Fecha de release
- Links a comparación de cambios
- Instrucciones de instalación

## 🎛️ Comandos Útiles

```bash
# Información completa
make info

# Gestión de versiones
make version-show
make version-set V=1.2.3
make version-bump-patch

# Builds
make build
make test-build

# Desarrollo
make dev-setup
make format
make lint
``` 