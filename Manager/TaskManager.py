from Manager import AccManage


class Taskmanger:
    task_name = 'TRenesas_all_175H'
    if AccManage.Device_ID == 'Mac':
        start_index = 0
        end_index = 125
    elif AccManage.Device_ID == '11':
        start_index = 125
        end_index = 250
    elif AccManage.Device_ID == 'sz':
        start_index = 250
        end_index = 375
    elif AccManage.Device_ID == '04':
        start_index = 375
        end_index = 500
    elif AccManage.Device_ID == '42':
        start_index = 400
        end_index = 500