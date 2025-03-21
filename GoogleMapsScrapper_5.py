import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup as bs
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains

class GoogleMapsScraper:
    SLEEP_ONE = 1
    SLEEP_TWO = 2
    SLEEP_THREE = 3
    SLEEP_FOUR = 4

    def __init__(self):
        self.driver = webdriver.Chrome()
        self.action = ActionChains(self.driver)
        self.init_driver_stealth()

    def init_driver_stealth(self):
        # 드라이버 스텔스 설정 적용
        stealth(
            self.driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )

    def navigate_to_url(self, url):
        self.driver.get(url)
        time.sleep(self.SLEEP_TWO)

    def perform_search(self, search_loc):
        # 초기 검색창 클릭 후 검색어 입력 및 검색 버튼 클릭
        search_input = self.driver.find_element(By.XPATH, r'//*//*[@id="searchboxinput"]')
        search_input.send_keys(Keys.ENTER)
        time.sleep(self.SLEEP_TWO)
        search_area = self.driver.find_element(By.XPATH, r'//*[@id="searchboxinput"]')
        search_area.send_keys(search_loc)
        time.sleep(self.SLEEP_TWO)
        search_button = self.driver.find_element(By.XPATH, r'//*[@id="searchbox-searchbutton"]')
        search_button.send_keys(Keys.ENTER)

    def click_place(self, p):
        # 페이지 내 특정 관광지 클릭
        xpath = (
            r'//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[1]/div[1]/div['
            + str(p)
            + r']/div/a'
        )
        element = self.driver.find_element(By.XPATH, xpath)
        element.send_keys(Keys.ENTER)
        time.sleep(self.SLEEP_THREE)

    def get_page_soup(self):
        html = self.driver.page_source
        return bs(html, 'html.parser')

    def extract_place_name(self, soup, p):
        # 장소명 추출
        selector = (
            '#QA0Szd > div > div > div.w6VYqd > div:nth-child(2) > div > div.e07Vkf.kA9KIf > '
            'div > div > div.m6QErb.DxyBCb.kA9KIf.dS8AEf.XiKgde.ecceSd > '
            'div.m6QErb.DxyBCb.kA9KIf.dS8AEf.XiKgde.ecceSd > '
            'div:nth-child(' + str(p) + ') > div > a'
        )
        place_elem = soup.select_one(selector)
        return str(place_elem.get("aria-label")) if place_elem else ""

    def click_review_tab(self):
        # 리뷰 탭 클릭
        tab_list = self.driver.find_elements(By.CLASS_NAME, "hh2c6")
        for tab in tab_list:
            aria_label = tab.get_attribute('aria-label')
            if aria_label and aria_label[-2:] == "리뷰":
                tab.send_keys(Keys.ENTER)
                break
        time.sleep(5)

    def scroll_review_section(self):
        # 리뷰 영역 스크롤 내리기
        scroll_element = self.driver.find_element(By.XPATH, r'//*[@id="QA0Szd"]/div/div/div[1]/div[3]/div/div[1]/div/div/div[3]')
        for _ in range(4):
            scroll_element.send_keys(Keys.PAGE_DOWN)

    def extract_reviews(self, place_name, review_limit):
        review_list = []
        for i in range(1, review_limit, 4):
            try:
                if i == 1:
                    self.scroll_review_section()
                time.sleep(1)
                xpath = (
                    r'//*[@id="QA0Szd"]/div/div/div[1]/div[3]/div/div[1]/div/div/div[3]/div[9]/div['
                    + str(i)
                    + r']'
                )
                element = self.driver.find_element(By.XPATH, xpath)
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                result_html = self.driver.page_source
                soup = bs(result_html, 'html.parser')
                time.sleep(5)
                selector = (
                    '#QA0Szd > div > div > div.w6VYqd > div.bJzME.Hu9e2e.tTVLSc > div > '
                    'div.e07Vkf.kA9KIf > div > div > div.m6QErb.DxyBCb.kA9KIf.dS8AEf.XiKgde > '
                    'div:nth-child(9) > div:nth-child(' + str(i) +
                    ') > div > div > div:nth-child(4) > div:nth-child(2)'
                )
                review_elem = soup.select_one(selector)
                time.sleep(2)
                if review_elem:
                    review_html = str(review_elem)
                    review_soup = bs(review_html, 'html.parser')
                    first_span = review_soup.find('span')
                    review_text = first_span.get_text(strip=True).replace("\n", " ") if first_span else ""
                    review_list.append([place_name, review_text])
                time.sleep(2)
            except Exception as e:
                self.scroll_review_section()
                continue
        return review_list

    def save_reviews_to_csv(self, filename, review_list, header, mode='w'):
        with open(filename, mode, encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            if mode == 'w':
                writer.writerow(header)
            for review in review_list:
                writer.writerow(review)

    def close(self):
        self.driver.quit()


def main():
    scraper = GoogleMapsScraper()
    url = 'https://www.google.com/maps'
    scraper.navigate_to_url(url)
    
    search_loc = '서울 관광지'  # [지역 이름]_관광지로 설정하는 것을 권장
    scraper.perform_search(search_loc)
    
    page_limit = 14  # (3,5,7,9,11,13)
    filename = './test.csv'
    header = ['place_name', 'review']
    
    for p in range(3, page_limit, 2):
        time.sleep(scraper.SLEEP_THREE)
        scraper.click_place(p)
        soup = scraper.get_page_soup()
        place_name = scraper.extract_place_name(soup, p)
        time.sleep(scraper.SLEEP_FOUR)
        
        scraper.click_review_tab()
        review_limit = 50  # (1,5,9,11,15...49)
        reviews = scraper.extract_reviews(place_name, review_limit)
        print("추출된 리뷰 개수:", len(reviews))
        
        if p == 3:
            scraper.save_reviews_to_csv(filename, reviews, header, mode='w')
        else:
            scraper.save_reviews_to_csv(filename, reviews, header, mode='a')
        time.sleep(2)
    
    print("성공")
    scraper.close()


if __name__ == "__main__":
    main()
