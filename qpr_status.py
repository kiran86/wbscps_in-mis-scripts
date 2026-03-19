from csv import excel
from hashlib import new
import requests
import pandas as pd
from bs4 import BeautifulSoup as bs

payload = {
    'username': 'admin',
    'pass': 'Admin@2024'
}
cookie = {'PHPSESSID': '7bb8622276757290a9ef7cf4f2b1c9ef'}
report_status = {'Submitted', 'Pending'}
# load QPR status base data
working_dir_path = input("Enter directory path for QPR status base data: ")
df_qpr_status_base = pd.read_excel(working_dir_path + "/QPR_Status_Bases.xlsx")
# drop serial column
del df_qpr_status_base["Unnamed: 0"]

# create data frame for each districts status URL
# URL for status page
STATUS_URL = 'http://wbscps.in/Home_MIS/Home/status'
with requests.Session() as s:
    r = s.post(STATUS_URL, cookies=cookie, data=payload)
root = bs(r.text, 'html.parser')
# find status table
table = root.find('table')
# read all rows
rows = table.find_all('tr')
# get column headers
headers = [elm.string for elm in rows[1].find_all('th')]
# get column values
values = []
for row in rows[2:]:
    table_cols = row.find_all('td')
    cols = [table_cols[1].string.strip(), table_cols[2].a.get('href')]
    values.append(cols)
# create data frame
df_districts = pd.DataFrame(values, columns=headers[1:])

df_dist_status = pd.DataFrame()
dist_status = []
index = 0
for REQUEST_URL in df_districts['Check Status']:
    with requests.Session() as s:
        r = s.post(REQUEST_URL, cookies=cookie, data=payload)
    root = bs(r.text, 'html.parser')
    # find data upload status table
    table = root.find('table')
    # read all rows
    rows = table.find_all('tr')
    # get column values
    tab_status = []
    for row in rows[2:]:
        table_cols = row.find_all('td')
        tab_status.append(table_cols[2].img.get('title'))
    dist_status.append(tab_status)
    index += 1
# create data frame
df_status = pd.DataFrame(dist_status)
# merge districts and corresponding status
df_dist_status = pd.merge(df_districts, df_status, left_index=True, right_index=True)
# remove link column
del df_dist_status["Check Status"]
# set headers from base
df_dist_status.columns = df_qpr_status_base.columns
# sort on district
df_dist_status = df_dist_status.sort_values(by="District", ignore_index=True)
# set serial to start from 1
df_dist_status.index += 1
# set data from base and readable format
for r in range(0,df_dist_status.index.size):
    for c in range(1,df_dist_status.columns.size):
        if str(df_dist_status.iloc[r, c]) == "Active":
            df_dist_status.iloc[r, c] = "\u2714"
        elif str(df_dist_status.iloc[r, c]) == "Not active" and df_qpr_status_base.iloc[r, c] == 1:
            df_dist_status.iloc[r, c] = "\u274c"
        else:
            df_dist_status.iloc[r, c] = "NA"
# write to excel file
df_dist_status.to_excel(working_dir_path + "/QPR_Status.xlsx")
