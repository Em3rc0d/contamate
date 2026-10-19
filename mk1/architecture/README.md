# Architecture · Diseño MVP-001

```text
Browser (localhost:8765) → FastAPI app → Document Parser / Review Engine → SQLite(/data)
                                          ↘ Local knowledge/Tasks
                                          ↘ Ollama (`ollama:11434`, red Compose)
                                 ┌ scheduler [perfil watch]
                                 └ voice [perfil voice; STT/TTS a demanda]
```

- `app`: FastAPI + UI estática, montajes de documentos `ro`, estado SQLite persistente.
- `ollama`: servidor local aislado de puertos host, descarga manual de pesos.
- `scheduler`: lectura e indexación incremental de carpetas autorizadas, no LLM permanente.
- `voice`: servicio separado para evitar consumo basal y mantener micrófono bajo demanda.
- `tests`: imagen independiente sin red y sin acceso a volúmenes de trabajo.

Decisiones en [`docs/DECISIONS.md`](../../docs/DECISIONS.md); amenazas en [`docs/DOCKER_SECURITY.md`](../../docs/DOCKER_SECURITY.md). Compose **no es garantía de aislamiento de salida**.
