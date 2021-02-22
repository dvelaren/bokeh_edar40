import pandas as pd
from functools import reduce
from parser_edar40.common.constants import DATE_COLUMN_NAME
from datetime import date, timedelta, datetime

# Flatten list function
def flatten(A):
    rt = []
    for i in A:
        if isinstance(i,list): rt.extend(flatten(i))
        else: rt.append(i)
    return rt

# Define function to create vars mask df
def create_vars_mask_df(column_names, vars):
    df = pd.DataFrame(vars.items(), columns=column_names)
    return df

# Define function to create meteo df
def create_meteo_df(units,
                    year_folders,
                    year_months,
                    column_names,
                    in_data_file_dir,
                    data_file_names):
    # Create units dataframe
    units_df = pd.DataFrame([units], columns=list(units.keys()))
    units_df['Fecha'] = pd.to_datetime(units_df['Fecha'])
    units_df.set_index('Fecha',inplace=True)
    
    # Initialize dataframe full (this will hold all the data)
    df_full = pd.DataFrame()

    # Start looking at respective files to be parsed depending on year and month
    for year in year_folders:
        for month in year_months[year]:
            df_list = []
            for col in column_names:
                df = pd.read_csv(f'{in_data_file_dir}/{year}/{month}/{data_file_names[col]}', 
                                sep=';',encoding='latin_1', usecols=['AÑO','MES','DIA']+column_names[col],
                                parse_dates={'Fecha':['AÑO','MES','DIA']})
                df['Fecha'] = pd.to_datetime(df['Fecha'])
                df.set_index('Fecha',inplace=True)
                df[column_names[col]] = df[column_names[col]].astype('float')
                df_list.append(df)
            df_tot = reduce(lambda df1,df2: pd.merge(df1,df2,on='Fecha',how='inner'), df_list)
            df_full=df_full.append(df_tot, sort=False)

    # Reset index of df_full in order to add units row
    df_full=df_full.reset_index()

    # Concatenate units row at the beginning of dataframe full
    df_full = pd.concat([units_df, df_full], ignore_index=True, axis=0, sort=False)
    df_full['Fecha'] = pd.to_datetime(df_full['Fecha'])

    df_full.set_index('Fecha', inplace=True)
    
    return df_full

def create_meteo_live_df(
    meteo_period2_file_name,
    meteo_period2_sheet_name,
    meteo_live_file_name,
    live_file_column_names,
    live_file_sheet_name):

    # Obtain latest version of PERIOD 2 files
    df_period_2=pd.read_excel(meteo_period2_file_name)
    df_period_2.set_index('Fecha', inplace=True)

    ## Check for new live data ##
    last_timestamp = df_period_2.index[-1].to_pydatetime().date() # Obtain last stored timestamp
    today = datetime.now().date() # Obtain today timestamp
    remaining_timestamps = pd.date_range(start=last_timestamp+timedelta(days=1), end=today, freq='d') # Compute remaining days to be compleated with live file

    # Flatten column names of the list
    col_names_flat = flatten(live_file_column_names.values())

    # Obtain latest meteo live file
    df_meteo_live = pd.read_excel(meteo_live_file_name,
                              usecols=['Fecha']+col_names_flat,
                              parse_dates=['Fecha'],
                              sheet_name=live_file_sheet_name)
    df_meteo_live = df_meteo_live.dropna()
    df_meteo_live.set_index('Fecha', inplace=True)

    # Convert METEO_LIVE units to destiny units
    df_meteo_live_units = df_meteo_live.copy()
    df_meteo_live_units[live_file_column_names['P24']] = df_meteo_live[live_file_column_names['P24']] * 10 # Convert precipitation [cm -> mm]
    df_meteo_live_units[live_file_column_names['TMED']] = df_meteo_live[live_file_column_names['TMED']] * 10 # Convert temperature [°C -> (1/10)°C]
    df_meteo_live_units[live_file_column_names['PRES']] = df_meteo_live[live_file_column_names['PRES']] * 100 # Convert pressure [kPa -> hPa]

    # Build dataframe with remaining timestamps
    df_new_data = df_meteo_live_units.loc[df_meteo_live_units.index.intersection(remaining_timestamps)]

    # Add new data to PERIOD_2
    df_period_2 = df_period_2.append(df_new_data)
    df_period_2.to_excel(meteo_period2_file_name, sheet_name=meteo_period2_sheet_name)
    
    return df_period_2

# Define auxiliary function for creating partial DF according to variables to be read from COMPLETE DF
def Create_Partial_DF(variables_file_name,
                      variables_sheet_name,
                      vars_ORIGEN_col_name,
                      vars_DESTINO_col_name,
                      df_COMPLETE,
                      original_vars_list_COMPLETE,
                      blnRename_columns,
                      blnConsider_UNITS):

    # Local variables
    columns_with_all_NaNs_list = []
    columns_with_all_NaNs_msg = ""
    columns_not_found_in_original_list = []
    columns_not_found_msg = ""
    
    # 1.2 Open file specifiying variables to be read from sheet variables_sheet_name (HEADER position does not need to be specified bacause it is 0)
    df_vars = pd.read_excel(io=variables_file_name, sheet_name=variables_sheet_name)
    
    # Now, get Sheet ID, influent DATA
    df_vars_ORIGEN_col_names = df_vars[vars_ORIGEN_col_name].dropna().values
    df_PARTIAL = df_COMPLETE.loc[:, df_vars_ORIGEN_col_names]
    
    # IMPORTANT: run the following cheks:
    # CHECK 1: Check if there has been any errors when pasrsing the data:
    # A typical error consists of misswritting some letter of a column name, which trigers a warning
    # ans returns all NaN values. We will check that.
    #
    # CHECK 2: Check if all columns ara in the original list of columns.
    for col in df_PARTIAL.columns:
        
        # CHECK 1
        if (df_PARTIAL[col].isnull().sum()== len(df_PARTIAL[col])):
            
            # Add column to list of columns with all NaNs
            columns_with_all_NaNs_list.append(col)
            
            # Create and print a message
            if (columns_with_all_NaNs_msg == ""):
                # Message initialisation:
                columns_with_all_NaNs_msg = "¡¡¡WARNING!!!: Las siguientes columnas tienen todos los valores a NaN"
            
            # Add name of column with all NaNs to message
            columns_with_all_NaNs_msg = columns_with_all_NaNs_msg + "; " + col

        # CHECK 2
        if not (col in original_vars_list_COMPLETE):
            # Add column to list of columns not found
            columns_not_found_in_original_list.append(col)
            
            # Create and print a message
            if (columns_not_found_msg == ""):
                # Message initialisation:
                columns_not_found_msg = "¡¡¡WARNING!!!: Las siguientes columnas no aparecen en la lista de variables del archivo Excel de datos ORIGEN"
            
            # Add name of column not found to message
            columns_not_found_msg = columns_not_found_msg + "; " + col

    # Print message, if columns with all NaNs exist
    if (columns_with_all_NaNs_msg != ""):
        print (columns_with_all_NaNs_msg)

    # Print message, if not found columns exist
    if (columns_not_found_msg != ""):
        print (columns_not_found_msg)

    # Rename colum names, if requested
    if (blnRename_columns==True):
        df_vars_DESTINO_col_names = df_vars[vars_DESTINO_col_name].values
        for i in range(0, len(df_vars_ORIGEN_col_names)):
            df_PARTIAL.rename(columns={df_vars_ORIGEN_col_names[i]: df_vars_DESTINO_col_names[i]}, inplace=True)

    # VERY IMPORTANT: before returning the dataframe, convert all values to numeric
    # IMPORTANT:
    # 1. As we do not need to change to numeric column DATE_COLUMN_NAME, use a temporary variable
    # 2. As we do not need to change to numeric row with information about UNITS, use a temporary variable
    temp_df_PARTIAl_Date_Column = df_PARTIAL[DATE_COLUMN_NAME]
    if (blnConsider_UNITS==True):
        temp_df_UNITS = df_PARTIAL.iloc[0].values
        
    
    # Convert values to numeric
    df_PARTIAL = df_PARTIAL.apply(pd.to_numeric, errors='coerce')
    
    # Recover column DATE_COLUMN_NAME abd row with information about UNITS
    df_PARTIAL[DATE_COLUMN_NAME] = temp_df_PARTIAl_Date_Column
    if (blnConsider_UNITS==True):
        df_PARTIAL.loc[0, :] = temp_df_UNITS
    
    # Return partial datafrme, list of problematic columns and list of columns not found
    return df_PARTIAL, columns_with_all_NaNs_list, columns_not_found_in_original_list