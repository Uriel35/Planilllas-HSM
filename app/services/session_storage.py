"""Persistencia local y atómica de los borradores de formularios."""
import json
import os
from pathlib import Path
import tempfile


def load_session(path):
    path = Path(path)
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('version') != 1:
        raise ValueError('El archivo de datos no tiene un formato compatible.')
    for name in ('patient', 'drafts', 'saved'):
        if not isinstance(data.get(name), dict):
            raise ValueError(f'Sección inválida: {name}')
    records = [data['patient']]
    for name in ('drafts', 'saved'):
        records.extend(data[name].values())
    for record in records:
        if not isinstance(record, dict) or any(not isinstance(v, (str, bool)) for v in record.values()):
            raise ValueError('Hay valores inválidos en los datos guardados.')
    if data.get('current') is not None and not isinstance(data['current'], str):
        raise ValueError('La planilla seleccionada no es válida.')
    return data


def save_session(path, data):
    path = Path(path)
    fd, temporary = tempfile.mkstemp(prefix='.session-', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)
