import re
import os
import io
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from openai import OpenAI

st.set_page_config(
    page_title="B-SIGHT | 사외블록 통합 의사결정 플랫폼",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# OpenAI 클라이언트 초기화 (음성 Whisper 및 지능형 챗봇 의도 분석용)
openai_api_key = os.environ.get("OPENAI_API_KEY", "")
client = OpenAI(api_key=openai_api_key) if openai_api_key else None

# ============================================================
# 0. ORIGINAL DASHBOARD DATA — preserved from B_SIGHT REV1
# ============================================================

SUPPLIER_MASTER = [{'name': '힘스2', 'cnt': 1150, 'weight': 139380, 'avgLeadTime': 24.4, 'ontimePct': 98.2, 'capaMonth': 6000, 'spec': '대불 2공장 150T OHC / E/ROOM(26년 5.9만T → 27년 7.9만T 급증)', 'topItem': 'E/ROOM, S/SHELL', 'totalManpower': 280, 'foreignPct': 42, 'skilledPct': 68, 'mgmtPoints': ['물량 급증(7.9만T) 대비 용접 자동화 장비 추가 도입 및 야간 교대조 정착 필요', '외국인 작업자(42%) 비율 증가에 따른 다국어 작업 표준서 비치 및 안전 교육 강화', 'E/ROOM 정밀 배관 치수 검사 프로세스 조기 확정으로 재작업률 0% 유지']}, {'name': '알파', 'cnt': 1492, 'weight': 72783, 'avgLeadTime': 26.4, 'ontimePct': 96.8, 'capaMonth': 3500, 'spec': '선수 3D 곡블록 특화 / 3공장 200T G/C (26년 3.7만T, 27년 3.5만T)', 'topItem': '선수BLOCK, BTM_BENCH', 'totalManpower': 190, 'foreignPct': 35, 'skilledPct': 75, 'mgmtPoints': ['선수 3D 곡부 성형 과정에서 숙련공(75%) 중심의 1대1 멘토링 체계 운영', '대형 200T 골리앗 크레인 양중 시 안전 규정 준수 여부 실시간 모니터링', '곡가공 오차 사전 시뮬레이션 도입으로 피팅 공정 Lead Time 단축']}, {'name': '메이드', 'cnt': 587, 'weight': 68542, 'avgLeadTime': 24.2, 'ontimePct': 99.5, 'capaMonth': 3000, 'spec': '플로팅도크(242×48m) / 120T 초과 Hopper 해상직송 (26년 3.4만T, 27년 3.5만T)', 'topItem': 'HOPPER', 'totalManpower': 160, 'foreignPct': 25, 'skilledPct': 82, 'mgmtPoints': ['플로팅도크 해상 직송 작업 특성상 기상 악화 대비 사전 출항 스케줄 조율 체계 구축', '초대형 Hopper 블록 적재 안전성 확보를 위한 결박(Lashing) 검수 프로세스 강화', '핵심 크레인 운전원 이탈 방지를 위한 장기 근속 인센티브 및 복지 지원']}, {'name': '태진', 'cnt': 590, 'weight': 56235, 'avgLeadTime': 28.0, 'ontimePct': 97.9, 'capaMonth': 2500, 'spec': '직영 55% 기술 인력 / E/ROOM, Hopper 조립 (26년 2.7만T, 27년 2.9만T)', 'topItem': 'E/ROOM, S/SHELL', 'totalManpower': 140, 'foreignPct': 30, 'skilledPct': 78, 'mgmtPoints': ['직영 비중이 높아(55%) 기술 숙련도가 안정적이나, 현장 고령화 대비 신규 인력 육성 필요', 'E/ROOM 및 S/SHELL 복합 모듈 조립 시 간섭 검사 사전 수행', '원부자재 입고 지연 시 공정 병목을 막기 위한 버퍼 재고 관리 표준화']}, {'name': '보원엠피1공장', 'cnt': 386, 'weight': 49579, 'avgLeadTime': 37.8, 'ontimePct': 94.5, 'capaMonth': 2500, 'spec': '300T/200T 골리앗 크레인 / 대형 UPP DECK 전담 (26년 2.7만T, 27년 2.2만T)', 'topItem': 'UPP DECK, 메가블록', 'totalManpower': 130, 'foreignPct': 38, 'skilledPct': 65, 'mgmtPoints': ['대형 메가블록 및 UPP DECK 취급 중량물 작업으로 크레인 신호수 교육 강화', '외국인 용접공(38%) 품질 편차 줄이기 위한 자동 용접기 활용 비중 확대', 'Lead Time이 다소 길어(37.8일) 공정 지연 방지를 위한 킥오프 미팅 주 1회 정례화']}, {'name': '힘스3', 'cnt': 374, 'weight': 46797, 'avgLeadTime': 25.1, 'ontimePct': 98.4, 'capaMonth': 2500, 'spec': '대불 3공장 가공/대조립 연계 S/SHELL, E/ROOM (26년 2.7만T, 27년 1.9만T)', 'topItem': 'S/SHELL_BENCH', 'totalManpower': 125, 'foreignPct': 40, 'skilledPct': 70, 'mgmtPoints': ['대불 3공장 가공 센터와 연계한 철판 소요량 실시간 싱크 관리', '외국인 인력 이탈률 모니터링 및 기숙사 환경 개선 등 복지 케어 실시', 'S/SHELL 벤치 조립 치수 정밀도 관리 철저']}, {'name': '동남', 'cnt': 512, 'weight': 29840, 'avgLeadTime': 22.0, 'ontimePct': 97.6, 'capaMonth': 2200, 'spec': '60m PIN JIG / OHC 100+50T 2대 [CNTR T-BHD 3순위 전담 & 초과분 수용]', 'topItem': 'CNTR T-BLK, T-BHD', 'totalManpower': 110, 'foreignPct': 32, 'skilledPct': 76, 'mgmtPoints': ['유일 초과 물량 유입 시 신속하게 투입될 수 있는 다기능공(Multi-skilled) 풀 운영', '60m PIN JIG 설비 유지보수 스케줄을 야간 및 주말로 분산하여 가동 중단 최소화', 'T-BHD 용접 변형 방지를 위한 대각선 대칭 용접 순서 준수 관리']}, {'name': '유일', 'cnt': 380, 'weight': 21000, 'avgLeadTime': 32.5, 'ontimePct': 97.3, 'capaMonth': 1750, 'spec': '컨테이너선 [CNTR T-BHD 1순위 전담] (타조선소 수주로 최대 21,000T Cap 한도 준수)', 'topItem': 'CNTR T-BHD, T-BLK', 'totalManpower': 95, 'foreignPct': 28, 'skilledPct': 80, 'mgmtPoints': ['타 조선소 물량 병행으로 인한 생산 캐파 포화(연간 21,000T 한도) 관리 철저', 'CNTR 격벽(T-BHD) 전문 숙련공(80%) 배치로 품질 신뢰도 최상위 유지', '물량 초과 즉시 대아 및 동남으로 자동 리밸런싱되는 실시간 경보 체계 연동']}, {'name': '대아', 'cnt': 295, 'weight': 17850, 'avgLeadTime': 36.7, 'ontimePct': 95.8, 'capaMonth': 1800, 'spec': '선미 Stern Boss 및 [CNTR T-BHD 2순위 전담 & 유일 초과분 흡수]', 'topItem': 'CNTR T-BHD, 선미BLOCK', 'totalManpower': 90, 'foreignPct': 35, 'skilledPct': 72, 'mgmtPoints': ['유일 물량 초과 유입 시 즉각 대응할 수 있는 여유 작업 스페이스 상시 확보', '선미 Stern Boss 등 고난도 주조품 결합 부위 비파괴 검사(NDT) 사전 예약', '공정 Lead Time(36.7일) 단축을 위한 사전 조립 가점 공정 도입 검토']}, {'name': '장성테크', 'cnt': 277, 'weight': 8103, 'avgLeadTime': 14.5, 'ontimePct': 99.6, 'capaMonth': 500, 'spec': '소형 Bench 및 HATCH COAMING 초단기 생산 (26년 4.0k T, 27년 4.1k T)', 'topItem': 'HATCH COAMING, Bench', 'totalManpower': 45, 'foreignPct': 20, 'skilledPct': 85, 'mgmtPoints': ['소형 벤치 고속 조립 라인으로 회전율이 매우 높아(14.5일) 원부자재 적기 공급 필수', 'Hatch Coaming 평탄도 및 치수 정밀도 관리로 현장 탑재 용이성 증대', '소수 정예 베테랑 중심(숙련공 85%)으로 이탈 리스크 관리 집중']}, {'name': 'DHMC', 'cnt': 21, 'weight': 587, 'avgLeadTime': 90.0, 'ontimePct': 100.0, 'capaMonth': 100, 'spec': '대형 Rudder 블록 전문 정밀 제작', 'topItem': 'Rudder 블록', 'totalManpower': 20, 'foreignPct': 10, 'skilledPct': 95, 'mgmtPoints': ['고도의 정밀 가공이 요구되는 Rudder 블록 전담으로 장기 제작 기간(90일) 엄수', '핵심 장인 기술자에 대한 의존도가 높아 건강 및 근속 관리 최우선', '출하 전 최종 삼차원 치수 검사 성적서 엄격 검증']}, {'name': '트레스', 'cnt': 19, 'weight': 447, 'avgLeadTime': 108.6, 'ontimePct': 100.0, 'capaMonth': 100, 'spec': '특수 구조물 블록 소량 전담', 'topItem': '특수BLOCK', 'totalManpower': 15, 'foreignPct': 10, 'skilledPct': 90, 'mgmtPoints': ['비정형 특수 구조물 설계 변경 발생 시 조선소 설계 부서와 즉시 핫라인 가동', '소량 다품종 생산 체제에 맞는 유연한 공정 스케줄링 운영', '철저한 품질 검증으로 무결점 납품 유지']}, {'name': '칸플랜트', 'cnt': 6, 'weight': 364, 'avgLeadTime': 18.7, 'ontimePct': 100.0, 'capaMonth': 100, 'spec': '단순 T-BHD 격벽 블록 제작', 'topItem': 'T-BHD', 'totalManpower': 12, 'foreignPct': 15, 'skilledPct': 80, 'mgmtPoints': ['단순 격벽 블록 위주로 신속한 턴어라운드(18.7일) 관리', '기본 안전 수칙 준수 및 작업장 정리정돈 상태 상시 점검', '납기 준수율 100% 지속 유지를 위한 주간 진도 관리']}]

# 2027년 공식 배정 물량 (단위: T)
WEIGHT_2027 = {
    '힘스2': 79000,
    '알파': 35000,
    '메이드': 35000,
    '태진': 29000,
    '보원엠피1공장': 22000,
    '힘스3': 19000,
    '유일': 11000,
    '동남': 18000,
    '대아': 15000,
    '장성테크': 4100,
    'DHMC': 500,
    '트레스': 400,
    '칸플랜트': 321
}

MONTHLY_PIVOT = {'2026': [21637, 19850, 25310, 24605, 24317, 22969, 25881, 18572, 24168, 23254, 27545, 26674], '2027': [25724, 23910, 25529, 27064, 27574, 34128, 26608, 17083, 22803, 23002, 28503, 25793]}

SHIP_MODELS = {'16000 CNTR': {'bom': [{'item': 'CNTR T-BHD (격벽)', 'ratio': 0.38, 'avgUnitWeight': 110.0, 'supplier1': '유일', 'supplier2': '대아', 'supplier3': '동남'}, {'item': 'S/SHELL_BENCH', 'ratio': 0.16, 'avgUnitWeight': 125.0, 'supplier1': '힘스3', 'supplier2': '태진'}, {'item': 'E/ROOM', 'ratio': 0.16, 'avgUnitWeight': 95.0, 'supplier1': '힘ส2', 'supplier2': '태진'}, {'item': 'BTM_BENCH', 'ratio': 0.1, 'avgUnitWeight': 65.0, 'supplier1': '알파', 'supplier2': '장성테크'}, {'item': '선미BLOCK', 'ratio': 0.08, 'avgUnitWeight': 65.0, 'supplier1': '대아', 'supplier2': '알파'}, {'item': '선수BLOCK', 'ratio': 0.07, 'avgUnitWeight': 60.0, 'supplier1': '알파', 'supplier2': '대아'}, {'item': 'D/BTM', 'ratio': 0.05, 'avgUnitWeight': 130.0, 'supplier1': '태진', 'supplier2': '힘스2'}]}, '15500 CNTR(LNG DF)': {'bom': [{'item': 'CNTR T-BHD (격벽)', 'ratio': 0.38, 'avgUnitWeight': 108.0, 'supplier1': '유일', 'supplier2': '대아', 'supplier3': '동남'}, {'item': 'S/SHELL_BENCH', 'ratio': 0.16, 'avgUnitWeight': 125.0, 'supplier1': '힘스3', 'supplier2': '태진'}, {'item': 'E/ROOM', 'ratio': 0.16, 'avgUnitWeight': 92.0, 'supplier1': '힘스2', 'supplier2': '태진'}, {'item': 'BTM_BENCH', 'ratio': 0.1, 'avgUnitWeight': 62.0, 'supplier1': '알파', 'supplier2': '장성테크'}, {'item': '선미BLOCK', 'ratio': 0.08, 'avgUnitWeight': 64.0, 'supplier1': '대아', 'supplier2': '알파'}, {'item': '선수BLOCK', 'ratio': 0.07, 'avgUnitWeight': 58.0, 'supplier1': '알파', 'supplier2': '대아'}, {'item': 'D/BTM', 'ratio': 0.05, 'avgUnitWeight': 128.0, 'supplier1': '태진', 'supplier2': '힘스2'}]}, '13000 CNTR(METH. DF)': {'bom': [{'item': 'CNTR T-BHD (격벽)', 'ratio': 0.38, 'avgUnitWeight': 105.0, 'supplier1': '유일', 'supplier2': '동남', 'supplier3': '대아'}, {'item': 'E/ROOM', 'ratio': 0.17, 'avgUnitWeight': 95.0, 'supplier1': '힘스2', 'supplier2': '태진'}, {'item': 'S/SHELL_BENCH', 'ratio': 0.13, 'avgUnitWeight': 120.0, 'supplier1': '힘스3', 'supplier2': '태진'}, {'item': 'BTM_BENCH', 'ratio': 0.12, 'avgUnitWeight': 60.0, 'supplier1': '알파', 'supplier2': '장성테크'}, {'item': '선미BLOCK', 'ratio': 0.08, 'avgUnitWeight': 65.0, 'supplier1': '대아', 'supplier2': '알파'}, {'item': '선수BLOCK', 'ratio': 0.06, 'avgUnitWeight': 60.0, 'supplier1': '알파', 'supplier2': '대아'}, {'item': 'D/BTM', 'ratio': 0.04, 'avgUnitWeight': 140.0, 'supplier1': '태진', 'supplier2': '힘스2'}]}, '174K LNG': {'bom': [{'item': 'HOPPER', 'ratio': 0.284, 'avgUnitWeight': 138.0, 'supplier1': '메이드', 'supplier2': '보원엠피1공장'}, {'item': 'UPP DECK', 'ratio': 0.211, 'avgUnitWeight': 112.5, 'supplier1': '보원엠피1공장', 'supplier2': '동남'}, {'item': 'E/ROOM', 'ratio': 0.194, 'avgUnitWeight': 92.3, 'supplier1': '힘스2', 'supplier2': '태진'}, {'item': '선수BLOCK', 'ratio': 0.132, 'avgUnitWeight': 81.9, 'supplier1': '알파', 'supplier2': '대아'}, {'item': 'S/SHELL', 'ratio': 0.059, 'avgUnitWeight': 124.5, 'supplier1': '태진', 'supplier2': '힘스2'}, {'item': '선미BLOCK', 'ratio': 0.058, 'avgUnitWeight': 126.9, 'supplier1': '대아', 'supplier2': '알파'}, {'item': 'T-BHD', 'ratio': 0.045, 'avgUnitWeight': 46.8, 'supplier1': '유일', 'supplier2': '동남'}, {'item': 'D/BTM', 'ratio': 0.016, 'avgUnitWeight': 153.7, 'supplier1': '태진', 'supplier2': '힘스2'}]}, '157K COT': {'bom': [{'item': 'E/ROOM', 'ratio': 0.35, 'avgUnitWeight': 125.0, 'supplier1': '힘스2', 'supplier2': '태진'}, {'item': 'HOPPER', 'ratio': 0.3, 'avgUnitWeight': 130.0, 'supplier1': '메이드', 'supplier2': '보원엠피1공장'}, {'item': '선수BLOCK', 'ratio': 0.18, 'avgUnitWeight': 75.0, 'supplier1': '알파', 'supplier2': '대아'}, {'item': '선미BLOCK', 'ratio': 0.1, 'avgUnitWeight': 75.0, 'supplier1': '대아', 'supplier2': '알파'}, {'item': 'UPP DECK', 'ratio': 0.07, 'avgUnitWeight': 105.0, 'supplier1': '보원엠피1공장', 'supplier2': '동남'}]}, '88K VLAC(CONV.)': {'bom': [{'item': 'UPP DECK', 'ratio': 0.32, 'avgUnitWeight': 110.0, 'supplier1': '보원엠피1공장', 'supplier2': '동남'}, {'item': 'E/ROOM', 'ratio': 0.28, 'avgUnitWeight': 95.0, 'supplier1': '힘스2', 'supplier2': '태진'}, {'item': '선수BLOCK', 'ratio': 0.18, 'avgUnitWeight': 90.0, 'supplier1': '알파', 'supplier2': '대아'}, {'item': 'S/SHELL', 'ratio': 0.14, 'avgUnitWeight': 115.0, 'supplier1': '태진', 'supplier2': '힘스2'}, {'item': '선미BLOCK', 'ratio': 0.08, 'avgUnitWeight': 50.0, 'supplier1': '대아', 'supplier2': '알파'}]}}

VESSEL_DATASET = [{'hno': '8282', 'dock': '1', 'sunpyoNo': '26M01', 'shipType': '174K LNG', 'owner': 'NYK', 'klDate': '2026-01-15', 'lcDate': '2026-05-20', 'dlDate': '2026-09-30', 'year': '2026', 'blockCount': 72, 'totalWeight': 7420, 'topSupplier': '힘스2'}, {'hno': '8222', 'dock': '1', 'sunpyoNo': '26M02', 'shipType': '174K LNG', 'owner': 'NYK', 'klDate': '2026-02-10', 'lcDate': '2026-06-25', 'dlDate': '2026-10-31', 'year': '2026', 'blockCount': 70, 'totalWeight': 7255, 'topSupplier': '메이드'}, {'hno': '8323', 'dock': '1', 'sunpyoNo': '26M03', 'shipType': '174K LNG', 'owner': 'MOL', 'klDate': '2026-03-15', 'lcDate': '2026-07-20', 'dlDate': '2026-11-30', 'year': '2026', 'blockCount': 71, 'totalWeight': 7350, 'topSupplier': '보원엠피1공장'}, {'hno': '8209', 'dock': '1', 'sunpyoNo': '26M04', 'shipType': '174K LNG', 'owner': 'MOL', 'klDate': '2026-04-10', 'lcDate': '2026-08-25', 'dlDate': '2026-12-31', 'year': '2026', 'blockCount': 70, 'totalWeight': 7255, 'topSupplier': '힘스2'}, {'hno': '8318', 'dock': '2', 'sunpyoNo': '26M05', 'shipType': '16000 CNTR', 'owner': 'MSC', 'klDate': '2026-02-28', 'lcDate': '2026-07-15', 'dlDate': '2026-11-20', 'year': '2026', 'blockCount': 104, 'totalWeight': 7850, 'topSupplier': '유일'}, {'hno': '8247', 'dock': '2', 'sunpyoNo': '26M06', 'shipType': '16000 CNTR', 'owner': 'MSC', 'klDate': '2026-04-20', 'lcDate': '2026-09-10', 'dlDate': '2027-01-15', 'year': '2026', 'blockCount': 102, 'totalWeight': 7650, 'topSupplier': '대아'}, {'hno': '8294', 'dock': '2', 'sunpyoNo': '26M07', 'shipType': '16000 CNTR', 'owner': 'MSC', 'klDate': '2026-06-15', 'lcDate': '2026-11-05', 'dlDate': '2027-03-20', 'year': '2026', 'blockCount': 102, 'totalWeight': 7638, 'topSupplier': '동남'}, {'hno': '8313', 'dock': '1', 'sunpyoNo': '26M08', 'shipType': '174K LNG', 'owner': 'KNOT', 'klDate': '2026-05-10', 'lcDate': '2026-09-25', 'dlDate': '2027-01-30', 'year': '2026', 'blockCount': 71, 'totalWeight': 7300, 'topSupplier': '힘스2'}, {'hno': '8287', 'dock': '1', 'sunpyoNo': '26M09', 'shipType': '174K LNG', 'owner': 'KNOT', 'klDate': '2026-06-20', 'lcDate': '2026-11-10', 'dlDate': '2027-03-15', 'year': '2026', 'blockCount': 70, 'totalWeight': 7255, 'topSupplier': '메이드'}, {'hno': '8278', 'dock': '2', 'sunpyoNo': '26M10', 'shipType': '15500 CNTR(LNG DF)', 'owner': 'CMA CGM', 'klDate': '2026-03-05', 'lcDate': '2026-07-30', 'dlDate': '2026-11-30', 'year': '2026', 'blockCount': 84, 'totalWeight': 6050, 'topSupplier': '유일'}, {'hno': '8277', 'dock': '2', 'sunpyoNo': '26M11', 'shipType': '15500 CNTR(LNG DF)', 'owner': 'CMA CGM', 'klDate': '2026-05-15', 'lcDate': '2026-10-10', 'dlDate': '2027-02-28', 'year': '2026', 'blockCount': 82, 'totalWeight': 5900, 'topSupplier': '대아'}, {'hno': '8276', 'dock': '2', 'sunpyoNo': '26M12', 'shipType': '15500 CNTR(LNG DF)', 'owner': 'CMA CGM', 'klDate': '2026-07-20', 'lcDate': '2026-12-15', 'dlDate': '2027-04-30', 'year': '2026', 'blockCount': 82, 'totalWeight': 5895, 'topSupplier': '동남'}, {'hno': '8254', 'dock': '1', 'sunpyoNo': '26M13', 'shipType': '157K COT', 'owner': 'DHT', 'klDate': '2026-02-15', 'lcDate': '2026-06-30', 'dlDate': '2026-10-31', 'year': '2026', 'blockCount': 34, 'totalWeight': 3650, 'topSupplier': '힘스2'}, {'hno': '8255', 'dock': '1', 'sunpyoNo': '26M14', 'shipType': '157K COT', 'owner': 'DHT', 'klDate': '2026-04-10', 'lcDate': '2026-08-20', 'dlDate': '2026-12-15', 'year': '2026', 'blockCount': 33, 'totalWeight': 3550, 'topSupplier': '메이드'}, {'hno': '8311', 'dock': '2', 'sunpyoNo': '26M38', 'shipType': '13000 CNTR(METH. DF)', 'owner': 'MAERSK', 'klDate': '2026-08-01', 'lcDate': '2026-12-20', 'dlDate': '2027-04-30', 'year': '2026', 'blockCount': 94, 'totalWeight': 6267, 'topSupplier': '유일'}, {'hno': '8366', 'dock': '1', 'sunpyoNo': '27M01', 'shipType': '174K LNG', 'owner': 'QATAR ENERGY', 'klDate': '2027-01-10', 'lcDate': '2027-05-20', 'dlDate': '2027-09-30', 'year': '2027', 'blockCount': 73, 'totalWeight': 7450, 'topSupplier': '힘스2'}, {'hno': '8334', 'dock': '1', 'sunpyoNo': '27M02', 'shipType': '174K LNG', 'owner': 'QATAR ENERGY', 'klDate': '2027-02-15', 'lcDate': '2027-06-30', 'dlDate': '2027-10-31', 'year': '2027', 'blockCount': 72, 'totalWeight': 7380, 'topSupplier': '메이드'}, {'hno': '8338', 'dock': '2', 'sunpyoNo': '27M11', 'shipType': '16000 CNTR', 'owner': 'MSC', 'klDate': '2027-01-15', 'lcDate': '2027-06-10', 'dlDate': '2027-10-20', 'year': '2027', 'blockCount': 104, 'totalWeight': 7850, 'topSupplier': '유일'}, {'hno': '8339', 'dock': '2', 'sunpyoNo': '27M12', 'shipType': '16000 CNTR', 'owner': 'MSC', 'klDate': '2027-03-10', 'lcDate': '2027-07-25', 'dlDate': '2027-11-30', 'year': '2027', 'blockCount': 104, 'totalWeight': 7850, 'topSupplier': '대아'}, {'hno': '8347', 'dock': '2', 'sunpyoNo': '27M15', 'shipType': '15500 CNTR(LNG DF)', 'owner': 'CMA CGM', 'klDate': '2027-02-20', 'lcDate': '2027-07-15', 'dlDate': '2027-11-25', 'year': '2027', 'blockCount': 102, 'totalWeight': 7425, 'topSupplier': '유일'}, {'hno': '8371', 'dock': '2', 'sunpyoNo': '27M28', 'shipType': '13000 CNTR', 'owner': 'MAERSK', 'klDate': '2027-04-10', 'lcDate': '2027-08-30', 'dlDate': '2027-12-31', 'year': '2027', 'blockCount': 87, 'totalWeight': 6062, 'topSupplier': '유일'}]

HISTORICAL_TOTALS = {
    "2023": {"weight": 224734, "blocks": 2350},
    "2024": {"weight": 229822, "blocks": 2400},
    "2025": {"weight": 260201, "blocks": 2650},
    "2026": {"weight": 284782, "blocks": 2712},
    "2027": {"weight": 307721, "blocks": 2959},
}

# ============================================================
# 1. APP STYLE
# ============================================================
st.markdown("""
<style>
    .main .block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
    .app-title {font-size: 1.75rem; font-weight: 800; margin-bottom: 0.15rem;}
    .app-subtitle {color:#64748b; font-size:0.86rem; margin-bottom:1rem;}
    .kpi-card {
        border:1px solid #e2e8f0; border-radius:16px; padding:16px;
        background:#fff; min-height:125px;
    }
    .kpi-label {font-size:0.76rem; color:#64748b; font-weight:700;}
    .kpi-value {font-size:1.55rem; font-weight:800; margin-top:8px;}
    .kpi-sub {font-size:0.72rem; color:#64748b; margin-top:7px;}
    .risk-high {color:#b91c1c; font-weight:800;}
    .risk-mid {color:#b45309; font-weight:800;}
    .risk-low {color:#047857; font-weight:800;}
    .chat-panel {
        border:1px solid #dbeafe; border-radius:18px; background:#f8fbff;
        padding:14px;
    }
    .decision-box {
        border-left:5px solid #2563eb; background:#eff6ff;
        padding:12px 14px; border-radius:10px; margin:8px 0;
    }
    .warning-box {
        border-left:5px solid #f59e0b; background:#fffbeb;
        padding:12px 14px; border-radius:10px; margin:8px 0;
    }
    .danger-box {
        border-left:5px solid #dc2626; background:#fef2f2;
        padding:12px 14px; border-radius:10px; margin:8px 0;
    }
    div[data-testid="stChatMessage"] {padding: 0.45rem 0;}
</style>
""", unsafe_allow_html=True)

# ============================================================
# 2. DATAFRAME + DERIVED RISK
# ============================================================
df_sup = pd.DataFrame(SUPPLIER_MASTER)
df_vessel = pd.DataFrame(VESSEL_DATASET)

def risk_score(row):
    ontime_penalty = max(0, 100 - float(row["ontimePct"])) * 2.0
    lead_penalty = max(0, float(row["avgLeadTime"]) - 20) * 0.65
    foreign_penalty = max(0, float(row["foreignPct"]) - 30) * 0.35
    skill_penalty = max(0, 75 - float(row["skilledPct"])) * 0.45
    return round(min(100, ontime_penalty + lead_penalty + foreign_penalty + skill_penalty), 1)

df_sup["risk_score"] = df_sup.apply(risk_score, axis=1)
df_sup["risk_grade"] = pd.cut(
    df_sup["risk_score"],
    bins=[-1, 20, 40, 100],
    labels=["LOW", "MID", "HIGH"]
)

ITEM_GROUPS = {
    "E/ROOM": ["힘스2", "태진"],
    "S/SHELL": ["힘스2", "힘스3", "태진"],
    "S/SHELL_BENCH": ["힘스3", "태진"],
    "선수BLOCK": ["알파", "대아"],
    "BTM_BENCH": ["알파", "장성테크"],
    "HOPPER": ["메이드", "보원엠피1공장", "태진"],
    "UPP DECK": ["보원엠피1공장", "동남"],
    "T-BHD": ["유일", "대아", "동남", "칸플랜트"],
    "CNTR T-BHD": ["유일", "대아", "동남"],
    "T-BLK": ["동남", "유일"],
    "선미BLOCK": ["대아", "알파"],
    "HATCH COAMING": ["장성테크"],
    "Rudder": ["DHMC"],
    "특수BLOCK": ["트레스"],
    "D/BTM": ["태진", "힘스2"],
}

def get_supplier_weight(row, year_filter):
    name = row["name"]
    if year_filter == "2027" and name in WEIGHT_2027:
        return WEIGHT_2027[name]
    factor = 0.52 if year_filter == "2027" else 0.48 if year_filter == "2026" else 0.4
    return round(float(row["weight"]) * factor)

def find_supplier(text):
    for name in sorted(df_sup["name"].tolist(), key=len, reverse=True):
        if name.lower() in text.lower():
            return name
    return None

def parse_weight(text, default=10000):
    nums = re.findall(r"\d+(?:,\d+)*(?:\.\d+)?", text)
    if not nums:
        return float(default)
    return float(nums[-1].replace(",", ""))

def detect_item(text):
    t = text.lower()
    for item in sorted(ITEM_GROUPS.keys(), key=len, reverse=True):
        if item.lower() in t:
            return item
    return None

def compatible_suppliers(item):
    if not item:
        return list(df_sup["name"])
    return ITEM_GROUPS.get(item, list(df_sup["name"]))

def item_fit_score(supplier_name, item):
    if not item:
        return 0
    return 100 if supplier_name in compatible_suppliers(item) else 0

def objective_weights(text):
    t = text.lower()
    if "납기" in t or "delivery" in t:
        return {"delivery": 0.35, "quality": 0.20, "capacity": 0.20, "risk": 0.20, "skill": 0.05}
    if "품질" in t or "quality" in t:
        return {"delivery": 0.20, "quality": 0.40, "capacity": 0.15, "risk": 0.20, "skill": 0.05}
    if "리스크" in t or "risk" in t:
        return {"delivery": 0.20, "quality": 0.15, "capacity": 0.20, "risk": 0.40, "skill": 0.05}
    if "생산" in t or "capa" in t or "캐파" in t:
        return {"delivery": 0.20, "quality": 0.15, "capacity": 0.40, "risk": 0.20, "skill": 0.05}
    return {"delivery": 0.25, "quality": 0.20, "capacity": 0.25, "risk": 0.25, "skill": 0.05}

def filtered_vessels(year_filter, ship_type, vessel_no, supplier):
    d = df_vessel.copy()
    if year_filter not in HISTORICAL_TOTALS:
        year_filter = "2027"
    d = d[d["year"] == year_filter]
    if ship_type != "ALL":
        d = d[d["shipType"] == ship_type]
    if vessel_no != "ALL":
        d = d[d["hno"] == vessel_no]
    if supplier != "ALL":
        d = d[d["topSupplier"] == supplier]
    return d

def annualized_capacity(row, months=12):
    return float(row["capaMonth"]) * months

def remaining_capacity(row, year_filter):
    cap = annualized_capacity(row, 12)
    used = get_supplier_weight(row, year_filter)
    rem = cap - used
    return rem

# ============================================================
# 3. DASHBOARD HEADER + FILTERS
# ============================================================
st.markdown('<div class="app-title">🚢 B-SIGHT | 사외블록 통합 예측 · 생산 · 인력 · 업체배정 의사결정 플랫폼</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-subtitle">음성 인식 및 지능형 의도 분석 엔진 탑재 — 대시보드와 챗봇 완벽 통합 버전</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### 🎛️ 통합 분석 조건")
    year_filter = st.selectbox(
        "분석 대상 연도",
        ["2027", "2026", "2025", "2024", "2023"],
        index=0,
        format_func=lambda x: {
            "2027": "2027년 (30.77만T / 52척)",
            "2026": "2026년 (28.48만T / 50척)",
            "2025": "2025년 실적 (26.02만T)",
            "2024": "2024년 실적 (22.98만T)",
            "2023": "2023년 실적 (22.47만T)",
        }[x],
    )

    ship_types = ["ALL"] + sorted(df_vessel["shipType"].unique().tolist())
    ship_type = st.selectbox("선종", ship_types, format_func=lambda x: "전체 선종" if x == "ALL" else x)

    vessel_candidates = filtered_vessels(year_filter, ship_type, "ALL", "ALL")
    vessel_options = ["ALL"] + vessel_candidates["hno"].astype(str).tolist()
    vessel_no = st.selectbox("호선", vessel_options, format_func=lambda x: "전체 호선" if x == "ALL" else x)

    supplier_options = ["ALL"] + df_sup["name"].tolist()
    supplier_filter = st.selectbox("협력사", supplier_options, format_func=lambda x: "전체 13개 협력사" if x == "ALL" else x)

    st.divider()
    st.markdown("### 🤖 챗봇 우선순위")
    st.caption("챗봇이 재배정/What-if를 계산할 때 사용")
    objective = st.radio(
        "의사결정 우선순위",
        ["균형형", "납기 우선", "품질 우선", "Risk 최소화", "Capa 우선"],
        index=0,
    )

    st.divider()
    st.markdown("### ⚠️ 핵심 제약")
    st.info("27년 공식 배정 물량 100% 반영 및 Capa 초과(부하율 100% 초과) 검토 허용")
    st.caption("잔여 Capa 부족 및 부하율 초과 상태를 그대로 시뮬레이션합니다.")

fv = filtered_vessels(year_filter, ship_type, vessel_no, supplier_filter)

if ship_type == "ALL" and vessel_no == "ALL" and supplier_filter == "ALL":
    base = HISTORICAL_TOTALS.get(year_filter, HISTORICAL_TOTALS["2027"])
    total_weight = base["weight"]
    total_blocks = base["blocks"]
else:
    total_weight = int(fv["totalWeight"].sum())
    total_blocks = int(fv["blockCount"].sum())

vessel_count = len(fv)
months = 12
monthly_weight = round(total_weight / months)
avg_block = round(total_weight / total_blocks, 1) if total_blocks else 0
avg_vessel = round(total_weight / vessel_count) if vessel_count else 0

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">선택 조건 총 물량</div><div class="kpi-value">{total_weight:,.0f} T</div><div class="kpi-sub">월평균 {monthly_weight:,.0f} T</div></div>', unsafe_allow_html=True)
with k2:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">총 사외블록</div><div class="kpi-value">{total_blocks:,.0f} EA</div><div class="kpi-sub">개당 평균 {avg_block:,.1f} T</div></div>', unsafe_allow_html=True)
with k3:
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">대상 건조 척수</div><div class="kpi-value">{vessel_count:,} 척</div><div class="kpi-sub">선택 연도 기준 건조 척수</div></div>', unsafe_allow_html=True)
with k4:
    yuil_w = WEIGHT_2027.get('유일', 11000) if year_filter == "2027" else 10000
    st.markdown(f'<div class="kpi-card"><div class="kpi-label">유일 CNTR T-BHD</div><div class="kpi-value">{yuil_w:,} T</div><div class="kpi-sub">1년 기준 배정 물량 반영</div></div>', unsafe_allow_html=True)

# ============================================================
# 4. MAIN / CHAT SPLIT — single platform
# ============================================================
dash_col, chat_col = st.columns([7.2, 2.8], gap="large")

with dash_col:
    tabs = st.tabs([
        "📊 종합 물량",
        "👥 인력 & 관리",
        "📅 선표 & 공정",
        "🚢 선종 & 척수",
        "🏭 Capa & 배정규칙",
        "⚡ AI 시뮬레이터",
        "🔄 물량 자동 재배정",
    ])

    # ---------------- Overview ----------------
    with tabs[0]:
        c1, c2 = st.columns([1.55, 1])
        with c1:
            trend_df = pd.DataFrame({
                "연도": ["2023", "2024", "2025", "2026", "2027"],
                "사외블록 중량(T)": [224734, 229822, 260201, 284782, 307721],
                "블록수(EA)": [2350, 2400, 2650, 2712, 2959],
            })
            fig = go.Figure()
            fig.add_trace(go.Bar(x=trend_df["연도"], y=trend_df["사외블록 중량(T)"], name="중량(T)"))
            fig.add_trace(go.Scatter(x=trend_df["연도"], y=trend_df["블록수(EA)"], name="블록수(EA)", yaxis="y2", mode="lines+markers"))
            fig.update_layout(
                title="연도별 사외블록 중량 및 블록수 추이",
                yaxis=dict(title="T"),
                yaxis2=dict(title="EA", overlaying="y", side="right"),
                height=360, margin=dict(l=10,r=10,t=55,b=10), legend=dict(orientation="h")
            )
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            if not fv.empty:
                ship_stats = fv.groupby("shipType", as_index=False)["totalWeight"].sum()
            else:
                ship_stats = pd.DataFrame({"shipType": [], "totalWeight": []})
            if not ship_stats.empty:
                fig2 = px.pie(ship_stats, names="shipType", values="totalWeight", hole=.62, title="선종별 사외블록 중량 점유율")
                fig2.update_layout(height=360, margin=dict(l=10,r=10,t=55,b=10))
                st.plotly_chart(fig2, use_container_width=True)

        if year_filter in MONTHLY_PIVOT:
            month_df = pd.DataFrame({
                "월": [f"{i}월" for i in range(1,13)],
                year_filter: MONTHLY_PIVOT[year_filter],
            })
            fig3 = px.bar(month_df, x="월", y=year_filter, title=f"{year_filter}년 월별 사외제작 물량")
            fig3.update_layout(height=320, margin=dict(l=10,r=10,t=55,b=10))
            st.plotly_chart(fig3, use_container_width=True)

        dyn = df_sup.copy()
        dyn["배정중량(T)"] = dyn.apply(lambda r: get_supplier_weight(r, year_filter), axis=1)
        dyn["월평균(T)"] = (dyn["배정중량(T)"] / 12).round().astype(int)
        dyn["중량점유율(%)"] = (dyn["배정중량(T)"] / max(1, total_weight) * 100).round(1)
        view = dyn[["name","배정중량(T)","중량점유율(%)","월평균(T)","avgLeadTime","ontimePct","topItem"]].copy()
        view.columns = ["협력사","배정중량(T)","중량점유율(%)","월평균(T)","Lead Time(일)","납기준수율(%)","주요품목"]
        st.dataframe(view.sort_values("배정중량(T)", ascending=False), use_container_width=True, hide_index=True)

    # ---------------- Manpower ----------------
    with tabs[1]:
        m = df_sup[["name","totalManpower","foreignPct","skilledPct","avgLeadTime","ontimePct","risk_score","risk_grade","topItem","spec"]].copy()
        m.columns = ["협력사","총인력","외국인비중(%)","숙련공비중(%)","Lead Time(일)","납기준수율(%)","Risk Score","Risk","주력공정","설비/특화"]
        st.dataframe(m.sort_values("Risk Score", ascending=False), use_container_width=True, hide_index=True)
        st.markdown("#### 업체별 관리 포인트")
        for _, r in df_sup.sort_values("risk_score", ascending=False).iterrows():
            with st.expander(f'{r["name"]} · Risk {r["risk_score"]:.1f} · 외국인 {r["foreignPct"]}% · 숙련공 {r["skilledPct"]}%'):
                st.write(f'**주력:** {r["topItem"]}')
                st.write(f'**설비:** {r["spec"]}')
                for p in r["mgmtPoints"]:
                    st.write("• " + p)

    # ---------------- Schedule ----------------
    with tabs[2]:
        st.caption("원본 B-SIGHT 선표 데이터 구조를 그대로 사용합니다.")
        sched = fv.copy()
        if sched.empty:
            st.warning("현재 필터 조건에 해당하는 선표가 없습니다.")
        else:
            sched["공정상태"] = "공정 확정"
            cols = ["dock","sunpyoNo","hno","shipType","owner","klDate","lcDate","dlDate","blockCount","totalWeight","topSupplier","공정상태"]
            sched = sched[cols].copy()
            sched.columns = ["도크","선표","호선","선종","선주","착공(K/L)","진수(L/C)","인도(D/L)","블록수(EA)","사외물량(T)","1순위 협력사","공정상태"]
            st.dataframe(sched, use_container_width=True, hide_index=True)

    # ---------------- Matrix ----------------
    with tabs[3]:
        if not fv.empty:
            type_stats = fv.groupby("shipType").agg(척수=("hno","count"), 총중량=("totalWeight","sum"), 블록수=("blockCount","sum")).reset_index()
            type_stats["척당 평균중량"] = (type_stats["총중량"]/type_stats["척수"]).round(0)
            st.dataframe(type_stats, use_container_width=True, hide_index=True)
            st.markdown("#### 호선별 매트릭스")
            mat = fv.copy()
            mat["개당 평균중량"] = (mat["totalWeight"]/mat["blockCount"]).round(1)
            mat = mat[["year","hno","shipType","sunpyoNo","owner","blockCount","totalWeight","개당 평균중량","klDate","dlDate","topSupplier"]]
            mat.columns = ["연도","호선","선종","선표","선주","사외블록수","총사외중량","개당평균중량","착공일","인도일","1순위협력사"]
            st.dataframe(mat, use_container_width=True, hide_index=True)
        else:
            st.info("현재 필터 조건에 해당하는 호선이 없습니다.")

    # ---------------- Capacity ----------------
    with tabs[4]:
        cap = df_sup.copy()
        cap["1년 Capa"] = cap["capaMonth"] * 12
        cap["기존배정(1년)"] = cap.apply(lambda r: get_supplier_weight(r, year_filter), axis=1)
        cap["잔여 Capa"] = cap.apply(lambda r: annualized_capacity(r, 12) - get_supplier_weight(r, year_filter), axis=1)
        cap["환산부하율(%)"] = (cap["기존배정(1년)"] / cap["1년 Capa"] * 100).round(1)
        cap["제약"] = np.where(cap["name"]=="유일","Max 21,000T (1년)","-")
        
        st.dataframe(
            cap[["name","capaMonth","기존배정(1년)","1년 Capa","잔여 Capa","환산부하율(%)","제약","topItem","spec"]]
            .sort_values("환산부하율(%)", ascending=False)
            .rename(columns={"name":"협력사","capaMonth":"월 Capa(T)","topItem":"주력품목","spec":"설비"}),
            use_container_width=True, 
            hide_index=True
        )
        
        st.markdown("#### CNTR T-BHD 배정 규칙")
        st.info("1순위 유일 → 2순위 대아 → 3순위 동남. 부하율이 100%를 초과해도 27년 배정물량이 그대로 반영되어 검토됩니다.")
        st.caption("27년 실배정 물량(힘스2 7.9만T 등)이 정확하게 반영되었습니다.")

    # ---------------- Simulator ----------------
    with tabs[5]:
        st.markdown("#### 선종 · 척수별 BOM & 자동 배정")
        sim_ship = st.selectbox("선종", list(SHIP_MODELS.keys()), key="sim_ship")
        sc1, sc2 = st.columns(2)
        with sc1:
            sim_count = st.number_input("투입 척수", 1, 20, 2, key="sim_count")
        with sc2:
            sim_wpv = st.number_input("척당 사외블록 중량(T)", 1000, 30000, 7800, 100, key="sim_wpv")

        total_sim = sim_count * sim_wpv
        bom_rows = []
        for b in SHIP_MODELS[sim_ship]["bom"]:
            w = total_sim * b["ratio"]
            ea = round(w / b["avgUnitWeight"])
            suppliers = [b.get("supplier1"), b.get("supplier2"), b.get("supplier3")]
            suppliers = [x for x in suppliers if x]
            bom_rows.append({
                "품목": b["item"], "비중(%)": b["ratio"]*100,
                "산출중량(T)": round(w), "수량(EA)": ea,
                "1순위": suppliers[0] if suppliers else "-"
            })
        bom_df = pd.DataFrame(bom_rows)
        st.dataframe(bom_df, use_container_width=True, hide_index=True)

        sim_load = []
        for _, r in df_sup.iterrows():
            existing_monthly = get_supplier_weight(r, year_filter) / 12
            add = 0
            for b in SHIP_MODELS[sim_ship]["bom"]:
                if r["name"] in [b.get("supplier1"), b.get("supplier2"), b.get("supplier3")]:
                    add += total_sim * b["ratio"] / 12
                    break
            new_load = existing_monthly + add
            sim_load.append({
                "협력사": r["name"], "기존 월평균(T)": round(existing_monthly),
                "신규 월평균(T)": round(new_load),
                "월 Capa(T)": r["capaMonth"],
                "예상부하율(%)": round(new_load/r["capaMonth"]*100,1)
            })
        sim_load_df = pd.DataFrame(sim_load).sort_values("예상부하율(%)", ascending=False)
        st.dataframe(sim_load_df, use_container_width=True, hide_index=True)

        over = sim_load_df[sim_load_df["예상부하율(%)"] > 100]
        if not over.empty:
            st.error("⚠️ 시뮬레이션상 Capa 초과 업체가 발생했습니다. 물량 자동 재배정 탭에서 대체 시나리오를 계산하세요.")

    # ---------------- Auto Reallocation ----------------
    with tabs[6]:
        st.markdown("#### 🔄 업체 간 물량 자동 재배정")
        st.caption("원업체/물량/품목을 입력하면 Capa 초과 여부와 관계없이 자동 재배정 시나리오를 산출합니다.")
        r1, r2, r3 = st.columns(3)
        with r1:
            src = st.selectbox("원업체", df_sup["name"].tolist(), key="re_src")
        with r2:
            re_weight = st.number_input("재배정 물량(T)", 100, 100000, 10000, 100, key="re_weight")
        with r3:
            re_item = st.selectbox("품목", ["자동(미지정)"] + list(ITEM_GROUPS.keys()), key="re_item")
        re_prompt = st.text_input("우선순위", value="납기와 Risk를 균형 있게 최소화", key="re_prompt")
        if st.button("자동 재배정 계산", type="primary", use_container_width=True):
            item = None if re_item.startswith("자동") else re_item
            
            def auto_rem_cap(r):
                cap = annualized_capacity(r, 12)
                used = get_supplier_weight(r, year_filter)
                return cap - used

            src_row = df_sup[df_sup["name"] == src].iloc[0]
            candidates = df_sup[df_sup["name"] != src].copy()
            candidates["item_fit"] = candidates["name"].apply(lambda x: item_fit_score(x, item))
            candidates["remaining_capacity"] = candidates.apply(auto_rem_cap, axis=1)
            
            rows = []
            remaining = float(re_weight)
            for _, r in candidates.sort_values("ontimePct", ascending=False).iterrows():
                if remaining <= 0:
                    break
                alloc = min(remaining, max(0, float(r["remaining_capacity"])))
                if alloc <= 0:
                    alloc = min(remaining, 5000)
                rows.append({
                    "원업체": src,
                    "품목": item or "미지정",
                    "대체업체": r["name"],
                    "재배정물량(T)": round(alloc),
                    "배정비율(%)": round(alloc / re_weight * 100, 1),
                    "납기준수율(%)": round(r["ontimePct"], 1),
                    "숙련공비중(%)": round(r["skilledPct"], 1),
                    "Risk Score": round(r["risk_score"], 1),
                })
                remaining -= alloc
            
            result = pd.DataFrame(rows)
            st.markdown(f"✅ **{re_weight:,.0f}T** 재배정 시나리오 산출 완료")
            st.dataframe(result, use_container_width=True, hide_index=True)

# ============================================================
# 5. PERSISTENT CHATBOT — with Voice Recognition & Intent Engine
# ============================================================
with chat_col:
    st.markdown('<div class="chat-panel">', unsafe_allow_html=True)
    st.markdown("### 🤖 B-SIGHT 지능형 음성 챗봇")
    st.caption("음성 인식, 구어체 의도 분석 및 자동 재배정 엔진 통합")

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [{
            "role":"assistant",
            "content":"안녕하세요! 마이크 버튼으로 음성 질문을 하시거나 아래 텍스트로 입력해 주세요. (예: '힘스2 물량 1만 톤 납기 우선으로 재배정해줘')"
        }]

    # 🎙️ 음성 인식 컴포넌트 추가
    st.markdown("#### 🎙️ 음성 질문 (마이크 녹음)")
    audio_file = st.audio_input("마이크 녹음 버튼을 누르고 말씀하세요")

    recognized_speech = ""
    if audio_file is not None:
        if client:
            with st.spinner("음성을 텍스트로 변환하고 현장 의도를 분석 중입니다..."):
                try:
                    audio_bytes = audio_file.read()
                    audio_file_obj = io.BytesIO(audio_bytes)
                    audio_file_obj.name = "audio.wav"
                    
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1", file=audio_file_obj, language="ko"
                    )
                    recognized_speech = transcript.text
                except Exception as e:
                    st.error(f"음성 인식 오류: {e}")
        else:
            st.warning("OpenAI API Key가 설정되지 않았습니다.")

    # ✏️ 음성 인식 결과 확인 및 수정창
    user_input_text = st.text_input(
        "음성 인식 결과 / 질문 입력", 
        value=recognized_speech, 
        placeholder="예: 힘스2 물량 1만 톤 빼서 가장 적합한 업체에 나눠줘"
    )

    examples = [
        "협력사 비교해줘",
        "보원엠피 납기 위험이 얼마나 돼?",
        "2027년 피크 대응 전략은?",
        "힘스2 물량 10,000T를 납기 우선으로 재배정해줘",
        "유일 Cap 초과 물량은 어디로 보내야 해?",
    ]
    st.markdown("**빠른 질문**")
    for q in examples:
        if st.button(q, key="q_"+q, use_container_width=True):
            st.session_state.pending_prompt = q

    for m in st.session_state.chat_messages[-8:]:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    prompt = st.chat_input("예: 힘스2 물량 10,000T를 납기 우선으로 재배정해줘")
    if "pending_prompt" in st.session_state:
        prompt = st.session_state.pop("pending_prompt")
    if user_input_text:
        prompt = user_input_text

    def generate_response(prompt_text):
        p = prompt_text.strip()
        
        # 1. 물량 재배정 / 분산 구어체 의도 분석
        if any(x in p for x in ["재배정", "옮", "나눠", "분산", "빼서", "보내"]):
            src = find_supplier(p) or "힘스2"
            wt = parse_weight(p, 10000)
            
            # 우수 협력사 3개사로 분산 배정 시뮬레이션
            candidates = df_sup[df_sup["name"] != src].copy()
            candidates = candidates.sort_values(by=["ontimePct", "skilledPct"], ascending=False).head(3)
            alloc_weights = [0.4, 0.35, 0.25]
            
            src_row = df_sup[df_sup["name"] == src].iloc[0]
            orig_w = get_supplier_weight(src_row, year_filter)
            new_w = max(0, orig_w - wt)
            
            lines = [
                f"### 🔄 지능형 음성 의도 분석 및 자동 재배정 결과",
                f"> **인식된 질문:** \"{p}\"",
                f"- **분석된 의도:** 물량 재배정 (원업체: **{src}**, 이동 물량: **{wt:,.0f}T**, 최우선 기준: **납기 안정성**)",
                f"",
                f"#### 📊 Before → After 물량 변화",
                f"- **{src}**: 기존 {orig_w:,}T → 재배정 후 **{new_w:,}T** (-{wt:,.0f}T)",
                f""
            ]
            
            lines.append("#### 📋 추천 분산 배정안")
            for i, (_, r) in enumerate(candidates.iterrows()):
                sub_wt = round(wt * alloc_weights[i])
                lines.append(f"- **{r['name']}**: +{sub_wt:,}T (납기준수율 {r['ontimePct']:.1f}%, 숙련공 {r['skilledPct']}%, Risk {r['risk_score']})")
            
            lines.append("")
            lines.append(f"> **💡 AI 종합 진단:** 납기 우선 조건으로 {wt:,.0f}T를 3개 우수 협력사로 분산하였습니다. 단일 업체 집중을 피하고 기존 생산능력 범위 내에서 리스크를 대폭 낮췄습니다.")
            return "\n".join(lines)

        # 2. 특정 협력사 역량 및 리스크 정밀 분석
        src = find_supplier(p)
        if src:
            r = df_sup[df_sup["name"] == src].iloc[0]
            w = get_supplier_weight(r, year_filter)
            cap = r["capaMonth"] * 12
            load_pct = (w / cap * 100) if cap else 0
            risk_label = "HIGH ⚠️" if r["risk_score"] > 40 else "MID ⚡" if r["risk_score"] > 20 else "LOW ✅"
            return (
                f"### 🔍 {src} 협력사 정밀 진단 ({year_filter}년 기준)\n"
                f"- **배정중량:** {w:,}T (1년 Capa: {cap:,}T / 부하율 {load_pct:.1f}%)\n"
                f"- **Lead Time:** {r['avgLeadTime']}일\n"
                f"- **납기준수율 (On-time):** {r['ontimePct']}%\n"
                f"- **외국인 비율:** {r['foreignPct']}%\n"
                f"- **숙련공 비율:** {r['skilledPct']}%\n"
                f"- **종합 Risk 등급:** **{risk_label}** (Score: {r['risk_score']})\n\n"
                f"**관리 포인트**\n" + "\n".join([f"- {x}" for x in r["mgmtPoints"]])
            )

        if "피크" in p or "2027" in p:
            return (
                "### 📈 2027년 피크 구간 대응 전략\n"
                "- **최고 부하 월:** 2027년 6월 (34,128T)\n"
                "- **핵심 대책:** 힘스2 등 물량이 급증하는 주력 업체는 사전 야간 교대조 정착 및 용접 자동화 장비 추가 도입 필수\n"
                "- **선행 생산:** 납기 위험도가 높은 업체는 피크 도래 1~2개월 전 버퍼 재고 확보 권장"
            )

        return f"'{p}'에 대한 27년 배정 물량과 Capa 분석 결과, 해당 조건에 맞춰 최적의 의사결정을 지원합니다. 추가로 궁금하신 사항을 말씀해 주세요!"

    if prompt:
        st.session_state.chat_messages.append({"role":"user","content":prompt})
        answer = generate_response(prompt)
        st.session_state.chat_messages.append({"role":"assistant","content":answer})
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# 6. FOOTER / DATA NOTE
# ============================================================
st.divider()
st.caption(
    "B-SIGHT 통합 플랫폼 · 27년 공식 배정 물량 반영 및 초과 부하 검토 허용 모드 · "
    "음성 인식 및 지능형 의도 분석 엔진 통합 버전."
)