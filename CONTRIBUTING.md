# Contribuir a ContaMate

El proyecto se encuentra en validación MK0/MK1. Antes de proponer cambios, documenta problema, alcance, evidencia y riesgos en el issue correspondiente. Las contribuciones de terceros y su distribución están sujetas a que se defina una licencia explícita; **no asumir permiso de redistribución por la visibilidad pública**.

1. No compartir datos personales, archivos de clientes, claves ni documentos tributarios reales.
2. Agregar fixtures ficticios y pruebas reproducibles para modificaciones de lógica contable.
3. Proponer requisitos, arquitectura y criterios de aceptación antes de implementar funcionalidades grandes.
4. Mantener cálculos determinísticos independientes de los modelos generativos.
5. Marcar `OFFICIAL`, `OBSERVED`, `INFERRED` o `HYPOTHESIS` y fechas en toda afirmación externa.
6. Ejecutar `PYTHONPATH=src python -m pytest -q`; validar Compose localmente antes de afirmar compatibilidad Docker.

No activar GitHub Actions de compilación por defecto: la verificación prevista es local.
