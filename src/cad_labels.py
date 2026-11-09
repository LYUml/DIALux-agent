"""Conservative fixture-label placement within the supplied room geometry."""
from shapely.geometry import Polygon, box
from shapely.affinity import rotate, translate


def place_fixture_labels(spec, layout, height, fixture_catalog=None):
    room = Polygon(spec['contour'])
    obstacles = [Polygon(p) for p in spec.get('exclusions', [])]
    bodies = []
    for fixture in layout['fixtures']:
        dimensions = spec['fixture'] if fixture_catalog is None else fixture_catalog[fixture['symbol_key']]
        width, depth = dimensions['width_m'], dimensions['depth_m']
        x, y = fixture['position_m'][:2]
        bodies.append(translate(rotate(box(-width/2, -depth/2, width/2, depth/2),
                                       fixture['rotation_deg'], origin=(0, 0)), x, y))
    occupied = obstacles + bodies
    result = {}
    for fixture, body in zip(layout['fixtures'], bodies):
        identity = fixture['id']
        # Deliberately generous envelopes, not a proof of rendered font metrics.
        half_width, half_height = len(identity)*height*.45, height*.8
        x, y = fixture['position_m'][:2]
        left, bottom, right, top = body.bounds
        gap = height*.3
        candidates = [(x, bottom-gap-half_height), (x, top+gap+half_height),
                      (right+gap+half_width, y), (left-gap-half_width, y)]
        candidates += [(x+shift, cy) for shift in (-half_width, half_width)
                       for cy in (bottom-gap-half_height, top+gap+half_height)]
        for cx, cy in candidates:
            envelope = box(cx-half_width, cy-half_height, cx+half_width, cy+half_height)
            if room.contains(envelope) and not any(envelope.intersects(o) for o in occupied):
                result[identity] = {'center_m': [cx, cy], 'envelope_m': list(envelope.bounds)}
                occupied.append(envelope)
                break
        else:
            raise ValueError(f'No clear label position for {identity}; revise annotation height or layout')
    return result
