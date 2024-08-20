from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime
from datetime import date
from db_config import create_connection
import numpy as np
import re
import time
import pandas as pd
import psycopg2

# start of the web scraping process
driver = webdriver.Chrome()
url = "https://www.pns.hk/zh-hk/%E9%A3%B2%E5%93%81%E3%80%81%E5%8D%B3%E6%B2%96%E9%A3%B2%E5%93%81/lc/04010000"
driver.get(url)
driver.maximize_window()
time.sleep(3)
driver.execute_script("window.scrollTo(0, document.body.scrollHeight/20);")

try:
    show_all_btn = driver.find_element(By.CSS_SELECTOR, 'div.toggleAllBtn')
    show_all_btn.click()
    time.sleep(2)
except Exception:
    pass

cancel_cookie_button = driver.find_element(By.XPATH, '//button[@class = "onetrust-close-btn-handler onetrust-close-btn-ui banner-close-button ot-close-icon"]')
cancel_cookie_button.click()
catagory_links = []
no_swiper_div = driver.find_element(By.CSS_SELECTOR, '.no-swiper')
links = no_swiper_div.find_elements(By.TAG_NAME, 'a')
for link in links:
    if link.get_attribute("href") != None:
        catagory_links.append(link.get_attribute("href"))
# Not including alchol beverage category
filtered_category_links = [link.get_attribute("href") for link in links if '酒精飲品' not in link.text] 


product_link = []
total_product_info_list = []
category_list = ['水', '原箱飲品', '汽水', '即飲茶類、咖啡、奶茶', '奶類、乳酪飲品', '植物奶、大豆飲品', '咖啡、沖調飲品、熱飲', '果汁、椰子水', '運動及能量飲品', '草本及健康飲品']
# the function for scraping all the product link
def get_product_link(filtered_category_links):
    for iink in filtered_category_links:
        driver.get(iink)
        time.sleep(1)
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_count = 0
        while scroll_count < 3:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                scroll_count += 1
            else:
                scroll_count = 0
            last_height = new_height
        containers = driver.find_elements(By.XPATH, "//div[@class = 'productContainer']")
        for container in containers:
            link  = container.find_element(By.TAG_NAME, 'a').get_attribute('href')
            product_link.append(link)

def get_product_info(link):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/10);")
    time.sleep(1)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/5);")
    time.sleep(2)
    product_info_list = []
    product_brand = driver.find_element(By.CLASS_NAME, "product-brand") 
    product_info_list.append(product_brand.text)
    product_name = driver.find_element(By.CLASS_NAME, "product-name")
    product_info_list.append(product_name.text)
    product_quanity = driver.find_element(By.CLASS_NAME, "sellQuantity")
    product_info_list.append(product_quanity.text)
    try:
        product_score = driver.find_element(By.CLASS_NAME, "score")
        product_info_list.append(product_score.text)
    except Exception as e:
        print (f'{link} : error {e}') 
        product_info_list.append(None)

    product_reviews = driver.find_element(By.CLASS_NAME, "reviews")
    product_info_list.append(product_reviews.text)
    product_packing = driver.find_element(By.CLASS_NAME, "product-unit")
    product_info_list.append(product_packing.text)
    product_pricing = driver.find_element(By.XPATH, '//div[@class="product-price-group"]')  # Need to spread out the price 
    product_info_list.append(product_pricing.text)
    try:
        product_stock = driver.find_element(By.XPATH, '//div[@class = "product-label-group"]')
        product_info_list.append(product_stock.text)
    except Exception as e:
        print (f'{link} : {e}')
        product_info_list.append(None)
    product_orgion = driver.find_element(By.CLASS_NAME, "info-content")
    product_info_list.append(product_orgion.text)
    try:
        product_offers = driver.find_element(By.CLASS_NAME, "other-offers-group")
        all_offers_list = product_offers.text.split('\n')
        max_offer_line = len(all_offers_list)
        for line_number in range(0, max_offer_line, 2):
            if  line_number > 0:                                               # only taking the prime number line as the header of the discount is in line 1 ,3 ,5 .....
                product_info_list.append(all_offers_list[line_number - 1])
    except Exception as e:
        print (f'{link} : error {e}') 
        product_info_list.append(None)
        
    product_category = driver.find_elements(By.TAG_NAME, "e2-breadcrumb")  # Need to sort for the actual category by the list
    for i in product_category:
        product_info_list.append(i.text)
        
    total_product_info_list.append(product_info_list)    
    
def scrape_products(link):
    driver.get(link)
    time.sleep(2)


def convert_quantity_unit(unit):
    if isinstance(unit, str):
        if 'K' in unit:
            return int(float(unit.replace('K', '').replace('+', '')) * 1000)
        elif 'M' in unit:
            return int(float(unit.replace('M', '').replace('+', '')) * 1000000)
        elif '+' in unit:
            return int(float(unit.replace('+', '')))
        elif unit == '':
            return 0
        elif unit.strip() == '':
            return 0
        elif unit.lower() == 'n/a':
            return 0
        else:
            return int(unit)
    else:
        return unit

def format_volume(product_packing):
    match = re.match(r"(\d+(\.\d+)?)(L|ML)(x(\d+))?", product_packing, re.IGNORECASE)
    if match:
        size, unit, multiplier = match.group(1), match.group(3).upper(), match.group(5)
        size = float(size) * (1000 if unit == "L" else 1)  
        count = int(multiplier) if multiplier else 1
        formatted_volume = f"{count}x{int(size)}ML"
        return formatted_volume
    else:
        return product_packing

def data_cleaning_country_for_df(country):
    if country == "UK":
        country = ("英國")
    elif country in ['中國 - 廣東', '西藏, 中國', "中國內地", "中國 (香港調配)", "中國<br/>(香港調配)<br/>", "原產地: 中國<BR>台灣包裝"]:
        country = "中國"
    elif country == "新西蘭<BR>":
        country = "新西蘭"
    elif country == "斯里蘭卡<BR>":
        country = "斯里蘭卡"
    elif country == "馬來西亞︰清涼爽, 菊花茶, 甘蔗水<br/><br/>中國︰馬蹄爽":
        country = "馬來西亞, 中國"
    elif country in ['送貨上門\n網購店取', '送貨上門\n不適用於離島地區', '網購店取', '其他', '商戶直送']:
        country = None
    elif country == 'Japan':
        country = '日本'
    elif country == 'Vietnam':
        country = '越南'
    elif country == '<BR>西班牙':
        country  = '西班牙'
    else:
        pass
    return country

def convert_stock_status(status):
    if status == '有貨':
        status = True
    elif status == '少量存貨':
        status = True
    else:
        status = False
    return status

# main web scraping script
get_product_link(filtered_category_links)
for link in product_link:
    scrape_products(link)
    get_product_info(link)


# after getting the product info, process to clean up the data
# standardize all to 13 columns
for product_info_list in total_product_info_list:
    if len(product_info_list) == 11:
        product_info_list.insert(9, None)
        product_info_list.insert(9, None)
    elif len(product_info_list) == 12:
        product_info_list.insert(11, None)
    elif len(product_info_list) == 13:
        pass
    elif len(product_info_list) > 13:
        product_info_list = product_info_list[0:12] + [product_info_list[-1]]
        
# data cleaning for discount price and normal price 
for product_info_list in total_product_info_list:
    if product_info_list[6].startswith('優惠價:\n'):
        product_info_list[6] = product_info_list[6].replace('優惠價:\n', '')
    else:
        pass
    if product_info_list[6].count('$') == 1:
        product_info_list[6] = float(product_info_list[6].replace('$', ''))
        product_info_list.insert( 7 , None)
    elif product_info_list[6].count('$') == 2:
        splited_price_list = product_info_list[6].split()
        product_info_list[6] = float (splited_price_list[0].replace('$', ''))
        product_info_list.insert( 7 , float (splited_price_list[1].replace('$', '')))

# cleaning the sell quanity, second cleaning comment numbers, third cleaning the category, forth cleaning for the packing
for product_info_list in total_product_info_list:
    product_info_list[2] = product_info_list[2].replace('已售 ', '')
    product_info_list[2] = convert_quantity_unit(product_info_list[2])
    sales_count_pattern = r'(\d+)' 
    found_result = re.findall(sales_count_pattern, product_info_list[4])
    if len(found_result) == 1:
        product_info_list[4] = found_result[0]
    else:
        product_info_list[4] = 0
    product_info_list[5] = format_volume(product_info_list[5])
    product_info_list[-1] = product_info_list[-1].split('\n') 
    for scraped_line in product_info_list[-1]:
       for category in category_list:
         if scraped_line == category:
             product_info_list[-1] = category

product_data = []
for product_info in total_product_info_list:
    product_data.append({
        'brand_name': product_info[0],
        'product_name': product_info[1],
        'quantity': product_info[2],
        'rating': product_info[3],
        'no_of_reviews': product_info[4],
        'packing': product_info[5],
        'current_price': product_info[6],
        'unit_price': product_info[7],
        'stock_status': product_info[8],
        'country': product_info[9],
        'promotion1': product_info[10],
        'promotion2': product_info[11],
        'promotion3': product_info[12],
        'category': product_info[13]
    })

pns_df = pd.DataFrame(product_data)

# data cleaning process inside the dataframe
pns_df['country'] = pns_df['country'].apply(data_cleaning_country_for_df)
pns_df['rating'] = pns_df['rating'].astype(float)
pns_df['no_of_reviews'] = pns_df['no_of_reviews'].astype(int)
duplicate_products = pns_df.duplicated(subset=['product_name'], keep=False)
pns_df.loc[duplicate_products, 'product_name'] = pns_df['brand_name'] + '' + pns_df['packing'] + '' +pns_df['product_name']
pns_df.drop_duplicates(subset=['product_name'], keep='first', inplace=True)
pns_df['stock_status'] = pns_df['stock_status'].apply(convert_stock_status)
today_date = date.today().strftime('%Y-%m-%d')
pns_df['date'] =  pd.to_datetime(today_date)
pns_df.to_csv('pns_df{today_date}.csv', index=False)

# start loading data into database
today = date.today().strftime('%Y-%m-%d')
today = pd.to_datetime(today)
conn, cur = create_connection()

try:
    query = "INSERT INTO dates (scrap_date) VALUES (%s) ON CONFLICT (scrap_date) DO NOTHING;"
    cur.execute(query, (today,))
    conn.commit()
    print("Date successfully inserted into the database.")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    conn.close()
    cur.close()

brand_name = pns_df['brand_name'].tolist() 
product_name = pns_df['product_name'].tolist() 
quanity = pns_df['quantity'].tolist()  
rating = pns_df['rating'].tolist() 
no_of_reviews = pns_df['no_of_reviews'].tolist() 
packing = pns_df['packing'].tolist() 
current_price = pns_df['current_price'].tolist()        
unit_price =  pns_df['unit_price'].tolist() 
stock_status = pns_df['stock_status'].tolist() 
country = pns_df['country'].tolist()
promo1 = pns_df['promotion1'].tolist() 
promo2 = pns_df['promotion2'].tolist() 
promo3 = pns_df['promotion3'].tolist() 
category = pns_df['category'].tolist()
scrap_date = pns_df['date'].tolist() 

conn, cur = create_connection()
product_pns_dict_list = []
for a, b, c, d, e in zip(brand_name, product_name, category, packing, country):
    product = {'brand_name': a, 'product_name': b, 'category': c, 'packing': d, 'country': e}
    product_pns_dict_list.append(product)

product_query = """INSERT INTO products_pns (brand_name, product_name, category, packing, country)
VALUES (%(brand_name)s, %(product_name)s, %(category)s, %(packing)s, %(country)s) ON CONFLICT DO NOTHING """

cur.executemany(product_query, product_pns_dict_list) 

fact_pns_dict_list = []
for a, b, c, d, e, f, g, h, i, j, k, l in zip(brand_name, product_name, quanity, rating, no_of_reviews, current_price, unit_price, stock_status, promo1, promo2, promo3, scrap_date):
    product = {'brand_name': a, 'product_name': b, 'quantity': c, 'rating': d, 'no_of_reviews': e, 'current_price': f, 'unit_price': g, 'stock_status': h, 'promotion1': i, 'promotion2': j, 'promotion3': k, 'scrap_date': l}
    fact_pns_dict_list.append(product)

fact_query = """
    INSERT INTO fact_pns (brand_name, product_name, quantity, rating, no_of_reviews, current_price, unit_price, stock_status, promotion1, promotion2, promotion3, scrap_date)
    VALUES (%(brand_name)s, %(product_name)s, %(quantity)s, %(rating)s, %(no_of_reviews)s, %(current_price)s, %(unit_price)s, %(stock_status)s, %(promotion1)s, %(promotion2)s, %(promotion3)s, %(scrap_date)s)
    ON CONFLICT DO NOTHING
"""

cur.executemany(fact_query, fact_pns_dict_list)


conn.commit()
cur.close()
conn.close()


