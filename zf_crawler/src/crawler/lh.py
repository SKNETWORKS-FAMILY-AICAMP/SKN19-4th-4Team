import time, requests
from datetime import datetime
from bs4 import BeautifulSoup
import json
import os

class LH():

    # ==================================
    # 1. 환경 설정 및 상수 정의
    # ==================================

    # 🚩 필터 기준: 게시일 >= 2024-11-01
    START_DATE_FILTER = datetime(2024, 11, 1)
    START_DATE_REQUEST = START_DATE_FILTER.strftime("%Y-%m-%d")

    # 현재 날짜 (조회 종료일)
    TODAY_DATE_REQUEST = datetime.now().strftime("%Y-%m-%d")

    BASE_URL = "https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancList.do"
    DETAIL_URL_BASE = "https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancInfo.do?mi=1026"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Referer": "https://apply.lh.or.kr/"
    }

    # Payload 템플릿
    FORM_DATA_TEMPLATE = {
        'currPage': 1,
        'panId': '',
        'cnpCd': '',
        'prevListCo': 50,
        'srchAisTpCd': '',
        'panSs': '',
        'startDt': START_DATE_REQUEST,
        'endDt': TODAY_DATE_REQUEST,
        'aisTpCd': '',
        'uppAisTpCd': '',
        'mi': '',
        'srchUppAisTpCd': '',
        'srchY': 'N',
        'srchFilter': 'N',
        'csCd': '',
        'CNP_CD': '',
        'ccrCnntSysDsCd': '',
        'xssChk': 'N',
        'panEdDt': TODAY_DATE_REQUEST.replace('-', ''),
        'listCo': 1000,
        'panNm': '',
        'indVal': 'N',
        'maxSn': 50,
        'mvinQf': '',
        'netbgn': '',
        'viewType': '',
        'panStDt': '',
        'minSn': 0,
        'schTy': '0',
        'page': 1,
    }

    # 🚩 임대/분양 유형 목록
    LEASE_TYPES = [
        "통합공공임대", "통합공공임대(신혼희망)", "국민임대", "공공임대", "영구임대", "행복주택",
        "행복주택(신혼희망)", "장기전세", "신축다세대매입임대", "매입임대",
        "전세임대", "집주인임대", "6년 공공임대주택"
    ]

    SALE_TYPES = [
        "분양주택", "공공분양(신혼희망)"
    ]

    ETC_TYPE = [
        "가정어린이집"
    ]

    
    def __init__(self):
        pass

    # ==================================
    # 2. 크롤링 핵심 함수
    # ==================================

    def crawl_lh_notices_all_data(self, annc_status:str=None):
        """LH 홈페이지에서 2024-11-01 이후의 모든 공고 데이터를 크롤링합니다."""
        all_data = []
        page = 1
        list_count = self.FORM_DATA_TEMPLATE['listCo']

        this_title = ""

        print('-'*77)
        print("🚀 LH 공고 데이터 전체 크롤링 시작 (POST 방식)...")
        if not annc_status:
            print(f"**필터 기준: [모든 유형] + 게시일 {self.FORM_DATA_TEMPLATE['startDt']} 이후 데이터 수집.**")
        else:
            print(f"**필터 기준: [유형 '{annc_status}'] + 게시일 {self.FORM_DATA_TEMPLATE['startDt']} 이후 데이터 수집.**")

        while True:
            form_data = self.FORM_DATA_TEMPLATE.copy()
            if annc_status:
                form_data['panSs'] = annc_status
            form_data['currPage'] = str(page)
            form_data['page'] = str(page)
            form_data['minSn'] = str((page - 1) * list_count)
            form_data['maxSn'] = str(page * list_count)
            form_data['prevListCo'] = str(list_count)

            print(f"\n📄 Crawling page {page} ({form_data['minSn']} to {form_data['maxSn']})...")

            try:
                response = requests.post(self.BASE_URL, data=form_data, headers=self.HEADERS, timeout=15)
                response.raise_for_status()

                # print(response.text)

                # break

                soup = BeautifulSoup(response.text, 'html.parser')
                rows = soup.select("div.bbs_ListA table tbody tr")
                raw_data_count = len(rows)

                if raw_data_count == 0:
                    print("🏁 데이터 없음. 목록의 끝에 도달했습니다. 크롤링 종료.")
                    break

                new_data_count = 0
                stop_crawling = False

                for row in rows:
                    try:
                        cols = [c.get_text(strip=True) for c in row.select("td")]
                        if len(cols) < 9:
                            continue

                        status = cols[7]
                        post_date_str = cols[5]

                        try:
                            post_date = datetime.strptime(post_date_str, '%Y.%m.%d')
                            if post_date < self.START_DATE_FILTER:
                                print(f"🚩 게시일 {post_date_str} 데이터가 필터 기준({self.START_DATE_REQUEST})보다 이전입니다. 추가 크롤링을 중단합니다.")
                                stop_crawling = True
                                break
                        except ValueError:
                            pass

                        title_anchor = row.select_one("td:nth-child(3) a")
                        em_tag = title_anchor.find('em')
                        if em_tag:
                            em_tag.extract()
                        title = title_anchor.get_text(strip=True).replace('\n', ' ')

                        this_title = title

                        """HTML 요소에서 상세 페이지 조회에 필요한 data 속성을 추출하여 URL을 생성합니다."""
                        data_panId = title_anchor.get('data-id1', '')
                        data_ccr = title_anchor.get('data-id2', '')
                        data_upp = title_anchor.get('data-id3', '')
                        data_ais = title_anchor.get('data-id4', '')

                        if all([data_panId, data_ccr, data_upp, data_ais]):
                            detail_url = (
                                f"{self.DETAIL_URL_BASE}&"
                                f"panId={data_panId}&"
                                f"ccrCnntSysDsCd={data_ccr}&"
                                f"uppAisTpCd={data_upp}&"
                                f"aisTpCd={data_ais}"
                            )
                        else:
                            continue

                        # 파일 정보 없는 경우 리턴
                        file_down_obj = row.select_one(".listFileDown")

                        if file_down_obj:
                            upp_ais_tp_cd = file_down_obj.get('data-id1', '')
                            ais_tp_cd = file_down_obj.get('data-id2', '')
                            ccr_cnnt_sys_ds_cd = file_down_obj.get('data-id3', '')
                            ls_sst = file_down_obj.get('data-id4', '')
                            pan_id = file_down_obj.get('data-id5', '')
                        else:
                            upp_ais_tp_cd = title_anchor.get('data-id3', '')
                            ais_tp_cd = title_anchor.get('data-id4', '')
                            ccr_cnnt_sys_ds_cd = title_anchor.get('data-id2', '')
                            ls_sst = ""
                            pan_id = title_anchor.get('data-id1', '')


                        # 공고 유형 판별
                        annc_type_simple = '기타'

                        if cols[1] in self.LEASE_TYPES:
                            annc_type_simple = '임대'
                        elif cols[1] in self.SALE_TYPES:
                            annc_type_simple = '분양'


                        all_data.append(
                            {
                                'annc_title': this_title, # 공고 제목
                                'annc_url': detail_url, # 공고 URL
                                'annc_type': annc_type_simple, # 공고 유형
                                'annc_dtl_type': cols[1], # 공고 유형 상세
                                'annc_region': cols[3], # 지역
                                'annc_pblsh_dt': post_date_str, # 게시일
                                'annc_deadline_dt': cols[6], # 마감일
                                'annc_status': status, # 공고 상태
                                'lh_pan_id': pan_id, # 공고 식별 ID
                                'lh_ais_tp_cd': ais_tp_cd, # 공고 유형 코드
                                'lh_upp_ais_tp_cd': upp_ais_tp_cd, # 상위 공고 유형 코드
                                'lh_ccr_cnnt_sys_ds_cd': ccr_cnnt_sys_ds_cd, # 연계 시스템 구분 코드
                                'lh_ls_sst': ls_sst, # 목록 상의 상태/순서
                            }
                        )


                        new_data_count += 1
                    except Exception as e:
                        print(f"🚨 오류: {e} - {this_title}")
                        continue

                print(f"✅ 페이지 {page} 로드 성공. {len(rows)}개 중 {new_data_count}개 데이터 추출.")

                if stop_crawling or raw_data_count < list_count:
                    print("🏁 크롤링 종료 조건 충족. 전체 크롤링 종료.")
                    break

                page += 1
                time.sleep(1)

            except requests.exceptions.RequestException as e:
                print(f"🚨 네트워크 또는 HTTP 요청 오류 발생: {e}")
                break
            except Exception as e:
                print(f"🚨 치명적인 오류 발생: {e}")
                break

        if all_data:
            print(f"\n✨ 전체 크롤링 완료. 총 {len(all_data)}건의 데이터를 수집했습니다.")
            # return pd.DataFrame(all_data)
            return all_data
        else:
            print("🎉 완료! 수집된 데이터가 없습니다.")
            return []
    

    def get_file_list(self,row):
        
        FILE_CALL_URL = "https://apply.lh.or.kr/lhapply/wt/wrtanc/wrtFileDownl.do"

        # 파일 조회용 크롤링
        form_data_file = {
            'uppAisTpCd1': row['lh_upp_ais_tp_cd'],
            'aisTpCd1': row['lh_ais_tp_cd'],
            'ccrCnntSysDsCd1': row['lh_ccr_cnnt_sys_ds_cd'],
            'lsSst1': row['lh_ls_sst'],
            'panId1': row['lh_pan_id']
        }

        response = requests.post(FILE_CALL_URL, data=form_data_file, headers=self.HEADERS, timeout=15)
        response.encoding = 'utf-8'
        response.raise_for_status()

        file_list = json.loads(response.text)
        
        ok_list = ('공고문(PDF)',)

        file_list = [obj for obj in file_list if obj['slPanAhflDsCdNm'] in ok_list]

        if len(file_list) == 0:
            raise Exception("파일 없음!")

        return file_list

    def down_file(self,file_id, file_info={}):

        
        download_url = f'https://apply.lh.or.kr/lhapply/lhFile.do?fileid={file_id}'

        file_response = requests.get(
            download_url,
            stream=True,
            timeout=30,
            verify=False
        )
        file_response.raise_for_status()

        if not file_response.content:
            raise Exception("파일 내용 없음")

        file_info['file_size'] = file_response.headers.get('Content-Length')
       
        # 폴더가 없는 경우 생성
        os.makedirs("./temp", exist_ok=True)
        
        file_path = "./temp/"+file_info['file_name']

        with open(file_path, mode='wb') as f:
            f.write(file_response.content)

        return file_path, file_info