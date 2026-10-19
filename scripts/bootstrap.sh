#!/usr/bin/env sh
set -eu
if [ -e .env ]; then echo '.env ya existe; no se reemplaza'; exit 0; fi
command -v openssl >/dev/null || { echo 'Se requiere openssl para generar el token seguro.' >&2; exit 1; }
secret=$(openssl rand -hex 32)
sed "s/REEMPLAZAR_CON_TOKEN_ALEATORIO_SEGURO_32_CHAR/$secret/" .env.example > .env
chmod 600 .env || true
echo 'Creado .env con token aleatorio. Consulta CONTAMATE_API_TOKEN para entrar al panel.'
