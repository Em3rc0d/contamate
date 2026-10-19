# Plan · Secuencia de aceptación MVP-001

## Gate A — Código (completado para fixtures)

- `PYTHONPATH=src python -m pytest -q`: 29/29.
- `python -m compileall -q src scripts services` y `node --check web/app.js`: sin fallas estáticas.
- Separación básica de RUC y token cubierta en tests.

## Gate B — Docker (pendiente)

- Iniciar Compose y verificar `docker compose ps`, health, logs, endpoints.
- Ejecutar suite de pruebas en servicio `tests`.
- Demostrar restauración de volúmenes/backup y ausencia de documentos modificados.

## Gate C — Modelos y voz (pendiente)

- Descargar `qwen3:1.7b` y medir latencia/RAM en equipo real.
- Confirmar salida restringida, manejo de timeouts e indisponibilidad de Ollama.
- Validar grabación a demanda STT y TTS con voces licenciadas, sin escucha continua.

## Gate D — Datos y dominio (pendiente)

- Obtener dataset de prueba autorizado y anonimizado, con ground truth por contador.
- Medir precisión/recall de hallazgos, falsas alarmas y escenarios atípicos.
- Sin datos reales hasta controles de seguridad y consentimiento explícitos.

La decisión de cierre requiere aprobar todos los gates aplicables, documentando responsables, fecha y evidencia.
