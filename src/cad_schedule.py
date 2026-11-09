"""Editable CAD line/text table from the position-linked schedule adapter."""
import textwrap
import ezdxf
from ezdxf.tools.text_size import text_size


def schedule_records(path, layer='SCHEDULE'):
    records = []
    for entity in ezdxf.readfile(path).modelspace():
        if entity.dxf.layer != layer:
            continue
        if entity.dxftype() == 'TEXT':
            records.append(('TEXT', entity.dxf.text, *[round(v,8) for v in entity.dxf.insert],
                            round(entity.dxf.height,8), round(entity.dxf.rotation,8)))
        elif entity.dxftype() == 'LINE':
            records.append(('LINE', *[round(v,8) for v in (*entity.dxf.start,*entity.dxf.end)]))
        else:
            raise ValueError('Unexpected schedule CAD entity')
    return sorted(records)


def add_schedule_table(doc, schedule, origin, height, symbol_dimensions=None, symbol_label=None):
    # Called only after fresh PDF reading and exact positional correspondence.
    model = doc.modelspace()
    if 'SCHEDULE' not in doc.layers:
        doc.layers.new('SCHEDULE', dxfattribs={'color':7})
    x, y = origin
    def text(value, px, py):
        value = str(value)
        if '%%' in value or any(ord(c)<32 for c in value):
            raise ValueError('Unsupported CAD text escape or control character in schedule')
        return model.add_text(value, dxfattribs={'layer':'SCHEDULE','height':height,'insert':(px,py)})
    if symbol_dimensions is not None:
        width,depth=symbol_dimensions['width_m'],symbol_dimensions['depth_m']
        vertices=[(x,y),(x+width,y),(x+width,y-depth),(x,y-depth)]
        for a,b in zip(vertices,vertices[1:]+vertices[:1]):
            model.add_line(a,b,dxfattribs={'layer':'SCHEDULE'})
        model.add_line(vertices[3],vertices[1],dxfattribs={'layer':'SCHEDULE'})
        text(symbol_label,x+width+height,y-height)
        y-=max(depth,height*2)+height*2
    lines = ['REPORT-LINKED LUMINAIRE SCHEDULE | SYNTHETIC TEST',
             'Reported product: '+schedule['product']['reported_label'],
             'Article: '+schedule['product']['article_number'],
             'Positions matched to this group; supplied alignment.' if symbol_dimensions is not None else 'Positions matched to all drawing fixtures; supplied alignment.',
             (f"Symbol envelope: {symbol_dimensions['width_m']} x {symbol_dimensions['depth_m']} m (supplied)"
              if symbol_dimensions is not None else 'Product identity and manufacturer dimensions not authenticated.')]
    if symbol_dimensions is not None:
        lines += [f"Mounting height: {symbol_dimensions['mounting_height_m']} m",
                  'Drawing IDs: '+', '.join(f['fixture_id'] for f in schedule['fixtures'])]
    for value in lines:
        if '%%' in value or any(ord(c)<32 for c in value):
            raise ValueError('Unsupported CAD text escape or control character in schedule')
        for line in textwrap.wrap(value, width=64):
            text(line, x, y)
            y -= height*2
    headers = ['Qty', 'W / fitting', 'lm / fitting', 'Total W']
    values = [schedule['quantity'], schedule['product']['power_w'],
              schedule['product']['luminaire_flux_lm'], schedule['total_reported_fixture_power_w']]
    widths = [height*n for n in (7, 14, 15, 13)]
    cells = [[text(value,0,0) for value in row] for row in (headers, values)]
    widths = [max(width, max(text_size(row[index]).width for row in cells)*1.1+height)
              for index,width in enumerate(widths)]
    row_height = height*2.5
    top = y+height
    for index, row in enumerate(cells):
        cursor = x
        for width, entity in zip(widths, row):
            entity.dxf.insert = (cursor+height*.5, top-(index+1)*row_height+height*.6,0)
            cursor += width
    for row in range(3):
        model.add_line((x,top-row*row_height),(x+sum(widths),top-row*row_height),dxfattribs={'layer':'SCHEDULE'})
    cursor = x
    for width in [0,*widths]:
        cursor += width
        model.add_line((cursor,top),(cursor,top-2*row_height),dxfattribs={'layer':'SCHEDULE'})
    y = top-2*row_height-height*2
    for value in ['Total is reported fixture power, not verified BEC load.',
                  'Source PDF SHA256:', schedule['report_sha256'][:32], schedule['report_sha256'][32:],
                  'Observed layout SHA256:', schedule['source_layout_sha256'][:32], schedule['source_layout_sha256'][32:]]:
        text(value,x,y)
        y -= height*2
