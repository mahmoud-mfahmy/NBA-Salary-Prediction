# -*- coding: utf-8 -*-
"""
Created on Sat Dec 19 20:08:16 2020

@author: Mahmoud
"""
import pandas as pd
from bs4 import BeautifulSoup
import requests
import html5lib
from pandas.io.html import read_html
import unicodedata


# Initalize empty lists for dataframes of both stat types
traditional_stats = []
advanced_stats = []

for year in range(2012,2021):
    trad_url = f"https://www.basketball-reference.com/leagues/NBA_{year}_per_game.html" # traditional 
    adv_url = f"https://www.basketball-reference.com/leagues/NBA_{year}_advanced.html" # advanced
    trad_table = read_html(trad_url,attrs={"class":"stats_table"})[0]
    adv_table = read_html(adv_url,attrs={"class":"stats_table"})[0]
    trad_table['Date'] = year # Add year column to discern season by season
    adv_table['Date'] = year
    traditional_stats.append(trad_table)
    advanced_stats.append(adv_table)

# Initiate list of empty dataframes for salaries
salaries = []
for year in range(2012,2021):
    # Get base web page
    salary_url = f"http://www.espn.com/nba/salaries/_/year/{year}/seasontype/1" 
    page = requests.get(salary_url).text
    soup = BeautifulSoup(page,'html5lib') 
    # Get the number of pages for each year
    mydivs = soup.find("div",{"class":"page-numbers"})
    no_pages = int(mydivs.text[-2:])
    # Add dataframe of salary for 2012
    sal_table = read_html(salary_url)[0]
    sal_table['Date'] = year
    salaries.append(sal_table)
    # Loop through all the pages for each year
    for i in range(2,no_pages+1):
        next_page = f"http://www.espn.com/nba/salaries/_/year/{year}/page/{i}/seasontype/1"    
        sal_table = read_html(next_page)[0]
        sal_table['Date'] = year
        salaries.append(sal_table)

########## First, combine and clean the two stat tables ##########
        
# Join the individual years
traditional_stats_all = pd.concat(traditional_stats)
advanced_stats_all = pd.concat(advanced_stats)
# Drop empty columns that existed because of the webpage
advanced_stats_all.drop(columns=['Unnamed: 19','Unnamed: 24'], inplace=True)
# When a player is traded, they get a row for each team, so we will only keep the row for their total stats
traditional_stats_all = traditional_stats_all.drop_duplicates(subset = ['Player','Date','Age'],keep='first')
advanced_stats_all = advanced_stats_all.drop_duplicates(subset = ['Player','Date','Age'],keep='first')
# Drop some rows which are just labels
traditional_stats_all.drop(traditional_stats_all[traditional_stats_all['Rk'] == 'Rk'].index, inplace=True)
advanced_stats_all.drop(advanced_stats_all[advanced_stats_all['Rk'] == 'Rk'].index, inplace=True)
# We will do an inner join on player name, date, and pos to account for players with the same name
all_stats = pd.merge(traditional_stats_all, advanced_stats_all, 
                     on = ['Player','Date','Pos'], how='inner', suffixes=('','_y'))  
# Convert unicode symbols to ASCII
all_stats['Player'] = all_stats['Player'].apply(lambda x:u"".join([c for c in unicodedata.normalize('NFKD',x) 
                                                             if not unicodedata.combining(c)]))
# Get rid of asterisks
all_stats['Player'] = all_stats['Player'].apply(lambda x: x.split('*')[0])

########## Now clean the salary table ##########
all_salaries = pd.concat(salaries)
all_salaries.rename(columns={0:"RK",1:"Player",2:"Team",3:"Salary"}, inplace=True)
# Drop identifying rows 
all_salaries.drop(all_salaries[all_salaries['RK'] == 'RK'].index, inplace=True)
# Remove positions, only keep names
all_salaries['Player'] = all_salaries['Player'].apply(lambda x: x.split(',')[0])
all_salaries.head()


########## Merge both dataframes to get final dataset ##########
data = pd.merge(all_stats, all_salaries, 
                     on = ['Player','Date'], how='inner')