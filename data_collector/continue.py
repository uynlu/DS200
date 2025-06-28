import argparse
import json
import tqdm

from data_collector.kol_info.youtube_scraper import YoutubeScraper

parser = argparse.ArgumentParser(description="Continue collecting data")
parser.add_argument("--file-path", type=str, required=True)
parser.add_argument("--saved-dir", type=str, required=True)
parser.add_argument("--link-path", type=str, required=True)
parser.add_argument("--kol-id", type=str, required=True)
args = parser.parse_args()

scraper = YoutubeScraper(args.file_path, args.saved_dir)

with open(args.link_path, "r", encoding="utf-8") as file:
    links = json.load(file)

for i, link in enumerate(links):
    if "https://www.youtube.com/watch?v=949Y2bsLDB0&pp=0gcJCc4JAYcqIYzv" in link:
        print(i)
        break

for link in tqdm(links[i:]):
    scraper.get_error_video_info(link, args.kol_id)
