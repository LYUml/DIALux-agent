"""Compare exact-scope report parameters with explicit expected values."""
import hashlib
import json
import math

if __package__:
    from .model_parameters import read_model_parameters
else:
    from model_parameters import read_model_parameters

FIELDS = {'ceiling_reflectance_pct', 'wall_reflectance_pct', 'floor_reflectance_pct',
          'maintenance_factor', 'mounting_height_m', 'wall_zone_m',
          'area_m2', 'height_m', 'workplane_m'}


def check_model_parameters(path: str, summary_id: str, expected_sha256: str,
                           expectations: dict) -> dict:
    """Require all supported parameters with explicit absolute tolerances.

    No default design criterion or rounding tolerance is silently adopted. A
    matching report is not proof of current native settings or fresh calculation.
    """
    if not isinstance(expectations, dict) or set(expectations) != FIELDS:
        raise ValueError('Explicit expectations for all nine supported parameters required')
    for key, item in expectations.items():
        if not isinstance(item, dict) or set(item) != {'value', 'absolute_tolerance'}:
            raise ValueError('Each expectation requires value and absolute_tolerance')
        for value in item.values():
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError('Expected values and tolerances must be finite numbers')
        value = item['value']
        if item['absolute_tolerance'] < 0:
            raise ValueError('Absolute tolerance must be nonnegative')
        if key.endswith('_pct') and not 0 <= value <= 100:
            raise ValueError('Reflectance expectation outside 0 to 100 percent')
        if key == 'maintenance_factor' and not 0 < value <= 1:
            raise ValueError('Maintenance factor expectation outside (0,1]')
        if key in {'area_m2', 'height_m', 'mounting_height_m'} and value <= 0:
            raise ValueError('Expected area and heights must be positive')
        if key in {'wall_zone_m', 'workplane_m'} and value < 0:
            raise ValueError('Expected zone and workplane must be nonnegative')
    report = read_model_parameters(path, summary_id)
    if not isinstance(expected_sha256, str) or report['report_sha256'] != expected_sha256:
        raise ValueError('Report hash differs from explicitly pinned source')
    checks = []
    for key in sorted(FIELDS):
        expected = expectations[key]
        actual = report['parameters'][key]
        error = abs(actual-expected['value'])
        checks.append({'parameter': key, 'reported': actual, **expected,
                       'absolute_error': error, 'matches': error <= expected['absolute_tolerance']})
    return {'schema': 'dialux-agent/model-parameter-check/v1',
            'report': report['report'], 'report_sha256': report['report_sha256'],
            'summary_id': summary_id, 'page': report['page'],
            'room_scene_header': report['room_scene_header'],
            'expectations_sha256': hashlib.sha256(json.dumps(expectations, sort_keys=True, allow_nan=False).encode()).hexdigest(),
            'all_reported_parameters_match': all(c['matches'] for c in checks), 'checks': checks,
            'live_model_verified': False, 'fresh_calculation_verified': False,
            'per_surface_materials_verified': False,
            'warning': 'Explicit comparison of rounded reported summaries only. Caller supplies expected values and tolerances; no engineering criterion or native-state correctness is inferred.'}
