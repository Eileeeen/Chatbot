import requests
from selenium import webdriver
from lxml import etree
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.support import expected_conditions as EC
import os
from selenium.webdriver.support.ui import WebDriverWait
import openpyxl
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

chrome_options = Options()
# 无窗口模式
# chrome_options.add_argument('--headless')
# 禁止硬件加速，避免严重占用cpu
# chrome_options.add_argument('--disable-gpu')
# 关闭安全策略
chrome_options.add_argument("disable-web-security")
# 禁止图片加载
# chrome_options.add_experimental_option('prefs', {'profile.managed_default_content_settings.images': 2,'permissions.default.stylesheet':2})
#
# 隐藏"Chrome正在受到自动软件的控制
chrome_options.add_argument('disable-infobars')
# 设置开发者模式启动，该模式下webdriver属性为正常值
chrome_options.add_experimental_option(
    'excludeSwitches', ['enable-automation'])
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
}
bro = webdriver.Chrome(options=chrome_options)
bro.implicitly_wait(10)


def get_url():
    url_list = []
    page_text = requests.get(
        url='https://www.saatva.com/mattresses', headers=headers).text
    tree = etree.HTML(page_text)
    div_list = tree.xpath(
        '//*[@id="app"]/div[1]/div[1]/main/section[1]/div[2]/div[2]/div')
    for i in div_list:
        url = i.xpath('./div/a/@href')[0]
        url = 'https://www.saatva.com'+url
        url_list.append(url)
    return url_list


def get_data(url):
    info = ''
    bro.get(url)
    time.sleep(2)
    page_text = bro.page_source
    tree = etree.HTML(page_text)
    title = tree.xpath(
        '//*[@id="productPanel"]/div/div/div[2]/div[1]/header/div/div[1]/h1/text()')
    info = ''.join(title)
    select_size = tree.xpath(
        '//*[@id="productPanelContent"]/div/div[1]/div/div[2]/div[1]/div')
    if len(select_size) == 0:
        select_size = tree.xpath(
            '//*[@id="productPanelContent"]/div/div[1]/div/div')
        if len(select_size) == 0:
            select_size = [0]
    for i in range(0, 5):
        ActionChains(bro).move_by_offset(0, 0).click().perform()  # 鼠标左键点击
        time.sleep(1)
    for i in range(1, len(select_size)+1):
        try:
            select = bro.find_element(
                By.XPATH, '//*[@id="productPanelContent"]/div/div[1]/div/div[2]/div[1]/div['+str(i)+']')
        except:
            select = bro.find_element(
                By.XPATH, '//*[@id="productPanelContent"]/div/div[1]/div/div['+str(i)+']/label/div')
        select.click()
        time.sleep(1)
        page = bro.page_source
        tree_detail = etree.HTML(page)
        size = tree_detail.xpath(
            '//*[@id="productPanelContent"]/div/div[1]/div/div[2]/div/div['+str(i)+']/label/div/text()')
        size = ''.join(size)
        if size == '':
            size = tree_detail.xpath(
                '//*[@id="productPanelContent"]/div/div[1]/div/div['+str(i)+']/label/div/text()')
            size = ''.join(size)
        price_size = tree_detail.xpath(
            '//*[@id="productPanel"]/div/div/div[2]/div[2]/div/span')
        if (len(price_size) == 1):
            price = tree_detail.xpath(
                '/html/body/div[2]/div[1]/div[1]/main/section/div/div/div[2]/div[2]/div/span[1]//text()')
        else:
            price = tree_detail.xpath(
                '/html/body/div[2]/div[1]/div[1]/main/section/div/div/div[2]/div[2]/div/span[2]//text()')
        price = ''.join(price)
        info = '\n'.join([info, 'price', size, price])
        # print([title, size, price])
    return info
