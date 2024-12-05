import os
import sys
import urllib.request
import datetime
import time
import json
import pandas as pd
import re
import streamlit as st
from io import BytesIO

client_id = 'qKDPt_KsCrYO3Nk_5zd5'
client_secret = 'Tcme4SOzTw'

title1 = []
pDate1 = []
description1 = []
link1 = []
keyword1 = []
dt_now = datetime.datetime.now().strftime('%Y-%m-%d')

#[CODE 1]
def getRequestUrl(url):
    req = urllib.request.Request(url)
    req.add_header("X-Naver-Client-Id", client_id)
    req.add_header("X-Naver-Client-Secret", client_secret)
    
    try:
        response = urllib.request.urlopen(req)
        if response.getcode() == 200:
            print("[%s] Url Request Success" % datetime.datetime.now())
            return response.read().decode('utf-8')
    except Exception as e:
        print(e)
        print("[%s] Error for URL : %s" % (datetime.datetime.now(), url))
        return None

#[CODE 2]
def getNaverSearch(node, srcText, start, display):
    base = "https://openapi.naver.com/v1/search"
    node = "/%s.json" % node
    
    # 검색어를 안전하게 인코딩하되 + 기호는 인코딩에서 제외합니다.
    encoded_query = urllib.parse.quote(srcText, safe='+')
    parameters = "?query=%s&start=%s&display=%s" % (encoded_query, start, display)

    url = base + node + parameters
    responseDecode = getRequestUrl(url)  # [CODE 1]

    if responseDecode is None:
        return None
    else:
        return json.loads(responseDecode)

#[CODE 3]
def getPostData(post, jsonResult, cnt, keyword):
    cleanr = re.compile('<.*?>')
    
    title = post['title']
    titlec = re.sub(cleanr, '', title)
    
    # 뉴스 기사 본문 전체 내용을 가져옵니다
    description = post['description']
    descriptionc = re.sub(cleanr, '', description)
    
    link = post['link']
    pDate = datetime.datetime.strptime(post['pubDate'], '%a, %d %b %Y %H:%M:%S +0900')
    pDate = pDate.strftime('%Y-%m-%d %H:%M:%S')

    title1.append(titlec)
    description1.append(descriptionc)
    link1.append(link)
    pDate1.append(pDate)
    keyword1.append(keyword)

    jsonResult.append({'cnt': cnt, 'title': title, 'description': description,
                       'link': link, 'pDate': pDate, 'keyword': keyword})
    return

#[CODE 0]
def main():
    st.markdown("<h1 style='color:green'>정부포상</h1> 관련 네이버 검색", unsafe_allow_html=True)
    st.write("네이버 뉴스에서 검색어를 입력 후 엑셀 파일로 다운로드")
    
    # 검색어 입력창 생성
    st.write("검색어를 입력하세요!")
    st.markdown("**주의할점**:<br>앞 단어 한칸 띄어쓰기 후 '+' 입력 후 바로 다음 단어 입력,<br>그리고 꼭 포함해야하는 단어는 앞 뒤 큰따옴표", unsafe_allow_html=True)
    st.write("\n(쉼표로 구분, 예: \"삿포로\" +\"맥주\", \"삿포로\" +\"술집\")")
    
    search_queries = st.text_input('')
    if st.button('검색 실행'):
        if not search_queries:
            st.warning('검색어를 입력하세요.')
            return
        
        search_queries = search_queries.split(', ')
        cnt = 0
        jsonResult = []

        for srcText in search_queries:
            jsonResponse = getNaverSearch('news', srcText.strip(), 1, 100)  # [CODE 2]
            if jsonResponse is None or 'total' not in jsonResponse:
                st.warning(f'검색 결과를 가져오지 못했습니다. 오류가 발생했을 수 있습니다. (검색어: {srcText})')
                continue

            total = jsonResponse['total']

            while (jsonResponse is not None) and (jsonResponse['display'] != 0):
                for post in jsonResponse['items']:
                    cnt += 1
                    getPostData(post, jsonResult, cnt, srcText)  # [CODE 3]
                    
                start = jsonResponse['start'] + jsonResponse['display']
                jsonResponse = getNaverSearch('news', srcText.strip(), start, 100)  # [CODE 2]

            st.write(f'전체 검색 ({srcText}) : %d 건' % total)
            
        # 데이터프레임 생성
        df = pd.DataFrame([title1, pDate1, description1, link1, keyword1]).T
        df.columns = ['제목', '날짜', '내용', '네이버뉴스주소', '검색된 키워드']

        # 파일명 생성
        safe_srcText = "_".join([re.sub(r'[\/*?:"<>|+]', "", query) for query in search_queries]).replace(" ", "_")
        file_name = f'{dt_now}_{safe_srcText}.xlsx'

        # 엑셀 파일로 변환 및 다운로드 링크 생성
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
            writer.close()
            processed_data = output.getvalue()
        
        st.download_button(label='엑셀 파일 다운로드', data=processed_data, file_name=file_name, mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
        st.success("가져온 데이터 : %d 건" % (cnt))

if __name__ == '__main__':
    main()
