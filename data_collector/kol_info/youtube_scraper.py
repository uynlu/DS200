from tqdm import tqdm
import requests
from bs4 import BeautifulSoup
import json
import time
import os
import re
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait

from data_collector.kol_info.base_scraper import BaseScraper
from data_collector.utils import set_up_driver


API = "AIzaSyCe7rO3TWJvfA8if54_pAqxDci1ZdxwBX0"


class YoutubeScraper(BaseScraper):
    def __init__(self, file_path: str, saved_dir: str):
        super().__init__(file_path, saved_dir)
        self.youtube_kols_general_info = self.kols_general_info.copy()
        self.youtube_kols_general_info.dropna(subset=["Youtube"], inplace=True)
        self.youtube_kols_general_info.reset_index(drop=True, inplace=True)

    def get_channel_info(self):
        print("*** Get Youtube channel information ***")
        if self.update_flag:
            with open(os.path.join(self.saved_dir, "youtube_channels_info.json"), "r", encoding="utf-8") as file:
                self.channels_info = json.load(file)

            if len(self.channels_info) == len(self.youtube_kols_general_info):
                print("The kols updated don't have youtube channels.")
                return

        self.kol_index_start = len(self.channels_info)
        self._get_channel_id()
        for i, channel_id in tqdm(self.channels_id):
            url = f"https://www.googleapis.com/youtube/v3/channels?part=statistics&key={API}&id={channel_id}"
            channel_info = json.loads(requests.get(url).text)
            self.channels_info.append({
                "id": str(self.youtube_kols_general_info["STT"][i]),
                "youtube_link": self.youtube_kols_general_info["Youtube"][i],
                "youtube_view_count": int(channel_info["items"][0]["statistics"]["viewCount"]),
                "youtube_subscriber_count": int(channel_info["items"][0]["statistics"]["subscriberCount"]),
                "youtube_video_count": int(channel_info["items"][0]["statistics"]["videoCount"])
            })
            with open(os.path.join(self.saved_dir, "youtube_channels_info.json"), "w", encoding="utf-8") as file:
                json.dump(self.channels_info, file, ensure_ascii=False, indent=4)
            
    def get_videos_info(self):
        print("*** Set up selenium driver ***")
        self.driver = set_up_driver()
        self.wait = WebDriverWait(self.driver, 10)

        if self.update_flag:
            with open(os.path.join(self.saved_dir, "youtube_videos_detail.json"), "r", encoding="utf-8") as file:
                self.videos_detail = json.load(file)

            with open(os.path.join(self.saved_dir, "youtube_videos_comments.json"), "r", encoding="utf-8") as file:
                self.videos_comments = json.load(file)
        
        j = len(self.videos_detail) + 1
        k = len(self.videos_comments) + 1
        for i in range(self.kol_index_start, len(self.youtube_kols_general_info)):
            print(f'*** Get videos information of {self.youtube_kols_general_info["KOL"][i]} ***')
            url = self.youtube_kols_general_info["Youtube"][i]
            self.driver.get(url)
            time.sleep(3)

            videos_button = self.wait.until(
                EC.element_to_be_clickable((
                    By.XPATH, '//yt-tab-shape[@tab-title="Videos"]'
                ))
            )
            videos_button.click()
            time.sleep(1.5)
            
            self._scroll_full_page()

            videos_element = self.driver.find_elements(By.TAG_NAME, 'ytd-rich-item-renderer')

            videos_link = []
            for video_element in tqdm(videos_element):
                video_link = video_element.find_element(By.ID, 'content') \
                    .find_element(By.ID, "thumbnail") \
                    .find_element(By.ID, "thumbnail") \
                    .get_attribute("href")
                videos_link.append(video_link)

            with open(os.path.join(self.saved_dir, f'youtube_videos_link_{self.youtube_kols_general_info["KOL"][i]}.json'), "w", encoding="utf-8") as file:
                json.dump(videos_link, file, indent=4, ensure_ascii=False)

            if os.path.exists(os.path.join(self.saved_dir, "youtube_videos_error.json")):
                with open(os.path.join(self.saved_dir, "youtube_videos_error.json"), "r", encoding="utf-8") as file:
                    youtube_videos_error = json.load(file)
            else:
                youtube_videos_error = []

            for video_link in tqdm(videos_link):
                try:
                    self.driver.get(video_link)
                    time.sleep(3)

                    if self.driver.find_elements(
                        By.CSS_SELECTOR, 'yt-mealbar-promo-renderer.style-scope.ytd-popup-container'
                    ):
                        no_thanks_button = self.driver.find_element(
                            By.XPATH, '//*[@id="dismiss-button"]/yt-button-shape/button'
                        )
                        no_thanks_button.click()
                        time.sleep(0.5)

                    if self.driver.find_elements(
                        By.XPATH, '//yt-formatted-string[@id="message"]//span[contains(text(), "Comments are turned off. ")]'
                    ):
                        continue

                    title, view_count, published_day, like_count, content, comment_count = self._get_video_detail()               
                    self.videos_detail.append({
                        "id": str(j),
                        "youtube_video_url": self.driver.current_url,
                        "youtube_video_title": title,
                        "youtube_video_view_count": view_count,
                        "youtube_video_published_day": published_day,
                        "youtube_video_like_count": like_count,
                        "youtube_video_content": content,
                        "youtube_video_comment_count": comment_count,
                        "kol_id": str(self.youtube_kols_general_info["STT"][i])  # Foreign key reference to self.channel_info
                    })
                    with open(os.path.join(self.saved_dir, "youtube_videos_detail.json"), "w", encoding="utf-8") as file:
                        json.dump(self.videos_detail, file, ensure_ascii=False, indent=4)

                    comments = self._get_video_comments()
                    for comment in comments:
                        self.videos_comments.append({
                            "id": str(k),
                            "youtube_video_comment": comment.strip(),
                            "youtube_video_id": str(j)
                        })
                        k += 1
                        
                    with open(os.path.join(self.saved_dir, "youtube_videos_comments.json"), "w", encoding="utf-8") as file:
                        json.dump(self.videos_comments, file, ensure_ascii=False, indent=4)

                    j += 1
                except Exception as e:
                    youtube_videos_error.append({
                        "kol": self.youtube_kols_general_info["KOL"][i],
                        "kol_id": str(self.youtube_kols_general_info["STT"][i]),
                        "error_video_url": video_link,
                        "error": str(e)
                    })
                    with open(os.path.join(self.saved_dir, "youtube_videos_error.json"), "w", encoding="utf-8") as file:
                        json.dump(youtube_videos_error, file, ensure_ascii=False, indent=4)

        self.driver.quit()

    def get_videos_hastags(self):
        with open(os.path.join(self.saved_dir, "youtube_videos_detail.json"), "r", encoding="utf-8") as file:
            self.videos_detail = json.load(file)
        
        for video_datail in self.videos_detail:
            content = video_datail.get("youtube_video_content", "")
            hashtags = re.findall(r"#\w+|#\S*[\w]", content)
            video_datail["youtube_video_hashtags"] = hashtags

        with open(os.path.join(self.saved_dir, "youtube_videos_detail_with_hashtags.json"), "w", encoding="utf-8") as file:
            json.dump(self.videos_detail, file, ensure_ascii=False, indent=4)

    def get_error_video_info(self, link: str = None, id: str = None):
        self.driver = set_up_driver()
        self.wait = WebDriverWait(self.driver, 10)

        with open(os.path.join(self.saved_dir, "youtube_videos_detail.json"), "r", encoding="utf-8") as file:
            self.videos_detail = json.load(file)

        with open(os.path.join(self.saved_dir, "youtube_videos_comments.json"), "r", encoding="utf-8") as file:
            self.videos_comments = json.load(file)
        
        j = len(self.videos_detail) + 1
        k = len(self.videos_comments) + 1
            
        self.driver.get(link)
        time.sleep(3)
        
        if self.driver.find_elements(
            By.CSS_SELECTOR, "yt-mealbar-promo-renderer.style-scope.ytd-popup-container"
        ):
            no_thanks_button = self.driver.find_element(
                By.XPATH, '//*[@id="dismiss-button"]/yt-button-shape/button'
            )
            no_thanks_button.click()
            time.sleep(0.5)

        if self.driver.find_elements(
            By.XPATH, '//yt-formatted-string[@id="message"]//span[contains(text(), "Comments are turned off. ")]'
        ):
            self.driver.quit()
            return

        title, view_count, published_day, like_count, content, comment_count = self._get_video_detail()               
        self.videos_detail.append({
            "id": str(j),
            "youtube_video_url": self.driver.current_url,
            "youtube_video_title": title,
            "youtube_video_view_count": view_count,
            "youtube_video_published_day": published_day,
            "youtube_video_like_count": like_count,
            "youtube_video_content": content,
            "youtube_video_comment_count": comment_count,
            "kol_id": id
        })
        with open(os.path.join(self.saved_dir, "youtube_videos_detail.json"), "w", encoding="utf-8") as file:
            json.dump(self.videos_detail, file, ensure_ascii=False, indent=4)

        comments = self._get_video_comments()
        for comment in comments:
            self.videos_comments.append({
                "id": str(k),
                "youtube_video_comment": comment.strip(),
                "youtube_video_id": str(j)
            })
            k += 1
        with open(os.path.join(self.saved_dir, "youtube_videos_comments.json"), "w", encoding="utf-8") as file:
            json.dump(self.videos_comments, file, ensure_ascii=False, indent=4)      
        
        self.driver.quit()

    def _get_channel_id(self):
        print("*** Get Youtube channel id ***")
        self.channels_id = []
        for i in tqdm(range(self.kol_index_start, len(self.youtube_kols_general_info))):
            url = self.youtube_kols_general_info["Youtube"][i]
            channel_response = requests.get(url)
            channel_soup = BeautifulSoup(channel_response.text, "html.parser")
            channel_meta_identifier = channel_soup.find("meta", itemprop="identifier")
            if channel_meta_identifier:
                channel_id = channel_meta_identifier.get("content")
                self.channels_id.append((i, channel_id))
            else:
                raise(f'Không tìm thấy channel ID của {self.youtube_kols_general_info["KOL"][i]}')
            
    def _get_video_detail(self):
        title_element = self.driver.find_element(By.CSS_SELECTOR, 'h1.ytd-watch-metadata yt-formatted-string')
        title = title_element.get_attribute("title")
        
        content_expandation_button = self.wait.until(
            EC.element_to_be_clickable((
                By.XPATH, '//*[@id="description-interaction"]'
            ))
        )

        self.driver.execute_script('arguments[0].scrollIntoView({block: "center"});', content_expandation_button)
        time.sleep(1)
        self.driver.execute_script('arguments[0].click();', content_expandation_button)
        time.sleep(1)

        self.wait.until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR, 'yt-formatted-string.style-scope.ytd-watch-info-text'
            ))
        )
        view_publishedday_element = self.wait.until(
            EC.presence_of_all_elements_located((
                By.CSS_SELECTOR, 'yt-formatted-string.style-scope.ytd-watch-info-text span'
            ))
        )
        view_count = int(view_publishedday_element[0].text[:-6].replace(",", ""))
        published_day = view_publishedday_element[2].text
        
        like_element = self.driver.find_element(
            By.XPATH,
            '//*[@id="top-level-buttons-computed"]/segmented-like-dislike-button-view-model/yt-smartimation/div/div/like-button-view-model/toggle-button-view-model/button-view-model/button'
        )
        like_count = int(like_element.get_attribute("aria-label")[27:-13].replace(",", ""))
        
        content_element = self.driver.find_element(
            By.CSS_SELECTOR,
            'ytd-text-inline-expander.style-scope.ytd-watch-metadata'
        )
        content = re.sub(r"\nTranscript.*?Show less\n", "", content_element.get_attribute("innerText"), flags=re.DOTALL)

        while True:
            self.driver.execute_script('window.scrollTo(0, document.documentElement.scrollHeight);')
            time.sleep(1)

            if self.driver.find_elements(By.CLASS_NAME, "style-scope.ytd-comments-header-renderer"):
                break

        comment_count_element = self.wait.until(
            EC.presence_of_element_located(( 
                By.CSS_SELECTOR, "yt-formatted-string.count-text.style-scope.ytd-comments-header-renderer"
            ))
        )

        comment_count_text = comment_count_element.text.strip()
        if len(comment_count_text) == 9:
            comment_count = 1
        else:
            comment_count = int(comment_count_text[:-9].replace(",", ""))

        return title, view_count, published_day, like_count, content, comment_count
    
    def _get_video_comments(self):
        self._scroll_full_page()
        
        comments_element = self.driver.find_elements(
            By.CSS_SELECTOR, 'ytd-comment-thread-renderer.style-scope.ytd-item-section-renderer'
        )

        comments = []
        for comment_element in comments_element:
            self.driver.execute_script(
                'arguments[0].scrollIntoView({behavior: "smooth", block: "center"});', comment_element
            )
            time.sleep(1)

            comment_text = self._get_and_format_comment(comment_element)
            comments.append(comment_text)

            if comment_element.find_elements(By.ID, 'more-replies'):
                more_reply_button = comment_element.find_element(
                    By.XPATH, './/*[@id="more-replies"]/yt-button-shape/button'
                )
                self.driver.execute_script('arguments[0].click();', more_reply_button)
                time.sleep(1.5)
                self.wait.until(
                    EC.presence_of_element_located((
                        By.CSS_SELECTOR, 'ytd-comment-replies-renderer'
                    ))
                )

                replies_container = comment_element.find_element(By.ID, "replies")
                while True:
                    if replies_container.find_elements(
                        By.XPATH, './/*[@id="contents"]/ytd-continuation-item-renderer'
                    ):
                        if replies_container.find_elements(
                            By.XPATH, './/*[@id="button"]/ytd-button-renderer/yt-button-shape/button'
                        ):
                            more_replies_button = replies_container.find_element(
                                By.XPATH, './/*[@id="button"]/ytd-button-renderer/yt-button-shape/button'
                            )
                            self.driver.execute_script("arguments[0].click();", more_replies_button)
                            time.sleep(1.5)
                        else:
                            break
                    else:
                        break

                replies_element = replies_container.find_elements(By.XPATH, './/ytd-comment-view-model')
                for reply_element in replies_element:
                    reply_text = self._get_and_format_comment(reply_element)
                    comments.append(reply_text)
        
        return comments

    def _scroll_full_page(self):
        last_height = self.driver.execute_script('return document.documentElement.scrollHeight')

        while True:
            self.driver.execute_script('window.scrollTo(0, document.documentElement.scrollHeight);')
            time.sleep(3)

            new_height = self.driver.execute_script('return document.documentElement.scrollHeight')
            if new_height == last_height:
                break
            last_height = new_height

    def _get_and_format_comment(self, comment_element: WebElement):
        comment_html_content = comment_element.find_element(By.ID, 'content').get_attribute('outerHTML')
        comment_soup = BeautifulSoup(comment_html_content, "html.parser")
        for img in comment_soup.find_all("img"):
            emoji = img.get("alt")
            img.replace_with(emoji)
        comment_text = comment_soup.get_text()
        return comment_text
