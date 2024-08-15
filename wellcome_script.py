from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime
from datetime import date
from db_config import conn, cur
import numpy as np
import re
import time
import pandas as pd
import psycopg2
import copy

# start webscraping
url = url = 'https://www.wellcome.com.hk/'
driver = webdriver.Chrome()
driver.get(url)
wait = WebDriverWait(driver, 3)
time.sleep(1)
driver.maximize_window()
element = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@id="easychat-chat-dismiss-social-subscriber"]')))
element.click()

link_list = []
product_info_list = []
brand_list = []
new_product_info = []
def to_drink_list(driver):
    wait = WebDriverWait(driver, 5)
    sorting_link = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@id="all-categories"]')))
    sorting_link.click()
    element = wait.until(EC.visibility_of_element_located((By.XPATH, '//a[contains(text(), "飲品")]')))
    element.click()
def expand(driver):
    driver.find_element(By.XPATH, "//div[text()='展開']").click()
def brand_list_get(driver):
    global brand_list
    elements = driver.find_elements(By.XPATH, "//div[contains(@data-v-0574b335, '') and contains(@class, 'mar-t-20 filter-scroll-container')]")
    brand_list = [i.text for i in elements]
    brand_list = map(lambda x: x.replace('\n', ',').split(','), brand_list)
    brand_list = list(brand_list)  
    return brand_list
def product_get(driver):
    global product_info_list
    elements = driver.find_elements(By.XPATH, '//div[@class="info-content"]')
    product_info = [i.text for i in elements]
    product_info = map(lambda x: x.replace('\n', ','), product_info)
    product_info = list(product_info)
    product_info_list.append(product_info)
    return product_info
    
def product_link_get(driver):
    global link_list
    elements = driver.find_elements(By.XPATH, "//a[contains(@class, 'a-link router-link ware-wrapper')]")
    for element in elements:
        a = element.get_attribute("href")
        link_list.append(a)
    return link_list

def next_page(driver):
    xpath = '//div[contains(@data-v-dd921116, "") and contains(text(), "下一頁")]'
    element = driver.find_element(By.XPATH, xpath)
    element.click()

def new_product_list(product_info_list, new_total_brand):
    global new_product_info
    excluded_words = ['品質', '送貨方式', '送貨', '加入購物車', '門市自取', '規格', '儲存方式', '產地', '常溫', '冷凍', '急凍']
    
    for list in product_info_list:
        list[0] = list[0].split(',')
        list[0] = [i for i in list[0] if i not in excluded_words and 'day' not in i and 'days' not in i] 
        if list[0][1].count('$') == 2:
            list[0][1] = list[0][1].split(' ')
            list[0][1].pop(1)
        else:
            list[0][1] = [list[0][1], list[0][1]]
        
        if list[0][-1] != '售罄':
            list[0].append(None)

        flag = False
        if not flag:
            for brand in new_total_brand:
                if brand in list[0][0]:
                    list[0].append(i)
                    flag = True
                    break
        if not flag:
            list[0].append(None)
        new_product_info.append(list)
    return new_product_info

# main webscraping script
to_drink_list(driver)
time.sleep(1)
expand (driver)
time.sleep(1)
brand_list_get(driver)
flag = False

while not flag:
    try:
        product_link_get(driver)
        time.sleep(2)
        next_page(driver)
        time.sleep(2)
    except:
        NoSuchElementException
        flag = True

for link in link_list:
    retry = True    
    while retry:
        try:
            driver.get(link)
            time.sleep(1)
            product_get(driver)
            time.sleep(1)
            retry = False
        except Exception as e:
            print(f'link: {link}, error: {e}')
            retry = True

# Sorting duplicate brand names and remove them
remove_list = []
Eng_brand_list = []
Chi_brand_list = []
new_total_brand = []
# handpickinng to remove or add brands as the product name normally contains the brand, but some time the brand name is slightly alter in the prodcut  
remove_brand = ['THE COFFEE ACA', 'VITA COCO', 'YOU.C1000 YOUC1000', 'DYDO', 'TARZA CAFFE TARZA', 'OPAL COFFEE OPAL', 'DON SIMON DON SMION', '汽水', 'ROBINSONS', ]
add_brand = ['咖啡學研', '維他COCO', 'You C1000', '大島', 'Tarza', 'Opal', 'Don Simon', 'OOHA', '羅便臣', 'Taster Choice', 'Acqua Panna', 'WATSONS', '冰格麗', '冰格麗', '統一', '鴻褔堂', '黑白', 'Lavazza', 'Kagome', '花斑茶社', '康果', '迎樂', '如果', '七喜', '西瑞斯', 'G7', '谷池', 'Don Smion']

for i, item in enumerate(brand_list[0]):
    for j in range(i+1 , len(brand_list[0])):

        if brand_list[0][j] in brand_list[0][i]:
            remove_list.append(brand_list[0][i])
            
remove_list.append('7 UP FREE 七喜輕怡')
remove_list.append('7 UP 七喜')
remove_list.append('WATSONS SODA 屈臣氏梳打')
sorted_brand_list = [i for i in brand_list[0] if i not in remove_list]
chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')
english_pattern = re.compile(r'^[a-zA-Z0-9&. ]+$')  

for word in sorted_brand_list:
    chinese_matches = chinese_pattern.findall(word)
    Chi_brand_list.extend(chinese_matches)
    if not chinese_matches:  # Check if no Chinese characters were found
        english_matches = english_pattern.findall(word)
        if english_matches:
              Eng_brand_list.extend(english_matches)

title_english_brand = copy.deepcopy(Eng_brand_list) 
title_english_brand = list(map(lambda x: x.title(), title_english_brand))
total = Chi_brand_list + Eng_brand_list + title_english_brand
for item in total:
    if item not in remove_brand:
        new_total_brand.append(item)
for item in add_brand:
    new_total_brand.append(item)

# remove all the empty list from the product_info_list if any
while True:
    try:
        product_info_list.remove([])
    except:
        print ('No empty list found')
        break

new_product_list(product_info_list, new_total_brand)

cleaned_product_info = []
# the prodcut info list contains nested lists, it denest the lists and return a single list for a product
# the idea is for looping every item in the product info list, when we encounter a nested list, we delist it and append it with orgional comtent to create a new list
for index , item in enumerate(new_product_info):
    emp = []
    for j in item:
            if isinstance(j, list):
                for k in j:
                    if isinstance(k, list):
                        for l in k:
                            emp.append(l)
                    else:
                        emp.append(k)
            else:
                emp.append(j)
    cleaned_product_info.append(emp)


for i in cleaned_product_info:
    while len(i) < 10:
        i.append(None)

# turm data into df and further cleaning
columns = ['product_name', 'current_price', 'unit_price', 'packing', 'country', 'stock_status', 'brand_name', 'discount_1', 'discount_2', 'discount_3']
data_dict_list = [dict(zip(columns, row)) for row in cleaned_product_info]
well_df = pd.DataFrame(data_dict_list)
well_df['current_price'] = well_df['current_price'].str.replace('$', '').apply(lambda x: x.split(' ')[0] if ' ' in x else x).astype(float)
well_df['unit_price'] = well_df['unit_price'].str.replace('$', '').apply(lambda x: x.split(' ')[0] if ' ' in x else x).astype(float)
new_column_order = ['brand_name'] + [col for col in well_df.columns if col != 'brand_name'] # just change the column order wont affect the data
well_df = well_df[new_column_order]
current_day = date.today().strftime('%Y-%m-%d')
well_df['date'] = pd.to_datetime(current_day)
print (well_df[well_df['brand_name'].isnull()])
csv_name = 'wellcome_{}.csv'.format(current_day)
well_df.to_csv(csv_name, index=False)

# loading data into sql database
product_name = well_df['product_name'].tolist()
brand_name = well_df['brand_name'].tolist()
packing = well_df['packing'].tolist()
country = well_df['country'].tolist()
current_price = well_df['current_price'].tolist()
unit_price = well_df['unit_price'].tolist()
discount_1 = well_df['discount_1'].tolist()
discount_2 = well_df['discount_2'].tolist()
discount_3 = well_df['discount_3'].tolist()
scrap_date = well_df['date'].tolist()

products_well_dict_list = []

for a, b, c, d in zip(brand_name, product_name, packing, country):
    product = {'brand_name': a, 'product_name': b, 'packing': c, 'country': d}
    products_well_dict_list.append(product)

insert_query = """INSERT INTO products_well (brand_name, product_name, packing, country)
VALUES (%s, %s, %s, %s) ON CONFLICT (product_name)
DO NOTHING """

cur.executemany(insert_query, [(d['brand_name'], d['product_name'], d['packing'], d['country']) for d in products_well_dict_list])

fact_well_dict_list = []
for a, b, c, d, e, f, g in zip(product_name, current_price, unit_price, discount_1, discount_2, discount_3, scrap_date):
    product_fact = {'product_name': a, 'current_price': b, 'unit_price': c, 'discount_1': d, 'discount_2': e, 'discount_3': f, 'scrap_date': g}
    fact_well_dict_list.append(product_fact)

insert_query = """INSERT INTO fact_well (product_name, current_price, unit_price, discount_1, discount_2, discount_3, scrap_date)
VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT
DO NOTHING """

cur.executemany(insert_query, [(d['product_name'], d['current_price'], d['unit_price'], d['discount_1'], d['discount_2'], d['discount_3'], d['scrape_date']) for d in fact_well_dict_list])
conn.commit()
conn.close()
cur.close()




