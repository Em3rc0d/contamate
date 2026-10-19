"""Diagnóstico de límites del contenedor y recomendación conservadora de tamaño de modelo.
No sustituye una medición de latencia real en hardware objetivo.
"""
import os
from pathlib import Path
import psutil

GIB = 1024 ** 3


def _cgroup_int(path):
    try:
        s = Path(path).read_text().strip()
        return None if s == 'max' else int(s)
    except (OSError, ValueError):
        return None


def resources():
    ram = psutil.virtual_memory()
    cap = _cgroup_int('/sys/fs/cgroup/memory.max')
    used = _cgroup_int('/sys/fs/cgroup/memory.current')
    available = ram.available
    if cap and used is not None:
        available = min(available, max(0, cap - used))
    return {
        'ram_host_total_gib': round(ram.total / GIB, 2),
        'ram_host_available_gib': round(ram.available / GIB, 2),
        'container_memory_limit_gib': round(cap / GIB, 2) if cap else None,
        'container_available_gib': round(available / GIB, 2),
        'cpu_visible': os.cpu_count(),
        'note': 'La RAM observada por el contenedor app no es la RAM disponible en el contenedor Ollama; medir ambos en destino.'
    }


def recommend(installed: list[dict], available_bytes: int | None = None):
    """Solo modelos locales descargados, regla heurística con reserva y fallback explícito."""
    if available_bytes is None:
        available_bytes = int(resources()['container_available_gib'] * GIB)
    options = [m for m in installed if m.get('name') and isinstance(m.get('size'), int)
               and not any(x in m['name'].lower() for x in ('embed', 'nomic', 'bge-', 'minilm', 'rerank'))]
    if not options:
        raise RuntimeError('Ollama no tiene modelos conversacionales descargados.')
    options.sort(key=lambda x: x['size'])
    affordable = [m for m in options if m['size'] * 1.6 + 512 * 1024**2 <= available_bytes * 0.7]
    # Elige el mayor que cumpla el presupuesto. Si ninguno cumple no solicita inferencia insegura.
    if not affordable:
        raise RuntimeError('Recursos insuficientes para seleccionar automáticamente un modelo. Especifica uno pequeño y calibra la memoria.')
    return affordable[-1]['name']
