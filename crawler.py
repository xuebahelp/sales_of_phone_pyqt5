import csv
import os.path
import sqlite3
import time

from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re


def element_located(xpath):
    print(f"定位元素：{xpath}")
    try:
        ele = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH,
                                            xpath))
        )
    except TimeoutException:
        print(f'元素：{xpath}等待超时')
    return ele


if __name__ == '__main__':
    MAX_PAGE = 10
    # 指定 chromedriver.exe 的路径
    chrome_driver_path = r"chromedriver/chromedriver.exe"  # 替换为你的 chromedriver.exe 路径
    # 配置 ChromeOptions
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9220")
    # 创建 WebDriver 实例，指定 chromedriver.exe 路径
    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    print('driver', driver, 'connected')
    driver.get("https://www.taobao.com")
    input_search = element_located('//*[@id="q"]')
    input_search.send_keys('手机')
    time.sleep(3)
    input_search.send_keys(Keys.RETURN)
    time.sleep(5)
    driver.switch_to.window(driver.window_handles[-1])
    for i in range(MAX_PAGE):
        print(f'处理第{i}页的数据')
        if i == 0:
            pass
        else:
            obj1 = driver.find_element(By.CLASS_NAME, 'next-pagination-pages')
            obj2 = obj1.find_element(By.CSS_SELECTOR, '[class^="next-icon next-icon-arrow-right"]')
            obj2.click()
            time.sleep(5)

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")
        parent_item = soup.select('div[class^="content--"]')
        items = parent_item[0].select('div[class^="tbpc-col"]')

        # 文件写入
        f = open('output.csv', 'a+', newline='', encoding='utf-8')
        wt = csv.writer(f)
        if not os.path.exists('output.csv'):
            wt.writerow(['img', 'title', 'brand', 'price', 'sales', 'shopname', 'comments_count_text', 'comments_count',
                         'star'])
        for item in items:  # doubleCardWrapperAda
            prefix = 'https:'
            url_a_obj = item.select('a[class^="doubleCardWrapperAda"]')[0]
            url = prefix + url_a_obj.get('href')
            img = item.select("img[class^='mainPic--']")[0].get('src') if len(
                item.select("img[class^='mainPic--']")) > 0 else '无'
            title = item.select('div[class^="title--"]')[0].text
            brand = 'other'
            if title.__contains__('华为') or title.lower().__contains__('huawei') or title.__contains__('荣耀'):
                brand = '华为'
            elif (title.__contains__('小米') or title.lower().__contains__('redmi') or
                  title.lower().__contains__('red mi')) or title.__contains__('红米'):
                brand = '小米'
            elif title.lower().__contains__('oppo') or title.lower().__contains__('realme') or title.__contains__('真我'):
                brand = 'oppo'
            elif title.lower().__contains__('vivo'):
                brand = 'vivo'
            elif title.lower().__contains__('oneplus') or title.__contains__('一加'):
                brand = '一加'
            elif title.lower().__contains__('moto') or title.__contains__('摩托罗拉'):
                brand = 'moto'
            price = item.select('div[class^="innerPrice"]')[0].text
            sales_text = item.select('span[class^="realSales--"]')[0].text if len(
                item.select('span[class^="realSales--"]')) > 0 else 100
            sales_text = str(sales_text)
            if sales_text.__contains__('万'):
                sales_text = sales_text.replace('万', '0000')
            sales = ''.join(re.findall(r'\d+', sales_text))
            shopname = item.select('span[class^="shopNameText--"]')[0].text

            # 跳转详情获取一些信息
            driver.execute_script(f"window.open('{url}', '_blank');")
            driver.switch_to.window(driver.window_handles[-1])  # 切换 到详情界面
            detail = driver.get(url)
            # time.sleep(20)
            detail_page_source = driver.page_source
            if detail_page_source.__contains__('captcha'):
                print('检测到需要你手动操作过滑块，你有30秒时间')
                time.sleep(30)
            detail_soup = BeautifulSoup(detail_page_source, "html.parser")
            comments_count_text = detail_soup.select('span[class^="tagItem--"]')[0].text if len(
                detail_soup.select('span[class^="tagItem--"]')) else '0'
            star = detail_soup.select('span[class^="starNum--"]')[0].text if len(
                detail_soup.select('span[class^="starNum--"]')) > 0 else '3'
            if comments_count_text.__contains__('万'):
                comments_count_text = comments_count_text.replace('万', '0000')
            comments_count = ''.join(re.findall(r'\d+', comments_count_text))
            time.sleep(2)
            driver.close()
            driver.switch_to.window(driver.window_handles[1])  # 详情切回来
            print('items', img, title, price, sales, shopname, comments_count_text, comments_count, star)
            wt.writerow([img, title, brand, price, sales, shopname, comments_count_text, comments_count, star])
            # insert into table
            connection = sqlite3.connect("phone_sales.db")  # 数据库文件
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO phone_sales (img, title, brand, price,sales_text, sales, shopname, comments_count_text, comments_count, star) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?,?)",
                (img, title, brand, price, sales_text, sales, shopname, comments_count_text, comments_count, star)
            )
            connection.commit()
        f.close()
    # print(page_source)
