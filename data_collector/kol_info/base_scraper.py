import pandas as pd
from tqdm import tqdm
import json
import os
import numpy as np


class BaseScraper:
    def __init__(
        self,
        file_path: str,
        saved_dir: str,
        flag: bool = False,
    ):
        self.saved_dir = saved_dir
        self.flag = flag
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
        # self.get_videos_hastags()
        
    def get_kol_info(self): 
        print("*** Get KOLs information ***")
        if self.flag == False:
            if os.path.exists(os.path.join(self.saved_dir, "kols_info.json")):
                with open(os.path.join(self.saved_dir, "kols_info.json"), "r", encoding="utf-8") as file:
                    self.kols_info = json.load(file)
                
                if len(self.kols_info) == len(self.kols_general_info):
                    print("*** Not crawl update ***")
                    return
                elif len(self.kols_info) < len(self.kols_general_info):
                    print("*** Update KOLs ***")
                    self.update_flag = True
        else:
            print("*** Re-crawl ***")

        for i in tqdm(range(len(self.kols_info), len(self.kols_general_info))):
            self.kols_info.append({
                "id": str(self.kols_general_info["STT"][i]),
                "name": self.kols_general_info["KOL"][i],
                "gender": 0 if self.kols_general_info["Giới tính"][i] == "Nam" else 1,
                "age": int(self.kols_general_info["Tuổi"][i]) if not pd.isna(self.kols_general_info["Tuổi"][i]) else np.nan,
                "field": self.kols_general_info["Lĩnh vực"][i]
            })

        with open(os.path.join(self.saved_dir, "kols_info.json"), "w", encoding="utf-8") as file:
            json.dump(self.kols_info, file, ensure_ascii=False, indent=4)

    def get_channel_info(self):
        raise NotImplementedError
    
    def get_videos_info(self):
        raise NotImplementedError
    
    def get_videos_hastags(self):
        raise NotImplementedError
