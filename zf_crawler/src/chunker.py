"""텍스트/테이블 청킹 모듈"""
import re
from typing import List, Optional
from dataclasses import dataclass, field
from .config import (
    MIN_CHUNK_SIZE, OPTIMAL_CHUNK_SIZE, MAX_CHUNK_SIZE,
    CHUNK_OVERLAP, MAX_TABLE_SIZE, TABLE_CONTEXT_KEYWORDS
)


@dataclass
class Chunk:
    text: str
    chunk_index: int
    page_number: int
    element_type: str  # 'text', 'table', 'heading'
    table_context: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    embedding: list = None


def count_tokens(text: str) -> int:
    """토큰 수 추정 (한글 기준)"""
    words = len(text.split())
    korean_chars = len(re.findall(r'[가-힣]', text))
    return words + korean_chars // 2


def split_text_into_chunks(text: str, chunk_size: int = OPTIMAL_CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """텍스트를 청크로 분할"""
    if count_tokens(text) <= chunk_size:
        return [text]

    paragraphs = re.split(r'\n\s*\n', text)
    chunks, current_chunk, current_size = [], [], 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        para_size = count_tokens(para)

        if para_size > chunk_size:
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk, current_size = [], 0
            chunks.extend(_split_by_sentences(para, chunk_size))
            continue

        if current_size + para_size <= chunk_size:
            current_chunk.append(para)
            current_size += para_size
        else:
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
            if overlap > 0 and current_chunk and count_tokens(current_chunk[-1]) <= overlap:
                current_chunk = [current_chunk[-1], para]
                current_size = count_tokens(current_chunk[-1]) + para_size
            else:
                current_chunk = [para]
                current_size = para_size

    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    return chunks


def _split_by_sentences(text: str, chunk_size: int) -> List[str]:
    """문장 단위로 분할"""
    sentences = re.split(r'(?<=[.!?。])\s+', text)
    chunks, current_chunk, current_size = [], [], 0

    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        sent_size = count_tokens(sent)
        if current_size + sent_size <= chunk_size:
            current_chunk.append(sent)
            current_size += sent_size
        else:
            if current_chunk:
                chunks.append(' '.join(current_chunk))
            current_chunk = [sent]
            current_size = sent_size

    if current_chunk:
        chunks.append(' '.join(current_chunk))
    return chunks


def clean_table_text(text: str) -> str:
    """테이블 텍스트 정리 (<br> 태그 제거, 불필요한 공백 정리)"""
    # <br> 태그를 공백으로 변환
    text = re.sub(r'<br\s*/?>', ' ', text, flags=re.IGNORECASE)
    # 연속 공백 정리
    text = re.sub(r'  +', ' ', text)
    return text


def extract_table_context(table_text: str) -> Optional[str]:
    """테이블 내용에서 컨텍스트(제목) 자동 추출"""
    lines = table_text.strip().split('\n')
    if not lines:
        return None

    # 마크다운 테이블인 경우 첫 행(헤더)에서 추출
    first_line = lines[0].strip()
    if first_line.startswith('|') and first_line.endswith('|'):
        # 헤더 셀 추출
        cells = [c.strip() for c in first_line.split('|') if c.strip()]
        if cells:
            # 주요 컬럼명 조합 (최대 3개)
            key_cells = [c for c in cells[:5] if len(c) >= 2 and not re.match(r'^[-\s]+$', c)][:3]
            if key_cells:
                return ' / '.join(key_cells)

    # 테이블 내용에서 키워드 추출
    keywords = [kw for kw in TABLE_CONTEXT_KEYWORDS if kw in table_text[:500]]
    if keywords:
        return ' / '.join(keywords[:3])

    return None


def chunk_table(table_text: str, context_title: str = None, max_size: int = MAX_TABLE_SIZE) -> List[str]:
    """테이블 청킹"""
    # 1. 텍스트 정리
    table_text = clean_table_text(table_text)

    # 2. 컨텍스트가 없으면 자동 추출
    if not context_title:
        context_title = extract_table_context(table_text)

    if count_tokens(table_text) <= max_size:
        return [f"## {context_title}\n\n{table_text}"] if context_title else [table_text]

    lines = table_text.split('\n')

    # 구분선 위치 찾기
    separator_idx = -1
    for i, line in enumerate(lines):
        if re.match(r'^\|[-:\s|]+\|$', line.strip()):
            separator_idx = i
            break

    # 구분선이 없거나 헤더가 비정상적이면 텍스트로 처리
    if separator_idx < 0 or separator_idx > 5:
        full_text = f"## {context_title}\n\n{table_text}" if context_title else table_text
        return split_text_into_chunks(full_text, chunk_size=max_size)

    # 헤더 추출
    header_text = '\n'.join(lines[:separator_idx + 1])
    header_size = count_tokens(header_text)

    # 데이터 행만 추출
    data_lines = lines[separator_idx + 1:]

    chunks, current_chunk, current_size = [], [], 0
    for line in data_lines:
        if not line.strip():
            continue
        line_size = count_tokens(line)
        if current_size + line_size + header_size <= max_size:
            current_chunk.append(line)
            current_size += line_size
        else:
            if current_chunk:
                chunk = header_text + '\n' + '\n'.join(current_chunk)
                chunks.append(f"## {context_title}\n\n{chunk}" if context_title else chunk)
            current_chunk = [line]
            current_size = line_size

    if current_chunk:
        chunk = header_text + '\n' + '\n'.join(current_chunk)
        chunks.append(f"## {context_title}\n\n{chunk}" if context_title else chunk)

    return chunks


def is_valid_chunk(text: str, min_size: int = MIN_CHUNK_SIZE) -> bool:
    """청크 유효성 검사"""
    if not text or not text.strip():
        return False
    stripped = text.strip()
    if len(stripped) < min_size:
        return False

    meaningless = [r'^-\s*\d+\s*-$', r'^#{1,6}\s*\d+\.?\s*$', r'^-{3,}$', r'^\*{3,}$']
    return not any(re.match(p, stripped) for p in meaningless)


def _find_context_from_previous(elements: List, current_idx: int, lookback: int = 5) -> Optional[str]:
    """테이블 앞 요소들에서 컨텍스트(제목/단지명 등) 추출

    heading이나 짧은 text 요소에서 의미있는 제목을 찾음
    """
    for j in range(current_idx - 1, max(-1, current_idx - lookback - 1), -1):
        prev = elements[j]
        content = prev.content.strip()

        # 페이지 번호나 무의미한 내용 무시
        if re.match(r'^-?\s*\d+\s*-?$', content):
            continue

        # heading은 무조건 사용
        if prev.element_type == 'heading':
            return content

        # 짧은 텍스트(100자 이하)는 제목일 가능성이 높음
        if prev.element_type == 'text' and len(content) <= 100:
            # page_header 태그 제거
            clean = re.sub(r'<page_header>([^<]+)</page_header>', r'\1', content)
            clean = clean.strip()
            if clean and len(clean) >= 3:
                return clean

    return None


def create_chunks_from_elements(elements: List, document_id: str = None) -> List[Chunk]:
    """ParsedElement 리스트에서 청크 생성"""
    chunks = []
    chunk_index = 0
    current_heading = None

    for i, elem in enumerate(elements):
        if elem.element_type == 'heading':
            current_heading = elem.content
            continue

        elif elem.element_type == 'table':
            # 1. metadata에 있으면 사용
            context = elem.metadata.get('context_title')

            # 2. 직전 heading 사용
            if not context:
                context = current_heading

            # 3. 컨텍스트가 없거나 너무 일반적이면 앞 요소에서 추출
            generic_contexts = ['소득', '자산', '면적', '임대', '보증금', '월세', '자격', '기준', '조건', '일정', '서류']
            if not context or any(context == gc or context.startswith(gc + ' /') for gc in generic_contexts):
                found = _find_context_from_previous(elements, i)
                if found:
                    context = found

            for tc in chunk_table(elem.content, context):
                if is_valid_chunk(tc, min_size=30):
                    # chunk_table에서 자동 생성된 ## 제목 추출
                    final_context = context
                    if not final_context and tc.startswith('## '):
                        final_context = tc.split('\n')[0][3:].strip()
                    chunks.append(Chunk(tc, chunk_index, elem.page_number, 'table', final_context, {'document_id': document_id}, embedding=None))
                    chunk_index += 1
            current_heading = None

        elif elem.element_type == 'text':
            text = f"## {current_heading}\n\n{elem.content}" if current_heading else elem.content
            current_heading = None
            for tc in split_text_into_chunks(text):
                if is_valid_chunk(tc):
                    chunks.append(Chunk(tc, chunk_index, elem.page_number, 'text', None, {'document_id': document_id}, embedding=None))
                    chunk_index += 1

    return chunks
