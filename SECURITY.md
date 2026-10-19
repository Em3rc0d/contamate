# Política de seguridad — versión experimental

ContaMate Local es un **prototipo de investigación**, no software auditado para producción ni asesor tributario. No lo publiques en Internet, no agregues credenciales SOL, contraseñas, RUC/documentos de terceros o archivos contables privados a GitHub.

- Solo `127.0.0.1:8765` en host controlado, token local secreto en `.env` ignorado por Git.
- Las carpetas originales se montan en modo lectura; verifica permisos del host y respaldos cifrados.
- Las consultas a un modelo no deben incluir datos confidenciales sin controles y consentimiento.
- No se realizan cambios automáticos de registros ni presentaciones ante SUNAT.
- El sistema no ha sido sometido a pentesting ni auditoría de dependencias.

**Reportes de vulnerabilidad:** por ahora, evita publicar datos sensibles o exploits en issues públicas; contacta al mantenedor por un canal privado indicado en el perfil del repositorio. Antes de abrir pilotos externos debe establecerse un canal dedicado.

Detalles en [docs/DOCKER_SECURITY.md](docs/DOCKER_SECURITY.md).
