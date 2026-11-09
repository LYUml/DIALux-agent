import copy
import math

import ezdxf
import pytest

from src.cad_dimensions import add_dimensions, dimension_records, compare_dimensions, validate_dimensions


def sample():
    return {'id': 'D001', 'p1_m': [2, 3], 'p2_m': [8, 3], 'base_m': [2, 2], 'angle_deg': 0}


def test_real_dimensions_roundtrip_and_tampering(tmp_path):
    doc = ezdxf.new('R2018')
    doc.units = 6
    add_dimensions(doc, [sample()], .15)
    path = tmp_path/'dimensions.dxf'
    doc.saveas(path)
    before = dimension_records(path)
    assert before['D001'][-1] == pytest.approx(6)
    entity = list(doc.modelspace().query('DIMENSION'))[0]
    entity.dxf.defpoint3 = (9, 3, 0)
    doc.saveas(path)
    with pytest.raises(ValueError, match='geometry'):
        compare_dimensions(before, dimension_records(path))
    entity.dxf.text = '6000 mm'
    doc.saveas(path)
    with pytest.raises(ValueError, match='manual text'):
        dimension_records(path)


@pytest.mark.parametrize('key,value', [
    ('p1_m', [math.nan, 0]), ('p2_m', [2, 3]), ('base_m', [True, 0]),
    ('angle_deg', 90), ('angle_deg', 180), ('id', 'bad'),
])
def test_invalid_or_zero_projected_dimensions(key, value):
    item = sample()
    item[key] = value
    with pytest.raises(ValueError):
        validate_dimensions([item])


def test_duplicate_identity_and_removed_record():
    with pytest.raises(ValueError, match='unique'):
        validate_dimensions([sample(), copy.deepcopy(sample())])
    with pytest.raises(ValueError, match='identity'):
        compare_dimensions({'D001': [6]}, {})


def test_dimension_units_override_tampering(tmp_path):
    doc = ezdxf.new()
    add_dimensions(doc, [sample()], .15)
    entity = list(doc.modelspace().query('DIMENSION'))[0]
    override = entity.override()
    override['dimlfac'] = 1
    override.commit()
    path = tmp_path/'wrong-units.dxf'
    doc.saveas(path)
    with pytest.raises(ValueError, match='millimetre'):
        dimension_records(path)
