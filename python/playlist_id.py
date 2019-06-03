#!/Library/Frameworks/Python.framework/Versions/3.5/bin/python3

from bs4 import BeautifulSoup
from urllib.request import urlopen
import re
import csv
import requests


def get_all_id(yt_url, yk_url, bi_url):
    # youtube and youku
    html_yt = urlopen(yt_url).read()
    html_yk = urlopen(yk_url).read()

    if SHOW_TMP:
        with open('./results/t.html', 'wb') as f:
            f.write(html_yt)

    bs_yt = BeautifulSoup(html_yt, "lxml")
    bs_yk = BeautifulSoup(html_yk, "lxml")

    items_yt = bs_yt.findAll('a', {"class": "pl-video-title-link yt-uix-tile-link yt-uix-sessionlink spf-link "})
    items_yk = bs_yk.findAll("a", {"target": "video", "data-from": "2-1"})
    yk_counter = 2
    while len(items_yk) < len(items_yt):
        html_yk = urlopen(yk_url+"?page=%i" % yk_counter).read()
        bs_yk = BeautifulSoup(html_yk, "lxml")
        items_yk += bs_yk.findAll("a", {"target": "video", "data-from": "2-1"})
        yk_counter += 1

    # bilibili
    if "cid" in bi_url:
        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
            "Host": "api.bilibili.com",
            "Referer": "https://space.bilibili.com/243821484",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
        }
        ptn_mid = re.compile("\.com/(\d+)")
        ptn_cid = re.compile("\?cid=(\d+)")
        ptn_order = re.compile("\&order=(\d)")
        mid = re.findall(ptn_mid, bi_url)[0]
        cid = re.findall(ptn_cid, bi_url)[0]
        ord = re.findall(ptn_order, bi_url)
        if not ord:
            ord = "0"
        else:
            ord = ord[0]
        bi_url = "https://api.bilibili.com/x/space/channel/video?mid=%s&cid=%s&order=%s" % (mid, cid, ord)
        req_bi = requests.get(bi_url).json()
        items_bi = req_bi['data']['list']['archives']
    else:
        html_bi = requests.get(bi_url).text
        bs_bi = BeautifulSoup(html_bi, "lxml")
        items_bi = bs_bi.findAll("option")

    with open('./results/%s.csv' % PL_NAME, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(('title_yt', 'yt_vid', 'yt_url', 'title_yk', 'yk_vid', 'yk_url', 'title_bi', 'bi_vid', 'bi_url'))
        for item_yt, item_yk, item_bi in zip(items_yt, items_yk, items_bi):
            v_url_yt = item_yt['href']
            v_url_yk = item_yk['href']
            if "cid" in bi_url:
                v_url_bi = "https://www.bilibili.com/video/av%i/" % item_bi['aid']
                v_id_bi = item_bi['aid']
                title_bi = item_bi['title'].strip()
            else:
                v_url_bi = "https://www.bilibili.com" + item_bi["value"]
                aid = re.findall(r"av(\d+)/", item_bi['value'])[0]
                page = re.findall(r"index_(\d+)\.html", item_bi['value'])[0]
                v_id_bi = aid + "&page=" + page
                title_bi = item_bi.get_text().strip()

            ptn_yt = re.compile('^/watch\?v=(.{11})')
            ptn_yk = re.compile('^//v\.youku\.com/v_show/id_(.{15})==\.html')

            match_yt = re.match(ptn_yt, v_url_yt)
            match_yk = re.match(ptn_yk, v_url_yk)

            v_id_yt = match_yt.group(1)
            v_id_yk = match_yk.group(1)

            v_url_yt = "https://www.youtube.com" + match_yt.group(0)
            v_url_yk = "http:" + match_yk.group(0)

            title_yt = item_yt.get_text().strip()
            title_yk = item_yk['title'].strip()

            title_yt = title_yt.replace("#", "").replace("-", ".").replace("良晓", "")
            title_yk = title_yk.replace("#", "").replace("-", ".").replace("良晓", "")
            title_bi = title_bi.replace("#", "").replace("-", ".").replace("良晓", "")
            if "cid" not in bi_url:
                title_bi = re.findall(r"\d+、(.*)", title_bi)[0]

            print(v_id_yt, title_yt, v_url_yt)
            print(v_id_yk, title_yk, v_url_yk)
            print(v_id_bi, title_bi, v_url_bi)

            # ('title_yt', 'yt_vid', 'yt_url', 'title_yk', 'yk_vid', 'yk_url', 'title_bi', 'bi_vid', 'bi_url')
            writer.writerow((title_yt, v_id_yt, v_url_yt, title_yk, v_id_yk, v_url_yk, title_bi, v_id_bi, v_url_bi))


def get_playlist(yt_url, yk_url):
    # youtube and youku
    html_yt = urlopen(yt_url).read()
    html_yk = urlopen(yk_url).read()

    if SHOW_TMP:
        with open('./results/t.html', 'wb') as f:
            f.write(html_yt)

    bs_yt = BeautifulSoup(html_yt, "lxml")
    bs_yk = BeautifulSoup(html_yk, "lxml")

    items_yt = bs_yt.findAll('a', {"class": "pl-video-title-link yt-uix-tile-link yt-uix-sessionlink spf-link "})
    items_yk = bs_yk.findAll("a", {"target": "video", "data-from": "2-1"})
    yk_counter = 2
    while len(items_yk) < len(items_yt):
        html_yk = urlopen(yk_url+"?page=%i" % yk_counter).read()
        bs_yk = BeautifulSoup(html_yk, "lxml")
        items_yk += bs_yk.findAll("a", {"target": "video", "data-from": "2-1"})
        yk_counter += 1

    with open('./results/%s.csv' % PL_NAME, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(('title_yt', 'yt_vid', 'yt_url', 'title_yk', 'yk_vid', 'yk_url',))
        for item_yt, item_yk in zip(items_yt, items_yk):
            v_url_yt = item_yt['href']
            v_url_yk = item_yk['href']

            ptn_yt = re.compile('^/watch\?v=(.{11})')
            ptn_yk = re.compile('^//v\.youku\.com/v_show/id_(.{15})==\.html')

            match_yt = re.match(ptn_yt, v_url_yt)
            match_yk = re.match(ptn_yk, v_url_yk)

            v_id_yt = match_yt.group(1)
            v_id_yk = match_yk.group(1)

            v_url_yt = "https://www.youtube.com" + match_yt.group(0)
            v_url_yk = "http:" + match_yk.group(0)

            title_yt = item_yt.get_text().strip()
            title_yk = item_yk['title'].strip()

            title_yt = title_yt.replace("#", "").replace("-", ".").replace("良晓", "")
            title_yk = title_yk.replace("#", "").replace("-", ".").replace("良晓", "")

            print(v_id_yt, title_yt, v_url_yt)
            print(v_id_yk, title_yk, v_url_yk)

            # ('title_yt', 'yt_vid', 'yt_url', 'title_yk', 'yk_vid', 'yk_url',)
            writer.writerow((title_yt, v_id_yt, v_url_yt, title_yk, v_id_yk, v_url_yk))


def assign_all_id(category_path, write=True):
    import os
    import pandas as pd
    os.chdir("/home/ryder/myblog")
    path = "./python/results/%s.csv" % PL_NAME
    pl_info = pd.read_csv(path)
    biids = pl_info["bi_vid"]
    ytids = pl_info["yt_vid"]
    ykids = pl_info['yk_vid']
    n_videos = len(ytids)
    for root, dirs, filenames in os.walk(category_path):
        for counter, fn in enumerate(filenames):
            with open(os.path.join(root, fn), 'r') as file:
                if counter >= n_videos-1:
                    break
                f_content = file.read()
                f_content = re.sub(r'youtube_id:[\W]*?\n', "youtube_id: %s\n" % ytids.iloc[counter], f_content)
                f_content = re.sub(r'youku_id:[\W]*?\n', "youku_id: %s\n" % ykids.iloc[counter], f_content)
                f_content = re.sub(r'bilibili_id:[\W]*?\n', "bilibili_id: %s\n" % biids.iloc[counter], f_content)

            if not write:
                print(f_content[:100])
            else:
                with open(os.path.join(root, fn), 'w') as file:
                    file.write(f_content)

def replace_id(category_path, player, write=True):
    import os
    import pandas as pd
    os.chdir("/home/ryder/myblog")
    path = "./python/results/%s.csv" % PL_NAME
    pl_info = pd.read_csv(path)

    if player == "bi":
        ids = pl_info["bi_vid"]
    elif player == "yt":
        ids = pl_info["yt_vid"]
    elif player == "yk":
        ids = pl_info['yk_vid']
    else:
        raise ValueError("player to be : 'bi', 'yt', 'yk'")
    n_videos = len(ids)

    for root, dirs, filenames in os.walk(category_path):
        for counter, fn in enumerate(filenames):
            with open(os.path.join(root, fn), 'r') as file:
                if counter >= n_videos:
                    break
                f_content = file.read()
                if player == 'yt':
                    f_content = re.sub(r'youtube_id: .*?\n', "youtube_id: %s\n" % ids.iloc[counter], f_content)
                elif player == "yk":
                    f_content = re.sub(r'youku_id:.*?\n', "youku_id: %s\n" % ids.iloc[counter], f_content)
                elif player == "bi":
                    f_content = re.sub(r'bilibili_id:.*?\n', "bilibili_id: %s\n" % ids.iloc[counter], f_content)

            if not write:
                print(f_content[:150])
            else:
                with open(os.path.join(root, fn), 'w') as file:
                    file.write(f_content)

def new_bi_id(category_path, write=True):
    import os
    import pandas as pd
    os.chdir("/home/ryder/myblog")
    path = "./python/results/%s.csv" % PL_NAME
    pl_info = pd.read_csv(path)

    ids = pl_info["bi_vid"]
    n_videos = len(ids)

    for root, dirs, filenames in os.walk(category_path):
        filenames.sort()
        for counter, fn in enumerate(filenames):
            with open(os.path.join(root, fn), 'r') as file:
                if counter >= n_videos:
                    break
                f_content = file.read()
                f_content = re.sub(r'---\n', "---\nbilibili_id: %s\n" % ids.iloc[counter], f_content, count=1)

            if not write:
                print(f_content[:400])
            else:
                with open(os.path.join(root, fn), 'w') as file:
                    file.write(f_content)


SHOW_TMP = False
PL_NAME = "selfdescipline"
CATEGORY_PATH = "./_tutorials/progress/thoughts"
WRITE_TO_FILE = False


pl_dict = {
    "thoughts": {
        "yt": "https://www.youtube.com/playlist?list=PLXO45tsB95cKaHtKLn-jat8SOGndS3MEt",
        "yk": "http://list.youku.com/albumlist/show/id_27399497",
        "bi": "http://www.bilibili.com/video/av52609663/",
    },


}


# get_all_id(yt_url=pl_dict[PL_NAME]["yt"], yk_url=pl_dict[PL_NAME]["yk"], bi_url=pl_dict[PL_NAME]["bi"],)
# get_playlist(yt_url=pl_dict[PL_NAME]["yt"], yk_url=pl_dict[PL_NAME]["yk"],)
# assign_all_id(category_path="./_tutorials/machine-learning/ML-practice", write=WRITE_TO_FILE)
# replace_id(category_path=CATEGORY_PATH, player='bi', write=WRITE_TO_FILE)
new_bi_id(category_path=CATEGORY_PATH, write=WRITE_TO_FILE)

