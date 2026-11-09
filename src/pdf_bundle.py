"""Explicit, source-bound assembly of static report pages using PDFium."""
from contextlib import closing
import hashlib
import io
import json
import math
from pathlib import Path

import pypdfium2 as pdfium
import pypdfium2.raw as raw


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _page_evidence(document, index):
    with closing(document[index]) as page:
        size = page.get_size()
        if any(not math.isfinite(v) or v <= 0 for v in size) or math.ceil(size[0])*math.ceil(size[1]) > 20_000_000:
            raise ValueError('Page exceeds bounded 72-dpi rendering size')
        with closing(page.get_textpage()) as text:
            text_hash = _sha(text.get_text_range().encode('utf-8'))
        with closing(page.render(scale=1)) as bitmap:
            image = bitmap.to_pil()
            pixels = _sha(image.tobytes())
            dimensions = list(image.size)
        return {'size_pt':list(size), 'text_sha256':text_hash,
                'render_72dpi_sha256':pixels, 'render_size_px':dimensions}


def build_pdf_bundle(sections: list, output_directory: str,
                     max_main_pages: int, max_bytes: int) -> dict:
    """Copy explicitly ordered 1-based pages, with no engineering authorship.

    Sources require SHA-256 pins. Static pages only; no form/signature preservation.
    Reopened output must match every source page's text, size and 72-dpi pixels.
    This is bounded rendering fidelity, not semantic or full-resolution proof.
    """
    if type(max_main_pages) is not int or not 1 <= max_main_pages <= 1000:
        raise ValueError('max_main_pages must be an integer from 1 to 1000')
    if type(max_bytes) is not int or max_bytes <= 0:
        raise ValueError('max_bytes must be a positive integer (decimal bytes)')
    if not isinstance(sections,list) or not 1 <= len(sections) <= 100:
        raise ValueError('Explicit nonempty sections required (maximum 100)')
    out = Path(output_directory).resolve()
    if out.exists():
        raise ValueError('New output directory required')
    mappings = []; sources = []; main_count = 0; seen = set(); appendix_started = False
    with pdfium.PdfDocument.new() as result:
        for section in sections:
            if not isinstance(section,dict) or set(section) != {'path','sha256','pages','role'}:
                raise ValueError('Section requires exactly path, sha256, pages and role')
            role = section['role']
            if role not in ('main','appendix') or (role == 'main' and appendix_started):
                raise ValueError('Main pages must precede appendices')
            appendix_started |= role == 'appendix'
            pages = section['pages']
            if not isinstance(pages,list) or not pages or any(type(n) is not int or n < 1 for n in pages):
                raise ValueError('Nonempty explicit 1-based page numbers required')
            if len(mappings)+len(pages) > 1000:
                raise ValueError('Maximum total page count is 1000')
            main_count += len(pages) if role == 'main' else 0
            if main_count > max_main_pages:
                raise ValueError('Main page limit exceeded')
            source = Path(section['path']).resolve(strict=True)
            data = source.read_bytes(); digest = _sha(data)
            if digest != section['sha256']:
                raise ValueError('Source SHA-256 differs: '+str(source))
            with pdfium.PdfDocument(data) as document:
                if document.get_formtype() != 0 or raw.FPDF_GetSignatureCount(document):
                    raise ValueError('Forms and signed documents are unsupported')
                for number in pages:
                    if number > len(document):
                        raise ValueError('Selected source page out of range')
                    identity = (digest,number)
                    if identity in seen:
                        raise ValueError('Duplicate source page selection')
                    seen.add(identity)
                    mappings.append({'output_page':len(mappings)+1, 'source':str(source),
                                     'source_sha256':digest, 'source_page':number, 'role':role,
                                     'evidence':_page_evidence(document,number-1)})
                result.import_pages(document,[n-1 for n in pages])
            sources.append({'path':str(source),'sha256':digest})
        if not main_count:
            raise ValueError('At least one main page required')
        stream = io.BytesIO(); result.save(stream); combined = stream.getvalue()
    if len(combined) > max_bytes:
        raise ValueError('Combined PDF byte limit exceeded')
    with pdfium.PdfDocument(combined) as reopened:
        if len(reopened) != len(mappings):
            raise ValueError('Reopened PDF page count differs')
        for index, mapping in enumerate(mappings):
            if _page_evidence(reopened,index) != mapping['evidence']:
                raise ValueError('Reopened PDF page rendering/text/size differs')
    for source in sources:
        if _sha(Path(source['path']).read_bytes()) != source['sha256']:
            raise ValueError('Source changed during assembly')
    manifest = {'schema':'dialux-agent/pdf-bundle/v1','state':'verified',
                'output':str(out/'bundle.pdf'),'sha256':_sha(combined),'size_bytes':len(combined),
                'page_count':len(mappings),'main_page_count':main_count,
                'max_main_pages':max_main_pages,'max_bytes':max_bytes,'pages':mappings,
                'rendering_72dpi_verified':True,'engineering_content_verified':False,
                'interactive_features_verified':False,'source_authenticity_verified':False}
    out.mkdir(parents=True,exist_ok=False)
    with (out/'bundle.pdf').open('xb') as file: file.write(combined)
    with (out/'manifest.json').open('x',encoding='utf-8') as file:
        json.dump(manifest,file,indent=2,allow_nan=False)
    return manifest


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request',required=True)
    args=parser.parse_args()
    print(json.dumps(build_pdf_bundle(**json.loads(Path(args.request).read_text(encoding='utf-8'))),indent=2))
