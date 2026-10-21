# ContaMate Local

**Copiloto documental local para el contador peruano** · PoC v0.1.0 → MVP-001 v0.2.0 · Docker Compose · Python/FastAPI · SQLite · Ollama opcional

> **Estado: MVP-001 implementado en código; todavía NO certificado para operación comercial.** El motor documental pasa 29 pruebas automatizadas en entorno Python local. El arranque de contenedores, inferencia Ollama, STT/TTS, desempeño en Windows y seguridad operacional están **pendientes de validación real**. No se ha consultado SUNAT ni se garantiza interpretación tributaria.

## Qué hace

- Registra empresas por RUC y acota carpetas autorizadas por expediente.
- Importa facturas UBL Invoice, registros CSV/XLSX y evidencia PDF digital.
- Contrasta documentos y registros para señalar faltantes, duplicados y diferencias con trazabilidad.
- Gestiona tareas y genera informes locales, con API y aplicación web monousuario.
- Permite consultas con un modelo local Ollama, **sin delegarle cálculos contables**.
- Ofrece voz y escaneo residente como perfiles Docker opcionales.

## Inicio rápido

```powershell
.\scripts\bootstrap.ps1
docker compose build
docker compose up -d
docker compose exec ollama ollama pull qwen3:1.7b
docker compose exec app python scripts/seed.py
docker compose --profile test run --rm --build tests
```

Abrir <http://localhost:8765> y utilizar el token local generado en `.env`. En Linux usar `./scripts/bootstrap.sh` en lugar de PowerShell.

**Advertencias:** Docker no fue ejecutado en el entorno original de desarrollo; estos comandos deben validarse en el host real. El inicio necesita descargar imágenes/modelos. `docker compose down -v` **destruye volúmenes**.

## Documentación por hitos

| Hito | Objetivo | Estado |
| --- | --- | --- |
| [MK0](mk0/README.md) | Descubrimiento de necesidad, competencia, riesgos y viabilidad | Investigación preliminar; gate comercial abierto |
| [MK1](mk1/README.md) | Diseño, requisitos, arquitectura, implementación y evaluación de MVP-001 | Código y pruebas locales; gates de integración abiertos |
| [Documentación técnica](docs/INDEX.md) | Guía de usuario, contratos, seguridad, pruebas y trazabilidad | Versionada |

El flujo documental empleado es **brainstorming → design → architecture → plan → build → test**, acompañado de **mining-site** (fuentes y evidencia) y **quarries** (extracción, hipótesis y hallazgos).

## Estructura

```text
mk0/{brainstorming,design,architecture,plan,build,test,quarries,mining-site}/
mk1/{brainstorming,design,architecture,plan,build,test,quarries,mining-site}/
docs/         Referencias técnicas, seguridad, contratos y guía
src/          Motor y API Python
web/          Interfaz local
scripts/      Bootstrap, demo, benchmark, scheduler, seed
services/     Servicio de voz opcional
tests/        Pruebas automatizadas
samples/      Datos ficticios, nunca clientes reales
imports/      Carpeta local ignorada (salvo .gitkeep)
compose*.yaml Docker Compose CPU y complemento GPU
```

## Seguridad, licencia y contribuciones

Este repositorio es **público**; no subas credenciales SOL, tokens, archivos de clientes o declaraciones reales. `.env` y `imports/` están excluidos mediante `.gitignore`. Leer [SECURITY.md](SECURITY.md) y [política Docker](docs/DOCKER_SECURITY.md).

**No se ha seleccionado una licencia de distribución.** El hecho de que el repositorio sea público no concede automáticamente permisos de uso, modificación o redistribución. Antes de abrirlo a contribuciones o distribuir el producto, elegir una licencia y revisar dependencias, especialmente voz Piper.

[Guía completa de ejecución](docs/USER_GUIDE.md) · [Contrato funcional](docs/MVP_CONTRACT.md) · [Evaluación de motores contables externos](docs/EXTERNAL-ACCOUNTING-CANDIDATES-2026-10-21.md) · [Criterios de aceptación](docs/MVP001_ACCEPTANCE.md) · [Estado de evidencia](docs/TRACEABILITY.md)
