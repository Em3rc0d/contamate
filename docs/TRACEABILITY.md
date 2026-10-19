# Evidencia y trazabilidad · corte 2026-10-19

| Afirmación | Evidencia disponible | Estado |
|---|---|---|
| Importar y analizar XML UBL / CSV / XLSX | `src/contamate/documents.py`, `tests/test_core.py` | Comprobado con fixtures ficticios |
| Conciliación y trazabilidad por archivo/fila | `src/contamate/review.py`, casos de prueba | Comprobado sobre escenario limitado |
| Separación por RUC y autorización de carpetas | `src/contamate/db.py`, pruebas | Comprobado localmente; falta auditoría de amenazas |
| API y autenticación local | `src/contamate/api.py`, `tests/test_api.py` | Comprobado con tests; no implica seguridad de producción |
| 29 pruebas automatizadas | `PYTHONPATH=src python -m pytest -q` | 29 correctas, ejecución local 2026-10-19 |
| Docker Compose arranca en Windows | `compose.yaml`, Dockerfiles | **No verificado** en host con Docker |
| Ollama conversa en ejecución real | `src/contamate/llm.py` | **No verificado** contra servidor levantado |
| Voz STT/TTS en producción | `services/voice_service.py` | **No verificado**, modelos no incluidos |
| Conector SUNAT/SIRE | No existe implementación oficial | **Fuera de MVP-001** |
| Reglas tributarias completas Perú | No existe cobertura integral | **No demostrado** |
| Seguridad lista para datos reales de clientes | Ver `DOCKER_SECURITY.md` | **No demostrada** |

No existen todavía benchmarks fiables de latencia, memoria o throughput por perfil hardware. Los XML/CSV del repositorio son **ficticios**, no corresponden a clientes o comprobantes verificados ante SUNAT.
