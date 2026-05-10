import xlsxwriter

import cs2_inventory_stuff
from helpers import *

def add_spreadsheet_datapoint_inventory(item_dict, steam_id):
    datapoints = {}
    date = int(time.time())

    for item in item_dict:
        datapoints[item] = {}
        datapoints[item][date] = {"count": item_dict[item][0],
                                  "value": item_dict[item][1]}

    add_datapoint(datapoints, steam_id + "_inventory.txt")

def add_datapoint(datapoints, filename):
    current_inventory_data = read_from_cache(filename)
    for item in datapoints:
        if item not in current_inventory_data:
            current_inventory_data[item] = {}

        key = list(datapoints[item].keys())[0]
        current_inventory_data[item][key] = datapoints[item][key]

    write_to_cache(current_inventory_data, filename)

def create_inventory_spreadseet(steam_id, params):
    inventory_data = read_from_cache(steam_id + "_inventory.txt")

    os.makedirs("inventory_workbooks", exist_ok=True)

    workbook = xlsxwriter.Workbook(
        f"inventory_workbooks/{steam_id}_inventory_{int(time.time())}.xlsx"
    )

    used_sheet_names = set()

    for item in inventory_data.keys():
        item_string = str(item)
        no_special = remove_special_chars(item_string)

        base_name = cs2_inventory_stuff.cleanup_name(no_special, 30, True)

        sheet_name = base_name
        counter = 1

        while sheet_name.lower() in used_sheet_names:
            suffix = f"_{counter}"
            sheet_name = (base_name[:30 - len(suffix)] + suffix)
            counter += 1

        used_sheet_names.add(sheet_name.lower())

        worksheet = workbook.add_worksheet(sheet_name)

        sorted_datapoints = sort_datapoints(inventory_data[item])

        row_num = 0
        for timestamp, datapoint in sorted_datapoints:
            row = create_row((timestamp, datapoint))
            for col_num, value in enumerate(row):
                worksheet.write(row_num, col_num, value)
            row_num += 1

    workbook.close()

def create_row(datapoint):
    row = [datapoint[0]]
    for keys in datapoint[1]:
        row.append(datapoint[1][keys])
    return row

def sort_datapoints(datapoints):
    sorted_items = []
    while(len(datapoints) > 0):
        min_timestamp = min(list(datapoints.keys()))
        sorted_items.append((min_timestamp, datapoints.pop(min_timestamp)))
    return sorted_items

def get_keys_from_params(inventory_data, params):
    keys = []
    first_item = list(inventory_data.keys())[0]
    datapoints_dict = inventory_data[first_item]
    inventory_datapoint_key = list(datapoints_dict.keys())[0]
    inventory_datapoint_key = datapoints_dict[inventory_datapoint_key]
    possible_parameters = list(inventory_datapoint_key.keys())
    for param in params:
        keys.append(possible_parameters[param])

    return keys

def list_to_dict(data):
    dict_to_return = {}
    for item in data:
        dict_to_return[item] = {}
        for entry in data[item]:
            key = list(entry.keys())[0]
            value = entry[key]
            dict_to_return[item][key] = value
            print(dict_to_return)

    return dict_to_return