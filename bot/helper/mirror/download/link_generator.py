from bot import (
    UNIFIED_EMAIL,
    UNIFIED_PASS,
    GDTOT_CRYPT,
    HUBDRIVE_CRYPT,
    KATDRIVE_CRYPT,
    DRIVEFIRE_CRYPT,
    XSRF_TOKEN,
    laravel_session,
)
from bot.helper.others.bot_utils import *
from bot.helper.others.exceptions import DirectDownloadLinkException
import re
import os
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By

import base64
import cloudscraper
from lxml import etree
from urllib.parse import urlparse, parse_qs
import requests

def direct_link_generator(link: str):
    if is_gdtot_link(link):
        return gdtot(link)
    elif is_unified_link(link):
        return unified(link)
    elif is_udrive_link(link):
        return udrive(link)
    elif is_sharer_link(link):
        return sharer_pw_dl(link)
    elif is_drivehubs_link(link):
        return drivehubs(link)
    else:
        raise DirectDownloadLinkException(f'No Direct link function found for {link}')

def gdtot(url: str) -> str:
    if GDTOT_CRYPT is None:
        raise DirectDownloadLinkException("GDTOT_CRYPT env var not provided")
    client = requests.Session()
    client.cookies.update({"crypt": GDTOT_CRYPT})
    res = client.get(url)
    res = client.get(f"https://new.gdtot.nl/dld?id={url.split('/')[-1]}")
    url = re.findall(r'URL=(.*?)"', res.text)[0]
    info = {}
    info["error"] = False
    params = parse_qs(urlparse(url).query)
    if "gd" not in params or not params["gd"] or params["gd"][0] == "false":
        info["error"] = True
        if "msgx" in params:
            info["message"] = params["msgx"][0]
        else:
            info["message"] = "Invalid link"
    else:
        decoded_id = base64.b64decode(str(params["gd"][0])).decode("utf-8")
        drive_link = f"https://drive.google.com/open?id={decoded_id}"
        info["gdrive_link"] = drive_link
    if not info["error"]:
        return info["gdrive_link"]
    else:
        raise DirectDownloadLinkException(f"{info['message']}")


account = {"email": UNIFIED_EMAIL, "passwd": UNIFIED_PASS}


def account_login(client, url, email, password):
    data = {"email": email, "password": password}
    client.post(f"https://{urlparse(url).netloc}/login", data=data)


def gen_payload(data, boundary=f'{"-"*6}_'):
    data_string = ""
    for item in data:
        data_string += f"{boundary}\r\n"
        data_string += (
            f'Content-Disposition: form-data; name="{item}"\r\n\r\n{data[item]}\r\n'
        )
    data_string += f"{boundary}--\r\n"
    return data_string


def parse_infou(data):
    info = re.findall(">(.*?)<\/li>", data)
    info_parsed = {}
    for item in info:
        kv = [s.strip() for s in item.split(":", maxsplit=1)]
        info_parsed[kv[0].lower()] = kv[1]
    return info_parsed


def unified(url: str) -> str:
    if (UNIFIED_EMAIL or UNIFIED_PASS) is None:
        raise DirectDownloadLinkException(
            "UNIFIED_EMAIL and UNIFIED_PASS env vars not provided"
        )
    client = cloudscraper.create_scraper(delay=10, browser='chrome')
    client.headers.update(
        {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36"
        }
    )

    account_login(client, url, account["email"], account["passwd"])

    res = client.get(url)
    key = re.findall('"key",\s+"(.*?)"', res.text)[0]

    ddl_btn = etree.HTML(res.content).xpath("//button[@id='drc']")

    info_parsed = parse_infou(res.text)
    info_parsed["error"] = False
    info_parsed["link_type"] = "login"  # direct/login

    headers = {
        "Content-Type": f"multipart/form-data; boundary={'-'*4}_",
    }

    data = {"type": 1, "key": key, "action": "original"}

    if len(ddl_btn):
        info_parsed["link_type"] = "direct"
        data["action"] = "direct"

    while data["type"] <= 3:
        try:
            response = client.post(url, data=gen_payload(data), headers=headers).json()
            break
        except:
            data["type"] += 1

    if "url" in response:
        info_parsed["gdrive_link"] = response["url"]
    elif "error" in response and response["error"]:
        info_parsed["error"] = True
        info_parsed["error_message"] = response["message"]
    else:
        info_parsed["error"] = True
        info_parsed["error_message"] = "Something went wrong :("

    if info_parsed["error"]:
        raise DirectDownloadLinkException(f"ERROR! {info_parsed['error_message']}")

    if urlparse(url).netloc == "appdrive.info":
        flink = info_parsed["gdrive_link"]
        return flink

    elif urlparse(url).netloc == "driveapp.in":
        res = client.get(info_parsed["gdrive_link"])
        drive_link = etree.HTML(res.content).xpath("//a[contains(@class,'btn')]/@href")[
            0
        ]
        flink = drive_link
        return flink

    else:
        res = client.get(info_parsed["gdrive_link"])
        drive_link = etree.HTML(res.content).xpath(
            "//a[contains(@class,'btn btn-primary')]/@href"
        )[0]
        flink = drive_link
        return flink
    

def parse_info(res, url):
    info_parsed = {}
    if 'drivebuzz' in url:
        info_chunks = re.findall('<td\salign="right">(.*?)<\/td>', res.text)
    elif 'sharer.pw' in url:
        f = re.findall(">(.*?)<\/td>", res.text)
        info_parsed = {}
        for i in range(0, len(f), 3):
            info_parsed[f[i].lower().replace(" ", "_")] = f[i + 2]
        return info_parsed
    else:
        info_chunks = re.findall(">(.*?)<\/td>", res.text)
    for i in range(0, len(info_chunks), 2):
        info_parsed[info_chunks[i]] = info_chunks[i + 1]
    return info_parsed


def udrive(url: str) -> str:
    if 'katdrive' or 'hubdrive' in url:
        client = requests.Session()
    else:
        client = cloudscraper.create_scraper(delay=10, browser='chrome')
        
    if "hubdrive" in url:
        if "hubdrive.in" in url:
            url = url.replace(".in",".pro")
        client.cookies.update({"crypt": HUBDRIVE_CRYPT})
    if "drivehub" in url:
        client.cookies.update({"crypt": KATDRIVE_CRYPT})
    if "katdrive" in url:
        client.cookies.update({"crypt": KATDRIVE_CRYPT})
    if "kolop" in url:
        client.cookies.update({"crypt": KATDRIVE_CRYPT})
    if "drivefire" in url:
        client.cookies.update({"crypt": DRIVEFIRE_CRYPT})
    if "drivebuzz" in url:
        client.cookies.update({"crypt": DRIVEFIRE_CRYPT})
    res = client.get(url)
    info_parsed = parse_info(res, url)
    info_parsed["error"] = False

    up = urlparse(url)
    req_url = f"{up.scheme}://{up.netloc}/ajax.php?ajax=download"

    file_id = url.split("/")[-1]

    data = {"id": file_id}

    headers = {"x-requested-with": "XMLHttpRequest"}

    try:
        res = client.post(req_url, headers=headers, data=data).json()["file"]
    except:
        raise DirectDownloadLinkException(
            "ERROR! File Not Found or User rate exceeded !!"
        )

    if 'drivefire' in url:
        decoded_id = res.rsplit('/', 1)[-1]
        flink = f"https://drive.google.com/file/d/{decoded_id}"
        return flink
    elif 'drivehub' in url:
        gd_id = res.rsplit("=", 1)[-1]
        flink = f"https://drive.google.com/open?id={gd_id}"
        return flink
    elif 'drivebuzz' in url:
        gd_id = res.rsplit("=", 1)[-1]
        flink = f"https://drive.google.com/open?id={gd_id}"
        return flink
    else:
        gd_id = re.findall('gd=(.*)', res, re.DOTALL)[0]

    info_parsed["gdrive_url"] = f"https://drive.google.com/open?id={gd_id}"
    info_parsed["src_url"] = url
    flink = info_parsed['gdrive_url']

    return flink
    


def sharer_pw_dl(url, forced_login=False):
    
    client = cloudscraper.create_scraper(delay=10, browser="chrome")
    
    client.cookies.update(
        {"XSRF-TOKEN": XSRF_TOKEN, "laravel_session": laravel_session}
    )

    res = client.get(url)
    token = re.findall("token\s=\s'(.*?)'", res.text, re.DOTALL)[0]

    ddl_btn = etree.HTML(res.content).xpath("//button[@id='btndirect']")

    info_parsed = parse_info(res, url)
    info_parsed["error"] = True
    info_parsed["src_url"] = url
    info_parsed["link_type"] = "login"  # direct/login
    info_parsed["forced_login"] = forced_login

    headers = {
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "x-requested-with": "XMLHttpRequest",
    }

    data = {"_token": token}

    if len(ddl_btn):
        info_parsed["link_type"] = "direct"
    if not forced_login:
        data["nl"] = 1

    try:
        res = client.post(url + "/dl", headers=headers, data=data).json()
    except:
        return info_parsed

    if "url" in res and res["url"]:
        info_parsed["error"] = False
        info_parsed["gdrive_link"] = res["url"]

    if len(ddl_btn) and not forced_login and not "url" in info_parsed:
        # retry download via login
        return sharer_pw_dl(url, forced_login=True)

    try:
        flink = info_parsed["gdrive_link"]
        return flink
    except:
        raise DirectDownloadLinkException(
            "ERROR! File Not Found or User rate exceeded !!"
        )
        
def drivehubs(url: str) -> str:
    os.chmod('/usr/src/app/chromedriver', 755)
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    wd = webdriver.Chrome('/usr/src/app/chromedriver', chrome_options=chrome_options)
    
    Ok = wd.get(url)
    wd.find_element(By.XPATH, '//button[@id="fast"]').click()
    sleep(10)
    wd.switch_to.window(wd.window_handles[-1])
    flink = wd.current_url
    wd.close()
    
    if 'drive.google.com' in flink:
      return flink
    else:
      raise DirectDownloadLinkException(f"ERROR! Maybe Direct Download is not working for this file !\n Retrived URL : {flink}")
