#!/usr/bin/env python
# coding: utf-8

# <h1> Step 1: Cleaning & combining </h1>

# In[27]:


def company_import_cleaning(year, mry): ## Parameters for mry: 'mry_interpolate', 'mry_standard'
    import numpy as np
    import pandas as pd
    from scipy.interpolate import interp1d
    
    pd.set_option('mode.chained_assignment', None)
    
    dir_data = 'data/2023'

    target = pd.read_excel(r''+dir_data+'/processed/IKEA_NSA_abs_er_'+year+'_vF.xlsx', sheet_name='Sheet 1')
    inventory = pd.read_excel(r''+dir_data+'/input/IKEA_NSA_'+year+'_BY_MRY_s3_perc.xlsx', sheet_name='Sheet 1') 
    
    if (year == '2018') | (year == '2019') | (year == '2020'):
        target = target[(target['emissions_base_year_percent'] >= 75) & (target['target_year_1'] >= target['base_year'])]
        target.dropna(subset=['emissions_base_year', 'base_year', 'targeted_reduction_1', 'percent_achieved_1', 'target_year_1'], inplace=True)
        target.reset_index(drop=True, inplace=True)
        
        for i in range(len(target)):
                target.loc[i, 'emissions_target_year_1'] = target.loc[i, 'emissions_base_year'] - (target.loc[i, 'emissions_base_year']*(target.loc[i, 'targeted_reduction_1']/100)) 
                target.loc[i, 'emissions_target_year_2'] = target.loc[i, 'emissions_base_year'] - (target.loc[i, 'emissions_base_year']*(target.loc[i, 'targeted_reduction_2']/100)) 
                target.loc[i, 'emissions_target_year_3'] = target.loc[i, 'emissions_base_year'] - (target.loc[i, 'emissions_base_year']*(target.loc[i, 'targeted_reduction_3']/100)) 
                target.loc[i, 'emissions_target_year_4'] = target.loc[i, 'emissions_base_year'] - (target.loc[i, 'emissions_base_year']*(target.loc[i, 'targeted_reduction_4']/100)) 
                target.loc[i, 'emissions_target_year_5'] = target.loc[i, 'emissions_base_year'] - (target.loc[i, 'emissions_base_year']*(target.loc[i, 'targeted_reduction_5']/100))
                target.loc[i, 'emissions_reporting_year_1'] = target.loc[i, 'emissions_base_year'] - ((target.loc[i, 'emissions_base_year'] * (target.loc[i, 'targeted_reduction_1']/100)) * (target.loc[i, 'percent_achieved_1']/100))
            
                
    elif (year != '2018' or year != '2019' or year != '2020'):
        target = target[(target['emissions_base_year_percent'] >= 75) & (target['target_year_1'] >= target['base_year'])]
        target.dropna(subset=['emissions_base_year', 'base_year', 'targeted_reduction_1', 'percent_achieved_1', 'target_year_1'], inplace=True)
        target.reset_index(drop=True, inplace=True)
        
        ## !! No additional calculations needed. Emissions in target year(s) and in reporting years were already calculated in the data received by CDP 
    
    for i, row in target.iterrows():
        targets_number = target.loc[i, ['targeted_reduction_1', 'targeted_reduction_2', 'targeted_reduction_3', 'targeted_reduction_4', 'targeted_reduction_5']].count()
        target.loc[i, 'nr_targets'] = targets_number
        
                               
    inventory['by_start_dt_s1'] = pd.to_datetime(inventory['by_start_dt_s1'], infer_datetime_format=True, errors='coerce')
    inventory['by_end_dt_s1'] = pd.to_datetime(inventory['by_end_dt_s1'],  infer_datetime_format=True, errors='coerce')
    inventory['by_start_dt_s2l'] = pd.to_datetime(inventory['by_start_dt_s2l'],  infer_datetime_format=True, errors='coerce')           
    inventory['by_end_dt_s2l'] = pd.to_datetime(inventory['by_end_dt_s2l'],  infer_datetime_format=True, errors='coerce')
    inventory['by_start_dt_s2m'] = pd.to_datetime(inventory['by_start_dt_s2m'],  infer_datetime_format=True, errors='coerce')
    inventory['by_end_dt_s2m'] = pd.to_datetime(inventory['by_end_dt_s2m'],  infer_datetime_format=True, errors='coerce')
    clean_inventory = inventory[~((inventory['by_emissions_s1'].isna() == True) & (inventory['by_emissions_s2l'].isna() == True) & (inventory['by_emissions_s2m'].isna() == True)) & 
          ~((inventory['mry_emissions_s1'].isna() == True) & (inventory['mry_emissions_s2l'].isna() == True) & (inventory['mry_emissions_s2m'].isna() == True)) &
                     ~((inventory['mry_start_dt'].isna() == True) | (inventory['mry_end_dt'].isna() == True))]
    clean_inventory[['by_emissions_s1', 'by_emissions_s2l', 'by_emissions_s2m', 'mry_emissions_s1', 'mry_emissions_s2l', 'mry_emissions_s2m']] = clean_inventory[['by_emissions_s1', 'by_emissions_s2l', 'by_emissions_s2m', 'mry_emissions_s1', 'mry_emissions_s2l', 'mry_emissions_s2m']].fillna(0)
                               
    combine1 = target.merge(clean_inventory, how='inner', on='account_id', suffixes=('_target','_inventory'))
    
    market_filter = (combine1['scope'].str.contains('market', case=False, na=False))
    location_filter = (combine1['scope'].str.contains('location', case=False, na=False))
    upstream_filter = (combine1['scope'].str.contains('upstream', case=False, na=False))
    downstream_filter = (combine1['scope'].str.contains('downstream', case=False, na=False))
    combine1['scope2_type'] = ''
    combine1['scope3_type'] = ''
    combine1.loc[market_filter, ['scope2_type']] = 'Market'
    combine1.loc[location_filter, ['scope2_type']] = 'Location'
    combine1.loc[~(market_filter | location_filter), ['scope2_type']] = 'NA'
    combine1.loc[upstream_filter, ['scope3_type']] = 'Upstream'
    combine1.loc[downstream_filter, ['scope3_type']] = 'Downstream'
    combine1.loc[~(upstream_filter | downstream_filter), ['scope3_type']] = 'NA'
    
    def sum_inventory_by_em(row):
          if row['scope2_type'] == 'Market':
            # return row['by_emissions_s1'] + row['by_emissions_s2m']
            ## Adjusted to remove overlap by assuming default 10% of scope 2 emissions overlap with the Scope 1 + Scope 2 total
            return (row['by_emissions_s1'] + row['by_emissions_s2m']) - (0.1 * row['by_emissions_s2m'])
          elif row['scope2_type'] == 'Location':
            # return row['by_emissions_s1'] + row['by_emissions_s2l']
            ## Adjusted to remove overlap by assuming default 10% of scope 2 emissions overlap with the Scope 1 + Scope 2 total
            return (row['by_emissions_s1'] + row['by_emissions_s2l']) - (0.1 * row['by_emissions_s2l'])
          else:
            return row['by_emissions_s1']
    
    def sum_inventory_mry_em(row):
          if row['scope2_type'] == 'Market':
            # return row['mry_emissions_s1'] + row['mry_emissions_s2m']
            ## Adjusted to remove overlap by assuming default 10% of scope 2 emissions overlap with the Scope 1 + Scope 2 total
            return (row['mry_emissions_s1'] + row['mry_emissions_s2m']) - (0.1 * row['mry_emissions_s2m'])
          elif row['scope2_type'] == 'Location':
            # return row['mry_emissions_s1'] + row['mry_emissions_s2l']
            ## Adjusted to remove overlap by assuming default 10% of scope 2 emissions overlap with the Scope 1 + Scope 2 total
            return (row['mry_emissions_s1'] + row['mry_emissions_s2l']) - (0.1 * row['mry_emissions_s2l'])
          else:
            return row['mry_emissions_s1']
    
    # Adjust inventory for target coverage (=emissions_base_year_percent)
    combine1['by_em_inventory'] = combine1.apply(sum_inventory_by_em, axis=1)*(combine1['emissions_base_year_percent']/100)
    
    combine1['reporting_year'] = combine1['mry_end_dt'].dt.strftime('%Y-%m-%d').str[:4]
    combine1['reporting_year'] = pd.to_numeric(combine1['reporting_year'], errors='coerce')
    
    combine1['ty1_em_inventory'] = combine1['by_em_inventory'] - (combine1['by_em_inventory']*(combine1['targeted_reduction_1']/100))
    
    
    ## Set parameter to be able to interpolate the mry emissions using by and ty emissions in place of the standard calculation based on the sum of reported mry emissions
    if mry == 'mry_interpolate':
        for i, row in combine1.iterrows():
            if combine1.loc[i, 'base_year'] == combine1.loc[i, 'target_year_1']:
                ## If base year and target year are equal, linear interpolation formula will not work as it will return 0/nan
                ## So if base year = target year, apply the standard formula to calculate mry inventory emissions
                combine1.loc[i, 'mry_em_inventory'] = sum_inventory_mry_em(row) * (combine1.loc[i, 'emissions_base_year_percent']/100)
                ## Emissions_reporting_year_1 from target data is left alone as calculation already performed in target data import
            else:
                ## Interpolate mry emissions for inventory data
#                 i_x = [combine1.loc[i, 'base_year'], combine1.loc[i, 'target_year_1']]
#                 i_y = [combine1.loc[i, 'by_em_inventory'], combine1.loc[i, 'ty1_em_inventory']]
                
#                 # interp_ix = combine1.loc[i, 'reporting_year']
#                 interp_ix = int(year)
                
#                 inventory_interp = interp1d(i_x, i_y, kind='linear', bounds_error=False, fill_value='extrapolate')
                
#                 combine1.loc[i, 'mry_em_inventory'] = inventory_interp(interp_ix)
                
#                 ## Interpolate mry emissions for target data
#                 t_x = [combine1.loc[i, 'base_year'], combine1.loc[i, 'target_year_1']]
#                 t_y = [combine1.loc[i, 'emissions_base_year'], combine1.loc[i, 'emissions_target_year_1']]
                
#                 # interp_tx = combine1.loc[i, 'reporting_year']
#                 interp_tx = int(year)
                
#                 target_interp = interp1d(t_x, t_y, kind='linear', bounds_error=False, fill_value='extrapolate')
                
#                 combine1.loc[i, 'emissions_reporting_year_1'] = target_interp(interp_tx)
                
                def linear_interpolation(x1, y1, x2, y2, x):
                    # Calculate the slope
                    slope = (y2 - y1) / (x2 - x1)

                    # Calculate the y value using the slope
                    y = y1 + slope * (x - x1)

                    return y

                x1, x2 = combine1.loc[i, 'base_year'], combine1.loc[i, 'target_year_1']
                y1_i, y2_i = combine1.loc[i, 'by_em_inventory'], combine1.loc[i, 'ty1_em_inventory']
                y1_t, y2_t = combine1.loc[i, 'emissions_base_year'], combine1.loc[i, 'emissions_target_year_1']
                x_i = int(year)
                x_t = int(year)

                interpolated_i = linear_interpolation(x1, y1_i, x2, y2_i, x_i)
                interpolated_t = linear_interpolation(x1, y1_t, x2, y2_t, x_t)
                
                combine1.loc[i, 'mry_em_inventory'] = interpolated_i
                
                combine1.loc[i, 'emissions_reporting_year_1'] = interpolated_t

                
    elif mry == 'mry_standard':
        ## Apply standard calculation for inventory mry emissions
        combine1['mry_em_inventory'] = combine1.apply(sum_inventory_mry_em, axis=1)*(combine1['emissions_base_year_percent']/100)
        ## Standard calculation for target data mry emissions already applied in target data import

    
        
    return combine1


# <h1> Step 2: Choosing data with regression </h1>

# In[46]:


def target_inventory_regression(frame): ## 'profile' was previously included as an additional parameter
    import numpy as np
    import pandas as pd
    from sklearn.linear_model import LinearRegression
    
    pd.set_option('mode.chained_assignment', None)
    
    dir_data = 'data/2023'
    
    for i in range(len(frame)):
        # if (((frame.at[i, 'emissions_base_year'] - frame.at[i, 'by_em_inventory'])/frame.at[i, 'by_em_inventory'])*100) < 10:
        ## updated percentage change formual to this: https://www.omnicalculator.com/math/percentage-difference
        if (abs(frame.at[i, 'emissions_base_year'] - frame.at[i, 'by_em_inventory'])/(((frame.at[i, 'by_em_inventory']+frame.at[i, 'emissions_base_year'])/2)))*100 < 10:
            frame.at[i, 'by_em_final'] = frame.at[i, 'by_em_inventory']
            frame.at[i, 'mry_em_final'] = frame.at[i, 'mry_em_inventory']
            frame.at[i, 'ty1_em_final'] = frame.at[i, 'ty1_em_inventory']
            frame.at[i, 'ty2_em_final'] = frame.at[i, 'by_em_final'] - (frame.at[i, 'by_em_final'] * (frame.at[i, 'targeted_reduction_2']/100))
            frame.at[i, 'ty3_em_final'] = frame.at[i, 'by_em_final'] - (frame.at[i, 'by_em_final'] * (frame.at[i, 'targeted_reduction_3']/100))
            frame.at[i, 'ty4_em_final'] = frame.at[i, 'by_em_final'] - (frame.at[i, 'by_em_final'] * (frame.at[i, 'targeted_reduction_4']/100))
            frame.at[i, 'ty5_em_final'] = frame.at[i, 'by_em_final'] - (frame.at[i, 'by_em_final'] * (frame.at[i, 'targeted_reduction_5']/100))
            frame.at[i, 'selected'] = 'Inventory'
        elif (frame.at[i, 'by_end_dt_s1'] != frame.at[i, 'by_end_dt_s2l']) | (frame.at[i, 'by_end_dt_s1'] != frame.at[i, 'by_end_dt_s2m']):
            frame.at[i, 'by_em_final'] = frame.at[i, 'emissions_base_year']
            frame.at[i, 'mry_em_final'] = frame.at[i, 'emissions_reporting_year_1']
            frame.at[i, 'ty1_em_final'] = frame.at[i, 'emissions_target_year_1']
            frame.at[i, 'ty2_em_final'] = frame.at[i, 'emissions_target_year_2']
            frame.at[i, 'ty3_em_final'] = frame.at[i, 'emissions_target_year_3']
            frame.at[i, 'ty4_em_final'] = frame.at[i, 'emissions_target_year_4']
            frame.at[i, 'ty5_em_final'] = frame.at[i, 'emissions_target_year_5']
            frame.at[i, 'selected'] = 'Target'
        else:
            x = frame.loc[i, ['base_year', 'reporting_year', 'target_year_1']].values.reshape((-1, 1))
            y_original = frame.loc[i, ['emissions_base_year', 'emissions_reporting_year_1', 'emissions_target_year_1']]
            y_inventory = frame.loc[i,['by_em_inventory', 'mry_em_inventory', 'ty1_em_inventory']]
            model_original = LinearRegression().fit(x, y_original)
            model_inventory = LinearRegression().fit(x, y_inventory)
            pred_original = model_original.predict(x)
            pred_inventory = model_inventory.predict(x)
            sumdiff_original = ((pred_original - y_original).sum())**2
            sumdiff_inventory =  ((pred_inventory - y_inventory).sum())**2
            if sumdiff_original < sumdiff_inventory:
                frame.at[i, 'by_em_final'] = frame.at[i, 'emissions_base_year']
                frame.at[i, 'mry_em_final'] = frame.at[i, 'emissions_reporting_year_1']
                frame.at[i, 'ty1_em_final'] = frame.at[i, 'emissions_target_year_1']
                frame.at[i, 'ty2_em_final'] = frame.at[i, 'emissions_target_year_2']
                frame.at[i, 'ty3_em_final'] = frame.at[i, 'emissions_target_year_3']
                frame.at[i, 'ty4_em_final'] = frame.at[i, 'emissions_target_year_4']
                frame.at[i, 'ty5_em_final'] = frame.at[i, 'emissions_target_year_5']
                frame.at[i, 'selected'] = 'Target'
            elif sumdiff_inventory < sumdiff_original:
                frame.at[i, 'by_em_final'] = frame.at[i, 'by_em_inventory']
                frame.at[i, 'mry_em_final'] = frame.at[i, 'mry_em_inventory']
                frame.at[i, 'ty1_em_final'] = frame.at[i, 'ty1_em_inventory']
                frame.at[i, 'ty2_em_final'] = frame.at[i, 'by_em_final'] - (frame.at[i, 'by_em_final'] * (frame.at[i, 'targeted_reduction_2']/100))
                frame.at[i, 'ty3_em_final'] = frame.at[i, 'by_em_final'] - (frame.at[i, 'by_em_final'] * (frame.at[i, 'targeted_reduction_3']/100))
                frame.at[i, 'ty4_em_final'] = frame.at[i, 'by_em_final'] - (frame.at[i, 'by_em_final'] * (frame.at[i, 'targeted_reduction_4']/100))
                frame.at[i, 'ty5_em_final'] = frame.at[i, 'by_em_final'] - (frame.at[i, 'by_em_final'] * (frame.at[i, 'targeted_reduction_5']/100))
                frame.at[i, 'selected'] = 'Inventory'
            else:
                frame.at[i, 'by_em_final'] = frame.at[i, 'emissions_base_year']
                frame.at[i, 'mry_em_final'] = frame.at[i, 'emissions_reporting_year_1']
                frame.at[i, 'ty1_em_final'] = frame.at[i, 'emissions_target_year_1']
                frame.at[i, 'ty2_em_final'] = frame.at[i, 'emissions_target_year_2']
                frame.at[i, 'ty3_em_final'] = frame.at[i, 'emissions_target_year_3']
                frame.at[i, 'ty4_em_final'] = frame.at[i, 'emissions_target_year_4']
                frame.at[i, 'ty5_em_final'] = frame.at[i, 'emissions_target_year_5']
                frame.at[i, 'selected'] = 'Target'
    
   
    frame = frame[(frame['reporting_year']>=frame['base_year']) & (frame['target_year_1']>=frame['reporting_year'])  & (frame['target_year_1']!=frame['base_year'])]
    # frame = frame[(frame['reporting_year']>=frame['base_year']) & (frame['target_year_1']>=year)  & (frame['target_year_1']!=frame['base_year'])]
    
    frame['target_year_2'].fillna(0, inplace=True)
    frame['target_year_3'].fillna(0, inplace=True)
    frame['target_year_4'].fillna(0, inplace=True)
    frame['target_year_5'].fillna(0, inplace=True)
    
    return frame


# <h1> Step 3: Creating Time Series with interpolation/extrapolation </h1>

# In[75]:


def time_series(selection): ## 'profile' was previously included as an additional parameter
    import numpy as np
    import pandas as pd
    from sklearn.linear_model import LinearRegression
    import useful_functions
    
    pd.set_option('mode.chained_assignment', None)
    
    dir_data = 'data/2023'
    
    
    PBL_CurrentPolicies = pd.read_excel(r''+dir_data+'/input/GP_CurPol.xlsx', sheet_name="data") 
    PBL_CurrentPolicies_GlobalEmissions=PBL_CurrentPolicies.copy()
    PBL_CurrentPolicies_GlobalEmissions = PBL_CurrentPolicies[(PBL_CurrentPolicies['Region']=="World") & (PBL_CurrentPolicies['Variable']=="Emissions|Kyoto Gases")]
    annual_change_PBL_IMAGE=float(PBL_CurrentPolicies_GlobalEmissions['2030']/PBL_CurrentPolicies_GlobalEmissions['2020'])**(1/(1-(2030-2020)))-1

    years = list(range(1990,2051))
    
    for i, row in selection.iterrows():
        if (selection.loc[i, 'profile'] == 1) | (selection.loc[i, 'profile'] == 4):
            selection['ty1_em_final'].where(~(selection['target_status_1']=='expired'), other=selection['mry_em_final'], inplace=True)
            selection['target_year_1'].where(~(selection['target_status_1']=='expired'), other=selection['reporting_year'], inplace=True)
            # for i, row in selection.iterrows():
            reported_zero_timestep_BY=False
            reported_zero_timestep_MRY=False
            #print('Index', i, '; a=', row['account_id'])
            extrapolation='PBL_IMAGE' #'constant', 'MRY_TY_growth', 'BY_TY_growth'
            last_milestone="1990" #'1990', 'BY', 'MRY', 'TY'
            t_BY=int(selection.loc[i, 'base_year'])
            t_MRY=int(selection.loc[i, 'reporting_year'])
            t_TY=int(selection.loc[i, 'target_year_1'])
            EM_BY=selection.loc[i,'by_em_final']
            EM_MRY=selection.loc[i,'mry_em_final']
            EM_TY=selection.loc[i, 'ty1_em_final']
            if (extrapolation=='constant'):
                annual_change=0
            elif (extrapolation=='MRY_TY_growth'):
                if (EM_MRY>0 & t_TY-t_MRY>0):
                    annual_change=(EM_TY/EM_MRY)**(1/(t_TY-t_MRY))-1
                else:
                    0
            elif(extrapolation=='BY_TY_growth'):
                if (EM_MRY>0 & t_TY-t_BY>0):
                    annual_change=(EM_TY/EM_BY)**(1/(t_TY-t_BY))-1
                else:
                    0
            elif(extrapolation=='PBL_IMAGE'):
                annual_change=annual_change_PBL_IMAGE
            else:
                # print("Unkown extrapolation method\n")
                annual_change=-1
            selection.loc[i, 'annual_change'] = annual_change

            for t in years:
                if last_milestone == "TY":
                    selection.loc[i,t] = selection.loc[i, t-1]*(1+annual_change)
                if last_milestone == "MRY":
                    if (t == selection.loc[i,'target_year_1']):
                        selection.loc[i,t] = selection.loc[i, 'ty1_em_final']
                        last_milestone = "TY"
                    else:
                        if (selection.loc[i, 'target_year_1']-selection.loc[i, 'reporting_year']) > 0:
                            selection.loc[i,t] = useful_functions.Interpolate(t, 
                                                            selection.loc[i, 'reporting_year'], 
                                                            selection.loc[i, 'target_year_1'],
                                                            selection.loc[i, 'mry_em_final'], 
                                                            selection.loc[i, 'ty1_em_final'])
                        elif reported_zero_timestep_MRY==False:
                            # print(str(combined_selection.loc[i, 'account_id'])+": division by zero\n") 
                            reported_zero_timestep_MRY=True 
                        else:
                            pass
                elif last_milestone == "BY":
                    if (t == selection.loc[i,'reporting_year']):                    
                        if (selection.loc[i, 'target_year_1'] == selection.loc[i, 'reporting_year']): # MRY and TY same year
                            selection.loc[i,t] = selection.loc[i, 'emissions_target_year_1']
                            last_milestone = "TY"
                        else:
                            selection.loc[i,t] = selection.loc[i, 'mry_em_final']
                            last_milestone = "MRY" 
                    else:
                        if (selection.loc[i, 'reporting_year']-selection.loc[i, 'base_year']) > 0:
                            selection.loc[i,t] = useful_functions.Interpolate(t, 
                                                            selection.loc[i, 'base_year'], 
                                                            selection.loc[i, 'reporting_year'],
                                                            selection.loc[i, 'by_em_final'], 
                                                            selection.loc[i, 'mry_em_final'])
                        elif reported_zero_timestep_BY==False:
                            # print(str(combined_selection.loc[i, 'account_id'])+": division by zero\n")
                            reported_zero_timestep_BY=True
                        else:
                            pass
                elif last_milestone == "1990":
                    if (t == selection.loc[i,'base_year']):                      
                        if (selection.loc[i, 'reporting_year'] == selection.loc[i, 'base_year']): # BY and MRY same year
                            selection.loc[i,t] = selection.loc[i, 'mry_em_final']
                            last_milestone = "MRY"
                        else:
                            selection.loc[i,t] = selection.loc[i, 'by_em_final']
                            last_milestone = "BY"
                    else:
                        selection.loc[i,t] = None
        elif (selection.loc[i, 'profile'] == 2):
            selection['ty1_em_final'].where(~(selection['target_status_1']=='expired'), other=selection['mry_em_final'], inplace=True)
            selection['target_year_1'].where(~(selection['target_status_1']=='expired'), other=selection['reporting_year'], inplace=True)
            selection['ty2_em_final'].where(~(selection['target_status_2']=='expired'), other=selection['mry_em_final'], inplace=True)
            selection['target_year_2'].where(~(selection['target_status_2']=='expired'), other=selection['reporting_year'], inplace=True)
            selection['ty3_em_final'].where(~(selection['target_status_3']=='expired'), other=selection['mry_em_final'], inplace=True)
            selection['target_year_3'].where(~(selection['target_status_3']=='expired'), other=selection['reporting_year'], inplace=True)
            selection['ty4_em_final'].where(~(selection['target_status_4']=='expired'), other=selection['mry_em_final'], inplace=True)
            selection['target_year_4'].where(~(selection['target_status_4']=='expired'), other=selection['reporting_year'], inplace=True)
            selection['ty5_em_final'].where(~(selection['target_status_5']=='expired'), other=selection['mry_em_final'], inplace=True)
            selection['target_year_5'].where(~(selection['target_status_5']=='expired'), other=selection['reporting_year'], inplace=True)
                # tmp = selection.copy()
            # for i, row in selection.iterrows():
            reported_zero_timestep_BY=False
            reported_zero_timestep_MRY=False
            #print('Index', i, '; a=', row['account_id'])
            extrapolation= 'PBL_IMAGE'
            last_milestone="1990" #'1990', 'BY', 'MRY', 'TY_1', 'TY_2', 'TY_3', 'TY_4', 'TY_5'
            t_BY=int(selection.loc[i, 'base_year'])
            t_MRY=int(selection.loc[i, 'reporting_year'])
            t_TY_1=int(selection.loc[i, 'target_year_1'])
            t_TY_2=int(selection.loc[i, 'target_year_2'])
            t_TY_3=int(selection.loc[i, 'target_year_3'])
            t_TY_4=int(selection.loc[i, 'target_year_4'])
            t_TY_5=int(selection.loc[i, 'target_year_5'])
            EM_BY=selection.loc[i,'by_em_final']
            EM_MRY=selection.loc[i,'mry_em_final']
            EM_TY_1=selection.loc[i, 'ty1_em_final']
            EM_TY_2=selection.loc[i, 'ty2_em_final']
            EM_TY_3=selection.loc[i, 'ty3_em_final']
            EM_TY_4=selection.loc[i, 'ty4_em_final']
            EM_TY_5=selection.loc[i, 'ty5_em_final']

            if (extrapolation=='constant'):
                annual_change=0
            elif (extrapolation=='MRY_TY_growth'):
                if (EM_MRY>0 & t_TY-t_MRY>0):
                    annual_change=(EM_TY/EM_MRY)**(1/(t_TY-t_MRY))-1
                else:
                    0
            elif(extrapolation=='BY_TY_growth'):
                if (EM_BY>0 & t_TY-t_BY>0): 
                    annual_change=(EM_TY/EM_BY)**(1/(t_TY-t_BY))-1
                else:
                    0
            elif(extrapolation=='PBL_IMAGE'):
                annual_change=annual_change_PBL_IMAGE
            else:
                print("Unkown extrapolation method\n")
                annual_change=-1
            if (i==1): 
                print("Annual change is: ", annual_change)
            selection.loc[i, 'annual_change'] = annual_change

            for t in years:
                if last_milestone == "TY_5":
                    selection.loc[i,t] = selection.loc[i, t-1]*(1+annual_change)
                if last_milestone == "TY_4":
                    if selection.loc[i,'target_year_5']==0: # if target year is NA or zero, extrapolate
                        selection.loc[i,t] = selection.loc[i, t-1]*(1+annual_change)
                    elif (t == selection.loc[i,'target_year_5']): # milestone reached, so in next step go to new target
                        selection.loc[i,t] = selection.loc[i, 'ty5_em_final']
                        last_milestone = "TY_5" ## How to change this?
                    else:
                        if (selection.loc[i, 'target_year_5']-selection.loc[i, 'target_year_4']) > 0: # interpolate if next target year is after current target year
                            selection.loc[i,t] = useful_functions.Interpolate(t, 
                                                            selection.loc[i, 'target_year_4'], 
                                                            selection.loc[i, 'target_year_5'],
                                                            selection.loc[i, 'ty4_em_final'], 
                                                            selection.loc[i, 'ty5_em_final'])
                        elif reported_zero_timestep_MRY==False:
                            # Target year appears twice in dataset (assumption: does not appear three time)
                            # print(str(selection.loc[i, 'account_id'])+": division by zero at last milestone TY_4\n") 
                            #selection.loc[i,t] = max(selection.loc[i, 'emissions_target_year_4'], selection.loc[i, 'emissions_target_year_5'])
                            #last_milestone = "TY_5"
                            reported_zero_timestep_MRY=True 
                        else:
                            pass
                if last_milestone == "TY_3":
                    if selection.loc[i,'target_year_4']==0: # if target year is NA or zero, extrapolate
                        selection.loc[i,t] = selection.loc[i, t-1]*(1+annual_change)
                    elif (t == selection.loc[i,'target_year_4']): # milestone reached, so in next step go to new target
                        if (selection.loc[i, 'target_year_4']==selection.loc[i, 'target_year_5']):
                            selection.loc[i,t] = min(selection.loc[i, 'ty4_em_final'], selection.loc[i, 'ty5_em_final'])
                            last_milestone = "TY_5"
                        else:
                            selection.loc[i,t] = selection.loc[i, 'ty4_em_final']
                        last_milestone = "TY_4"
                    else:
                        if (selection.loc[i, 'target_year_4']-selection.loc[i, 'target_year_3']) > 0: # interpolate if next target year is after current target year
                            selection.loc[i,t] = useful_functions.Interpolate(t, 
                                                            selection.loc[i, 'target_year_3'], 
                                                            selection.loc[i, 'target_year_4'],
                                                            selection.loc[i, 'ty3_em_final'], 
                                                            selection.loc[i, 'ty4_em_final'])
                        elif reported_zero_timestep_MRY==False:
                            # Target year appears twice in dataset (assumption: does not appear three time)
                            # print(str(selection.loc[i, 'account_id'])+": division by zero at last milestone TY_3\n") 
                            #selection.loc[i,t] = max(selection.loc[i, 'emissions_target_year_3'], selection.loc[i, 'emissions_target_year_4'])
                            #last_milestone = "TY_4"
                            reported_zero_timestep_MRY=True 
                        else:
                            pass
                if last_milestone == "TY_2":
                    if selection.loc[i,'target_year_3']==0: # if target year is NA or zero, extrapolate
                        selection.loc[i,t] = selection.loc[i, t-1]*(1+annual_change)
                    elif (t == selection.loc[i,'target_year_3']): # milestone reached, so in next step go to new target
                        if (selection.loc[i, 'target_year_3']==selection.loc[i, 'target_year_4']):
                            selection.loc[i,t] = min(selection.loc[i, 'ty3_em_final'], selection.loc[i, 'ty4_em_final'])
                            last_milestone = "TY_4"
                        else:
                            selection.loc[i,t] = selection.loc[i, 'ty3_em_final']
                        last_milestone = "TY_4"
                    else:
                        if (selection.loc[i, 'target_year_3']-selection.loc[i, 'target_year_2']) > 0: # interpolate if next target year is after current target year
                            selection.loc[i,t] = useful_functions.Interpolate(t, 
                                                            selection.loc[i, 'target_year_2'], 
                                                            selection.loc[i, 'target_year_3'],
                                                            selection.loc[i, 'ty2_em_final'], 
                                                            selection.loc[i, 'ty3_em_final'])
                        elif reported_zero_timestep_MRY==False:
                            # Target year appears twice in dataset (assumption: does not appear three time)
                            # print(str(selection.loc[i, 'account_id'])+": division by zero  at last milestone TY_2\n") 
                            #selection.loc[i,t] = max(selection.loc[i, 'emissions_target_year_2'], selection.loc[i, 'emissions_target_year_3'])
                            #last_milestone = "TY_3"
                            reported_zero_timestep_MRY=True 
                        else:
                            pass
                if last_milestone == "TY_1":
                    if (t == selection.loc[i,'target_year_2']): # milestone reached, so in next step go to new target
                        if (selection.loc[i, 'target_year_2']==selection.loc[i, 'target_year_3']):
                            selection.loc[i,t] = min(selection.loc[i, 'ty2_em_final'], selection.loc[i, 'ty3_em_final'])
                            last_milestone = "TY_3"
                        else:
                            selection.loc[i,t] = selection.loc[i, 'ty2_em_final']
                            last_milestone = "TY_2"
                    else:
                        if (selection.loc[i, 'target_year_2']-selection.loc[i, 'target_year_1']) > 0: # interpolate if next target year is after current target year
                            selection.loc[i,t] = useful_functions.Interpolate(t, 
                                                            selection.loc[i, 'target_year_1'], 
                                                            selection.loc[i, 'target_year_2'],
                                                            selection.loc[i, 'ty1_em_final'], 
                                                            selection.loc[i, 'ty2_em_final'])
                        elif reported_zero_timestep_MRY==False:
                            # Target year appears twice in dataset (assumption: does not appear three time)
                            # print(str(selection.loc[i, 'account_id'])+": division by zero at t: ", t, ", last milestone TY_1\n")
                            #selection.loc[i,t] = max(selection.loc[i, 'emissions_target_year_1'], selection.loc[i, 'emissions_target_year_2'])
                            #last_milestone = "TY_2"
                            reported_zero_timestep_MRY=True 
                        else:
                            pass
                if last_milestone == "MRY":
                    if (t == selection.loc[i,'target_year_1']):
                        if (selection.loc[i, 'target_year_1']==selection.loc[i, 'target_year_2']):
                            selection.loc[i,t] = min(selection.loc[i, 'ty1_em_final'], selection.loc[i, 'ty2_em_final'])
                            last_milestone = "TY_2"
                        else:
                            selection.loc[i,t] = selection.loc[i, 'ty1_em_final']
                            last_milestone = "TY_1"
                    else:
                        if (selection.loc[i, 'target_year_1']-selection.loc[i, 'reporting_year']) > 0:
                            selection.loc[i,t] = useful_functions.Interpolate(t, 
                                                            selection.loc[i, 'reporting_year'], 
                                                            selection.loc[i, 'target_year_1'],
                                                            selection.loc[i, 'mry_em_final'], 
                                                            selection.loc[i, 'ty1_em_final'])
                        elif reported_zero_timestep_MRY==False:
                            # print(str(selection.loc[i, 'account_id'])+": division by zero  at last milestone MRY\n") 
                            reported_zero_timestep_MRY=True 
                        else:
                            pass
                if last_milestone == "BY":
                    if (t == selection.loc[i,'reporting_year']):                    
                        if (selection.loc[i, 'reporting_year'] == selection.loc[i, 'target_year_2']): # MRY and TY1, TY2 same year
                            selection.loc[i,t] = min(selection.loc[i, 'mry_em_final'], selection.loc[i, 'ty1_em_final'], selection.loc[i, 'ty2_em_final'])
                            last_milestone = "TY_2"
                        elif (selection.loc[i, 'reporting_year'] == selection.loc[i, 'target_year_1']): # MRY and TY same year
                            selection.loc[i,t] = min(selection.loc[i, 'mry_em_final'], selection.loc[i, 'ty1_em_final'])
                            last_milestone = "TY_1"
                        else:
                            selection.loc[i,t] = selection.loc[i, 'mry_em_final']
                            last_milestone = "MRY" 
                    else:
                        if (selection.loc[i, 'reporting_year']-selection.loc[i, 'base_year']) > 0:
                            selection.loc[i,t] = useful_functions.Interpolate(t, 
                                                            selection.loc[i, 'base_year'], 
                                                            selection.loc[i, 'reporting_year'],
                                                            selection.loc[i, 'by_em_final'], 
                                                            selection.loc[i, 'mry_em_final'])
                        elif reported_zero_timestep_BY==False:
                            # print(str(selection.loc[i, 'account_id'])+": division by zero at last milestone BY\n")
                            reported_zero_timestep_BY=True
                        else:
                            pass
                if last_milestone == "1990":
                    if (t == selection.loc[i,'base_year']):                      
                        if (selection.loc[i, 'base_year'] == selection.loc[i, 'target_year_1']):
                            selection.loc[i,t] = min(selection.loc[i, 'by_em_final'], selection.loc[i, 'mry_em_final'], selection.loc[i, 'ty1_em_final'])
                            last_milestone = "TY_1"
                        elif (selection.loc[i, 'base_year'] == selection.loc[i, 'reporting_year']): # BY and MRY same year
                            selection.loc[i,t] = min(selection.loc[i, 'by_em_final'], selection.loc[i, 'mry_em_final'])
                            last_milestone = "MRY"
                        else:
                            selection.loc[i,t] = selection.loc[i, 'by_em_final']
                            last_milestone = "BY"
                    else:
                        selection.loc[i,t] = None
    return selection

