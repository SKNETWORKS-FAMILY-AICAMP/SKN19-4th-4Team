"""PDF 파싱 모듈 - LlamaParse + Camelot 하이브리드"""
import os
import re
from pathlib import Path
from dataclasses import dataclass, field
from llama_cloud_services import LlamaParse


@dataclass
class ParsedElement:
    """파싱된 문서 요소"""
    content: str
    element_type: str  # 'text', 'table', 'heading'
    page_number: int
    metadata: dict = field(default_factory=dict)


@dataclass
class ParsedDocument:
    """파싱된 문서"""
    file_path: str
    external_id: str
    elements: list
    raw_markdown: str


def parse_pdf(file_path: Path, external_id: str, use_camelot: bool = True) -> ParsedDocument:
    """PDF 파싱 (LlamaParse + Camelot 하이브리드)"""
    if not os.getenv("LLAMA_CLOUD_API_KEY"):
        raise ValueError("LLAMA_CLOUD_API_KEY 환경변수 필요")

    parser = LlamaParse(result_type="markdown", verbose=True)
    json_result = parser.get_json_result(str(file_path))

    elements = []
    raw_parts = []

    if json_result and 'pages' in json_result[0]:
        for page in json_result[0]['pages']:
            page_num = page.get('page', 1)
            content = page.get('md', '').strip()
            if content:
                raw_parts.append(content)
                elements.extend(_extract_elements(content, page_num))

    # Camelot으로 테이블 대체
    if use_camelot:
        elements = _replace_with_camelot(file_path, elements)

    return ParsedDocument(str(file_path), external_id, elements, "\n\n".join(raw_parts))


def _replace_with_camelot(file_path: Path, elements: list) -> list:
    """LlamaParse 테이블을 Camelot 테이블로 대체"""
    try:
        from .camelot_table_extractor import extract_tables_by_page
        camelot_tables = extract_tables_by_page(file_path)
    except Exception as e:
        print(f"Camelot 실패: {e}")
        return elements

    if not camelot_tables:
        return elements

    camelot_idx = {p: 0 for p in camelot_tables}
    result = []

    for elem in elements:
        if elem.element_type != 'table':
            result.append(elem)
            continue

        page = elem.page_number
        if page in camelot_tables:
            idx = camelot_idx[page]
            if idx < len(camelot_tables[page]):
                ct = camelot_tables[page][idx]
                camelot_idx[page] += 1
                if ct.accuracy >= 70.0:
                    result.append(ParsedElement(
                        ct.markdown, 'table', page,
                        {'accuracy': ct.accuracy, 'source': 'camelot'}
                    ))
                    continue
        result.append(elem)

    # 미사용 Camelot 테이블 추가
    for page, tables in camelot_tables.items():
        for t in tables[camelot_idx.get(page, 0):]:
            if t.accuracy >= 70.0:
                result.append(ParsedElement(t.markdown, 'table', page, {'source': 'camelot'}))

    result.sort(key=lambda x: (x.page_number, x.element_type == 'table'))
    return result


def _extract_elements(markdown: str, page_number: int) -> list:
    """마크다운에서 요소 추출"""
    elements = []
    current_text = []
    current_table = []
    in_table = False

    for line in markdown.split('\n'):
        # 헤딩
        if line.startswith('#'):
            if current_text:
                text = '\n'.join(current_text).strip()
                if text:
                    elements.append(ParsedElement(text, 'text', page_number))
                current_text = []

            level = len(line) - len(line.lstrip('#'))
            heading = line.lstrip('#').strip()
            if heading:
                elements.append(ParsedElement(heading, 'heading', page_number, {'level': level}))

        # 테이블
        elif line.strip().startswith('|'):
            if not in_table:
                if current_text:
                    text = '\n'.join(current_text).strip()
                    if text:
                        elements.append(ParsedElement(text, 'text', page_number))
                    current_text = []
                in_table = True
            current_table.append(line)

        else:
            if in_table:
                elements.append(ParsedElement('\n'.join(current_table), 'table', page_number))
                current_table = []
                in_table = False
            if line.strip():
                current_text.append(line)

    # 마지막 처리
    if in_table and current_table:
        elements.append(ParsedElement('\n'.join(current_table), 'table', page_number))
    elif current_text:
        text = '\n'.join(current_text).strip()
        if text:
            elements.append(ParsedElement(text, 'text', page_number))

    return elements
