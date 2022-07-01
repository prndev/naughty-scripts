#!/usr/bin/env python3

import argparse
from http.cookiejar import MozillaCookieJar
import requests
import re
import os
import shutil
from lxml import etree

# https://stackoverflow.com/questions/13137817/how-to-download-image-using-requests
def download_to_file(url, file):
    if (not file):
        return False
    print(f"Downloading {url}…")
    r = requests.get(url, stream=True)
    r.raise_for_status()
    r.raw.decode_content = True
    shutil.copyfileobj(r.raw, file)
    return True

def _prepare_file(url, target_directory):
    target_filename = os.path.basename(url)
    target_path = os.path.join(target_directory, target_filename)
    if not os.path.isfile(target_path):
        return open(target_path, 'wb')
    else:
        print(f"{target_path} already exists.")
        return None
        
def download_noclobber(url, target_directory):
    file = _prepare_file(url, target_directory)
    return download_to_file(url, file)

def _store_description(submission_description_dom, target_directory):
    submission_description_text = submission_description_dom.xpath('string()')
    submission_description_words = re.split(r'[\t\r\n ]+', submission_description_text)
    if (args.description_length and len(submission_description_words) > args.description_length):
        file = _prepare_file(".".join(submission_url.split(".")[:-1])+".html", target_directory)
        if (file):
            file.write(submission_description.encode('utf-8'))
            print("Long description saved.")
    if (args.youtube):
        for link in set(re.findall(r'https://[^.&+;]+\.youtube\.com/[^"<]+', submission_description_text)):
            print(f"Found YouTube link: {link}")
    if (args.e621):
        for link in set(re.findall(r'https://e621.net/posts/[0-9]+', submission_description_text)):
            print(f"Found e621 link: {link}")

def _store_linked_media(submission_description_dom, target_directory):
    links = submission_description_dom.xpath('//a')
    for link in links:
        href = link.get('href')
        if (href.split('.')[-1] in ["webm","mp4","mp3"]):
            print(f"Description contains a link to a media file: {href}")
            download_noclobber(href, target_directory)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""
        Downloader for FurAffinity
        Part of the https://github.com/prndev/naughty-scripts collection.
    """, epilog="""
        This tool does not handle any login data. You need to log into FurAffinity and export your session cookie into a file (see cookiejar parameter).
    """)
    parser.add_argument("--cookiejar", help="Path to Mozilla cookie jar file (default: cookies.txt).", type=str, default="cookies.txt")
    parser.add_argument("--gallery", help="Path of gallery to download (default: msg/submissions).", type=str, default="msg/submissions")
    parser.add_argument("--baseurl", help="Base URL to download from (default: https://www.furaffinity.net).", type=str, default="https://www.furaffinity.net")
    parser.add_argument("--outdir", help="Path to directory to download into (default: Downloads).", type=str, default="Downloads")
    parser.add_argument("--all", help="When a file exists, proceed to the next one instead of stopping.", action="store_true")
    parser.add_argument("--youtube", help="Search description for links to YouTube.", action="store_true")
    parser.add_argument("--e621", help="Search description for links to e621.", action="store_true")
    parser.add_argument("--description-length", help="If the description contains many words (default: 300), it is downloaded, too.", type=int, default=300)
    parser.add_argument("--start-page", help="Page to start downloading gallery (default: 1).", type=str, default="1")
    args = parser.parse_args()
    
    cookiejar = MozillaCookieJar()
    cookiejar.load(args.cookiejar, ignore_discard=True, ignore_expires=True)

    args.gallery = args.gallery.strip("/")
    gallery_title = args.gallery.split("/")[-1]
    target_directory = os.path.join(args.outdir, gallery_title)
    os.makedirs(target_directory, exist_ok=True)
    
    gallery_page = ""
    next_gallery_page = args.start_page
    stop = False
    while next_gallery_page and next_gallery_page != gallery_page and not stop:
        gallery_page = next_gallery_page
        url = f"{args.baseurl}/{args.gallery}/{gallery_page}"
        print(f"Fetching {url}…")
        request = requests.get(url, cookies=cookiejar)
        gallery_html = request.text
        #with open("dbg.html","w") as f:
        #    f.write(gallery_html)
        next_gallery_page = re.findall(f'(?<=/{args.gallery}/)[^/"]+', gallery_html)
        next_gallery_page = next_gallery_page[-1] if next_gallery_page else "" # galleries might not have any button at all
        next_gallery_page = next_gallery_page.split("@")[0].replace("new","").strip("~") # in msg/submissions, this can read "new~12345678@48" up to "new@48"

        submission_ids = set(re.findall('(?<=/view/)[^/]+', gallery_html))
        submission_ids = [int(sid) for sid in submission_ids]
        for submission_id in sorted(submission_ids, reverse=True):
            url = f"{args.baseurl}/view/{submission_id}"
            print(f"Fetching {url}…")
            request = requests.get(url, cookies=cookiejar)
            submission_html = request.text

            submission_url = "https:"+re.search('[^"]+(?=">Download</a>)', submission_html).group(0)
            if (not download_noclobber(submission_url, target_directory) and not args.all):
                print("Not continuing.")
                stop = True
                break
                
            else:
                # FA's HTML is too broken for this to be useful
                #submission_description_dom = gallery_dom.xpath('//div[contains(@class, "submission-description")]')[0]
                
                submission_description = re.search('<div class="submission-description.*?</div>', submission_html, re.DOTALL).group(0)
                submission_description_dom = etree.HTML(submission_description)

                _store_description(submission_description_dom, target_directory)
                _store_linked_media(submission_description_dom, target_directory)

    print("Finished.")
