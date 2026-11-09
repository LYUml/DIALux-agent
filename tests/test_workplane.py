import pytest
from src.workplane import parse_workplane_page

HEADER='Building . Storey . Room (Light scene 1)'
TEXT='Project\n'+HEADER+'\nCalculation objects\nWorking planes\nProperties \u0112 Emin Emax Uo (g1) g2 Index\n(Target) (Target)\nWorking plane (Room) 497 lx 31.5 lx 621 lx 0.063 0.051 WP1\nPerpendicular illuminance (adaptive) (>= 500 lx) (>= 0.60)\nHeight: 0.800 m, Wall zone: 0.000 m\n20'


def test_direct_extrema_are_not_reconstructed_from_rounded_ratio():
    r=parse_workplane_page(TEXT,HEADER,'WP1')
    values={m['metric']:m['value'] for m in r['measurements']}
    assert values['minimum_illuminance']==31.5
    assert values['minimum_illuminance']!=values['average_perpendicular_illuminance']*values['uniformity_u0']
    assert values['maximum_illuminance']==621
    assert not r['task_surface_applicability_verified']


@pytest.mark.parametrize('change',['header','surface','duplicate','columns','basis','height','order','uniformity'])
def test_workplane_refuses_ambiguous_or_mismatched_scope(change):
    text=TEXT
    if change=='header': text=text.replace(HEADER,'Other room')
    if change=='surface': text=text.replace('WP1','WP2')
    if change=='duplicate': text+='\nWorking plane (Room) 497 lx 31.5 lx 621 lx 0.063 0.051 WP1'
    if change=='columns': text=text.replace('Emin Emax','Emax Emin')
    if change=='basis': text=text.replace('Perpendicular illuminance','Vertical illuminance')
    if change=='height': text+='\nHeight: 0.800 m, Wall zone: 0.000 m'
    if change=='order': text=text.replace('31.5 lx','700 lx')
    if change=='uniformity': text=text.replace('0.063','1.1')
    with pytest.raises(ValueError):parse_workplane_page(text,HEADER,'WP1')


def test_unlit_uniformity_stays_unavailable():
    text=TEXT.replace('497 lx 31.5 lx 621 lx 0.063 0.051','0 lx 0 lx 0 lx - -')
    r=parse_workplane_page(text,HEADER,'WP1')
    assert r['unavailable_uniformity']
    assert len(r['measurements'])==3
