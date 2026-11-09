"""Explicit linear CAD dimensions; coordinates in metres, labels in millimetres."""
import math
import re

import ezdxf


APP = 'DIALUX_AGENT_DIMENSION'


def validate_dimensions(items):
    if not isinstance(items, list) or len(items) > 1000:
        raise ValueError('Dimensions must be a list of at most 1000 entries')
    seen = set()
    for item in items:
        if not isinstance(item, dict) or set(item) != {'id', 'p1_m', 'p2_m', 'base_m', 'angle_deg'}:
            raise ValueError('Dimension requires id, p1_m, p2_m, base_m and angle_deg')
        identity = item['id']
        if not isinstance(identity, str) or not re.fullmatch(r'D[0-9]{1,8}', identity) or identity in seen:
            raise ValueError('Dimension IDs must be unique D-prefixed numbers')
        seen.add(identity)
        for key in ('p1_m', 'p2_m', 'base_m'):
            value = item[key]
            if not isinstance(value, list) or len(value) != 2 or any(
                type(v) not in (int, float) or not math.isfinite(v) for v in value
            ):
                raise ValueError('Dimension coordinates must be finite XY metres')
        angle = item['angle_deg']
        if type(angle) not in (int, float) or not math.isfinite(angle) or not 0 <= angle < 180:
            raise ValueError('Dimension angle must be in [0, 180) degrees')
        direction = (math.cos(math.radians(angle)), math.sin(math.radians(angle)))
        length = abs(sum((b-a)*v for a,b,v in zip(item['p1_m'], item['p2_m'], direction)))
        if length < .001:
            raise ValueError('Projected dimension must be at least one millimetre')
    return items


def add_dimensions(doc, items, text_height):
    items = validate_dimensions(items)
    if not items:
        return
    doc.appids.new(APP)
    doc.layers.new('DIMENSIONS', dxfattribs={'color': 7})
    for item in items:
        dimension = doc.modelspace().add_linear_dim(
            base=item['base_m'], p1=item['p1_m'], p2=item['p2_m'], angle=item['angle_deg'],
            dxfattribs={'layer': 'DIMENSIONS'},
            override={'dimlfac': 1000, 'dimpost': '<> mm', 'dimdec': 0,
                      'dimtxt': text_height, 'dimasz': text_height*.7, 'dimgap': text_height*.4})
        dimension.dimension.set_xdata(APP, [(1000, item['id'])])
        dimension.render()


def dimension_records(path):
    doc = ezdxf.readfile(path)
    records = {}
    for entity in doc.modelspace().query('DIMENSION'):
        if not entity.has_xdata(APP):
            raise ValueError('Dimension is missing agent identity')
        tags = entity.get_xdata(APP)
        identity = tags[0].value if len(tags) == 1 and tags[0].code == 1000 else None
        if not isinstance(identity, str) or not re.fullmatch(r'D[0-9]{1,8}', identity) or identity in records:
            raise ValueError('Invalid or duplicate native dimension identity')
        style = entity.override()
        if (entity.dxf.dimtype & 7) != 0 or entity.dxf.text not in ('', '<>'):
            raise ValueError('Unexpected dimension type or manual text override')
        if style.get('dimlfac') != 1000 or style.get('dimpost') != '<> mm' or style.get('dimdec') != 0:
            raise ValueError('Dimension millimetre label settings changed')
        records[identity] = [*entity.dxf.defpoint2, *entity.dxf.defpoint3,
                             *entity.dxf.defpoint, entity.dxf.angle, entity.get_measurement()]
    return records


def compare_dimensions(before, after):
    if set(before) != set(after) or any(
        len(before[key]) != len(after[key]) or any(
            not math.isclose(a, b, rel_tol=0, abs_tol=1e-8)
            for a, b in zip(before[key], after[key])) for key in before
    ):
        raise ValueError('Native dimension geometry or identity changed')
