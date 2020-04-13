import argparse
import json
from bs4 import BeautifulSoup
import requests
import os
import sys
import re
import pandas as pd
import numpy as np

output_file_base = 'wiki-data-'

# South Korea processing
south_korea_page = "https://en.wikipedia.org/wiki/2020_coronavirus_pandemic_in_South_Korea"

r = requests.get(south_korea_page)
soup = BeautifulSoup(r.text, 'html.parser')

# Get the stats table
table_attrs = {
    'class': ['wikitable', 'mw-collapsible',
              'float', 'mw-made-collapsible'],
    'style': 'text-align:right; font-size:80%; text-align:right;' }
try:
    stats_table = soup.find_all('table', attrs=table_attrs)[0]
except:
    raise RuntimeError("Couldn't find south korea statistics table!")

# Check that we have the right table
sk_init_title = "New COVID-19 cases reported in South Korea by region"
if stats_table.caption.text[:len(sk_init_title)] != sk_init_title:
    raise RuntimeError("Didn't find correct sk stats table!")

# Build column labels
table_rows = stats_table.find_all('tr')
column_regions = []

cells = table_rows[0].find_all('th')
for cell in cells:
    colspan = cell.get('colspan')
    if colspan is not None:
        for i in range(int(colspan)):
            column_regions += [[cell.text.strip()]]
    else:
        column_regions += [[cell.text.strip(),None]]

# Small correction
for i in range(len(column_regions)):
    if column_regions[i][0] == 'Disch.':
        column_regions[i] = ['Disch.']

# Add sub-region name
cells = table_rows[1].find_all('th')
i = 0
for cell in cells:
    while len(column_regions[i]) != 1:
        i += 1
    column_regions[i].append(cell.text.strip())
    i += 1

# Get column ranges
i_start = 0
while i_start < len(column_regions):
    if column_regions[i_start][0] != 'Report as of':
        break
    i_start += 1
i_end = i_start
while i_end < len(column_regions):
    if column_regions[i_end][0] == 'Confirmed':
        break
    i_end += 1

# Initialize pandas dataframe
sk_df = pd.DataFrame(columns = ['date', 'time', 'region', 'subregion', 'cases', 'deaths'])

is_date = re.compile('^[0-9][0-9][0-9][0-9]\-[0-9][0-9]\-[0-9][0-9]$')
cd_extract = re.compile('^\(([0-9]*)\)[^0-9]?([0-9]*)$')
ignore_ref = re.compile('^(\-?[0-9]*)\[.*\]$')
plain_val = re.compile('^(\-?[0-9]*)$')
multi_row = 0
date_text = None
time_text = None
for row in table_rows:
    process_row = False
    is_multirow = False
    cells = row.find_all('td')
    if len(cells) > 0:
        date_text_temp = cells[0].text.strip()
        if is_date.match(date_text_temp):
            # Check whether this date spans multiple rows.
            rowspan = cells[0].get('rowspan')
            if rowspan is not None:
                multirow = int(rowspan)-1
            date_text = date_text_temp
            time_text = cells[1].text.strip()
            process_row = True
        else:
            if multirow > 0:
                multirow -= 1
                time_text = cells[0].text.strip()
                process_row = True
                is_multirow = True
    if time_text == '24:00':
        time_text = '23:59'
    if process_row:
        for i in range(i_start, i_end):
            if is_multirow:
                I = i-1
            else:
                I = i
            cell_text = cells[I].text.strip().replace('−', '-')
            if cell_text != "":
                extracted = False
                if not extracted:
                    match = cd_extract.match(cell_text)
                    if match:
                        deaths = int(match.group(1))
                        if match.group(2) == '':
                            cases = 0
                        else:
                            cases = int(match.group(2))
                        extracted = True
                if not extracted:
                    match = ignore_ref.match(cell_text)
                    if match:
                        deaths = 0
                        cases = int(match.group(1))
                        extracted = True
                if not extracted:
                    match = plain_val.match(cell_text)
                    if match:
                        deaths = 0
                        cases = int(match.group(1))
                    else:
                        raise RuntimeError(f"South Korea Fall back match failed! {{{cell_text}}} {row}")
                sk_df = sk_df.append({'date':date_text,
                                      'time':time_text,
                                      'region': column_regions[i][0],
                                      'subregion': column_regions[i][1],
                                      'cases': cases,
                                      'deaths': deaths}, ignore_index=True)

# Italy processing
italy_page = "https://en.wikipedia.org/wiki/2020_coronavirus_pandemic_in_Italy"

r = requests.get(italy_page)
soup = BeautifulSoup(r.text, 'html.parser')

# Get the stats table
table_attrs = {
    'class': ['wikitable', 'mw-collapsible',
              'mw-made-collapsible'],
    'style': 'float:left; text-align:right; font-size:82%;' }
try:
    stats_table = soup.find_all('table', attrs=table_attrs)[0]
except:
    raise RuntimeError("Couldn't find italy statistics table!")

# Check that we have the right table
sk_init_title = "Daily COVID-19 cases in Italy by region"
if stats_table.caption.text[:len(sk_init_title)] != sk_init_title:
    raise RuntimeError("Didn't find correct it stats table!")

# Build column labels
table_rows = stats_table.find_all('tr')
column_regions = []

cells = table_rows[0].find_all('th')
for cell in cells:
    colspan = cell.get('colspan')
    if colspan is not None:
        for i in range(int(colspan)):
            column_regions += [[cell.text.strip()]]
    else:
        rowspan = cell.get('rowspan')
        if rowspan is not None:
            column_regions += [[cell.text.strip(),None]]
        else:
            column_regions += [[cell.text.strip()]]

# Add sub-region name
cells = table_rows[1].find_all('th')
i = 0
for cell in cells:
    while len(column_regions[i]) != 1:
        i += 1
    column_regions[i].append(cell.text.strip())
    i += 1

# Get column ranges
i_start = 0
while i_start < len(column_regions):
    if column_regions[i_start][0] != 'Date':
        break
    i_start += 1
i_end = i_start
while i_end < len(column_regions):
    if column_regions[i_end][0] == 'Confirmed':
        break
    i_end += 1

# Initialize pandas dataframe
it_df = pd.DataFrame(columns = ['date', 'region', 'subregion', 'cases', 'deaths'])

is_date = re.compile('^[0-9][0-9][0-9][0-9]\-[0-9][0-9]\-[0-9][0-9]$')
val = re.compile('^(\((\-?[0-9]*)\))?([^0-9])?(\-?[0-9]*)?$')
date_text = None

for row in table_rows:
    process_row = False
    cells = row.find_all('td')
    if len(cells) > 0:
        date_text_temp = cells[0].text.strip()
        if is_date.match(date_text_temp):
            # Check whether this date spans multiple rows.
            date_text = date_text_temp
            process_row = True
    if process_row:
        for i in range(i_start, i_end):
            cell_text = cells[i].text.strip().replace('−', '-').replace('–', '-').replace(',', '')
            if cell_text != "":
                extracted = False
                if not extracted:
                    match = val.match(cell_text)
                    if match:
                        if (match.group(4) is None) or (match.group(4) == ''):
                            cases = 0
                        else:
                            cases = int(match.group(4))
                        if (match.group(1) is None) or (match.group(2) == ''):
                            deaths = 0
                        else:
                            deaths = int(match.group(2))
                        extracted = True
                if not extracted:
                    raise RuntimeError(f"Italy Matching failed! {i} {{{cell_text}}} ({row})")

                it_df = it_df.append({'date':date_text,
                                      'region': column_regions[i][0],
                                      'subregion': column_regions[i][1],
                                      'cases': cases,
                                      'deaths': deaths}, ignore_index=True)

sk_df.to_csv(output_file_base+'sk.csv', index=False)
it_df.to_csv(output_file_base+'it.csv', index=False)
