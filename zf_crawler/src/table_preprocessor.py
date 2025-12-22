"""테이블 셀 텍스트 정규화 모듈

PDF에서 추출된 테이블의 셀 텍스트를 정규화합니다.
- 한글 문자 사이 줄바꿈/공백 제거
- 연속 공백 정리
- 확장 가능한 패턴 기반 처리
"""
import re
from typing import List, Tuple, Optional
from .config import CELL_NORMALIZE_RULES, COLUMN_SPECIFIC_RULES


def apply_normalize_rule(text: str, pattern: str, replacement: str, repeat: int = 1) -> str:
    """단일 정규화 규칙 적용

    Args:
        text: 입력 텍스트
        pattern: 정규식 패턴
        replacement: 대체 문자열
        repeat: 반복 횟수 (0=변화없을때까지 반복)

    Returns:
        정규화된 텍스트
    """
    if repeat == 0:
        # 변화가 없을 때까지 반복
        prev = None
        while prev != text:
            prev = text
            text = re.sub(pattern, replacement, text)
        return text
    else:
        for _ in range(repeat):
            text = re.sub(pattern, replacement, text)
        return text


def normalize_cell_text(text: str, rules: List[Tuple] = None) -> str:
    """셀 텍스트 정규화

    Args:
        text: 원본 셀 텍스트
        rules: 적용할 규칙 리스트. None이면 기본 규칙 사용

    Returns:
        정규화된 텍스트
    """
    if not text:
        return ""

    rules = rules or CELL_NORMALIZE_RULES

    for rule in rules:
        pattern, replacement, description, repeat = rule
        text = apply_normalize_rule(text, pattern, replacement, repeat)

    return text


def _merge_broken_table_lines(lines: List[str]) -> List[str]:
    """여러 줄에 걸쳐 깨진 테이블 행을 병합

    PDF 추출 시 셀 내 줄바꿈이 테이블 행 분리로 잘못 인식되는 경우 처리
    예: '| 단지 | 공급\n형별 |' → '| 단지 | 공급형별 |'

    Args:
        lines: 원본 라인 리스트

    Returns:
        병합된 라인 리스트
    """
    if not lines:
        return lines

    merged = []
    current_line = ""

    for line in lines:
        stripped = line.strip()

        # 빈 줄은 그대로
        if not stripped:
            if current_line:
                merged.append(current_line)
                current_line = ""
            merged.append(line)
            continue

        # 구분선(---|---|---)은 그대로
        if re.match(r'^\|[\s\-:|]+\|$', stripped):
            if current_line:
                merged.append(current_line)
                current_line = ""
            merged.append(line)
            continue

        # 테이블 행 시작 (|로 시작하고 |로 끝남)
        if stripped.startswith('|') and stripped.endswith('|'):
            if current_line:
                merged.append(current_line)
            current_line = line
            continue

        # 테이블 행 시작만 (|로 시작하지만 |로 안 끝남) - 다음 줄에 이어짐
        if stripped.startswith('|') and not stripped.endswith('|'):
            if current_line:
                merged.append(current_line)
            current_line = line
            continue

        # 테이블 행 끝만 (|로 안 시작하지만 |로 끝남) - 이전 줄에서 이어짐
        if not stripped.startswith('|') and stripped.endswith('|'):
            if current_line:
                # 이전 줄과 현재 줄 병합 (줄바꿈 없이)
                current_line = current_line.rstrip() + stripped
            else:
                current_line = line
            merged.append(current_line)
            current_line = ""
            continue

        # 테이블 중간 부분 (|로 시작도 끝도 안함) - 이전 줄에서 이어짐
        if current_line:
            # 이전 줄과 현재 줄 병합
            current_line = current_line.rstrip() + stripped
        else:
            # 테이블이 아닌 일반 텍스트
            merged.append(line)

    if current_line:
        merged.append(current_line)

    return merged


def normalize_markdown_table(markdown: str) -> str:
    """마크다운 테이블 전체 정규화

    테이블의 각 셀에 정규화 규칙을 적용합니다.
    여러 줄에 걸쳐 깨진 테이블 행도 처리합니다.

    Args:
        markdown: 마크다운 테이블 문자열

    Returns:
        정규화된 마크다운 테이블
    """
    if not markdown or not markdown.strip():
        return markdown

    lines = markdown.split('\n')

    # 1단계: 깨진 테이블 행 병합
    lines = _merge_broken_table_lines(lines)

    normalized_lines = []

    for line in lines:
        if not line.strip():
            normalized_lines.append(line)
            continue

        # 구분선(---|---|---)은 그대로 유지
        if re.match(r'^\|[\s\-:|]+\|$', line.strip()):
            normalized_lines.append(line)
            continue

        # 테이블 행이 아니면 그대로
        if not line.strip().startswith('|'):
            normalized_lines.append(line)
            continue

        # 테이블 셀 분리 및 정규화
        # 이스케이프된 파이프(\|)를 임시 문자로 대체
        temp_line = line.replace('\\|', '\x00PIPE\x00')
        cells = temp_line.split('|')

        normalized_cells = []
        for cell in cells:
            # 임시 문자를 다시 이스케이프된 파이프로 복원
            cell = cell.replace('\x00PIPE\x00', '\\|')
            # 셀 내용 정규화
            normalized_cell = normalize_cell_text(cell)
            normalized_cells.append(normalized_cell)

        normalized_lines.append('|'.join(normalized_cells))

    return '\n'.join(normalized_lines)


def normalize_dataframe_cell(value) -> str:
    """DataFrame 셀 값 정규화

    pandas DataFrame의 셀 값에 정규화 적용

    Args:
        value: 셀 값 (any type)

    Returns:
        정규화된 문자열
    """
    if value is None:
        return ""

    text = str(value).strip()
    return normalize_cell_text(text)


class TablePreprocessor:
    """테이블 전처리기 클래스

    확장 가능한 테이블 전처리를 위한 클래스.
    규칙을 동적으로 추가/제거할 수 있습니다.
    """

    def __init__(self, rules: List[Tuple] = None):
        """
        Args:
            rules: 사용할 규칙 리스트. None이면 기본 규칙 사용
        """
        self.rules = list(rules or CELL_NORMALIZE_RULES)
        self.column_rules = dict(COLUMN_SPECIFIC_RULES)

    def add_rule(self, pattern: str, replacement: str, description: str, repeat: int = 1, index: int = None):
        """규칙 추가

        Args:
            pattern: 정규식 패턴
            replacement: 대체 문자열
            description: 규칙 설명
            repeat: 반복 횟수
            index: 삽입 위치 (None이면 끝에 추가)
        """
        rule = (pattern, replacement, description, repeat)
        if index is None:
            self.rules.append(rule)
        else:
            self.rules.insert(index, rule)

    def remove_rule(self, index: int):
        """규칙 제거

        Args:
            index: 제거할 규칙 인덱스
        """
        if 0 <= index < len(self.rules):
            self.rules.pop(index)

    def normalize_cell(self, text: str, column_name: str = None) -> str:
        """셀 텍스트 정규화

        Args:
            text: 원본 텍스트
            column_name: 컬럼명 (컬럼별 추가 규칙 적용용)

        Returns:
            정규화된 텍스트
        """
        result = normalize_cell_text(text, self.rules)

        # 컬럼별 추가 규칙 적용
        if column_name:
            for keyword, rule_indices in self.column_rules.items():
                if keyword in column_name:
                    for idx in rule_indices:
                        if 0 <= idx < len(self.rules):
                            rule = self.rules[idx]
                            result = apply_normalize_rule(
                                result, rule[0], rule[1], rule[3]
                            )

        return result

    def normalize_table(self, markdown: str) -> str:
        """마크다운 테이블 정규화

        Args:
            markdown: 마크다운 테이블 문자열

        Returns:
            정규화된 마크다운 테이블
        """
        return normalize_markdown_table(markdown)

    def get_rules_info(self) -> List[dict]:
        """현재 규칙 정보 반환"""
        return [
            {
                'index': i,
                'pattern': rule[0],
                'replacement': repr(rule[1]),
                'description': rule[2],
                'repeat': rule[3]
            }
            for i, rule in enumerate(self.rules)
        ]

