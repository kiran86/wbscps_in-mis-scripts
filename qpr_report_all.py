import requests
import pandas as pd
from bs4 import BeautifulSoup as bs
from tqdm import tqdm

payload = {
    'username': 'admin',
    'pass': 'Admin@1234'
}
cookie = {'PHPSESSID': '55e595625a8b5b1a77e3c2f3387dc2c5779043e9'}

BASE_URL = 'http://wbscps.in/Home_MIS/Home/dashboard/'

# get all links
with requests.Session() as s:
    r = s.post(BASE_URL, cookies=cookie, data=payload)
root = bs(r.text, 'lxml')
nav = root.header
report_tables = []
report_links = []
for url in nav.find_all('a'):
    if "table" in url.get_text('span').strip().lower():
        report_tables.append(url.get_text('span').strip())
        report_links.append(url.get('href'))

QUATER = "OCTOBER,2022---DECEMBER,2022"

### get report links ###
for i in range(len(report_links)):
    print("Processing report on " + report_tables[i])
    # page marker
    page_no = 0
    # table header
    headers = []
    # table column values
    values = []
    # loop once, for testing
    while page_no == 0:
    # loop infinitely
    #while True:
        REPORT_URL = report_links[i]
        if page_no != 0:
            REPORT_URL = report_links[i] + "/" + str(page_no) + "?"
        with requests.Session() as s:
            r = s.post(REPORT_URL, cookies=cookie, data=payload)
        root = bs(r.text, 'html.parser')
        # find status table
        table = root.find('table')
        print("Processing " + REPORT_URL + ": ")
        # if no table found, break loop
        if table is None:
            print("-----No matching data found!")
            break
        # read all rows
        rows = table.find_all('tr')
        # get column headers one time
        if len(headers) == 0:
            headers = [elm.string for elm in rows[0].find_all('th')]
            # remove extra headers
            # headers.pop(0)
            # headers.pop(1)
        # get column values
        for row in rows[1:]:
            table_cols = row.find_all('td')
            # check for quater
            if table_cols[2].string.strip() != QUATER:
                continue
            #print("-----Found data for " + table_cols[1].string + " " + table_cols[3].string)
            links = row.find_all("a", string = 'View')
            link = str(links[0].get('onclick')).split("'")[1]
            cols = [table_cols[1].string.strip(), table_cols[3].string, link]
            values.append(cols)
        page_no = page_no + 20
    n_reports = len(values)
    print("Total " + str(n_reports) + " reports found!")
    print("Generating reports...")
    ### get reports ###
    #link_i = 0
    report_cols = []
    report_data = []
    df_report_data = pd.DataFrame()
    # excel to write report
    exl_writer = pd.ExcelWriter("..//Reports/" + report_tables[i] + "_" + QUATER + ".xlsx",
                                engine='xlsxwriter',
                                engine_kwargs={'options':{'strings_to_numbers': True}})
    # get the generated excel workbook
    workbook = exl_writer.book
    # loop through each link
    for link_i in tqdm(range(0, n_reports)):
        REPORT_URL = values[link_i][2]
        report_cols.clear()
        report_data.clear()
        del df_report_data
        with requests.Session() as s:
            r = s.post(REPORT_URL, cookies=cookie, data=payload)
        # using html5lib parser because of bad html tagging
        root = bs(r.text, 'html5lib')
        # find status table
        table = root.find('table')
        # read all rows
        rows = table.find_all('tr')
        # traverse rows
        for row in rows[2:]:
            if rows.index(row) == 2:
                report_cols = [elm.string.strip() for elm in row.find_all("th")]
            else:
                report_data.append([elm.string.strip() for elm in row.find_all('td')])
        df_report_data = pd.DataFrame(report_data, columns=report_cols)
        sheet = "Sheet" + str(link_i)
        df_report_data.to_excel(exl_writer, sheet_name=sheet, index=False, startrow=2)
        # get sheet
        worksheet = exl_writer.sheets[sheet]
        # write header
        for c, s in enumerate(values[link_i][:2]):
            worksheet.write(0, c, s)
        link_i += 1
    exl_writer.close()
