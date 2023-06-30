import ssl
import time

from bs4 import BeautifulSoup
import requests
from WRTools import IPHelper, UserAgentHelper, LogHelper, WaitHelp, ExcelHelp, PathHelp
import os
import digikey
from digikey.v3.productinformation import KeywordSearchRequest



ssl._create_default_https_context = ssl._create_unverified_context

sourceFile_dic = {'fileName': PathHelp.get_file_path('TInfenion_40H', 'Task.xlsx'),
                  'sourceSheet': 'ppn',
                  'colIndex': 1,
                  'startIndex': 0,
                  'endIndex': 2}
result_save_file = PathHelp.get_file_path('TInfenion_40H', 'digikey_status.xlsx')

log_file = '//Digikey/DJ_product_status_log.txt'
cookies = {'fc_locale':'zh-CN', 'fc_timezone':'Asia%2FShanghai'}
headers = {'User-Agent': UserAgentHelper.getRandowUA(),
               'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
               'Accept-Encoding': 'gzip,deflate, br',
               'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
               'Connection': 'keep-alive'}
default_url = 'https://www.digikey.com/'

def get_dg_product_status(cate_index, cate_name):
    headers['User-Agent'] = UserAgentHelper.getRandowUA_Mac()
    url = f"https://www.digikey.cn/en/products/detail/*/{cate_name}/4914222?amp%3BWT.z_header=search_go"
    print(f'url is: {url}')
    try:
        req = requests.get(url=url, headers=headers, cookies=cookies, timeout=(600, 360))
        if cate_index > 0 and cate_index % 15 == 0:
            WaitHelp.waitfor_account_import(True, False)
        else:
            WaitHelp.waitfor(True, isDebug=False)
    except Exception as e:
        LogHelper.write_log(log_file, f'{cate_name} request get exception: {e}')
        return
    # print(f'respond is :{req.text}')
    if req.status_code != 200:
        LogHelper.write_log(log_file, f'{cate_name} req.status_code: {req.status_code}')
    soup = BeautifulSoup(req.text, 'lxml')
    try:
        #prodcut description
        try:
            des_table = soup.select('table')[0]
            des_tbody = des_table.select('tbody')[0]
            des_tr = des_tbody.select('tr')[3]
            des_title = des_tr.select('td')[0].text
            if des_title == 'Description':
                des_td = des_tr.select('td')[1]
                des_content = des_td.text
            else:
                des_content = '//'
        except:
            des_content = '//'
        # product status
        try:
            sta_table = soup.select('table')[1]
            sta_tbody = sta_table.select('tbody')[0]
            sta_tr = sta_tbody.select('tr')[4]

            status_title = sta_tr.select('td')[0].text
            if status_title == 'Product Status':
                sta_td = sta_tr.select('td')[1]
                status_content = sta_td.text
            else:
                status_content = '//'
        except:
            status_content = '//'
        result = [cate_name, des_content, status_content]
        WaitHelp.waitfor(False, isDebug=False)
    except Exception as e:
        LogHelper.write_log(log_file, f'{cate_name} request get exception: {e}')
        result = [[cate_name, "//", '//']]
    ExcelHelp.add_arr_to_sheet(
            file_name=result_save_file,
            sheet_name='digikey_status',
            dim_arr=[result])


def combine_result(source_files:[], aim_file):
    for temp in source_files:
        data = ExcelHelp.read_sheet_content_by_name(file_name=temp, sheet_name='digikey_status')
        ExcelHelp.add_arr_to_sheet(file_name=aim_file, sheet_name='digikey_status', dim_arr=data)
        time.sleep(2.0)


def main():
    all_cates = ExcelHelp.read_col_content(file_name=sourceFile_dic['fileName'],
                                           sheet_name=sourceFile_dic['sourceSheet'],
                                           col_index=sourceFile_dic['colIndex'])
    for (cate_index, cate_name) in enumerate(all_cates):
        if cate_index in range(sourceFile_dic['startIndex'], sourceFile_dic['endIndex']):
            print(f'cate_index is: {cate_index}  cate_name is: {cate_name}')
            if cate_name is None:
                break;
            get_dg_product_status(cate_index, cate_name)


def testDigikey():
    os.environ['DIGIKEY_CLIENT_ID'] = 'G2LPNfi9s5dalamAEx1jzZ6VKtga6jTS'
    os.environ['DIGIKEY_CLIENT_SECRET'] = 'PjIFbMXbWLwpcqY4'
    os.environ['DIGIKEY_CLIENT_SANDBOX'] = 'True'
    os.environ['DIGIKEY_STORAGE_PATH'] = '/Users/liuhe/Library/Caches/Firefox/Profiles/p7u49s1s.default-release-1/cache2'
    os.environ['DIGIKEY_REDIRECT_URI'] = 'https://molies.net/'

    # Query product number
    dkpn = '296-6501-1-ND'
    part = digikey.product_details(dkpn)

    # Search for parts
    search_request = KeywordSearchRequest(keywords='CRCW080510K0FKEA', record_count=10)
    result = digikey.keyword_search(body=search_request)
    print(result)


def combine_upload_result():
    source_file = PathHelp.get_file_path(None, 'TNXP.xlsx')
    files = ["/Users/liuhe/Desktop/progress/TNXP/discontiue/p4/discontiue/n41.xlsx",
             "/Users/liuhe/Desktop/progress/TNXP/discontiue/p4/discontiue/n43.xlsx",
             "/Users/liuhe/Desktop/progress/TNXP/discontiue/p4/discontiue/n45.xlsx"
             ]
    result = []
    for temp in files:
        sheet_content = ExcelHelp.read_sheet_content_by_name(file_name=temp, sheet_name='My Lists Worksheet')
        for (row_index, row) in enumerate(sheet_content):
            if row_index > 0:
                if str(row[1]).__len__() >= 0:
                    if str(row[2]).__len__() >= 0:
                        result.append([str(row[3]), str(row[1]), str(row[2]), str(row[4]), time.strftime('%Y-%m-%d', time.localtime())])
                    else:
                        result.append([str(row[1]), "/", "/", "/", time.strftime('%Y-%m-%d', time.localtime())])
    save_sheet = 'My Lists Worksheet'
    ExcelHelp.add_arr_to_sheet(file_name=source_file, sheet_name=save_sheet, dim_arr=result)
    partion(source_file=source_file, source_sheet=save_sheet)


def partion(source_file, source_sheet):
    sheet_content = ExcelHelp.read_sheet_content_by_name(file_name=source_file, sheet_name=source_sheet)
    history_continue = ExcelHelp.read_col_content(file_name=source_file, sheet_name='discontinue', col_index=1)
    history_making = ExcelHelp.read_col_content(file_name=source_file, sheet_name='making', col_index=1)
    history_noData = ExcelHelp.read_col_content(file_name=source_file, sheet_name='noData', col_index=1)
    discontiue_result = []
    making_result = []
    noData_result = []
    for row in sheet_content:
        if row.__len__() > 4:
            if str(row[3]).__len__() == 0 or str(row[3]) == 'None':
                if not (row[0] in history_noData):
                    noData_result.append([row[0], row[1], row[4]])
            elif row[3] == 'Obsolete' or row[3] == 'Last Time Buy' or row[3] == '停产' or row[3] == '最后售卖':
                if not (row[0] in history_continue):
                    discontiue_result.append([row[0], row[1], row[4]])
            else:
                if not (row[0] in history_making):
                    making_result.append([row[0], row[1], row[4]])

    ExcelHelp.add_arr_to_sheet(file_name=source_file, sheet_name='discontinue', dim_arr=discontiue_result)
    ExcelHelp.add_arr_to_sheet(file_name=source_file, sheet_name='making', dim_arr=making_result)
    ExcelHelp.add_arr_to_sheet(file_name=source_file, sheet_name='noData', dim_arr=noData_result)


def deal_upload():
    digikey_upload_file = PathHelp.get_file_path(None, 'TDigikey_upload.xlsx')
    ExcelHelp.delete_sheet_content(digikey_upload_file, 'Sheet1')
    all_cates = ExcelHelp.read_col_content(file_name=PathHelp.get_file_path("TRenesas_MCU_115H", 'Task.xlsx'),
                                           sheet_name='ppn',
                                           col_index=1)
    ExcelHelp.add_arr_to_col(file_name=digikey_upload_file, sheet_name='Sheet1', dim_arr=all_cates)


if __name__ == '__main__':
    deal_upload()
    # main()
