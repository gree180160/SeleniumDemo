# 根据buyer 获取record


import datetime
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from WRTools import ChromeDriverManager
import ssl
from Manager import AccManage
from WRTools import ExcelHelp, WaitHelp, PathHelp, LogHelper, MySqlHelp_recommanded
import time


accouts_arr = [AccManage.Wheat['c'], AccManage.Wheat['n'], AccManage.Wheat['p']]
ssl._create_default_https_context = ssl._create_unverified_context

sourceFile_dic = {'fileName': PathHelp.get_file_path(None, 'TICHot_202401.xlsx'),
                  'sourceSheet': 'buyer',
                  'colIndex': 1,
                  'startIndex': 134, # page5， buyer_index is:
                  'endIndex': 143}

result_save_file = PathHelp.get_file_path(None, 'TICHot_202401.xlsx')
result_save_sheet = 'Wheat_buyer'
logFile = PathHelp.get_file_path('Wheat', 'Wheat_log.txt')

login_url = 'https://app.51wheatsearch.com/gs/index.html#/login'
default_url = 'https://app.51wheatsearch.com/gs/index.html#/resource/gather/customs'
total_page = 1
current_page = 1 #infenion 305

driver_option = webdriver.ChromeOptions()
driver_option.add_argument("–incognito")
#  等待初始HTML文档完全加载和解析，
driver_option.page_load_strategy = 'eager'
prefs = {"profile.managed_default_content_settings.images": 2}
driver_option.add_experimental_option('prefs', prefs)
driver = ChromeDriverManager.getWebDriver(1)
driver.set_page_load_timeout(1000)


# 登陆
def loginAction(aim_url):
    driver.get(aim_url)
    time.sleep(5.0)
    login_types = driver.find_elements(By.CSS_SELECTOR, 'div.ant-tabs-tab')
    if login_types.__len__() > 0:
        time.sleep(10.0)
        sub_long = login_types[1]
        sub_long.click()
        time.sleep(3.0)
        company_name = driver.find_element(By.CSS_SELECTOR, '#mobileOrName')
        company_name.clear()
        company_name.send_keys(accouts_arr[0])
        use_name = driver.find_element(By.CSS_SELECTOR, '#emailOrMobile')
        use_name.clear()
        use_name.send_keys(accouts_arr[1])
        pw = driver.find_element(By.CSS_SELECTOR, '#password')
        pw.clear()
        pw.send_keys(accouts_arr[2])
        time.sleep(3.0)
        login_button = driver.find_elements(By.TAG_NAME, 'button')[-1]
        login_button.click()
        WaitHelp.waitfor(True, False)
    else:
        print('login error')
        sys.exit()


def set_filter(start_date:str, end_date:str):
    driver.get(default_url)
    WaitHelp.waitfor(True, False)
    #submit form
    card_one = driver.find_elements(By.CSS_SELECTOR, 'div.ant-card-body')[0]
    sub_form = card_one.find_elements(By.CSS_SELECTOR, 'div.ant-space-item')[2]
    sub_form.click()
    WaitHelp.waitfor(False, False)
    #set filters
    # contry
    select_contry = driver.find_elements(By.CSS_SELECTOR, 'span.anticon.anticon-down')[0]
    select_contry.click()
    time.sleep(3.0)
    alert_area = driver.find_elements(By.CSS_SELECTOR, 'div.ant-modal-body')[0]
    ru_button = alert_area.find_elements(By.XPATH, "//button[@title='俄罗斯']")[0]
    ru_button.click()
    # from date
    # clear default date
    ac = ActionChains(driver)
    pick_start = driver.find_elements(By.CSS_SELECTOR, 'span.ant-picker-suffix')[0]
    ac.move_to_element(pick_start)
    ac.click(pick_start).perform()
    start_picker = driver.find_elements(By.CSS_SELECTOR, 'div.ant-picker')[0]
    start_input = start_picker.find_element(By.TAG_NAME, 'input')
    start_input.send_keys(start_date)
    # end date
    # clear default date
    pick_end = driver.find_elements(By.CSS_SELECTOR, 'span.ant-picker-suffix')[1]
    ac.move_to_element(pick_end)
    ac.click(pick_end).perform()
    end_picker = driver.find_elements(By.CSS_SELECTOR, 'div.ant-picker')[1]
    end_picker = end_picker.find_element(By.TAG_NAME, 'input')
    end_picker.send_keys(end_date)
    # 为了让结束日期有效，假装设置提单号，让日历选择器结束工作
    input_card_content(0, '')


# search one ppn
def goToBuyer(buyer: str):
    try:
        input_area_buyer = driver.find_elements(By.CSS_SELECTOR, value='input.ant-input')[5]
        input_area_buyer.clear()
        input_area_buyer.send_keys('')
        try:
            clear_button = driver.find_elements(By.CSS_SELECTOR, "span.ant-input-clear-icon")[5]
            clear_button.click()
            time.sleep(2.0)
        except Exception as e:
            print(f'can not click clear button 5')
        input_area_buyer = driver.find_elements(By.CSS_SELECTOR, value='input.ant-input')[5]
        input_area_buyer.clear()
        input_area_buyer.send_keys(buyer)
        search_button = driver.find_elements(By.CSS_SELECTOR, 'button.ant-btn.ant-btn-primary')[1]
        search_button.click()
    except:
        print('input buyer error')


# 在input 中delete old content ,input new content
# item: [提单号, 产品关键词, 产品关键词HS, 采购商名称, 供应商名称]
def input_card_content(item_index: int , new_content: str):
    try:
        filter_form_area = driver.find_element(By.CSS_SELECTOR, value='form.ant-form.ant-form-vertical')
        input_item = filter_form_area.find_elements(By.CSS_SELECTOR, value='input.ant-input')[item_index]
        old_keyword = input_item.get_attribute('value')
        if old_keyword and old_keyword.__len__() > 0:
            ac = ActionChains(driver)
            try:
                clear_button = filter_form_area.find_elements(By.CSS_SELECTOR, value='span.ant-input-clear-icon')[
                    item_index]
                svg = clear_button.find_element(By.TAG_NAME, 'svg')
                ac.move_to_element(svg)
                ac.click(svg).perform()
            except:
                print('can not click keyword clear button')
        input_item.send_keys(new_content)
    except Exception as e:
        LogHelper.write_log(logFile, f'set input content error item_index is: {item_index}, new content is :{new_content} {e}')


def get_page_info(for_current):
    global current_page, total_page
    if for_current:
        try:
            current = driver.find_element(By.CSS_SELECTOR, 'li.ant-pagination-item-active')
            current_page = int(current.text)
            print(f'current_page is: {current_page}')
        except:
            print('get current page error')
    else:
        try:
            page_container = driver.find_elements(By.TAG_NAME, 'ul')[3]
            page_elements = page_container.find_elements(By.TAG_NAME, 'li')
            if page_elements.__len__() == 3:
                total_page = 1
            else:
                total_page_li = page_elements[-3]
                total_page = int(total_page_li.text)
                total_page = min(10, total_page) #max page is 50
            print(f'total_page is: {total_page}')
        except Exception as e:
            total_page = 0
            LogHelper.write_log(logFile, f'get total page error {e}')


def set_page_count():
    try:
        page_area = driver.find_elements(By.CSS_SELECTOR, 'li.ant-pagination-options')
        if page_area.__len__() > 0:
            page_selection_items = page_area[0].find_elements(By.CSS_SELECTOR, 'span.ant-select-selection-item')
            if page_selection_items.__len__() > 0:
                page_selection_items[-1].click()
                time.sleep(2.0)
                select_options = driver.find_elements(By.CSS_SELECTOR, 'div.ant-select-item.ant-select-item-option')
                if select_options.__len__() > 0:
                    max_option = select_options[-1]
                    max_option.click()
                    WaitHelp.waitfor(True, False)
        else:
            print('no page selection')
    except Exception as e:
        LogHelper.write_log(logFile, f'set_page_count error {e}')


def go_to_next_page(buyer_index, buyer_name):
    now = datetime.datetime.now()
    h_value = (now.hour)
    if h_value >= 22 or h_value <= 8:
        return
    if current_page < total_page:
        try:
            next_page_li = driver.find_element(By.CSS_SELECTOR, 'li.ant-pagination-next')
            next_button = next_page_li.find_element(By.CSS_SELECTOR, 'button.ant-pagination-item-link')
            next_button.click()
            WaitHelp.waitfor_account_import(True, False)
            anly_webdriver(buyer_index, buyer_name)
        except Exception as e:
            LogHelper.write_log(f'click next page button error {e}')
            return


# 分析html 文件
def anly_webdriver(buyer_index, buyer_name):
    get_page_info(for_current=True)
    if total_page == 1:
        get_page_info(for_current=False)
    if total_page <= 0:
        return
    result = []
    try:
        table_container = driver.find_element(By.CSS_SELECTOR, 'div.ant-table.ant-table-ping-right.ant-table-fixed-column.ant-table-scroll-horizontal.ant-table-has-fix-right')
        table = table_container.find_element(By.TAG_NAME, 'table')
        tbody = table.find_element(By.CSS_SELECTOR, 'tbody.ant-table-tbody')
        row_list = tbody.find_elements(By.CSS_SELECTOR, 'tr.ant-table-row.ant-table-row-level-0')
        for row in row_list:
            row_info = get_rowInfo(buyer_name, row)
            result.append(row_info)
        if row_list.__len__() > 0:
            # ExcelHelp.add_arr_to_sheet(file_name=result_save_file, sheet_name=result_save_sheet, dim_arr=result)
            try:
                MySqlHelp_recommanded.DBRecommandChip().wheat_buyer_write(result)
            except:
                print('write db error')
            if current_page < total_page:
                go_to_next_page(buyer_index, buyer_name)
    except Exception as e:
        LogHelper.write_log(logFile, f'anly_webdriver error {e}')


def get_rowInfo(buyer_name, row):
    # old ['buyer_name', 'data', 'buyer', 'supplier', 'des', 'buy_contry', 'supplier_contry', record_time]
    #new  (keyword, wheat_date, buyer, supplier, HSCode, description, buy_country, supplier_country, productContry, weight, number, totalValue, current_page, task_name)
    td_list = row.find_elements(By.TAG_NAME, 'td')
    buyer = td_list[1].text.replace('/', '%2F')
    buyer = buyer.replace('\x1e', ' (tim)')
    task_name = "TICHot_202401"
    result = [buyer_name, td_list[0].text, buyer, td_list[2].text, td_list[3].text, td_list[4].text, "" , "",  td_list[5].text, td_list[6].text, td_list[7].text, td_list[8].text, str(current_page), task_name]
    return result


def main():
    global total_page, current_page
    all_cates = ExcelHelp.read_col_content(file_name=sourceFile_dic['fileName'],
                                           sheet_name=sourceFile_dic['sourceSheet'],
                                           col_index=sourceFile_dic['colIndex'])
    for (buyer_index, buyer_name) in enumerate(all_cates):
        now = datetime.datetime.now()
        h_value = now.hour
        if h_value >= 22 or h_value <= 8:
            continue
        if buyer_name is None or buyer_name.__contains__('?'):
            continue
        elif buyer_index in range(sourceFile_dic['startIndex'], sourceFile_dic['endIndex']):
            print(f'buyer_index is: {buyer_index}  buyer_name is: {buyer_name}')
            goToBuyer(buyer_name)
            WaitHelp.waitfor_account_import(True, False)
            set_page_count()
            current_page = total_page = 1
            anly_webdriver(buyer_index, buyer_name)


if __name__ == "__main__":
    loginAction(default_url)
    driver.get(default_url)
    set_filter(start_date='2023-03-18', end_date='2024-03-18')
    main()
