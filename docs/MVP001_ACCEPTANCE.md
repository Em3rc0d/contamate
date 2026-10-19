# MVP-001 — Contrato de aceptación (2026-10-17)

## Alcance implementado

Un sistema local de revisión asistida que consume exportaciones autorizadas, discrimina empresas por RUC, compara registros estructurados con XML UBL Invoice, conserva evidencia y proporciona una explicación opcional vía Ollama. La voz se aísla en un contenedor opt-in. **No** es un ERP ni un servicio autorizado SUNAT.

**Topología:** `app` (FastAPI + CLI + SQLite, puerto host `127.0.0.1:8765`), `ollama` (red Compose interna; modelos persistentes) y `voice` (servicio STT/TTS bajo `--profile voice`) y `scheduler` (daemon opcional bajo `--profile watch`) y `tests` (suite aislada bajo `--profile test`). El navegador muestra hallazgos y no envía archivos a terceros.

## Gates / evidencia / estado al entregar

| Gate | Requisito | Estado | Evidencia / límite |
|---|---|---|---|
| M1 | Regresión de PoC v0.1 | PASS local | 22 pruebas base |
| M2 | API local con token | PASS local | `tests/test_api.py`, casos HTTP |
| M3 | Discriminación multiempresa | PASS local | API + SQLite, bloquear raíces solapadas |
| M4 | Revisión de importes sin LLM | PASS local | XML/CSV/XLSX y `Decimal`, comparador anterior |
| M5 | UI estática sin dependencias cloud | PASS parcial | Archivos servidos mediante TestClient y comprobación sintáctica JS; sin prueba navegador real |
| M6 | Dockerfile y Compose operativos | PENDIENTE | Docker no instalado en el entorno de entrega; falta `docker compose build/up` sobre máquina destino |
| M7 | Modelo Qwen3 ejecutado en contenedor | PENDIENTE | No se puede validar sin Ollama descargado y Docker destino |
| M8 | Latencia/VRAM/RAM en equipos | PENDIENTE | `scripts/benchmark.py` mide ejecución real; cero benchmarks obtenidos en esta entrega |
| M9 | STT navegador/Whisper | PENDIENTE | Servicio implementado, falta descarga de pesos y prueba micrófono |
| M10 | TTS Piper en español | PENDIENTE | Servicio implementado, voz no distribuida; requiere archivos de modelo y revisión de licencia |
| M11 | PDFs escaneados/OCR, XML variados, integración SUNAT | FUERA DEL ALCANCE | Deben diseñarse y validarse en posteriores hitos |

## Prueba de aceptación integrada (cuando Docker esté disponible)

1. Generar `.env` con token seguro. Levantar `app` y `ollama` con Compose CPU.
2. Descargar explícitamente `qwen3:1.7b` y ejecutar `python scripts/seed.py` dentro del contenedor app.
3. Abrir `http://localhost:8765` e ingresar el token. Deben aparecer empresas de prueba.
4. Elegir Empresa A y `2026-09`, escanear y revisar; deben aparecer `AMOUNT_MISMATCH` y `MISSING_XML`.
5. Empresa B debe exhibir `MISSING_REGISTER`, sin evidencias de Empresa A.
6. Descargar informe; debe contener archivos, montos, filas y aclaración de no-validación SUNAT.
7. Preguntar: "¿Qué diferencias encontraste en las compras de septiembre?"; Ollama debe responder en español con soporte documental, sin inventar certificaciones SUNAT.
8. Ejecutar `python scripts/benchmark.py --model qwen3:1.7b --trials 3` y registrar mediana/tokens por segundo/RAM.
9. Activar el perfil `voice` y probar grabación corta de español; revisar que el texto del dictado no dispara modificaciones.
10. Proveer voz española autorizada en `voices/es.onnx` + `.json`; escuchar una respuesta.
11. Repetir la ejecución en equipo CPU de 8 GB y uno de 16 GB; documentar presión de memoria, rendimiento y errores.

## Criterios antes de promoción a MVP comercial

- Ninguna afirmación de cumplimiento tributario automatizado; resultados deben reproducirse desde evidencia.
- Pruebas con archivos anonimizados del flujo real de un contador, con consentimiento y respaldo.
- Probar control de acceso, cifrado del disco, recuperación de SQLite y compatibilidad Windows Docker Desktop.
- Revisar licencias redistributivas de Ollama, pesos Qwen, Whisper, Piper y voz específica.
- El rendimiento suficiente para el equipo objetivo **no** está demostrado. Cambiar límites/modelo al medir.
