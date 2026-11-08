import copy
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from backend import create_room, inspect_stf
from dialux_agent import inventory, verify


@pytest.fixture
def spec():
    return json.loads((ROOT / 'examples/validation-room.json').read_text())


def test_roundtrip(spec, tmp_path):
    path = tmp_path / 'room.stf'
    result = create_room(spec, str(path))
    room = inspect_stf(str(path))['salas'][0]
    assert result['dialux_import_verified'] is False
    assert room['area_m2'] == 24
    assert room['altura_m'] == 3
    assert room['plano_trabajo_m'] == .8
    assert room['reflectancia_techo'] == 70
    assert room['factor_mantenimiento'] == .8


@pytest.mark.parametrize('key,value', [
    ('name', 'x\n[Project]'), ('units', 'mm'), ('assumptions', []),
    ('height_m', float('nan')), ('workplane_m', 3),
    ('maintenance_factor', 0), ('wall_reflectance_pct', 101),
    ('contour', [[0,0],[2,2],[0,2],[2,0]]),
    ('height_m', True), ('height_m', '3'), ('assumptions', ['']),
    ('assumptions', [42]), ('contour', []), ('contour', [1,2,3]),
    ('contour', [[False,0],[2,0],[2,2]]),
])
def test_reject_invalid(spec, tmp_path, key, value):
    spec[key] = value
    path = tmp_path / 'invalid.stf'
    with pytest.raises((ValueError, TypeError)):
        create_room(spec, str(path))
    assert not path.exists()


def test_preserve_existing(spec, tmp_path):
    path = tmp_path / 'existing.stf'
    path.write_bytes(b'original')
    with pytest.raises(ValueError):
        create_room(spec, str(path))
    assert path.read_bytes() == b'original'


def test_source_changes_detected(tmp_path):
    path = tmp_path / 'source.dwg'
    path.write_bytes(b'AC1032original')
    manifest = inventory(str(tmp_path))
    assert verify(manifest)['ok']
    path.write_bytes(b'AC1032modified')
    assert verify(manifest)['changed_or_missing'] == ['source.dwg']


def test_cli_from_other_directory(tmp_path):
    output = tmp_path / 'cli.stf'
    command = [sys.executable, str(ROOT/'src/dialux_agent.py'), 'room-create',
               '--spec', str(ROOT/'examples/validation-room.json'), '--output', str(output)]
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['area_m2'] == 24
    second = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert second.returncode != 0
    assert json.loads(second.stdout)['ok'] is False
