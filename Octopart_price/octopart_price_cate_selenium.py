import base64
import ssl
import sys

import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from WRTools import ExcelHelp, LogHelper, PathHelp, WaitHelp
import octopart_price_info
from Manager import TaskManager, URLManager
import re

ssl._create_default_https_context = ssl._create_unverified_context

driver_option = webdriver.ChromeOptions()
driver = uc.Chrome(use_subprocess=True)
driver.set_page_load_timeout(480)
# logic
# https://octopart.com/search?q=8P34S1204NLGI8&currency=USD&specs=0
default_url = 'https://octopart.com/what-is-octopart'

sourceFile_dic = {'fileName': PathHelp.get_file_path(TaskManager.Taskmanger().task_name, 'Task.xlsx'),
                  'sourceSheet': 'ppn',
                  'colIndex': 1,
                  'startIndex': TaskManager.Taskmanger().start_index,
                  'endIndex': TaskManager.Taskmanger().end_index}
result_save_file = PathHelp.get_file_path(TaskManager.Taskmanger().task_name, 'octopart_price.xlsx')

log_file = PathHelp.get_file_path('Octopart_price', 'ocopar_price_log.txt')


# 跳转到下一个指定的型号
def go_to_cate(pn_index, pn):
    try:
        url = URLManager.octopart_get_page_url(pn, 1, URLManager.Octopart_manu.NoManu)
        url.replace(' ', '')
        driver.get(url)
    except Exception as e:
        LogHelper.write_log(log_file_name=log_file, content=f'{pn} go_to_cate except: {e}')
        if str(e.msg).__contains__('Timed out'):
            driver.reconnect()
            sys.exit()


# 获取cate
def get_cate_name(cate_area, opn) -> str:
    cate_name = ''
    try:
        cate_name = cate_area.find_element(By.CSS_SELECTOR, 'div.jsx-312275976.jsx-1485186546.mpn').text
        # cate_name = cate_area.find_element(By.TAG_NAME, 'mark').text
    except Exception as e:
        LogHelper.write_log(log_file_name=log_file, content=f'{opn} cannot check keyname: {e}')
    return cate_name


# 获取manu
def get_manufacture_name(cate_area, opn) -> str:
    manu_name = ''
    try:
        header = cate_area.find_element(By.CSS_SELECTOR, 'div.jsx-2471764431.header')
        manu_name = header.find_elements(By.CSS_SELECTOR, 'div.jsx-312275976.jsx-1485186546.manufacturer-name-and-possible-tooltip')[0].text
    except Exception as e:
        LogHelper.write_log(log_file_name=log_file, content=f'{opn} cannot check manufacture: {e}')
    return manu_name


# 将页面tr的内容 转化成octopart_price_info
# tr: contain row info
def get_supplier_info(tr, ppn, manu_name) -> octopart_price_info:
    td_arr = tr.find_elements(by=By.TAG_NAME, value='td')
    is_star = 1
    distribute_tr = td_arr[1]
    try:
        distribute_name = distribute_tr.find_element(by=By.TAG_NAME, value='a').text
    except:
        distribute_name = '--'
    SKU_tr = td_arr[2]
    try:
        sku = SKU_tr.text
    except:
        sku = "--"
    stock_tr = td_arr[3]
    try:
        stock = stock_tr.text
    except:
        stock = '--'
    MOQ_tr = td_arr[4]
    try:
        moq = MOQ_tr.text
    except:
        moq = '--'
    currency_type_tr = td_arr[6]
    try:
        currency_type = currency_type_tr.text
    except:
        currency_type = '--'
    k_price_tr = td_arr[10]
    try:
        k_price = k_price_tr.text
    except:
        k_price = '--'
    try:
        updated_div = tr.find_element(by=By.CSS_SELECTOR, value='div.updated-tooltip')
        updated_span = updated_div.find_element(By.TAG_NAME, 'span')
        updated = updated_span.text
    except:
        updated = '--'
    manu_name = manu_name
    octopart_price_ele = octopart_price_info.Octopart_price_info(cate=ppn, manu=manu_name, is_star=is_star,
                                                                 distribute=distribute_name, SKU=sku, stock=stock,
                                                                 MOQ=moq, currency_type=currency_type, k_price=k_price,
                                                                 updated=updated)
    return octopart_price_ele


# 展开这个cate的更多distribute info
def click_more_row(row, ppn):
    try:
        button = row.find_element(By.CSS_SELECTOR, 'button.jsx-1990075996.show-button')
        button.click()
        WaitHelp.waitfor_octopart(False, False)
    except Exception as e:
        LogHelper.write_log(log_file_name=log_file, content=f'{ppn} click more exception: ')


#  请求频繁，导致出现弹框，有则关闭，无则异常
def close_alert():
    try:
        close_button = driver.find_element(by=By.CLASS_NAME, value='jsx-535551409.close-button')
        close_button.click()
    except Exception as e:
        return


# 解析某个型号的页面信息，如果有更多，直接点击，然后只选择start ， 遇到第一个不是star 的就返回
def analy_html(pn_index, pn):
    valid_supplier_arr = []
    try:
        all_cates_table = driver.find_elements(By.CSS_SELECTOR, 'div.jsx-2906236790.prices-view')
        if all_cates_table.__len__() > 0:
            left_rows = all_cates_table[0].find_elements(By.CSS_SELECTOR, 'div.jsx-4014881838.part')
            showed_rows = left_rows
        # 默认直接显示的row
        for temp_cate_row in showed_rows:
            try:
                ppn = get_cate_name(cate_area=temp_cate_row, opn=pn)
                manu = get_manufacture_name(cate_area=temp_cate_row, opn=pn)
                tables = temp_cate_row.find_elements(By.CSS_SELECTOR, 'table')
                for temp_table in tables:
                    first_th_text = temp_table.find_elements(By.TAG_NAME, 'th')[1].text
                    if first_th_text == 'Authorized Distributors':
                        tbody = temp_table.find_element(By.TAG_NAME, 'tbody')
                        tr_list = tbody.find_elements(By.TAG_NAME, 'tr')
                        for tr_temp in tr_list:
                            cate_price_ele = get_supplier_info(tr=tr_temp, ppn=ppn, manu_name=manu)
                            valid_supplier_arr.append(cate_price_ele.descritpion_arr() + [pn])
            except Exception as e:
                LogHelper.write_log(log_file_name=log_file, content=f'{pn} 当个cate 解析异常：{e} ')
    except Exception as e:
        LogHelper.write_log(log_file_name=log_file, content=f'{pn} 页面 解析异常：{e} ')
    ExcelHelp.add_arr_to_sheet(
        file_name=result_save_file,
        sheet_name='octopart_price',
        dim_arr=valid_supplier_arr)
    valid_supplier_arr.clear()


def main():
    all_cates = ExcelHelp.read_col_content(file_name=sourceFile_dic['fileName'],
                                           sheet_name=sourceFile_dic['sourceSheet'],
                                           col_index=sourceFile_dic['colIndex'])
    for (pn_index, pn) in enumerate(all_cates):
        if pn is None or pn.__contains__('?'):
            continue
        elif pn_index in range(sourceFile_dic['startIndex'], sourceFile_dic['endIndex']):
            print(f'pn_index is: {pn_index}  pn is: {pn}')
            go_to_cate(pn_index, pn)
            WaitHelp.waitfor_octopart(True,False)
            close_alert()
            analy_html(pn_index, pn)


if __name__ == "__main__":
    driver.get(default_url)
    WaitHelp.waitfor_octopart(False, False)
    main()
