"""Guarded numeric commits for a rigid array transform; native adapters supply I/O."""
import math

MOTION_FIELDS=('PolygonPosition_X','PolygonPosition_Y','PolygonPosition_Z','ArrangementRotation_Z')
COUNT_FIELDS=('ElementCountX','ElementCountY')
FIELDS=COUNT_FIELDS+MOTION_FIELDS+('ArrangementObjectName',)


def _display_values(values):
    if not isinstance(values,dict) or set(values)!=set(FIELDS):
        raise ValueError('Complete native array fields required')
    result={}
    for key in FIELDS:
        value=values[key]
        if not isinstance(value,str) or not value.strip():
            raise ValueError('Native array values must be nonempty display strings')
        if key=='ArrangementObjectName': result[key]=value;continue
        try: result[key]=float(value)
        except (ValueError,OverflowError) as exc: raise ValueError('Invalid array number') from exc
        if not math.isfinite(result[key]): raise ValueError('Nonfinite array number')
    if any(result[k]!=int(result[k]) or not 1<=result[k]<=1000 for k in COUNT_FIELDS) or result[COUNT_FIELDS[0]]*result[COUNT_FIELDS[1]]>2000:
        raise ValueError('Unsupported native array counts')
    return result


def commit_array_fields(expected, requested, read_fields, write_field, record):
    """Check the complete field vector before/after every submitted edit.

    write_field must guard native selection, SetValue, then explicitly focus the
    supplied commit field. record must durably persist intent before writing.
    This internal helper does not inspect individual fixture geometry or save.
    """
    committed=_display_values(expected)
    if not isinstance(requested,dict) or set(requested)!=set(MOTION_FIELDS):
        raise ValueError('Exact XYZ and Z-rotation targets required')
    if any(type(v) not in (int,float) or not math.isfinite(v) for v in requested.values()):
        raise ValueError('Finite numeric array targets required')
    completed=[]
    def check(stage):
        actual=_display_values(read_fields())
        for key in FIELDS:
            same=actual[key]==committed[key] if key in COUNT_FIELDS+('ArrangementObjectName',) else math.isclose(actual[key],committed[key],rel_tol=0,abs_tol=.00051)
            if not same:
                raise ValueError(f'Array {stage} differs at {key}; committed fields={completed}; inspect before retry')
        return actual
    check('initial state')
    for index,key in enumerate(MOTION_FIELDS):
        check('before write')
        value=requested[key]
        if math.isclose(value,committed[key],rel_tol=0,abs_tol=1e-10): continue
        record({'state':'pending_field','field':key,'target':value,'completed_fields':list(completed)})
        write_field(key,value,MOTION_FIELDS[(index+1)%len(MOTION_FIELDS)])
        committed[key]=value
        check('after commit')
        completed.append(key)
        record({'state':'field_verified','field':key,'completed_fields':list(completed)})
    after=check('final state')
    return {'before':dict(expected),'after':after,'completed_fields':completed,
            'fixture_geometry_verified':False,'native_project_saved':False}
