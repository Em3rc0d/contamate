# Seguridad y operaciones Docker — MVP-001

- La única publicación de puerto del host es `127.0.0.1:8765`; no cambiar a `0.0.0.0`, no exponerlo con túneles/reverse proxy públicos.
- Token local aleatorio de 256 bits requerido para todas las rutas de datos; el navegador lo mantiene solo en memoria hasta cerrar o recargar. No guardar `.env` en Git.
- Ollama y voz se descubren solo por DNS dentro de la red privada de Compose. **La red no tiene bloqueo de egreso general**: Ollama y STT pueden descargar modelos bajo instrucciones explícitas/primer uso; no equivalen a aislamiento de red formal.
- Archivos originales desde `./imports` y `./samples`: montajes `ro`. Cada carpeta se autoriza a un único expediente sin superposiciones. SHA-256 controla indexación incremental; no es prueba SUNAT.
- SQLite y modelos están en volúmenes Docker persistentes: no se eliminan con `docker compose down`. **`docker compose down -v` destruirá los volúmenes**, incluidos los expedientes y modelos.
- Backup básico (contenedor detenido): `docker compose stop app`, luego `docker run --rm -v contamate_contamate_data:/data:ro -v "${PWD}:/backup" alpine tar czf /backup/contamate-backup.tar.gz -C /data .` (ajustar nombre del volumen verificado por `docker volume ls`, sintaxis PowerShell distinta). Para instalaciones reales establecer política cifrada, restauración probada y auditada.
- API no habilita escritura de documentos originales ni ediciones contables. Operaciones permitidas: importar índice local, registrar empresa/tarea/fuente, comparar, responder y exportar informe.
- No incluye TLS/autenticación multiusuario/rate limiting/seguridad de sesión empresarial. Para PoC monousuario localhost únicamente.
- Contenedor de voz usa dependencia Piper con licencia GPL-3.0-or-later; la comercialización exige revisión jurídica/técnica y licencias de voz concretas.
- Las imágenes `ollama/ollama:latest` y `python:3.12-slim-bookworm` son bases de conveniencia para el piloto; antes de distribuir, fijar digest, generar SBOM y pasar un escáner de vulnerabilidades.
- Ollama debe tener `OLLAMA_NO_CLOUD=1`; se deben verificar conexiones de red si se publican promesas de privacidad total.
