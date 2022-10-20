import base64
import random
import ssl
import time
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from WRTools import UserAgentHelper, LogHelper, ExcelHelp, WaitHelp, EmailHelper, PathHelp

ssl._create_default_https_context = ssl._create_unverified_context

driver_option = webdriver.ChromeOptions()
# 青果proxy
proxyAddr = "http://tunnel5.qg.net:18716"
driver_option.add_argument('--proxy-server=%(server)s' % {"server": proxyAddr})
# driver_option.add_argument("–incognito")  #隐身模式
# 等待初始HTML文档完全加载和解析，
# driver_option.page_load_strategy = 'eager'
driver = uc.Chrome(use_subprocess=True, options=driver_option)
# logic
default_url = 'https://octopart.com/'

keyword_source_file = PathHelp.get_file_path(super_path=None, file_name='TKeywords.xlsx')
log_file = PathHelp.get_file_path(super_path='Octopart_category', file_name='octopart_key_cate_log.txt')

totol_page = 1
current_page = 1
# 出现安全验证的次数，连续三次则关闭webdriver
security_times = 0


def get_url(key_name, page, alpha, manu_ids) -> str:
    manu_param = '&manufacturer_id=' + manu_ids.replace(';', '&manufacturer_id=')
    page_param = '' if page == 1 else '&start=' + str(page*10 - 10)
    url = f'https://octopart.com/search?q={key_name}{alpha}&currency=USD&specs=0{manu_param}{page_param}'
    return url


# 验证是否处于验证IP 页面
def is_security_check(driver) -> bool:
    global security_times
    result = False
    try:
        alert = driver.find_element(by=By.CSS_SELECTOR, value='div.inner.narrow')
        if alert and len(alert) > 0:
            result = True
            security_times += 1
            EmailHelper.mail_ip_error("mac")
            # QGHelp.maintainWhiteList()  #todo remove qg
            time.sleep(60)
    except:
        result = False
        security_times = 0
    if security_times > 3:
        driver.close()
    return result


# 获取总页数
def set_totalpage(driver):
    global totol_page
    try:
        ul = driver.find_element(by=By.CSS_SELECTOR, value='ul.jsx-4126298714.jumps')
        li_last = ul.find_elements(by=By.CSS_SELECTOR, value='li.jsx-4126298714')[-1]
        a = li_last.find_element(by=By.CSS_SELECTOR, value='a')
        totol_page = int(a.text)
    except:
        totol_page = 1


# 确定根据key 是否有匹配的结果，避开建议性的结果
def has_content(driver) -> bool:
    result = True
    try:
        no_result = driver.find_elements(by=By.CSS_SELECTOR, value='div.jsx-1140710980.no-results-found')
        if no_result and len(no_result) > 0:
            result = False
    except:
        result = True
    return result


# 跳转到下一个指定的型号,alpha, page , 的那一页
def go_to_cate(key_and_alpha, url):
    try:
        if driver.current_url.startswith('https://octopart.com/search?q='):
            if driver.current_url == url:
                return
            driver.get(url)
        else:
            driver.get(url)
    except Exception as e:
        LogHelper.write_log(log_file_name=log_file, content=f'{key_and_alpha} go_to_cate except: {e}')

'''
def go_next_page(key_name, alpha):
    global current_page
    if not check_valid_key(key_name):
        current_page = totol_page
        return
    try:
        next_button = driver.find_element(by=By.CSS_SELECTOR, value='a.jsx-1876408219.next')
        next_button.click()
    except Exception as e:
        LogHelper.write_log(log_file_name=log_file, content=f'{key_name+alpha} go_to_cate except: {e}')
    current_page += 1
'''


#     判断key是否有必要查询
# def check_valid_key(key_name):
#     return key_name != last_unvalid_key


def get_category(key_index, key_name, manu_ids, alpha):
    global current_page, totol_page
    current_page = 1
    totol_page = 1
    while current_page <= totol_page:
        print(f'key_index is: {key_index} key_name is: {key_name} alpha is: {alpha} page is: {current_page} totalpage is : {totol_page}')
        try:
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": f"{UserAgentHelper.getRandowUA_windows()}",
                "platform": "Windows"})
            go_to_cate(key_and_alpha=key_name+alpha, url=get_url(key_name=key_name, manu_ids=manu_ids, alpha=alpha, page=current_page))
            if current_page > 1 and current_page%15 == 0:
                time.sleep(500)
            else:
                WaitHelp.waitfor_octopart(is_load_page=True, isDebug=False)
        except Exception as e:
            current_page += 1
            LogHelper.write_log(log_file, f'{key_name} request get exception: {e}')
            return
        if is_security_check(driver):
            current_page += 1
            LogHelper.write_log(log_file_name=log_file, content=f'{key_name} ip security check')
            break
        if not has_content(driver=driver):
            current_page += 1
            break
        set_totalpage(driver)
        analyth_html(key_name=key_name, alpha=alpha)
        time.sleep(2)
        current_page += 1


# 解析html，获取cate，manu
def analyth_html(key_name, alpha):
    try:
        table = driver.find_element(by=By.CSS_SELECTOR, value='div.jsx-2172888034.prices-view')
        cate_first = table.find_elements(by=By.CSS_SELECTOR, value='div.jsx-2172888034')
        cate_left = table.find_elements(by=By.CSS_SELECTOR, value='div.jsx-2400378105.part')
        cates_all = cate_first + cate_left
        info_list = []
        for temp_cate in cates_all:
            header = temp_cate.find_element(by=By.CSS_SELECTOR, value='div.jsx-3355510592.header')
            try:
                manu = header.find_element(by=By.CSS_SELECTOR, value='div.jsx-312275976.jsx-2649123136.manufacturer-name-and-possible-tooltip').text
            except:
                manu = None
            try:
                cate_name = header.find_element(by=By.CSS_SELECTOR, value='div.jsx-312275976.jsx-2649123136.mpn').text
            except:
                cate_name = None
            if cate_name and manu:
                if cate_name.startswith(key_name):
                    info_list.append([cate_name, manu, key_name+alpha, current_page])
        if len(info_list) > 0:
            ExcelHelp.add_arr_to_sheet(file_name=f'{key_name}.xlsx', sheet_name='all', dim_arr=info_list)
    except Exception as e:
        LogHelper.write_log(log_file, f'{key_name+alpha} analyth_html exception: {e}')


def main():
    add_alphabet_list = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U',
                'V', 'W', 'X', 'Y', 'Z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    key_list = ExcelHelp.read_col_content(file_name=keyword_source_file, sheet_name='all', col_index=1)
    manuid_list = ExcelHelp.read_col_content(file_name=keyword_source_file, sheet_name='all', col_index=3)
    for (key_index, key_name) in enumerate(key_list):
        if key_index%6 == 0 or key_index%6 == 1:
            for alpha in add_alphabet_list:
                get_category(key_index=key_index, key_name="TPS1", manu_ids = "370" , alpha="")
                # get_category(key_index=key_index, key_name=key_name, manu_ids = str(manuid_list[key_index]) , alpha=alpha)


def getURL():
    add_alphabet_list = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S',
                         'T', 'U',
                         'V', 'W', 'X', 'Y', 'Z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    key_list = ExcelHelp.read_col_content(file_name=keyword_source_file, sheet_name='all', col_index=1)
    manuid_list = ExcelHelp.read_col_content(file_name=keyword_source_file, sheet_name='all', col_index=3)
    url_list = []
    for (key_index, key_name) in enumerate(key_list):
        if key_index % 6 > 1:
            for alpha in add_alphabet_list:
                url = get_url(key_name=key_name, page=current_page, alpha=alpha, manu_ids=str(manuid_list[key_index]))
                url_list.append([url])
                # get_category(key_index=key_index, key_name=key_name, manu_ids = str(manuid_list[key_index]) , alpha=alpha)
    ExcelHelp.add_arr_to_sheet(file_name=keyword_source_file, sheet_name='urls2345', dim_arr=url_list)


if __name__ == "__main__":
    # UserAgentHelper.driver_update_UA(webdriver=driver)
    # driver.get(default_url)
    # WaitHelp.waitfor_octopart(True, False)
    # main()
    getURL()
