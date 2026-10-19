# Seguridad y limitaciones regulatorias de PoC

1. **Datos reales:** NO utilizar comprobantes reales con información sensible en repositorios públicos. Para pruebas, trabajar con documentos ficticios o anonimizados.
2. **Permisos:** las carpetas se autorizan por RUC. El escáner no debe recorrer enlaces simbólicos fuera de la carpeta. El equipo y usuario del SO constituyen el límite de seguridad de esta PoC.
3. **Archivos no confiables:** bloquear DTD, entidades XML, extensiones desconocidas, CSV ambiguos, ZIP XLSX excesivos y extracción de macros; no ejecutar código de documentos. `openpyxl` no evalúa fórmulas: valores cacheados no son verificación independiente.
4. **IA:** endpoint Ollama restringido a loopback. Los datos incluidos en prompts son no confiables. No se permite ejecución de herramientas, y no hay conexión SUNAT en PoC.
5. **Normativa:** autenticidad y vigencia son metadatos del operador, no hechos confirmados. Las tasas tributarias, excepciones, calendario SOL y estado de CPE requieren fuentes específicas y validaciones adicionales.
6. **Sin garantías:** el XML no acredita aceptación SUNAT; no se comprueban CDR, firmas, autenticidad, condiciones de deducibilidad ni declaraciones. La ausencia de hallazgos no implica cumplimiento tributario.
7. **Almacenamiento:** SQLite es texto claro. Se intenta restringir permisos de archivos en POSIX; Windows depende de ACL y protección del perfil. La PoC no cifra DB, copias ni reportes. Exigir plan formal antes de procesar expedientes reales.
8. **Dependencias:** `pypdf` es BSD-3-Clause, `openpyxl` MIT, `defusedxml` PSF; verificar versiones/licencias al distribuir. Piper mantenido por OHF tiene GPL-3.0 y requiere revisión legal para redistribución/integración comercial; usar ejecutable externo opcional por ahora.
9. **Actualizaciones:** no hay actualizaciones automáticas de normativa ni de binarios, ni servicios que recolecten telemetría. Evitar presentar el corpus como actualizado.
10. **Pruebas pendientes:** malware documental, fuzzing, concurrencia, resistencia a archivos maliciosos complejos, autenticación, cifrado, benchmarking Windows, recovery de transacciones y pilotos con contadores peruanos.
