# Registro de decisiones de ingeniería

| ID | Decisión | Estado | Motivo / trade-off |
| --- | --- | --- | --- |
| ADR-001 | Producto local-first, expedientes multi-RUC | Aceptada para MVP-001 | Privacidad y trabajo en PCs de oficina; mayores responsabilidades locales de backup |
| ADR-002 | Python/FastAPI/SQLite monoproceso con scheduler opcional | Aceptada para piloto | Reduce costos/operación; concurrencia debe medirse |
| ADR-003 | Herramientas determinísticas para cifras contables | Aceptada | Un LLM puede explicar, no dar fe de cálculos ni normas |
| ADR-004 | Ollama como proveedor inicial, no dependencia del núcleo | Aceptada | Evita bloquear revisión documental; hardware variable |
| ADR-005 | Docker Compose CPU por defecto; GPU como override | Aceptada para piloto | Facilidad de instalación, no sustituye benchmark |
| ADR-006 | Voz como perfil opcional, push-to-talk | Aceptada para piloto | Menor consumo y exposición de micrófono |
| ADR-007 | Adaptadores SUNAT/SIRE sin escrituras en MVP-001 | Diferida | Requiere permisos, credenciales y pruebas oficiales |
| ADR-008 | Distribución comercial/licencia aún no resueltas | Abierta | Revisar licencias de motores, modelos, voz y componentes |

**Regla de avance:** ninguna decisión pendiente de seguridad, datos reales o viabilidad comercial se considera implícitamente resuelta por existir código ejecutable.
