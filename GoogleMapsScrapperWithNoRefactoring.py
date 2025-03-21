import time
import warnings
import csv
import pprint

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup as bs

from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

#ActionChains모듈 가져오기
from selenium.webdriver import ActionChains

driver = webdriver.Chrome()
#ActionChains생성
action = ActionChains(driver)

sleep_for_one=1
sleep_for_two=2
sleep_for_three=3
sleep_for_four=4
# apply stealth settings
stealth(
    driver,
    languages=["en-US", "en"],
    vendor="Google Inc.",
    platform="Win32",
    webgl_vendor="Intel Inc.",
    renderer="Intel Iris OpenGL Engine",
    fix_hairline=True,
)

url= 'https://www.google.com/maps'
driver.get(url)

time.sleep(sleep_for_two)


 # 검색어 전달
driver.find_element(By.XPATH, r'//*//*[@id="searchboxinput"]').send_keys(Keys.ENTER)  # 돋보기 클릭
time.sleep(sleep_for_two) # Let the user actually see something!
search_area = driver.find_element(By.XPATH, r'//*[@id="searchboxinput"]') # 구글 검색창
search_loc = '서울 관광지'
search_area.send_keys(search_loc)
time.sleep(sleep_for_two) # Let the user actually see something!
driver.find_element(By.XPATH, r'//*[@id="searchbox-searchbutton"]').send_keys(Keys.ENTER)  # 돋보기 클릭릭


time.sleep(sleep_for_three)


page_limit= 14  #(3,5,7,9,11,13)
for p in range(3,page_limit,2): 

    time.sleep(sleep_for_three)
    driver.find_element(By.XPATH,r'//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[1]/div[1]/div['+str(p)+']/div/a').send_keys(Keys.ENTER) #특정 관광지 
    html= driver.page_source
    soup=bs(html,'html.parser')


    place=soup.select_one('#QA0Szd > div > div > div.w6VYqd > div:nth-child(2) > div > div.e07Vkf.kA9KIf > div > div > div.m6QErb.DxyBCb.kA9KIf.dS8AEf.XiKgde.ecceSd > div.m6QErb.DxyBCb.kA9KIf.dS8AEf.XiKgde.ecceSd > div:nth-child('+str(p)+') > div > a')
    
    print(str(place))
    place_name = str(place.get("aria-label")) #장소명 출력력

    time.sleep(sleep_for_four)
     
    tabList =driver.find_elements(By.CLASS_NAME,"hh2c6")
    print(len(tabList))
    for k in range(0, len(tabList)):
        s=str(tabList[k].get_attribute( 'aria-label' ))[-2:]
        if(s=="리뷰"):
            tabList[k].send_keys(Keys.ENTER)
            break


    time.sleep(5)

    # ==================== 리뷰탭 클릭하기


    review_list=[]
     
    review_limit=50   #(1,5,9,11,15...49) 
    for i in range(1, review_limit , 4):
     try:
        if(i==1):
            for u in range(0,4):
             driver.find_element(By.XPATH,r'//*[@id="QA0Szd"]/div/div/div[1]/div[3]/div/div[1]/div/div/div[3]').send_keys(Keys.PAGE_DOWN)
                # 스크롤바 내리기

        time.sleep(1)
        element=driver.find_element(By.XPATH,r'//*[@id="QA0Szd"]/div/div/div[1]/div[3]/div/div[1]/div/div/div[3]/div[9]/div['+str(i)+']')  


        driver.execute_script("arguments[0].scrollIntoView(true);",element) #특정 요소로 스크롤 되기.  //예외 발생 가능
        
       
        result_html=driver.page_source
        
        soup=bs(result_html, 'html.parser')
        
        time.sleep(5)
        

        review=soup.select_one('#QA0Szd > div > div > div.w6VYqd > div.bJzME.Hu9e2e.tTVLSc > div > div.e07Vkf.kA9KIf > div > div > div.m6QErb.DxyBCb.kA9KIf.dS8AEf.XiKgde > div:nth-child(9) > div:nth-child('+str(i)+') > div > div > div:nth-child(4) > div:nth-child(2)')
        time.sleep(2)
        review_html=str(review)
    
        soup = bs(review_html, 'html.parser')

        # 첫 번째 <span> 태그 가져오기
        first_span = soup.find('span')

        # 텍스트 추출
        review_text = first_span.get_text(strip=True).replace("\n"," ")
        
        review_format=[]
        #print(place_name+review_text)
        review_format.append(place_name)
        review_format.append(review_text)
        review_list.append(review_format)
        time.sleep(2)
     except:
         for u in range(0,4):
            driver.find_element(By.XPATH,r'//*[@id="QA0Szd"]/div/div/div[1]/div[3]/div/div[1]/div/div/div[3]').send_keys(Keys.PAGE_DOWN)
         continue    

    print(len(review_list)) 
    if p == 3:
        f = open('./test.csv', 'w', encoding='utf-8-sig', newline='')  # 파일명 써주기 
        writer_csv = csv.writer(f)
        header = ['place_name', 'review']
        writer_csv.writerow(header)

        for i in review_list:
            writer_csv.writerow(i)

    else:   
    	# 파일이 이미 존재하므로, 존재하는 파일에 이어서 쓰기 
        f = open('./test.csv', 'a', encoding='utf-8-sig', newline='')
        writer_csv = csv.writer(f)

        for i in review_list:
            writer_csv.writerow(i)
    time.sleep(2)        


print("성공")       
















