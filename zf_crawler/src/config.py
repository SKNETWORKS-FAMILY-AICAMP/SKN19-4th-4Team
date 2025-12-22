"""
ZIP-FIT 프로젝트 설정 파일
임대/분양 공고문 기반 RAG 챗봇을 위한 DB 구축 설정
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 경로 설정
CURRENT_DIR = Path(__file__).parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
DATA_DIR = CURRENT_DIR / "data"

# PDF 파일 경로
LEASE_PDF_DIR = DATA_DIR / "LH_lease_서울.경기"
SALE_PDF_DIR = DATA_DIR / "LH_sale_서울.경기"

# CSV 파일 경로
LEASE_CORE_CSV = DATA_DIR / "lh_lease_notices-download_core.csv"
LEASE_META_CSV = DATA_DIR / "lh_lease_notices_eng_core.csv"
SALE_CORE_CSV = DATA_DIR / "lh_sale_notices-download_core.csv"
SALE_META_CSV = DATA_DIR / "lh_sale_notices_eng_core.csv"

# DB 설정 (psycopg2 호환)
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'dbname': os.getenv('DB_NAME')
}

# API 키
UPSTAGE_API_KEY = os.getenv('UPSTAGE_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# 임베딩 설정
EMBEDDING_MODEL_NAME = 'text-embedding-3-small'
EMBEDDING_DIMENSION = 1536

# 청킹 설정
MIN_CHUNK_SIZE = 50       # 최소 청크 크기 (문자) - 이보다 짧으면 필터링
OPTIMAL_CHUNK_SIZE = 600  # 최적 청크 크기 (토큰)
MAX_CHUNK_SIZE = 1200     # 최대 청크 크기 (토큰)
CHUNK_OVERLAP = 150       # 청크 오버랩 (토큰)
MAX_TABLE_SIZE = 3000     # 테이블 최대 크기 (토큰)

# 처리 설정
BATCH_SIZE = 10
MAX_WORKERS = 4

# 테이블 컨텍스트 추출용 키워드
TABLE_CONTEXT_KEYWORDS = [
    '소득', '자산', '면적', '임대', '보증금', '월세',
    '자격', '기준', '조건', '일정', '서류'
]

# =============================================================================
# 테이블 셀 텍스트 정규화 설정 (패턴 기반 - 확장 가능)
# =============================================================================
# 각 규칙: (패턴, 대체문자열, 설명, 반복횟수)
# 반복횟수: 패턴을 몇 번 반복 적용할지 (0=무한반복하여 변화없을때까지)

CELL_NORMALIZE_RULES = [
    # 1. 한글 문자 사이의 줄바꿈 제거 (공급\n형별 → 공급형별)
    (r'([가-힣])\n([가-힣])', r'\1\2', '한글 사이 줄바꿈 제거', 0),

    # 2. 일반 줄바꿈을 공백으로 변환
    (r'[\r\n]+', ' ', '줄바꿈 공백 변환', 1),

    # 3. 한글 문자 사이의 단일 공백 제거 (양 주 옥 정 → 양주옥정)
    (r'([가-힣])\s([가-힣])', r'\1\2', '한글 사이 공백 제거', 0),

    # 4. 한글과 숫자 사이 공백 제거 (옥정 3 → 옥정3)
    (r'([가-힣])\s+(\d)', r'\1\2', '한글-숫자 사이 공백 제거', 0),

    # 5. 한글과 영문 사이 공백 제거 (송내 S → 송내S)
    (r'([가-힣])\s+([A-Za-z])', r'\1\2', '한글-영문 사이 공백 제거', 0),

    # 6. 영문과 숫자 사이 공백 제거 (S 1 → S1)
    (r'([A-Za-z])\s+(\d)', r'\1\2', '영문-숫자 사이 공백 제거', 0),

    # 7. 연속 공백 정리
    (r'\s{2,}', ' ', '연속 공백 정리', 1),

    # 8. 셀 앞뒤 공백 제거 (strip)
    (r'^\s+|\s+$', '', '앞뒤 공백 제거', 1),
]

# 테이블 특정 컬럼에만 적용할 규칙 (선택적)
# 키: 컬럼명에 포함된 키워드, 값: 추가 적용할 규칙 인덱스 리스트
COLUMN_SPECIFIC_RULES = {
    # 현재는 모든 컬럼에 동일 규칙 적용
    # 필요시 특정 컬럼에 추가 규칙 지정 가능
    # 예: '단지': [추가규칙인덱스],
}
