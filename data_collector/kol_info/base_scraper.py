import pandas as pd
from tqdm import tqdm
import json
import os
import numpy as np
from selenium.webdriver.support.ui import WebDriverWait

from data_collector.utils import set_up_driver


class BaseScraper:
    def __init__(
        self,
        file_path: str,
        saved_dir: str
    ):
        self.saved_dir = saved_dir

        self.update_flag = False
        self.kols_general_info = pd.read_excel(file_path, skiprows=1, sheet_name="KOLs")

        self.kols_info = []
        self.channels_info = []
        self.videos_detail = []
        self.videos_comments = []

    def main(self):
        print("*** Start crawling ***")
        self.get_kol_info()
        self.get_channel_info()
        self.get_videos_info()
        
    def get_kol_info(self): 
        print("*** Get KOLs information ***")
        if os.path.exists(os.path.join(self.saved_dir, "kols_info.json")):
            with open(os.path.join(self.saved_dir, "kols_info.json"), "r", encoding="utf-8") as file:
                self.kols_info = json.load(file)
            
            if len(self.kols_info) == len(self.kols_general_info):
                print("*** Re-crawl, not update ***")
                return
            elif len(self.kols_info) < len(self.kols_general_info):
                print("*** Update KOLs ***")
                self.update_flag = True
            
        for i in tqdm(range(len(self.kols_info), len(self.kols_general_info))):
            self.kols_info.append({
                "id": str(self.kols_general_info["STT"][i]),
                "name": self.kols_general_info["KOL"][i],
                "gender": 0 if self.kols_general_info["Giới tính"][i] == "Nam" else 1,
                "age": int(self.kols_general_info["Tuổi"][i]) if not pd.isna(self.kols_general_info["Tuổi"][i]) else np.nan,
                "field": self.kols_general_info["Lĩnh vực"][i]
            })

        with open(f"{self.saved_dir}\\kols_info.json", "w", encoding="utf-8") as file:
            json.dump(self.kols_info, file, ensure_ascii=False, indent=4)

    def get_channel_info(self):
        raise NotImplementedError
    
    def get_videos_info(self):
        raise NotImplementedError
    
    def _set_up_driver(self):
        print("*** Set up selenium driver ***")
        self.driver = set_up_driver()
        self.wait = WebDriverWait(self.driver, 10)
