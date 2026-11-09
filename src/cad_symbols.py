"""Strict shape evidence for the agent's rectangular luminaire CAD blocks."""
import math
import ezdxf


def fixture_block_records(path):
    doc=ezdxf.readfile(path)
    names={e.dxf.name for e in doc.modelspace().query('INSERT[layer=="LUMINAIRES"]')}
    if not names: raise ValueError('No luminaire blocks to verify')
    result={}
    def vector(value):
        values=tuple(float(v) for v in value)
        if any(not math.isfinite(v) for v in values): raise ValueError('Nonfinite block geometry')
        return values
    for name in sorted(names):
        block=doc.blocks.get(name)
        shapes=[];attributes=[]
        for entity in block:
            kind=entity.dxftype()
            if kind=='LINE':
                shapes.append(('LINE',vector(entity.dxf.start),vector(entity.dxf.end),vector(entity.dxf.extrusion),float(entity.dxf.thickness)))
            elif kind=='LWPOLYLINE':
                shapes.append(('LWPOLYLINE',bool(entity.closed),float(entity.dxf.elevation),
                    float(entity.dxf.const_width),vector(entity.dxf.extrusion),float(entity.dxf.thickness),
                    tuple(vector(point) for point in entity.get_points('xyseb'))))
            elif kind=='ATTDEF':
                attributes.append((entity.dxf.tag,entity.dxf.text,vector(entity.dxf.insert),
                    float(entity.dxf.height),float(entity.dxf.rotation),int(entity.dxf.halign),int(entity.dxf.valign)))
            else:
                raise ValueError('Unsupported luminaire block entity: '+kind)
        if not shapes or [a[0] for a in attributes]!=['FIXTURE_ID']:
            raise ValueError('Expected luminaire shape and one FIXTURE_ID definition')
        result[name]={'base_point':vector(block.block.dxf.base_point),
                      'shapes':sorted(shapes,key=repr),'attributes':attributes}
    return result


def compare_fixture_blocks(before,after):
    def same(a,b):
        if isinstance(a,dict):
            return isinstance(b,dict) and set(a)==set(b) and all(same(a[k],b[k]) for k in a)
        if isinstance(a,(tuple,list)):
            return isinstance(b,(tuple,list)) and len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
        if isinstance(a,bool): return type(b) is bool and a==b
        if isinstance(a,(int,float)):
            return type(b) in (int,float) and math.isfinite(a) and math.isfinite(b) and math.isclose(a,b,rel_tol=0,abs_tol=1e-8)
        return type(a) is type(b) and a==b
    if not same(before,after): raise ValueError('Native luminaire block shapes or definitions changed')
