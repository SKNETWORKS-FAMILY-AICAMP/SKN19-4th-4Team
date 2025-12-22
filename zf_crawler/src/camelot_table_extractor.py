"""Camelot 기반 PDF 테이블 추출"""
import camelot
import pandas as pd
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class ExtractedTable:
    page_number: int
    markdown: str
    headers: List[str]
    row_count: int
    col_count: int
    accuracy: float
    bbox: tuple = (0, 0, 0, 0)
    metadata: Dict = field(default_factory=dict)


def detect_header_rows(df: pd.DataFrame) -> int:
    """헤더 행 수 감지"""
    if df.empty or len(df) < 2:
        return 1

    header_keywords = {
        '구분', '항목', '유형', '자격', '기준', '요건', '내용', '순번', '번호',
        '순위', '단지', '주소', '면적', '세대', '신청', '접수', '서류', '일정',
        '기간', '대상', '조건', '공급', '타입', '호수', '층', '금액', '비고'
    }

    header_count = 0
    for i in range(min(4, len(df))):
        row_values = df.iloc[i].tolist()
        row_text = ' '.join(str(v) for v in row_values if v)
        numbers = sum(1 for v in row_values if str(v).replace(',', '').replace('.', '').isdigit())
        if numbers > len(row_values) // 2:
            break
        if any(kw in row_text for kw in header_keywords):
            header_count = i + 1
        else:
            break
    return max(1, header_count)


def merge_header_rows(df: pd.DataFrame, num_header_rows: int) -> List[str]:
    """여러 헤더 행을 하나로 병합"""
    if num_header_rows <= 1:
        return df.iloc[0].tolist()

    merged = []
    for col_idx in range(len(df.columns)):
        parts = []
        for row_idx in range(num_header_rows):
            val = str(df.iloc[row_idx, col_idx]).strip()
            if val and val not in parts:
                parts.append(val)
        merged.append(' - '.join(parts) if parts else f"col_{col_idx}")
    return merged


def clean_text(text: str) -> str:
    """NUL 문자 제거"""
    if not text:
        return ""
    text = text.replace('\x00', '')
    return ''.join(c for c in text if c >= ' ' or c in '\t\n\r')


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    """DataFrame을 마크다운 테이블로 변환"""
    if df.empty:
        return ""

    num_header_rows = detect_header_rows(df)
    headers = merge_header_rows(df, num_header_rows)
    data_df = df.iloc[num_header_rows:].reset_index(drop=True)
    headers = [clean_text(str(h).strip()) if h else f"col_{i}" for i, h in enumerate(headers)]

    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    for _, row in data_df.iterrows():
        cells = []
        for val in row.tolist():
            cell = clean_text(str(val).strip()) if val else ""
            cell = cell.replace("|", "\\|").replace("\n", " ")
            cells.append(cell)
        lines.append("| " + " | ".join(cells) + " |")

    return "\n".join(lines)


def extract_tables_from_pdf(pdf_path: Path, pages: str = "all", flavor: str = "lattice") -> List[ExtractedTable]:
    """PDF에서 테이블 추출"""
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")

    try:
        tables = camelot.read_pdf(str(pdf_path), pages=pages, flavor=flavor, copy_text=['v', 'h'])
    except Exception as e:
        print(f"Camelot 추출 실패: {e}")
        if flavor == "lattice":
            try:
                tables = camelot.read_pdf(str(pdf_path), pages=pages, flavor="stream")
            except:
                return []
        else:
            return []

    extracted = []
    for table in tables:
        df = table.df
        if df.empty:
            continue

        extracted.append(ExtractedTable(
            page_number=table.page,
            markdown=dataframe_to_markdown(df),
            headers=[str(h).strip() for h in df.iloc[0].tolist() if h],
            row_count=len(df),
            col_count=len(df.columns),
            accuracy=getattr(table, 'accuracy', 0.0),
            bbox=getattr(table, '_bbox', (0, 0, 0, 0))
        ))
    return extracted


def extract_tables_by_page(pdf_path: Path, page_numbers: List[int] = None) -> Dict[int, List[ExtractedTable]]:
    """페이지별로 테이블 추출"""
    pages = ",".join(map(str, page_numbers)) if page_numbers else "all"
    tables = extract_tables_from_pdf(pdf_path, pages=pages)

    by_page = {}
    for table in tables:
        by_page.setdefault(table.page_number, []).append(table)
    return by_page
