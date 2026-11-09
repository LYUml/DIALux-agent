"""Fixed-paper model-space frames; preserves all engineering coordinates."""
from ezdxf import bbox
from ezdxf.tools.text_size import text_size


def add_sheet(doc, config):
    required = {'paper','scale_denominator','title','drawing_number','revision'}
    if not isinstance(config,dict) or set(config)!=required:
        raise ValueError('Sheet requires paper, scale_denominator, title, drawing_number and revision')
    papers={'A3':(420,297),'A2':(594,420),'A1':(841,594),'A0':(1189,841)}
    paper=config['paper']; scale=config['scale_denominator']
    if not isinstance(paper,str) or paper not in papers or type(scale) is not int or scale not in {25,50,100,200,500}:
        raise ValueError('Unsupported sheet paper or fixed scale')
    for key in ('title','drawing_number','revision'):
        value=config[key]
        if not isinstance(value,str) or not value.strip() or len(value)>100 or not value.isascii() or '%%' in value or any(ord(c)<32 for c in value):
            raise ValueError('Sheet metadata requires plain ASCII text without CAD escapes')
    if doc.units!=6 or 'SHEET' in doc.layers:
        raise ValueError('Sheet requires metre drawing units and no existing sheet layer')
    model=doc.modelspace()
    bounds=bbox.extents(model,fast=False)
    if not bounds.has_data:
        raise ValueError('Cannot frame empty drawing')
    unit=scale/1000
    width,height=((v-40)*unit for v in papers[paper])
    pad=5*unit; title_height=30*unit
    if bounds.size.x>width-2*pad or bounds.size.y>height-title_height-2*pad:
        raise ValueError('Drawing content does not fit requested sheet at fixed scale')
    left=bounds.extmin.x-pad; top=bounds.extmax.y+pad
    right=left+width; bottom=top-height; split=bottom+title_height
    doc.layers.new('SHEET',dxfattribs={'color':7})
    def line(a,b):model.add_line(a,b,dxfattribs={'layer':'SHEET'})
    for a,b in [((left,bottom),(right,bottom)),((right,bottom),(right,top)),
                ((right,top),(left,top)),((left,top),(left,bottom)),
                ((left,split),(right,split)),((left,bottom+15*unit),(right,bottom+15*unit))]:line(a,b)
    def label(value,x,y,max_width):
        entity=model.add_text(value,dxfattribs={'layer':'SHEET','height':2.5*unit,'insert':(x,y)})
        if text_size(entity).width*1.1>max_width:
            raise ValueError('Sheet metadata exceeds its titleblock cell')
    label(config['title'],left+pad,bottom+22*unit,width-2*pad)
    cells=[('Drawing: '+config['drawing_number']),('Revision: '+config['revision']),
           f"{paper} | 1:{scale} | SYNTHETIC TEST"]
    for index,value in enumerate(cells):
        x=left+index*width/3
        if index:line((x,bottom),(x,bottom+15*unit))
        label(value,x+pad,bottom+6*unit,width/3-2*pad)
    return {'paper':paper,'scale_denominator':scale,'frame_m':[left,bottom,right,top],
            'content_bounds_m':[bounds.extmin.x,bounds.extmin.y,bounds.extmax.x,bounds.extmax.y],
            'margin_mm':20,'titleblock_height_mm':30,
            'estimated_content_fit':True,'native_print_verified':False}
