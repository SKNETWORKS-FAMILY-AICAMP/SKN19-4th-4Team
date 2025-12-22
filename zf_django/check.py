# check_env.py
from decouple import config

print("--- .env 테스트 시작 ---")
try:
    # 1. DB 이름 읽어오기 시도
    db_name = config('DB_NAME')
    print(f"✅ 성공! DB_NAME = {db_name}")
except Exception as e:
    print(f"❌ 실패! 원인: {e}")

try:
    # 2. SECRET_KEY 읽어오기 시도
    secret = config('DJANGO_SECRET_KEY')
    print(f"✅ 성공! SECRET_KEY 앞 5글자 = {secret[:5]}")
except Exception as e:
    print(f"❌ 실패! SECRET_KEY를 못 찾았습니다. (띄어쓰기를 확인하세요)")