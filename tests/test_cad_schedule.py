import ezdxf
from src.cad_schedule import add_schedule_table, schedule_records


def test_schedule_records_preserve_values_and_detect_text_or_geometry_changes(tmp_path):
    doc = ezdxf.new('R2018')
    schedule = {'quantity':6,'product':{'reported_label':'Test product','article_number':'123',
                'power_w':26.,'luminaire_flux_lm':3602.}, 'total_reported_fixture_power_w':156.,
                'report_sha256':'a'*64,'source_layout_sha256':'b'*64}
    add_schedule_table(doc,schedule,(0,-2),.175)
    path = tmp_path/'schedule.dxf'
    doc.saveas(path)
    original = schedule_records(path)
    texts = [row[1] for row in original if row[0]=='TEXT']
    assert '26.0' in texts and '3602.0' in texts and '156.0' in texts
    assert 'a'*32 in texts and 'b'*32 in texts
    entity = next(e for e in doc.modelspace().query('TEXT') if e.dxf.text == '26.0')
    entity.dxf.text = '25.0'
    doc.saveas(path)
    assert schedule_records(path) != original
    entity.dxf.text = '26.0'
    entity.dxf.insert = (100,100,0)
    doc.saveas(path)
    assert schedule_records(path) != original
