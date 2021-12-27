import logging
from logging import handlers
import sys
import time
import string
import json
import csv
import requests
from bs4 import BeautifulSoup
import pandas as pd

from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox import options
from selenium.webdriver.firefox.options import Options
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chromium.options import ChromiumOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, RemoteDriverServerException


class StudyIndia:
    def __init__(self) -> None:
        # Logger stuff
        self.log = logging.getLogger(f"my_logger")
        self.log.setLevel(logging.INFO)
        format = logging.Formatter("[%(asctime)s][%(levelname)s]: %(message)s")

        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(format)

        fh = handlers.RotatingFileHandler('progress.log')
        fh.setFormatter(format)
        fh.setLevel(logging.WARNING)

        self.log.addHandler(fh)
        self.log.addHandler(ch)

    def __del__(self) -> None:
        try:
            self.driver.close()
        except:
            pass

    def load_json_file(self, filename) -> dict:
        data = {}
        with open(filename, 'r') as rf:
            data = json.load(rf)
        return data

    def save_json_file(self, filename, data: dict):
        with open(filename, 'w') as wf:
            json.dump(data, wf)

    def get_links(self):
        options = Options()
        options.headless = False
        self.driver = webdriver.Firefox(
            options=options, executable_path='./geckodriver')
        # self.driver.maximize_window()
        for letter in list(string.ascii_uppercase):
            self.log.info(f"Doing: {letter}")
            self.driver.get(
                f'http://www.studyguideindia.com/Colleges/default.asp?cat={letter}')
            time.sleep(3)
            xpath = '//td/a'
            links = self.load_json_file('database/links.json')
            count = 2
            while True:
                for i in range(len(self.driver.find_elements(By.XPATH, xpath))):
                    try:
                        college_url = self.driver.find_element(
                            By.XPATH, f"({xpath})[{i+1}]").get_attribute("href")
                        links[college_url] = 0
                    except:
                        pass

                self.save_json_file('database/links.json', links)
                try:
                    element = self.driver.find_element(By.LINK_TEXT, 'Next>>')
                    self.driver.execute_script(
                        "arguments[0].click();", element)
                    time.sleep(5)
                    self.log.info(f"[{letter}]Clicked page: {count}")
                    count += 1
                except Exception as e:
                    # print(e)
                    self.log.info("Couldn't click next page.")
                    break

    def extract_details(self, url,count,length):
        response = requests.get(url)
        self.log.info(f"{count}/{length} {response.status_code} {response.reason}")
        if response.status_code != 200:
            if response.status_code == 404:
                pass
            else:
                self.log.info("Sleeping for 60 seconds.")
                time.sleep(60)
            raise TimeoutError
        soup = BeautifulSoup(response.content,'html.parser')
        # print(soup.prettify)
        rows = soup.find('div',{'id':'college_details-new'}).div.table.tbody.find_all('tr')
        data = {
            'url': url
        }
        for row in rows:
            key = row.find_all('td')[0].text.strip()
            value = row.find_all('td')[1].text.strip()
            data[key] = value

        # print(data)
        return data
        # self.driver.get(url)
        # xpath = "(//div[@id='college_details-new']//table)[1]//td"
        # odd = True
        # key = 'temp'
        # data = {'url': url}
        # for i in range(len(self.driver.find_elements(By.XPATH, xpath))):
        #     if odd:
        #         key = self.driver.find_element(
        #             By.XPATH, f"({xpath})[{i+1}]").text.strip()
        #         odd = False
        #     else:
        #         data[key] = self.driver.find_element(
        #             By.XPATH, f"({xpath})[{i+1}]").text.strip()
        #         odd = True

        # return data

    def save_to_csv(self,data):
        keys = ['url', 'College Name', 'Type of Institution', 'Category', 'Address', 'Phone', 'Fax', 'Website', 'Approved By', 'E-Mail', 'Affiliated to', 'Sub Type of Institution']
        row = []
        for key in keys:
            if key in data:
                row.append(data[key])
            else:
                row.append(None)

        with open('database/colleges.csv','a',encoding='utf-8-sig') as wf:
            writer = csv.writer(wf)
            writer.writerow(row)

    def query_colleges(self):
        colleges = self.load_json_file('database/links.json')
        # options = Options()
        # options.headless = True
        # self.driver = webdriver.Firefox(
        #     options=options, executable_path='./geckodriver')
        count = self.load_json_file('database/progress.json')['count']
        length = len(colleges)
        # data = self.load_json_file('database/colleges.json')
        i = 1
        not_found = self.load_json_file('database/not_found.json')
        for college in colleges.keys():
            if i < count:
                i += 1
                continue
            # self.log.info()
            try:
                data = self.extract_details(college,count,length)
                self.save_to_csv(data)
            except Exception as e:
                self.log.warning(e)
                not_found[college] = 1
                self.save_json_file('database/not_found.json',not_found)
                # self.log.info('Sleeping for 5 mins.')
                # time.sleep(60*5)
            # self.save_json_file('database/colleges.json', data)
            count += 1
            self.save_json_file('database/progress.json', {"count": count})

    def generate_csv(self):
        colleges = self.load_json_file('database/colleges.json')
        data = []
        for url in colleges.keys():
            data.append(colleges[url])

        df = pd.DataFrame(data)
        df.to_csv('database/colleges.csv')


if __name__ == '__main__':
    S = StudyIndia()
    S.query_colleges()
    # S.extract_details('http://www.studyguideindia.com/Colleges/Management-Studies/a-&-m-institute-of-management-and-technology.html')

    # S.generate_csv()
    # print(len(S.load_json_file('database/colleges.json')))
