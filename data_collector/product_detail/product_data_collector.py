import pandas as pd
import os
from tqdm import tqdm
import json


def collect_product_data(file_path: str, saved_dir: str):
    products_general_info = pd.read_excel(file_path, skiprows=1, sheet_name="Sản phẩm")

    if os.path.exists(os.path.join(saved_dir, "products_info.json")):
        with open(f"{saved_dir}\\products_info.json", "r", encoding="utf-8") as file:
            products_info = json.load(file)
        
        if len(products_info) == len(products_general_info):
            print("*** Not update ***")
            return
        elif len(products_info) < len(products_general_info):
            print("*** Update products ***")
    else:
        print("*** Get products detail ***")
        products_info = []
    
    for i in tqdm(range(len(products_general_info))):
        products_info.append({
            "id": str(products_general_info["STT"][i]),
            "name": products_general_info["Tên sản phẩm"][i],
            "type": products_general_info["Loại sản phẩm"][i],
            "brand": products_general_info["Nhãn hàng"][i],
            "description": products_general_info["Mô tả"][i],
            "price": int(products_general_info["Giá cả"][i])
        })

    with open(f"{saved_dir}\\products_info.json", "w", encoding="utf-8") as file:
        json.dump(products_info, file, indent=4, ensure_ascii=False)
