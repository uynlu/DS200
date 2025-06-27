import argparse

from data_collector.product_detail.product_data_collector import collect_product_data
from data_collector.kol_info.youtube_scraper import YoutubeScraper
from data_collector.kol_info.tiktok_scraper import TiktokScraper


parser = argparse.ArgumentParser(description="Collect data")
parser.add_argument("--file-path", type=str, required=True)
parser.add_argument("--saved-dir", type=str, required=True)
parser.add_argument("--info-type", type=str, choices=["product", "kol"], required=True)
parser.add_argument("--social-media-type", type=str, choices=["youtube", "tiktok"])
args = parser.parse_args()

if args.info_type == "product":
    collect_product_data(args.file_path, args.saved_dir)
else:
    if args.social_media_type == "youtube":
        scraper = YoutubeScraper(args.file_path, args.saved_dir)
    else:
        scraper = TiktokScraper(args.file_path, args.saved_dir)

    scraper.main()


# python data_collector\\run.py --file-path .\\dataset\\Link.xlsx --saved-dir .\\dataset\\database\\products_detail --info-type product
# python data_collector\\run.py --file-path .\\dataset\\Link.xlsx --saved-dir .\\dataset\\database\\kols_info --info-type kol --social-media-type youtube
# python data_collector\\run.py --file-path .\\dataset\\Link.xlsx --saved-dir .\\dataset\\database\\kols_info --info-type kol --social-media-type tiktok
