'''
초단타 스켈핑

Step 1 : 상승률 상위 200종목 선정(Symbol List)

1-1 종목 선정 주기
-> 특정 조건에 따라?
-> 특정 시간에 따라?

Step 2 : 상위 200 중 조건에 맞는 종목 필터링(Final Symbol List)

2-1 필터링 조건 설정
-> marketeye(복수종목선정)
    - 거래량
    - 상한가 달성 전 / vi 해당 전

Step 3 : 해당 종목 매수

- 시장가

Step 4 : 해당 종목 매도(특정 조건 하)


- 매 스텝 당 slack으로 메세지 전송


'''

from slack import post_message
import win32com.client
import os, sys, ctypes
import pandas as pd
from datetime import datetime
import time, calendar
from cybos_base import *
from configs import *
from strategy import *
from mariadb import *
import time

kospi, kosdaq = code_name()
kospi_re = {v:i for i,v in (kospi.items())}
kosdaq_re = {v:i for i,v in (kospi.items())}


if __name__ == '__main__':
    '''
    global 변수 설정
    '''
    print('check_creon_system() :', check_creon_system())  # 크레온 접속 점검
    t_now = datetime.now()
    # 장 시작
    t_9 = t_now.replace(hour=9, minute=0, second=0, microsecond=0)
    # 장 종료
    t_exit = t_now.replace(hour=15, minute=20, second=0, microsecond=0)
    # 토/일 종료
    today = datetime.today().weekday()
    if today == 5 or today == 6:  # 토요일이나 일요일이면 자동 종료
        print('Today is', 'Saturday.' if today == 5 else 'Sunday.')
        sys.exit(0)
    #장 시작 전 당일 계좌상태 확인
    stocks = get_stock_balance('ALL')  # 보유한 모든 종목 조회

    total_cash = int(get_current_cash())  # 100% 증거금 주문 가능 금액 조회
    print('100% 증거금 주문 가능 금액 :', total_cash)
    try:
        while True:
            # 현재 시각
            t_now = datetime.now()
            # 장 시작 메세지 전송
            if t_now == t_9 :
                text = '국내 정규장 시작했습니다'
                post_message(slack_api_token, "#주식", text)
            # 장 종료 메세지 전송
            if t_exit < t_now:  # PM 03:20 ~ :프로그램 종료
                text = '국내 정규장 종료했습니다. 프로그램 종료합니다.'
                post_message(slack_api_token, "#주식", text)
                # 그날의 상위종목 DB로 전송


                sys.exit(0)
            # 장 중간 거래
            if t_9 < t_now < t_exit :
                # 상승 200종목 가져오기
                '''
                codes : 상승률 200종목 종목코드
                symbol_list : 종목코드 / 종목명 / 현재가 / 대비플래그 / 대비 / 대비율(등락률) / 거래량
                rqField & symbol_list2 : 종목코드, 시간, 대비부호, 대비, 현재가, 시가, 매도호가, 매수호가, 거래량, 거래대금, 전일거래량, 체결강도

                '''
                codes = []
                symbol_list = []
                obj7043 = Cp7043()
                obj7043.Request(codes, symbol_list)

                # 종목정보 가져오기
                # rqField = [0,1,2,3,4,10,17,11, 22, 24]  # 요청 필드
                symbol_list2 = CpMarketEye_v2(codes)

                # 필터링 후 매수 대상 종목선정
                final_symbol_list = filtering(symbol_list2)


                if len(final_symbol_list) >= 1 :
                    # 매수
                    # 우선은 한종목 전체 매수
                    final_symbol_list = final_symbol_list[0]

                    buy(company_code=final_symbol_list[0])
                    if final_symbol_list[0] in kospi.values() :
                        text = '{} 매수 완료'.format(kospi[final_symbol_list[0]])
                    else :
                        text = '{} 매수 완료'.format(kosdaq[final_symbol_list[0]])
                    post_message(slack_api_token, "#주식", text)

                    stocks = get_stock_balance('ALL')  # 보유한 모든 종목 조회

                    # 현재상황 판단 -> 매도 시그널 제공시 전체 매도
                    while True and len(stocks) != 0 :
                        condition(stocks)
                        #1.5초마다 재판단
                        time.sleep(1.5)

                    if len(stocks) != 0 :
                        # 매도
                        sell_all()
                    else :
                        pass
                else :
                    pass


            # 3초후 재탐색

            time.sleep(3)

    except Exception as ex:
        print('`main -> exception! ' + str(ex) + '`')

'''
종목코드, 시간, 대비부호, 대비, 현재가, 시가, 매도호가, 매수호가, 거래량, 거래대금, 전일거래량, 체결강도

상승률 : 현재가 / 시가
체결강도 : 특정 시점 매수 / 매도 * 100 
'''
