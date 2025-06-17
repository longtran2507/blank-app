import pandas as pd  # 데이터 처리 및 CSV 파일 저장을 위한 라이브러리
from bs4 import BeautifulSoup  # HTML 파싱을 위한 라이브러리
import requests  # HTTP 요청을 보내기 위한 라이브러리
import time

def find_item_value(keys, values, item):
    index = -1
    try:
        index = keys.index(item)
        if index >=0 & index < len(keys):
            return values[index]
        else:
            return ""
    except:
        return ""
    
def get_detail_info(detail_soup):
    # Key: table.table-basic-infomation-primary > tbody > tr.field > th.field-label
    # Value: table.table-basic-infomation-primary > tbody > tr.field > td.field-value > div.value-container > div.value
    # 자본금, 매출액, 설립일, 대표자
    items = ["자본금","매출액", "설립일", "대표자"]
    
    key_elements = detail_soup.select(
        "table.table-basic-infomation-primary > tbody > tr.field > th.field-label")
    value_elements = detail_soup.select(
        "table.table-basic-infomation-primary > tbody > tr.field > td.field-value")
    print("key_elements", key_elements)
    print("value_elements", value_elements)
    key_list = [ key.get_text(strip=True) for key in key_elements ]
    value_list = [ value.get_text(strip=True) for value in value_elements ]
    print("key_list", key_list)
    print("value_list", value_list)
    
    capital = find_item_value(key_list, value_list, items[0])
    print("자본금:", capital)
    sales = find_item_value(key_list, value_list, items[1])
    print("매출액:", sales)
    foundation_date = find_item_value(key_list, value_list, items[2])
    print("설립일:", foundation_date)
    ceo = find_item_value(key_list, value_list, items[3])
    print("대표자:", ceo)
    return (capital, sales, foundation_date, ceo)
    
    
def get_jobkorea_data(corp_name_list, page_no=1):
    """
    JobKorea 웹사이트에서 기업 정보를 크롤링하여 데이터프레임으로 반환하는 함수.
    Args:
        corp_name_list (List[str]): 검색할 기업명 리스트.
        page_no (int): 검색 결과 페이지 번호 (기본값: 1).
    Returns:
        pd.DataFrame: 크롤링된 기업 정보를 포함하는 데이터프레임.
    """
    jobkorea_data = []  # 크롤링된 데이터를 저장할 리스트
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    
    # Convert DataFrame to list if needed
    if isinstance(corp_name_list, pd.DataFrame):
        corp_name_list = corp_name_list['기업명'].tolist()
        
    for corp_name in corp_name_list:
        # URL encode the company name
        corp_name_encoded = requests.utils.quote(corp_name)
        url = f"https://www.jobkorea.co.kr/Search/?stext={corp_name_encoded}&tabType=corp&Page_No={page_no}"
        response = requests.get(url, headers=headers)  # HTTP GET 요청을 보내고 응답 받기
        soup = BeautifulSoup(response.text, "html.parser")  # HTML 응답을 파싱

        # Flex 컴포넌트 구조에서 기업 정보를 포함하는 부분 찾기
        #           Flex_display_flex__i0l0hl2 Flex_direction_row__i0l0hl3 Flex_justify_space-between__i0l0hlf
        #           .Flex_display_flex__i0l0hl2 .Flex_direction_row__i0l0hl3 Flex_justify_space-between__i0l0hlf
        flex_containers = soup.find_all(
            "div",
            class_="Flex_display_flex__i0l0hl2 Flex_direction_row__i0l0hl3 Flex_justify_space-between__i0l0hlf",
        )

        # Flex 컨테이너 개수를 출력 (디버깅용)
        print(f"Found {len(flex_containers)} flex containers for {corp_name}")
        
        for container in flex_containers: # 10개 중에 1개씩 처리 한다.
            # 내부 Flex 컨테이너 찾기
            #           Flex_display_flex__i0l0hl2 Flex_gap_space12__i0l0hls Flex_direction_row__i0l0hl3
            inner_flex = container.find(
                "div",
                class_="Flex_display_flex__i0l0hl2 Flex_gap_space12__i0l0hls Flex_direction_row__i0l0hl3",
            )
            if not inner_flex:  # 내부 Flex 컨테이너가 없으면 건너뜀
                continue

            # span 태그에서 정보 추출
            spans = inner_flex.find_all(
                "span", class_="Typography_variant_size14__344nw27"
            )
            #print(spans)
            
            if len(spans) >= 3:  # 필요한 정보가 포함된 span 태그가 3개 이상인 경우
                if len(spans) == 3:
                    corp_type = (
                        spans[0].get_text(strip=True) if spans[0] else None
                    )  # 기업형태
                    corp_location = (
                        spans[1].get_text(strip=True) if spans[1] else None
                    )  # 지역
                    corp_industry = (
                        spans[2].get_text(strip=True) if spans[2] else None
                    )  # 업종
                elif len(spans) == 4: 
                    corp_type = (
                        spans[1].get_text(strip=True) if spans[1] else None
                    )  # 기업형태
                    corp_location = (
                        spans[2].get_text(strip=True) if spans[2] else None
                    )  # 지역
                    corp_industry = (
                        spans[3].get_text(strip=True) if spans[3] else None
                    )  # 업종
                
                # 찾은 회사의 링크 URL을 구한다. 
                # get()을 이용해서 (requests.get) 이동한다.
                # 이동한 상세 페이지에서 자본금과 매출액을 구해온다.
                # 추출된 데이터를 딕셔너리로 저장
                
                if container:
                    #                                             Flex_display_flex__i0l0hl2 Flex_gap_space4__i0l0hly Flex_direction_column__i0l0hl4
                    parent = container.find_parent('div', class_="Flex_display_flex__i0l0hl2 Flex_gap_space4__i0l0hly Flex_direction_column__i0l0hl4")
                    if parent:
                        a_tag = parent.find('a', href=True)
                        #print(a_tag)
                        if a_tag:
                            print("링크:", a_tag['href'])
                            # 방어코드를 넣으세요.  select_one으로 가져온 결과가 None 일때의 처리 등.
                            detail_response = requests.get(a_tag['href'], headers=headers)  # HTTP GET 요청을 보내고 응답 받기
                            detail_soup = BeautifulSoup(detail_response.text, "html.parser")  # HTML 응답을 파싱
                            
                            get_detail_info(detail_soup)
                            # #company-body > div.company-body-infomation.is-fixed > div.company-infomation-row.basic-infomation > div > table > tbody > tr:nth-child(3) > td:nth-child(2) > div > div > div.value
                            # value_container가 None 일 때 오류가 발생하지 않도록 처리해주세요(방어코드)
                            value_container = detail_soup.select_one("div.company-infomation-row.basic-infomation > div > table > tbody > tr:nth-child(3) > td:nth-child(2) > div > div")
                            if not value_container:
                                capital_tag = None
                            else:
                                capital_tag = value_container.select_one(".value")
                            if capital_tag:
                                capital = capital_tag.text 
                            else:
                                capital = ""
                            print("자본금: ", capital)
                            # #company-body > div.company-body-infomation.is-fixed > div.company-infomation-row.basic-infomation > div > table > tbody > tr:nth-child(3) > td:nth-child(4) > div > div > div.value
                            sales_container = detail_soup.select_one("div.company-infomation-row.basic-infomation > div > table > tbody > tr:nth-child(3) > td:nth-child(4) > div > div")
                            if sales_container:
                                sales_tag = sales_container.select_one(".value")
                            else:
                                sales_tag = None
                            if sales_tag:
                                sales = sales_tag.text 
                            else:
                                sales = ""
                            #print("매출액: ", sales)
                            ceo_tag = detail_soup.select_one("div.company-infomation-row.basic-infomation > div > table > tbody > tr:nth-child(4) > td:nth-child(2) > div > div")
                            if ceo_tag:
                                ceo = ceo_tag.text 
                            else:
                                ceo = ""
                            #print("대표자: ", ceo)
                            # 설립일: #company-body > div.company-body-infomation.is-fixed > div.company-infomation-row.basic-infomation > div > table > tbody > tr:nth-child(2) > td:nth-child(4) > div > div > div.value
                            foundation_date_tag = detail_soup.select_one("div.company-infomation-row.basic-infomation > div > table > tbody > tr:nth-child(2) > td:nth-child(4) > div > div > div.value")
                            if foundation_date_tag:
                                foundation_date = foundation_date_tag.text 
                            else:
                                foundation_date = ""
                            #print("설립일", foundation_date)
                            
                        else:
                            pass
                            #print("a 태그를 찾을 수 없습니다.")
                    else:
                        print("부모 div를 찾을 수 없습니다.")
                else:
                    print("대상 div를 찾을 수 없습니다.")
                    
                jobkorea_data.append(
                    {
                        "기업명": corp_name,
                        "기업형태": corp_type,
                        "지역": corp_location,
                        "업종": corp_industry,
                        "자본금": capital,
                        "매출액": sales,
                        "대표자": ceo,
                        "설립일": foundation_date
                    }
                )
                # 추출된 데이터를 출력 (디버깅용)
                print(f"추출된 데이터: {corp_name}, {corp_type}, {corp_location}, {corp_industry}")
            else:
                # span 태그가 부족한 경우 경고 메시지 출력
                print(f"정보가 충분하지 않음: {len(spans)} 개의 span 태그 발견")
            time.sleep(3)
    # 크롤링된 데이터를 데이터프레임으로 변환하여 반환

    return pd.DataFrame(jobkorea_data)


if __name__ == "__main__":
    """
    메인 실행 코드: CSV 파일에서 기업명을 읽어와 크롤링 수행
    """
    try:
        # Read target companies
        target_companies = pd.read_csv("company_list.csv", encoding="utf-8-sig")

        target_companies_name = target_companies['회사명'].dropna().unique().tolist()

        # Get data
        test_data = get_jobkorea_data(target_companies_name)

        # Save results
        output_file = "jobkorea_data.csv"
        test_data.to_csv(output_file, index=False, encoding="utf-8-sig")
        print(f"Data saved to {output_file}")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")