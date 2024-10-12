#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import numpy as np
import pandas as pd
import pathlib
import math


# 
# <br>
# This module checks duplicate records in the data from the R-script (IKEA_NSA_target_matching_2018_2022_v2.R). The input data covers one year (from 2018-2022) <br>
# and each dataset contains company emissions and targets which are divided into four profile. Companies can be included in multiple profiles, and therefore<br>
# a choice has to be made which row is selected for the final analysis (in AmbitionPathways_script.py)<br>
# â€¢	Profile 1 companies reported only 1 target in a single year<br>
# â€¢	Profile 2 companies are companies with multiple sequential targets, but which refer to the same defined scope of emissions<br>
# â€¢	Profile 3 companies are companies that have multiple targets that cover different emission scopes (i.e. a Scope 1 emissions target for 2030 and a Scope 2 emissions target for 2035) --> NOT INCLUDED<br>
# â€¢	Profile 4 companies are those companies which do not fit in any of the previously defined profiles and for which one scope and target year combination is prioritized<br>
# 

# In[ ]:


dir_data_str = 'data/2023'
dir_data = pathlib.Path(dir_data_str)


# init parameters

# In[ ]:


years = [2018, 2019, 2020, 2021, 2022]
#years = [2021]
profiles = [1, 2, 4]


# In[ ]:


col_select_1_4 = ['account_id', 'scope', 'simple_scope', 'base_year', 'emissions_base_year', 'emissions_base_year_percent', 'target_year', 'target_id', 'target_status']
col_select_2 = ['account_id', 'scope', 'simple_scope', 'base_year', 'emissions_base_year', 'emissions_base_year_percent', 
                'target_year_1', 'target_id_1', 'target_status_1', 
                'target_year_2', 'target_id_2', 'target_status_2', 
                'target_year_3', 'target_id_3', 'target_status_3', 
                'target_year_4', 'target_id_4', 'target_status_4', 
                'target_year_5', 'target_id_5', 'target_status_5']
rename_columns_1_4 = {'target_year':'target_year_1', 'target_id':'target_id_1', 'target_status':'target_status_1',
                      'targeted_reduction':'targeted_reduction_1', 'SBTi_status': 'SBTi_status_1', 'please_explain': 'please_explain_1', 'percent_achieved':'percent_achieved_1', 
                      'emissions_target_year':'emissions_target_year_1', 'emissions_reporting_year':'emissions_reporting_year_1', 'target_ambition':'target_ambition_1'}


# In[ ]:


simple_scopes = set()
scopes = set()


# In[ ]:


simple_scopes_priority = {'S1S2': 9, 'S1S2S3': 8, 'S1':  7, 'S1S3': 6, 'S2': 5, 'S2S3': 4}


# In[ ]:


z = np.array([0])


# In[ ]:


def main():
    ProcessDuplicates()


# In[ ]:


def determine_score(profile, full_scope, short_scope, emissions_base_year_percent, base_year, nr_targets=1):
    '''
    Determines the score needed for selection of duplicates
    0. profile 2 gets priority, then profile 1 and finally profile 4 (profile 3 is not yet included)
    1. simple_scope: S1S2 preferred over S1, S2 or S1S2S3, S1S3, S2S3
    2. location prefered over market
    3. number of targets
    4. largest emissions_base_year_percent
    5. most recent base year is preffered
    score is 10*[1]+1*[2]
    '''
    # 0. profile 2 has highest priority, then scope 1 and 4
    match profile:
        case 2:
            id1 = 9
        case 1:
            id1 = 8
        case 4:
            id1 = 7
        case _:
            id1 = 0
    
    # 1. process simple scope based on priority given by simple_scopes_priority
    # value between 1 and 9
    id2 = 0
    try:
        id2 = simple_scopes_priority[short_scope]
    except:
        print("scope ", short_scope, " does not exist")
        id2 = 9
    
    # 2. process location/market charachteristic
    # value between 1 and 4
    if "location" in full_scope:
        id3 = 9
    elif "market" in full_scope:
        id3 = 8
    elif full_scope == "Scope 1":
        id3 = 7
    else:
        print(f"No market or location can be determined from ", full_scope)
        id3 = 0
    
    # 3. nr of targets
    # value (until now) not higher than 7
    if nr_targets < 1 or nr_targets > 9:
        print(f"The number of targets (profile {profile}) is not between 1 and 9, adjust data or code")
        id4 = 9
    else:
        id4 = 10-int(nr_targets)

    # 4. coverage BY emissions
    # TO DO 100 results in 10, must result in 9
    id5 = math.floor((9/10)*emissions_base_year_percent/10)
    
    # 5. base year
    #used for score after the decimail point
    id6 = base_year/2030

    # calculate total score
    id = pow(10,4)*id1 + pow(10,3)*id2 + pow(10,2)*id3 + pow(10,1)*id4 + pow(10,0)*id5 + id6
    #print(f'id1: {id1}, id2: {id2}, id3: {id3}, id4: {id4}, id5: {id5}, id6: {id6}, id: {id}')
    
    return id


# In[ ]:


def ProcessDuplicates():
    '''
    For each year and profile dataset, duplicates are identified, and one is selected (based on scoring algorithm)
    Duplicates can exist within and between profiles of one specific year
    Then for each year, the different profiles are combined
    '''
    # First check the different values for scopes
    print("Checking if scopes in data are already defined")
    for y in years:
        print(y)
        df_profiles = pd.DataFrame(columns=col_select_2)
        # concat profiles to one dataset for a specific year
        # and check scopes in data 
        for p in profiles:
                # read in excel file with profiles (CDP data)
                filenamedata = f'IKEA_NSA_abs_er_{y}_prof{p}_vF.xlsx'
                print(filenamedata)
                data = dir_data / 'input' / filenamedata
                df_data = pd.read_excel(data)
                # check scopes
                scopes_profile = pd.unique(df_data['scope'])
                simple_scopes_profile = pd.unique(df_data['simple_scope'])
                for x1 in scopes_profile:
                    scopes.add(x1)
                for x2 in simple_scopes_profile:
                    simple_scopes.add(x2)
                # selected needed columns and add to total dataframe
                if p in (1,4):
                    #df_data_selection = df_data[col_select_1_4].copy()
                    df_data_selection=df_data.copy()
                    df_data_selection.rename(rename_columns_1_4, axis='columns', inplace=True)
                    df_data_selection['profile'] = p
                else:
                    #df_data_selection = df_data[col_select_2].copy()
                    df_data_selection=df_data.copy()
                    df_data_selection['profile'] = p
                df_profiles = pd.concat([df_profiles, df_data_selection])
        df_profiles_filename = 'df_profile_'+str(y)+'.csv'
        df_profiles_file = dir_data / 'processed/check' / df_profiles_filename 
        df_profiles.to_csv(df_profiles_file, sep=';')
    
        print("Scopes: ", scopes, "\n")
        print("Simple scopes: ", simple_scopes, "\n")
        
        for x in simple_scopes:
            if x in simple_scopes_priority.keys():
                print(f"OK {x}, ' in known list of simple scopes")
            else:
                print(f"CHECK {x} is not known yet, check data or add to definitions in code")
        print("\n")

        # Identify duplicates and select the most preferred one
        # 1. per profile
        # 2. do companies appear in multiple profiles? 
        '''
        I. Add selection identifier
            0. profile
            1. simple_scope: S1S2 preferred over S1, S2 or S1S2S3, S1S3, S2S3
            2. location prefered over market
            3. largest emissions_base_year_percent
        II. Sort on identifier
        III. Use duplicated function
        ''' 
        # 1. determine and process duplicates for each profile
        maskdata=df_profiles.duplicated('account_id', keep=False)
        # save to csv file
        tmp = df_profiles[maskdata].sort_values(by=['account_id'])
        tmp.to_csv(f'{dir_data}/processed/check/duplicates_profile_{y}.csv', sep=';')
        df_profiles_duplicates = (
            df_profiles[maskdata]
            #.loc[:, col_select_2+['profile']]
            .set_index('account_id')
            .sort_values(by=['account_id'])
            .assign(nr_targets=lambda x: 
                    (x['target_year_1']/x['target_year_1']).fillna(0) +
                    (x['target_year_2']/x['target_year_2']).fillna(0) +
                    (x['target_year_3']/x['target_year_3']).fillna(0) +
                    (x['target_year_4']/x['target_year_4']).fillna(0) +
                    (x['target_year_5']/x['target_year_5']).fillna(0)
                    )
        )
        if df_profiles_duplicates.empty:
            df_profiles_duplicates['score'] = 9
        else:
            df_profiles_duplicates['score']=df_profiles_duplicates.apply(lambda x: determine_score(x['profile'], 
                                                                                                   x['scope'], 
                                                                                                   x['simple_scope'], 
                                                                                                   x['emissions_base_year_percent'], 
                                                                                                   x['base_year'],
                                                                                                   x['nr_targets']), axis=1)
        # save duplicates to csv        
        df_profiles_duplicates['score'] = df_profiles_duplicates['score'].map('{:,}'.format)
        df_profiles_duplicates.sort_index(inplace=True)                                                                                                      
        filename = 'duplicates_profiles_criteria_'+str(y)+'.csv'
        output_file = dir_data / 'processed/check' / filename
        df_profiles_duplicates['avg_rank']=df_profiles_duplicates.groupby('account_id')['score'].rank(method='average', ascending=False)
        df_profiles_duplicates['min_rank']=df_profiles_duplicates.groupby('account_id')['score'].rank(method='min', ascending=False)
        df_profiles_duplicates['max_rank']=df_profiles_duplicates.groupby('account_id')['score'].rank(method='max', ascending=False)
        df_profiles_duplicates['rank']=df_profiles_duplicates.groupby('account_id')['score'].rank(method='first', ascending=False)
        df_profiles_duplicates.to_csv(output_file, sep=';')
        df_duplicates = df_profiles_duplicates[df_profiles_duplicates['rank']>1.5]
        filename = 'duplicates_removed_'+str(y)+'.csv'
        output_file = dir_data / 'processed/check' / filename
        df_duplicates.to_csv(output_file, sep=';')
        
        df_profiles_duplicates_nochoice = df_profiles_duplicates[df_profiles_duplicates['rank']==1.5]
        filename = 'duplicates_nochoice_'+str(y)+'.csv'
        output_file = dir_data / 'processed/check' / filename
        df_profiles_duplicates_nochoice.to_csv(output_file, sep=';')
        df_duplicates = df_profiles_duplicates[df_profiles_duplicates['rank']==1].reset_index()
        filename = 'duplicates_'+str(y)+'.csv'
        output_file = dir_data / 'processed/check' / filename
        df_duplicates.to_csv(output_file, sep=';')

        # process duplicates in original CDP input data (df_profiles)
        # 1. remove records for which duplicates exist
        # 1.a check which files in original are duplicates and only keep non-duplicartes
        df_duplicates_tmp = df_duplicates['account_id']
        df = pd.merge(df_profiles, df_duplicates_tmp, on=['account_id'], how='outer', indicator=True)
        df_right = df[df['_merge']=='right_only']
        df_left = df[df['_merge']=='left_only']
        df_both = df[df['_merge']=='both']
        df_left.to_csv(f'{dir_data}/processed/check/check_left_{y}.csv', sep=';')
        df_both.to_csv(f'{dir_data}/processed/check/check_both_{y}.csv', sep=';')
        # check on inconsistencies
        df_right.to_csv(f'{dir_data}/processed/check/check_right_{y}.csv', sep=';')
        cnt_right=len(df_right['account_id'])
        if (cnt_right>0):
            print(f"For year {y} some records appear both in the dataframe without duplicates and the duplicates dataframe")    

        #1.b combine original without duplicates and processed duplicates (df_duplicates)
        df_final = pd.concat([df_left, df_duplicates], axis=0)
        df_final.columns = df_final.columns.str.rstrip('_x') 
        cnt_left=len(df_left['account_id'])
        cnt_duplicates=len(df_duplicates['organization'])
        cnt_final=len(df_final['organization'])
        print(f"Number of rows: {cnt_left} in non-duplicates, {cnt_duplicates} in duplicates, and {cnt_final} in final dataframe")
        df_final.to_excel(f'{dir_data}/processed/IKEA_NSA_abs_er_{y}_vF.xlsx', sheet_name='Sheet 1', index=False)
        # 2. add processed duplicates that only include one occurence (df_profiles_duplicates_keep)


# In[ ]:


if __name__ == '__main__':
      main()
      

