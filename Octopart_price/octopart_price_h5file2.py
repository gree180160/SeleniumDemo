# 根据关键字查找P/N, manu
from bs4 import BeautifulSoup
from WRTools import LogHelper, PathHelp, ExcelHelp
from urllib.parse import urlparse, parse_qs, parse_qsl
import os
import re
import base64
import octopart_price_info

result_save_file_arr = ['/Users/liuhe/Desktop/progress/TReneseas_all/Octopart_pageMore_price0.xlsx',
                        '/Users/liuhe/Desktop/progress/TReneseas_all/Octopart_pageMore_price1.xlsx',
                        '/Users/liuhe/Desktop/progress/TReneseas_all/Octopart_pageMore_price2.xlsx',
                        '/Users/liuhe/Desktop/progress/TReneseas_all/Octopart_pageMore_price3.xlsx']
log_file = '//Octopart_category/octopart_key_cate_log.txt'
html_file_path = '/Users/liuhe/Desktop/progress/TReneseas_all/pageMore_htmlFiles'


# 获取所有octopart 的html文件
def get_files():
    path = html_file_path
    file_name_list = os.listdir(path)
    result = []
    for temp in file_name_list:
        if temp.endswith('.htm') or temp.endswith('.html')  or temp.endswith('.mhtml'):
            result.append(temp)
    return result


# *********************************从html files 分析价格数据*****************************************************
# 根据html 文件，获取页面所有cate的price信息，并保存,每1k 的cate，保存在一个excel 中
def manu_get_price(file_name_index, file_name):
    path = f'{html_file_path}/{file_name}'
    htmlfile = open(path, 'r', encoding='utf-8')
    htmlhandle = htmlfile.read()
    soup = BeautifulSoup(htmlhandle, 'html5lib')
    manu_analy_html(soup=soup, htmlhandle=htmlhandle, fileName=file_name, file_name_index=file_name_index)


# 解析某个型号的页面信息，如果有更多，直接点击，然后只选择start ， 遇到第一个不是star 的就返回
def manu_analy_html(soup, htmlhandle, fileName, file_name_index):
    # 是否需要继续展开。 出现第一条非start数据后不再展开
    try:
        # all_cates = soup.select('div.jsx-922694994.results')[0]
        all_cates = soup.select('div.jsx-2172888034.prices-view')[0]
    except Exception as e:
        LogHelper.write_log(log_file_name=log_file, content=f'{fileName} all_cates exception:{e}')
        return
    # try:
    #     first_search_result = all_cates.select('div.jsx-2172888034')[0]
    # except:
    #     first_search_result = all_cates.select('div.jsx-2172888034.part')[0]
    other_search_result = all_cates.select('div.jsx-2400378105.part')
    all_row = other_search_result
    for temp_row in all_row:
        cate_name = manu_get_cate_name(one_row=temp_row, file_name=fileName)
        if '?' in cate_name:
            continue
        manu_name = manu_get_manufacture_name(one_row=temp_row, file_name=fileName)
        # 默认直接显示的row
        valid_supplier_arr = []
        tr_arr = []
        try:
            cate_table = temp_row.select('tbody')[0]
            tr_arr = cate_table.select('tr')
            for tr in tr_arr:
                cate_price_ele = manu_get_supplier_info(tr=tr, cate_name=cate_name, manu_name=manu_name)
                # 只有实心(1)数据才是有效的，只有空心(-1)才需要停止loop
                # 此处保留未授权的supplier 数据，为以后查找
                if cate_price_ele.is_valid_supplier() or True:
                    valid_supplier_arr.append(cate_price_ele.descritpion_arr())
                else:
                    print(f'supplier invalid: {cate_price_ele.description_str()}')
                    if cate_price_ele.stop_loop():
                        need_more = False
        except Exception as e:
            need_more = False
            LogHelper.write_log(log_file_name=log_file, content=f'{cate_name} 默认打开的内容解析异常：{e} ')
        sheet_name_base64str = str(base64.b64encode(cate_name.encode('utf-8')), 'utf-8')
        ExcelHelp.add_arr_to_sheet(
            file_name=result_save_file_arr[file_name_index % result_save_file_arr.__len__()],
            sheet_name=sheet_name_base64str,
            dim_arr=valid_supplier_arr)
        valid_supplier_arr.clear()


# 获取cate
def manu_get_cate_name(one_row, file_name) -> bool:
    html_cate_name = ''
    try:
        cate_div = one_row.select('div.jsx-312275976.jsx-2018853745.mpn')[0]
        html_cate_name = cate_div.text
    except Exception as e:
        LogHelper.write_log(log_file_name=log_file, content=f'{file_name} cannot check keyname: {e}')
    return html_cate_name


# 获取manu
def manu_get_manufacture_name(one_row, file_name) -> bool:
    html_manu_name = ''
    try:
        manu_name_value = one_row.select('div.jsx-312275976.jsx-2018853745.manufacturer-name-and-possible-tooltip')[0].text
        html_manu_name = manu_name_value
    except Exception as e:
        LogHelper.write_log(log_file_name=log_file, content=f'{file_name} cannot check manufacture: {e}')
    return html_manu_name


# 手动解析html files 将页面tr的内容 转化成octopart_price_info
# tr: contain row info
def manu_get_supplier_info(tr, cate_name, manu_name) -> octopart_price_info:
    td_arr = tr.select('td')
    star_td = td_arr[0]
    is_star = 0
    is_star = 0
    try:
        a = star_td.select('a')[0]
        title = a['title']
        if title == 'Non-Authorized Stocking Distributor':
            is_star = -1
        elif title == 'Authorized Distributor':
            is_star = 1
        else:
            is_star = 0
    except:
        is_star = -1
    distribute_tr = td_arr[1]
    try:
        distribute_name = distribute_tr.select('a')[0].text
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
    updated_tr = td_arr[12]
    try:
        updated_span = updated_tr.select('span')[0]
        updated = updated_span.text
    except:
        updated = '--'
    manu_name = manu_name
    octopart_price_ele = octopart_price_info.Octopart_price_info(cate=cate_name, manu=manu_name, is_star=is_star,
                                                                 distribute=distribute_name, SKU=sku, stock=stock,
                                                                 MOQ=moq, currency_type=currency_type, k_price=k_price,
                                                                 updated=updated)
    return octopart_price_ele


def main():
    file_name_list = get_files()
    print(f'file count is :{file_name_list.__len__()}')
    sublist = file_name_list
    for (file_name_index, file_name) in enumerate(sublist):
        if file_name_index in range(1809, 10000):
            print(f'file_index is: {file_name_index}, file name is: {file_name}')
            manu_get_price(file_name_index, file_name)


if __name__ == "__main__":
    main()

