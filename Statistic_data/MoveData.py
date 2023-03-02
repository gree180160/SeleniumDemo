# 将findchips 数据， IC——Stock， IC-Hot， price 合并到一个excel到all_info 中
import time

from WRTools import ExcelHelp, PathHelp

# ------------findchip----------------------
# 将临时保存的数据转移到汇总数据到excel
def findchips_move_data(source_file: str, source_sheet: str, aim_file: str, aim_sheet):
    ExcelHelp.move_sheet_to_row(source_file_list=[source_file], source_sheet=source_sheet, aim_file=aim_file, aim_sheet=aim_sheet)


# 将同一个ppn到所有stock 累加，然后按照保存到数组中, 没有数据的，用/填充
def findchips_stock_sum(source_file: str):
    pps = ExcelHelp.read_col_content(file_name=source_file, sheet_name='ppn', col_index=1)
    result = []
    for (index, temp_ppn) in enumerate(pps):
        ppn_info = [temp_ppn, '/']
        findchip_stocks = ExcelHelp.read_sheet_content_by_name(file_name=source_file, sheet_name='findchip_stock')
        for row_content in findchip_stocks:
            try:
                ppn = str(row_content[0])
            except:
                ppn = None
            if ppn:
                try:
                    stock = int(row_content[5])
                except:
                    stock = 0
                if ppn == temp_ppn:
                    # 第一条记录
                    if ppn_info[1] == '/':
                        ppn_info[1] = stock
                    else:
                        ppn_info[1] += stock

        result.append(ppn_info)
    ExcelHelp.add_arr_to_sheet(file_name=source_file, sheet_name="findchips_stock_sum", dim_arr=result)


# move part sheet_content to other sheet position
# 因为第一行为标题行，所有从第二行开始写入数据
def move_part_to_part(source_file: str,
                      source_sheet: str,
                      from_col: int,
                      to_col: int,
                      aim_file: str,
                      aim_sheet: str,
                      start_col: int):
    source_data = ExcelHelp.read_from_col_to_col(file_name=source_file, sheet_name=source_sheet, from_col=from_col, to_col=to_col)
    ExcelHelp.save_one_col(file_name=aim_file, sheet_name=aim_sheet, col_index=start_col, dim_arr=source_data, skip_row_count=1)


#   将ppn, manu 复制到all——info sheet 中
def move_ppn_to_allInfo(source_file: str):
    move_part_to_part(
        source_file=source_file,
        source_sheet='ppn',
        from_col=1,
        to_col=2,
        aim_file=source_file,
        aim_sheet='all_info',
        start_col=1)


#  将IC_supplier_count, IC_stock_count 复制到all——info sheet 中
def move_IC_stock_to_allInfo(source_file: str):
    move_part_to_part(
        source_file=source_file,
        source_sheet='IC_Stock',
        from_col=3,
        to_col=4,
        aim_file=source_file,
        aim_sheet='all_info',
        start_col=3)


#   将pm_record, pm,pr,grade,复制到all——info sheet 中
def move_BomOct_to_allInfo(source_file: str):
    # pm_record
    move_part_to_part(
        source_file=source_file,
        source_sheet='bom_octopart_price',
        from_col=7,
        to_col=7,
        aim_file=source_file,
        aim_sheet='all_info',
        start_col=5)
    # pm, pr
    move_part_to_part(
        source_file=source_file,
        source_sheet='bom_octopart_price',
        from_col=3,
        to_col=4,
        aim_file=source_file,
        aim_sheet='all_info',
        start_col=6)
    # grade
    move_part_to_part(
        source_file=source_file,
        source_sheet='bom_octopart_price',
        from_col=6,
        to_col=6,
        aim_file=source_file,
        aim_sheet='all_info',
        start_col=8)


#   将ppnd的stock sum, 复制到all——info sheet 中
def move_findchip_to_allInfo(source_file: str, findchip_file:str):
    findchip_file = findchip_file
    findchips_move_data(source_file=findchip_file, source_sheet='findchip_stock', aim_file=source_file, aim_sheet="findchip_stock")
    findchips_stock_sum(source_file=source_file)
    move_part_to_part(
        source_file=source_file,
        source_sheet='findchips_stock_sum',
        from_col=2,
        to_col=2,
        aim_file=source_file,
        aim_sheet='all_info',
        start_col=9)


# 结算IC—hot,并倒入all_info
def move_IC_hot(source_file: str):
    pps = ExcelHelp.read_col_content(file_name=source_file, sheet_name='ppn', col_index=1)
    week_data = ExcelHelp.read_sheet_content_by_name(file_name=source_file, sheet_name='IC_hot_week')
    week_record_ppns = ExcelHelp.read_col_content(file_name=source_file, sheet_name='IC_hot_week', col_index=1)
    month_data = ExcelHelp.read_sheet_content_by_name(file_name=source_file, sheet_name='IC_hot_month')
    month_record_ppns = ExcelHelp.read_col_content(file_name=source_file, sheet_name='IC_hot_month', col_index=1)
    all_ppn_hot = []
    for (index, temp_ppn) in enumerate(pps):
        if temp_ppn in week_record_ppns:
            value_index = week_record_ppns.index(temp_ppn)
            row_data = week_data[value_index]
            week_data_str_list = row_data[1:]
            week_data_int_list = []
            for cell_value in week_data_str_list:
                try:
                    week_data_int_list.append(int(cell_value))
                except:
                    print("move_IC_hot_week cell content error")
            first_week_value = week_data_int_list[0]
            week_data_int_list.sort()
            record_data = [temp_ppn, first_week_value, week_data_int_list[-1], week_data_int_list[-2], week_data_int_list[0]]
        else:
            record_data = [temp_ppn, "/", "/", "/", "/"]

        if temp_ppn in month_record_ppns:
            value_index = month_record_ppns.index(temp_ppn)
            row_data = month_data[value_index]
            month_data_str_list = row_data[1:]
            month_data_int_list = []
            for cell_value in month_data_str_list:
                try:
                    month_data_int_list.append(int(cell_value))
                except:
                    print("move_IC_hot_month cell content error")
            first_month_value = month_data_int_list[0]
            month_data_int_list.sort()
            record_data.append(first_month_value)
            record_data.append(month_data_int_list[-1])
            record_data.append(month_data_int_list[-2])
            record_data.append(month_data_int_list[0])
        else:
            record_data.append('/')
            record_data.append('/')
            record_data.append('/')
            record_data.append('/')
        all_ppn_hot.append(record_data)
    ExcelHelp.add_arr_to_sheet(file_name=source_file, sheet_name='IC_hot_sorted', dim_arr=all_ppn_hot)
    time.sleep(2.0)
    move_part_to_part(
        source_file=source_file,
        source_sheet='IC_hot_sorted',
        from_col=2,
        to_col=9,
        aim_file=source_file,
        aim_sheet='all_info',
        start_col=10)

def move_DijiKey(source_file: str, dijikey_file: str):
    ppns = ExcelHelp.read_col_content(file_name=source_file, sheet_name='ppn', col_index=1)
    dijikey_data = ExcelHelp.read_sheet_content_by_name(file_name=dijikey_file, sheet_name='dijikey_status')
    result = []
    for (index, ppn) in enumerate(ppns):
        diji_record = [ppn, '//', '//']
        for (diji_index, diji_info) in enumerate(dijikey_data):
            if ppn == diji_info[0]:
                diji_record = diji_info
                break
        result.append(diji_record)
    ExcelHelp.add_arr_to_sheet(file_name=source_file, sheet_name='dijikey_status', dim_arr=result)
    move_part_to_part(
        source_file=source_file,
        source_sheet='dijikey_status',
        from_col=2,
        to_col=3,
        aim_file=source_file,
        aim_sheet='all_info',
        start_col=18)



if __name__ == "__main__":
    source_file = PathHelp.get_file_path('TInfenion_55H', 'Task.xlsx')
    move_ppn_to_allInfo(source_file=source_file)
    move_IC_stock_to_allInfo(source_file=source_file)
    move_BomOct_to_allInfo(source_file=source_file)
    move_findchip_to_allInfo(source_file=source_file, findchip_file=PathHelp.get_file_path('TInfenion_50H', 'findchip_stock.xlsx'))
    move_DijiKey(source_file=source_file, dijikey_file=PathHelp.get_file_path('TInfenion_50H', 'dijikey_status.xlsx'))
    move_IC_hot(source_file=source_file)


