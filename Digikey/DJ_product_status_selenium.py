import base64
import random
import ssl
import time

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from WRTools import IPHelper, UserAgentHelper, LogHelper, PathHelp, ExcelHelp, WaitHelp, StringChange
from selenium.common.exceptions import TimeoutException
from Manager import TaskManager


ssl._create_default_https_context = ssl._create_unverified_context

driver = uc.Chrome(use_subprocess=True)
driver.set_page_load_timeout(360)
# logic


sourceFile_dic = {'fileName': PathHelp.get_file_path(None, 'TRuNeeds0918.xlsx'),
                  'sourceSheet': 'ppn',
                  'colIndex': 1,
                  'startIndex': 9,
                  'endIndex': 100}
result_save_file = PathHelp.get_file_path(None, 'TRuNeeds0918.xlsx')

# sourceFile_dic = {'fileName': PathHelp.get_file_path("TInfenion_80H", 'Task.xlsx'),
#                   'sourceSheet': 'ppn',
#                   'colIndex': 1,
#                   'startIndex': 393,
#                   'endIndex': 430} # 101 unfinished
# result_save_file = PathHelp.get_file_path("TInfenion_80H", 'digikey_status.xlsx')

default_url = 'https://www.digikey.com/'
log_file = PathHelp.get_file_path('Digikey', 'DJ_product_status_log.txt')
timeout_ppn = None


# 收获地点选择美国
def select_usa():
    try:
        usa = driver.find_elements(By.CLASS_NAME, 'domain-suggest__domain')[1]
        usa.click()
    except:
        print('usa error')
    try:
        accept_button = driver.find_elements(By.CLASS_NAME, 'secondary.button')[0]
        accept_button.click()
    except:
        print('accept_button error')
    WaitHelp.waitfor(False, False)


# 跳转到下一个指定的型号
def go_to_cate(cate_index, cate_name):
    global timeout_ppn
    timeout_ppn = None
    try:
        header_area = driver.find_element(by=By.CLASS_NAME, value='header__search')
        input = header_area.find_element(by=By.TAG_NAME, value='input')
        input.clear()
        input.send_keys(cate_name)
        search_button = header_area.find_element(by=By.CLASS_NAME, value='search-button')
        search_button.click()
    except TimeoutException:
        timeout_ppn = cate_name
    except Exception as e:
        LogHelper.write_log(log_file_name=log_file, content=f'go_to_cate {cate_name} exception is: {e}')


# 解析某个型号的页面信息，先看未折叠的前三行，判断是否需要展开，展开，解析，再判断，再展开，再解析。。。。
def analy_html(cate_index, cate_name):
    # 判断是否需要点击详情
    #document.getElementsByClassName('tss-1abf7dr-Link-anchor-buttonAnchor')
    if driver.current_url.__contains__('/products/detail'):
        getElement(cate_name)
    else:
        try:
            detail_links = driver.find_elements(By.CSS_SELECTOR, 'a.tss-1abf7dr-Link-anchor-buttonAnchor')
            if detail_links.__len__() > 2:
                detail_links = detail_links[0:2]
            if detail_links.__len__() > 0:
                print(f'{cate_name} go to details count {detail_links.__len__()}')
                for temp_link in detail_links:
                    temp_link.click()
                    WaitHelp.waitfor_account_import(True, False)
                    getElement(cate_name)
            else:
                print('没有建议 一个 ppn')
        except:
            print('直接展示')


def getElement(keyword):
    ppn_area = driver.find_element(By.TAG_NAME, 'h1')
    ppn = ppn_area.text
    try:
        des_table = driver.find_element(By.TAG_NAME, 'table')
        des_tbody = des_table.find_element(By.TAG_NAME, 'tbody')
        des_tr = des_tbody.find_elements(By.TAG_NAME, 'tr')[3]
        des_title = des_tr.find_elements(By.TAG_NAME, 'td')[0].text
        if des_title == 'Description':
            des_td = des_tr.find_elements(By.TAG_NAME, 'td')[1]
            des_content = des_td.text
        else:
            des_content = '//'
    except:
        des_content = '//'
    # product status
    # try:
    #     sta_table = driver.find_element(By.ID, 'product-attributes')
    #     sta_tbody = sta_table.find_elements(By.TAG_NAME, 'tbody')[0]
    #     sta_tr = sta_tbody.find_elements(By.TAG_NAME, 'tr')[4]
    #
    #     status_title = sta_tr.find_elements(By.TAG_NAME, 'td')[0].text
    #     if status_title == 'Product Status':
    #         sta_td = sta_tr.find_elements(By.TAG_NAME, 'td')[1]
    #         status_content = sta_td.text
    #     else:
    #         status_content = '//'
    # except:
    #     status_content = '//'
    try:
        sta_table = driver.find_element(By.ID, 'product-attributes')
        sta_tbody = sta_table.find_elements(By.TAG_NAME, 'tbody')[0]
        sta_tr = sta_tbody.find_elements(By.TAG_NAME, 'tr')[-2]

        status_title = sta_tr.find_elements(By.TAG_NAME, 'td')[0].text
        if status_title == 'Supplier Device Package' or status_title == '供应商器件封装':
            sta_td = sta_tr.find_elements(By.TAG_NAME, 'td')[1]
            suppplier_package = sta_td.text
        else:
            suppplier_package = '//'
    except:
        suppplier_package = '//'
    result = [ppn, des_content, suppplier_package,keyword, time.strftime('%Y-%m-%d', time.localtime())]
    print('begin write data ')
    ExcelHelp.add_arr_to_sheet(
        file_name=result_save_file,
        sheet_name='digikey_status',
        dim_arr=[result])
    print('end write data ')


def main():
    # 4,6
    # https://www.digikey.com/en/products/filter/power-management-pmic/voltage-reference/693?s=N4IgTCBcDaIIIBECMBWAHGOAlAKgLRAF0BfIA
    all_cates = ExcelHelp.read_col_content(file_name=sourceFile_dic['fileName'],
                                           sheet_name=sourceFile_dic['sourceSheet'],
                                           col_index=sourceFile_dic['colIndex'])
    for (cate_index, cate_name) in enumerate(all_cates):
        if cate_name is None or cate_name.__contains__('?'):
            continue
        elif cate_index in range(sourceFile_dic['startIndex'], sourceFile_dic['endIndex']):
            print(f'cate_index is: {cate_index}  cate_name is: {cate_name}')
            go_to_cate(cate_index, str(cate_name))
            if cate_index > 0 and cate_index % 15 == 0:
                time.sleep(480)
            else:
                WaitHelp.waitfor_account_import(True, False)
            analy_html(cate_index, str(cate_name))


# 供应商器件封装
if __name__ == "__main__":
    driver.get(default_url)
    select_usa()
    main()

