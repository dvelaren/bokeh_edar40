# Required Libraries
import pandas as pd
import numpy as np
import time
from datetime import date, timedelta, datetime

# Constants
from parser_edar40.common.constants import *

# Settings
from parser_edar40.common.settings import *

# Helpers
from parser_edar40.helpers import create_vars_mask_df, Create_Partial_DF, create_meteo_df

def parser():
    print('Ejecutando parser')
    # 0 Create Vars ABSOLUTAS csv file
    df_abs = create_vars_mask_df(VARS_COLUMN_NAMES, VARS_NORMA_ABSOLUTAS)
    df_abs.to_csv(OUT_VARS_ABSOLUTAS_FILE_NAME, index=False, sep=';')

    # 0 Create Vars RENDIMIENTOS csv file
    df_rend = create_vars_mask_df(VARS_COLUMN_NAMES, VARS_NORMA_RENDIMIENTOS)
    df_rend.to_csv(OUT_VARS_RENDIMIENTOS_FILE_NAME, index=False, sep=';')

    # 0 We first open the Excel file
    # Measure computation time (start time).
    start_t = time.time()
    xl = pd.ExcelFile(IN_DATA_FILE_NAME)
    end_t = time.time()
    print("\nComputation time for reading COMPLETE Excel file is %g seconds.\n" %
        (end_t - start_t))

    # 1. We start processing sheet ID.
    # 1.0 Call the Excel file parsing function, specifiying SHEET NAME and HEADER in order to create main df_ID dataframe.
    df_ID = xl.parse(sheet_name=IN_DATA_SHEET_NAME_ID, header=3)

    # Next, get dataframe with UNITS information that will be used to insert later
    if (blnConsider_UNITS == True):
        df_ID_UNITS = xl.parse(sheet_name=IN_DATA_SHEET_NAME_ID, nrows=2)

    # Save units in df_ID
    if (blnConsider_UNITS == True):
        df_ID.iloc[1] = df_ID_UNITS.iloc[1].values

    # Delete rows with no data after HEADER
    if (blnConsider_UNITS == True):
        df_ID.drop(df_ID.index[[0]], inplace=True)
    else:
        df_ID.drop(df_ID.index[[0, 1]], inplace=True)

    # Reset index, if necessary:
    # + Depending on pandas' version (pd.__version__), the above main reading of the main .xslx file
    #   gives a different results:
    # + Version '0.24.0': Dataframe's Index is an autonumeric and a column of name "Unnamed: 0"
    #                     (specified in constant FIRST_UNKONW_COLUMN_NAME) is created
    #                     where the datetime information is stored.
    # + Version '0.23.4': Dataframe's Index is the column storing the datetime information.
    # + Also, if first column is called DATE_COLUMN_NAME, reset index but drop previous one.

    if ((df_ID.columns[0] != FIRST_UNKONW_COLUMN_NAME) and (df_ID.columns[0] != DATE_COLUMN_NAME)):
        df_ID.reset_index(drop=False, inplace=True)
    else:
        df_ID.reset_index(drop=True, inplace=True)

    # Rename column 0 (which has date information but a non specific column name) to DATE_COLUMN_NAME.
    df_ID.rename(columns={df_ID.columns[0]: DATE_COLUMN_NAME}, inplace=True)

    # Convert column DATE_COLUMN_NAME of df_influente to pandas timestamp format.
    df_ID[DATE_COLUMN_NAME] = pd.to_datetime(df_ID[DATE_COLUMN_NAME].astype(
        str), errors="coerce", infer_datetime_format=True)

    # IMPORTANT: make sure the information is consistent, saving all values in only date part format.
    # Otherwise, when joining different dataframes on index of type pandas datetime, if there are values in different format
    # (some only date, some date and time, although time is 00:00:00), they will be exclusive.
    df_ID[DATE_COLUMN_NAME] = df_ID[DATE_COLUMN_NAME].dt.date

    # Remove duplicates
    df_ID.drop_duplicates(subset=[DATE_COLUMN_NAME], keep='first', inplace=True)
    df_ID.reset_index(drop=True, inplace=True)

    # Create list of column names of sheet ID, if requested
    colum_names_sheet_ID_list = list(df_ID.columns)
    if (blnCreate_ID_sheet_columns_list == True):
        with open(ID_EDAR_CARTUJA_ID_sheet_column_names_FILE_NAME, 'w') as f:
            for item in colum_names_sheet_ID_list:
                f.write("%s\n" % item)

    # 1.1 Open file specifiying variables to be read from sheet ID_INFLUENTE (HEADER position does not need to be specified bacause it is 0)
    (df_ID_influente,
    columns_with_all_NaNs_list_ID_influente,
    columns_not_found_in_original_list_ID_influente) = Create_Partial_DF(VARIABLES_TO_READ_FILE_NAME,
                                                                        VARIABLES_FILE_SHEET_ID_INFLUENTE,
                                                                        VARS_ORIGEN_COL_NAME,
                                                                        VARS_DESTINO_COL_NAME,
                                                                        df_ID,
                                                                        colum_names_sheet_ID_list,
                                                                        True,
                                                                        blnConsider_UNITS)

    # Work out variables to be calculated
    # 1. SO4 entrada influente (KG SO4/dia) = SO4 entrada influente (mg SO4/l) * Caudal influente (m3/dia) / 1000
    # 2. P-PO4 entrada influente (KG PO4/dia) = P-PO4 entrada influente (mg P-PO4/l) * Caudal influente (m3/dia) / 1000
    # 3. Ratio DBO5/DQO = DBO5 entrada influente (mg DBO5/l) / DQO entrada influente (mg DQO/l)
    #
    # IMPORTANT: like in NumPy, basic arithmetic operations in Pandas (+, -, *, /, etc.) are ELEMENT-WISE.
    # IMPORTANT: make calculations for rows starting from row=1 because in row=0 UNIT  information is stored.

    if (blnConsider_UNITS == True):
        start_row = 1
    else:
        start_row = 0

    df_ID_influente.loc[start_row:, "influente_SO4"] = df_ID_influente.loc[start_row:,
                                                                        "influente_SO4_conc"] * df_ID_influente.loc[start_row:, "influente_CAUDAL"] / 1000
    df_ID_influente.loc[start_row:, "influente_P-PO4"] = df_ID_influente.loc[start_row:,
                                                                            "influente_P-PO4_conc"] * df_ID_influente.loc[start_row:, "influente_CAUDAL"] / 1000
    # df_ID_influente.loc[start_row:, "influente_ratio_DBO5t_DQOt"] = df_ID_influente.loc[start_row:,
    #                                                                                     "influente_DBO5t_conc"] / df_ID_influente.loc[start_row:, "influente_DQOt_conc"]
    df_ID_influente.loc[start_row:, "influente_ratio_DBO5t_DQOt"] = df_ID_influente.loc[start_row:, "influente_DBO5t_conc"].div(df_ID_influente.loc[start_row:, "influente_DQOt_conc"].where(df_ID_influente.loc[start_row:, "influente_DQOt_conc"]!=0,np.nan))

    # 1.2 Open file specifiying variables to be read from sheet ID_BIOS (HEADER position does not need to be specified bacause it is 0)
    (df_ID_bios,
    columns_with_all_NaNs_list_ID_bios,
    columns_not_found_in_original_list_ID_bios) = Create_Partial_DF(VARIABLES_TO_READ_FILE_NAME,
                                                                    VARIABLES_FILE_SHEET_ID_BIOS,
                                                                    VARS_ORIGEN_COL_NAME,
                                                                    VARS_DESTINO_COL_NAME,
                                                                    df_ID,
                                                                    colum_names_sheet_ID_list,
                                                                    True,
                                                                    blnConsider_UNITS)

    # Work out variables to be calculated
    # 4. Ratio DBO5/DQO entrada bios = DBO5 entrada BIOS(mg DBO5/l) / DQO entrada BIOS (mg DQO/l)
    # 5. DO ZONA 1 media BIOS = PROMEDIO (O2 Bio1 Zona 1, O2 Bio2 Zona 1, O2 Bio3 Zona 1)
    # 6. DO ZONA 2 media BIOS = PROMEDIO (O2 Bio1 Zona 2, O2 Bio2 Zona 2, O2 Bio3 Zona 2)
    #
    # IMPORTANT: like in NumPy, basic arithmetic operations in Pandas (+, -, *, /, etc.) are ELEMENT-WISE.
    # IMPORTANT: make calculations for rows starting from row=1 because in row=0 UNIT  information is stored.

    if (blnConsider_UNITS == True):
        start_row = 1
    else:
        start_row = 0

    # df_ID_bios.loc[start_row:, "bios_IN_ratio_DBO5t_DQOt"] = df_ID_bios.loc[start_row:,
    #                                                                         "bios_IN_DBO5t_conc"] / df_ID_bios.loc[start_row:, "bios_IN_DQOt_conc"]
    df_ID_bios.loc[start_row:, "bios_IN_ratio_DBO5t_DQOt"] = df_ID_bios.loc[start_row:, "bios_IN_DBO5t_conc"].div(df_ID_bios.loc[start_row:, "bios_IN_DQOt_conc"].where(df_ID_bios.loc[start_row:, "bios_IN_DQOt_conc"]!=0,np.nan))
    df_ID_bios.loc[start_row:, "bios_manipulable_O2_Promedio_Zona_1"] = (df_ID_bios.loc[start_row:, "bios_manipulable_O2_Bio1_Zona_1"] +
                                                                        df_ID_bios.loc[start_row:, "bios_manipulable_O2_Bio2_Zona_1"] +
                                                                        df_ID_bios.loc[start_row:, "bios_manipulable_O2_Bio3_Zona_1"]) / 3
    df_ID_bios.loc[start_row:, "bios_manipulable_O2_Promedio_Zona_2"] = (df_ID_bios.loc[start_row:, "bios_manipulable_O2_Bio1_Zona_2"] +
                                                                        df_ID_bios.loc[start_row:, "bios_manipulable_O2_Bio2_Zona_2"] +
                                                                        df_ID_bios.loc[start_row:, "bios_manipulable_O2_Bio3_Zona_2"]) / 3

    # 1.3 Open file specifiying variables to be read from sheet ID_FANGOS (HEADER position does not need to be specified bacause it is 0)
    (df_ID_fangos,
    columns_with_all_NaNs_list_ID_fangos,
    columns_not_found_in_original_list_ID_fangos) = Create_Partial_DF(VARIABLES_TO_READ_FILE_NAME,
                                                                    VARIABLES_FILE_SHEET_ID_FANGOS,
                                                                    VARS_ORIGEN_COL_NAME,
                                                                    VARS_DESTINO_COL_NAME,
                                                                    df_ID,
                                                                    colum_names_sheet_ID_list,
                                                                    True,
                                                                    blnConsider_UNITS)

    # 1.4 Open file specifiying variables to be read from sheet ID_HORNO (HEADER position does not need to be specified bacause it is 0)
    (df_ID_horno,
    columns_with_all_NaNs_list_ID_horno,
    columns_not_found_in_original_list_ID_horno) = Create_Partial_DF(VARIABLES_TO_READ_FILE_NAME,
                                                                    VARIABLES_FILE_SHEET_ID_HORNO,
                                                                    VARS_ORIGEN_COL_NAME,
                                                                    VARS_DESTINO_COL_NAME,
                                                                    df_ID,
                                                                    colum_names_sheet_ID_list,
                                                                    True,
                                                                    blnConsider_UNITS)

    # 1.5 Open file specifiying variables to be read from sheet ID_EFLUENTE (HEADER position does not need to be specified bacause it is 0)
    (df_ID_efluente,
    columns_with_all_NaNs_list_ID_efluente,
    columns_not_found_in_original_list_ID_efluente) = Create_Partial_DF(VARIABLES_TO_READ_FILE_NAME,
                                                                        VARIABLES_FILE_SHEET_ID_EFLUENTE,
                                                                        VARS_ORIGEN_COL_NAME,
                                                                        VARS_DESTINO_COL_NAME,
                                                                        df_ID,
                                                                        colum_names_sheet_ID_list,
                                                                        True,
                                                                        blnConsider_UNITS)

    # 1.6 Open file specifiying variables to be read from sheet ID_ELECTRICIDAD (HEADER position does not need to be specified bacause it is 0)
    (df_ID_electricidad,
    columns_with_all_NaNs_list_ID_electricidad,
    columns_not_found_in_original_list_ID_electricidad) = Create_Partial_DF(VARIABLES_TO_READ_FILE_NAME,
                                                                            VARIABLES_FILE_SHEET_ID_ELECTRICIDAD,
                                                                            VARS_ORIGEN_COL_NAME,
                                                                            VARS_DESTINO_COL_NAME,
                                                                            df_ID,
                                                                            colum_names_sheet_ID_list,
                                                                            True,
                                                                            blnConsider_UNITS)

    # Aggregate all columns with all NaN values in a unique list
    columns_with_all_NaNs_list_ID = (columns_with_all_NaNs_list_ID_influente
                                    + columns_with_all_NaNs_list_ID_bios
                                    + columns_with_all_NaNs_list_ID_fangos
                                    + columns_with_all_NaNs_list_ID_horno
                                    + columns_with_all_NaNs_list_ID_efluente
                                    + columns_with_all_NaNs_list_ID_electricidad)

    # Aggregate all columns not found in the original vars list in a unique list
    columns_not_found_in_original_list_ID = (columns_not_found_in_original_list_ID_influente
                                            + columns_not_found_in_original_list_ID_bios
                                            + columns_not_found_in_original_list_ID_fangos
                                            + columns_not_found_in_original_list_ID_horno
                                            + columns_not_found_in_original_list_ID_efluente
                                            + columns_not_found_in_original_list_ID_electricidad)

    # 1.7 Join all dataframes of interest.
    # Set as index column DATE_COLUMN_NAME on dataframes to be joined.
    df_ID_influente.set_index(keys=DATE_COLUMN_NAME,
                            drop=True, inplace=True, verify_integrity=True)
    df_ID_bios.set_index(keys=DATE_COLUMN_NAME, drop=True,
                        inplace=True, verify_integrity=True)
    df_ID_fangos.set_index(keys=DATE_COLUMN_NAME, drop=True,
                        inplace=True, verify_integrity=True)
    df_ID_horno.set_index(keys=DATE_COLUMN_NAME, drop=True,
                        inplace=True, verify_integrity=True)
    df_ID_efluente.set_index(keys=DATE_COLUMN_NAME, drop=True,
                            inplace=True, verify_integrity=True)
    df_ID_electricidad.set_index(
        keys=DATE_COLUMN_NAME, drop=True, inplace=True, verify_integrity=True)

    # Now, join the dataframes
    df_ID_out = df_ID_influente.join(
        [df_ID_bios, df_ID_fangos, df_ID_horno, df_ID_efluente, df_ID_electricidad], how="inner")

    # 2. We now process sheet YOKO
    # 2.0 Call the Excel file parsing function, specifiying SHEET NAME and HEADER in order to create main df_YOKO dataframe.
    df_YOKO = xl.parse(sheet_name=IN_DATA_SHEET_NAME_YOKO, header=4)

    # NOTE: we do need to get UNITS information in another dataframe as we do for ID and ANALITIC because in YOKO
    #       units information os below header row.

    # Delete rows with no data after HEADER
    df_YOKO.drop(df_YOKO.index[[0]], inplace=True)

    # Reset index, if necessary:
    # + Depending on pandas' version (pd.__version__), the above main reading of the main .xslx file
    #   gives a different results:
    # + Version '0.24.0': Dataframe's Index is an autonumeric and a column of name "Unnamed: 0"
    #                     (specified in constant FIRST_UNKONW_COLUMN_NAME) is created
    #                     where the datetime information is stored.
    # + Version '0.23.4': Dataframe's Index is the column storing the datetime information.
    # + Also, if first column is called DATE_COLUMN_NAME, reset index but drop previous one.

    if ((df_YOKO.columns[0] != FIRST_UNKONW_COLUMN_NAME) and (df_YOKO.columns[0] != DATE_COLUMN_NAME)):
        df_YOKO.reset_index(drop=False, inplace=True)
    else:
        df_YOKO.reset_index(drop=True, inplace=True)

    # Rename column 0 (which has date information but a non specific colun name) to DATE_COLUMN_NAME.
    df_YOKO.rename(columns={df_YOKO.columns[0]: DATE_COLUMN_NAME}, inplace=True)

    # Convert column DATE_COLUMN_NAME of df_influente to pandas timestamp format.
    df_YOKO[DATE_COLUMN_NAME] = pd.to_datetime(df_YOKO[DATE_COLUMN_NAME].astype(
        str), errors="coerce", infer_datetime_format=True)

    # IMPORTANT: make sure the information is consistent, saving all values in only date part format.
    # Otherwise, when joining different dataframes on index of type pandas datetime, if there are values in different format
    # (some only date, some date and time, although time is 00:00:00), they will be exclusive.
    df_YOKO[DATE_COLUMN_NAME] = df_YOKO[DATE_COLUMN_NAME].dt.date

    # Remove duplicates
    df_YOKO.drop_duplicates(subset=[DATE_COLUMN_NAME], keep='first', inplace=True)
    df_YOKO.reset_index(drop=True, inplace=True)

    # Create list of column names of sheet YOKO, if requested
    colum_names_sheet_YOKO_list = list(df_YOKO.columns)
    if (blnCreate_YOKO_sheet_columns_list == True):
        with open(ID_EDAR_CARTUJA_YOKO_sheet_column_names_FILE_NAME, 'w') as f:
            for item in colum_names_sheet_YOKO_list:
                f.write("%s\n" % item)

    # 2.1 Open file specifiying variables to be read from sheet YOKO (HEADER position does not need to be specified bacause it is 0)

    (df_YOKO_partial,
    columns_with_all_NaNs_list_YOKO_partial,
    columns_not_found_in_original_list_YOKO_partial) = Create_Partial_DF(VARIABLES_TO_READ_FILE_NAME,
                                                                        VARIABLES_FILE_SHEET_YOKO,
                                                                        VARS_ORIGEN_COL_NAME,
                                                                        VARS_DESTINO_COL_NAME,
                                                                        df_YOKO,
                                                                        colum_names_sheet_YOKO_list,
                                                                        True,
                                                                        blnConsider_UNITS)

    # Aggregate all columns with all NaN values in a unique list
    columns_with_all_NaNs_list_YOKO = columns_with_all_NaNs_list_YOKO_partial

    # Aggregate all columns not found in the original vars list in a unique list
    columns_not_found_in_original_list_YOKO = columns_not_found_in_original_list_YOKO_partial

    # 2.2 Join all dataframes of interest.

    # Set as index column DATE_COLUMN_NAME on dataframes to be joined.
    df_YOKO_partial.set_index(keys=DATE_COLUMN_NAME,
                            drop=True, inplace=True, verify_integrity=True)

    # Now, join the dataframes
    df_YOKO_out = df_YOKO_partial

    # 3. We now process sheet ANALITICA
    # 3.0 Call the Excel file parsing function, specifiying SHEET NAME and HEADER in order to create main df_ANALITICA dataframe.

    df_ANALITICA = xl.parse(sheet_name=IN_DATA_SHEET_NAME_ANALITICA, header=4)

    # Next, get dataframe with UNITS information that will be used to insert later
    if (blnConsider_UNITS == True):
        df_ANALITICA_UNITS = xl.parse(
            sheet_name=IN_DATA_SHEET_NAME_ANALITICA, nrows=3)

    # Save units in df_ID
    if (blnConsider_UNITS == True):
        df_ANALITICA.iloc[1] = df_ANALITICA_UNITS.iloc[2].values

    # Delete rows with no data after HEADER
    if (blnConsider_UNITS == True):
        df_ANALITICA.drop(df_ANALITICA.index[[0]], inplace=True)
    else:
        df_ANALITICA.drop(df_ANALITICA.index[[0, 1]], inplace=True)

    # Reset index, if necessary:
    # + Depending on pandas' version (pd.__version__), the above main reading of the main .xslx file
    #   gives a different results:
    # + Version '0.24.0': Dataframe's Index is an autonumeric and a column of name "Unnamed: 0"
    #                     (specified in constant FIRST_UNKONW_COLUMN_NAME) is created
    #                     where the datetime information is stored.
    # + Version '0.23.4': Dataframe's Index is the column stroing the datetime information.
    # + Also, if first column is called DATE_COLUMN_NAME, reset index but drop previous one.

    if ((df_ANALITICA.columns[0] != FIRST_UNKONW_COLUMN_NAME) and (df_ANALITICA.columns[0] != DATE_COLUMN_NAME)):
        df_ANALITICA.reset_index(drop=False, inplace=True)
    else:
        df_ANALITICA.reset_index(drop=True, inplace=True)

    # Rename column 0 (which has date information but a non specific colun name) to DATE_COLUMN_NAME.
    df_ANALITICA.rename(
        columns={df_ANALITICA.columns[0]: DATE_COLUMN_NAME}, inplace=True)

    # Convert column DATE_COLUMN_NAME of df_influente to pandas timestamp format.
    df_ANALITICA[DATE_COLUMN_NAME] = pd.to_datetime(
        df_ANALITICA[DATE_COLUMN_NAME].astype(str), errors="coerce", infer_datetime_format=True)

    # IMPORTANT: make sure the information is consistent, saving all values in only date part format.
    # Otherwise, when joining different dataframes on index of type pandas datetime, if there are values in different format
    # (some only date, some date and time, although time is 00:00:00), they will be exclusive.
    df_ANALITICA[DATE_COLUMN_NAME] = df_ANALITICA[DATE_COLUMN_NAME].dt.date

    # Remove duplicates
    df_ANALITICA.drop_duplicates(
        subset=[DATE_COLUMN_NAME], keep='first', inplace=True)
    df_ANALITICA.reset_index(drop=True, inplace=True)

    # Create list of column names of sheet ANALITICA, if requested
    colum_names_sheet_ANALITICA_list = list(df_ANALITICA.columns)
    if (blnCreate_ANALITICA_sheet_columns_list == True):
        with open(ID_EDAR_CARTUJA_ANALITICA_sheet_column_names_FILE_NAME, 'w') as f:
            for item in colum_names_sheet_ANALITICA_list:
                f.write("%s\n" % item)

    # 3.1 Open file specifiying variables to be read from sheet ANALITICA (HEADER position does not need to be specified bacause it is 0)

    (df_ANALITICA_partial,
    columns_with_all_NaNs_list_ANALITICA_partial,
    columns_not_found_in_original_list_ANALITICA_partial) = Create_Partial_DF(VARIABLES_TO_READ_FILE_NAME,
                                                                            VARIABLES_FILE_SHEET_ANALITICA,
                                                                            VARS_ORIGEN_COL_NAME,
                                                                            VARS_DESTINO_COL_NAME,
                                                                            df_ANALITICA,
                                                                            colum_names_sheet_ANALITICA_list,
                                                                            True,
                                                                            blnConsider_UNITS)

    # Aggregate all columns with all NaN values in a unique list
    columns_with_all_NaNs_list_ANALITICA = columns_with_all_NaNs_list_ANALITICA_partial

    # Aggregate all columns not found in the original vars list in a unique list
    columns_not_found_in_original_list_ANALITICA = columns_not_found_in_original_list_ANALITICA_partial

    # 3.2 Join all dataframes of interest.

    # Set as index column DATE_COLUMN_NAME on dataframes to be joined.
    df_ANALITICA_partial.set_index(
        keys=DATE_COLUMN_NAME, drop=True, inplace=True, verify_integrity=True)

    # Now, join the dataframes
    df_ANALITICA_out = df_ANALITICA_partial

    # 4 Finally, join all three partial dataframes df_ID_out, df_YOKO_out and df_ANALITICA_out, before creating the OUTPUT DATA CSV file.
    df_OUT = df_ID_out.join([df_YOKO_out, df_ANALITICA_out], how="inner")

    # Save results to OUTPUT DATA CSV file. Respect 'standard' format: ',' for separation, '.' for decimals.
    # Before that, decide whether or not filter on column Fecha.
    # If so, convert Date information from index to a normal column first.
    # NOTE: data must be filtered for the several periods, in this case PERIOD_1 and PERIOD_2.
    #       Therefore, several CSV files (in this case 2, por PERIOD_1 and PERIOD_2) will be generated.

    # PERIOD_1
    df_OUT_date_filtered_PERIOD_1 = df_OUT.copy()
    df_OUT_date_filtered_PERIOD_1.reset_index(drop=False, inplace=True)

    # Convert column DATE_COLUMN_NAME of df_OUT_date_filtered_PERIOD_1 to pandas timestamp format.
    df_OUT_date_filtered_PERIOD_1[DATE_COLUMN_NAME] = pd.to_datetime(
        df_OUT_date_filtered_PERIOD_1[DATE_COLUMN_NAME].astype(str), errors="coerce", format="%Y-%m-%d")

    # PERIOD_2
    df_OUT_date_filtered_PERIOD_2 = df_OUT.copy()
    df_OUT_date_filtered_PERIOD_2.reset_index(drop=False, inplace=True)

    # Convert column DATE_COLUMN_NAME of df_OUT_date_filtered_PERIOD_2 to pandas timestamp format.
    df_OUT_date_filtered_PERIOD_2[DATE_COLUMN_NAME] = pd.to_datetime(
        df_OUT_date_filtered_PERIOD_2[DATE_COLUMN_NAME].astype(str), errors="coerce", format="%Y-%m-%d")

    # Then, convert str_start_date_filter_PERIOD_1/2 and str_end_date_filter_PERIOD_1/2 to pandas timestamp format and filter.
    # PERIOD_1
    pd_start_date_filter_PERIOD_1 = pd.to_datetime(
        str_start_date_filter_PERIOD_1, errors="coerce", format="%Y-%m-%d")
    df_OUT_date_filtered_PERIOD_1 = df_OUT_date_filtered_PERIOD_1.loc[(
        df_OUT_date_filtered_PERIOD_1[DATE_COLUMN_NAME] > pd_start_date_filter_PERIOD_1)]

    if (blnFilter_on_start_date == True):
        # PERIOD_2
        pd_start_date_filter_PERIOD_2 = pd.to_datetime(
            str_start_date_filter_PERIOD_2, errors="coerce", format="%Y-%m-%d")
        df_OUT_date_filtered_PERIOD_2 = df_OUT_date_filtered_PERIOD_2.loc[(
            df_OUT_date_filtered_PERIOD_2[DATE_COLUMN_NAME] > pd_start_date_filter_PERIOD_2)]

    # PERIOD_1
    pd_end_date_filter_PERIOD_1 = pd.to_datetime(
        str_end_date_filter_PERIOD_1, errors="coerce", format="%Y-%m-%d")
    df_OUT_date_filtered_PERIOD_1 = df_OUT_date_filtered_PERIOD_1.loc[(
        df_OUT_date_filtered_PERIOD_1[DATE_COLUMN_NAME] <= pd_end_date_filter_PERIOD_1)]

    if (blnFilter_on_end_date == True):
        # PERIOD_2
        pd_end_date_filter_PERIOD_2 = pd.to_datetime(
            str_end_date_filter_PERIOD_2, errors="coerce", format="%Y-%m-%d")
        df_OUT_date_filtered_PERIOD_2 = df_OUT_date_filtered_PERIOD_2.loc[(
            df_OUT_date_filtered_PERIOD_2[DATE_COLUMN_NAME] <= pd_end_date_filter_PERIOD_2)]

    # Previous filtering deletes UNITS row. Therefore, it must be recovered.
    if (blnConsider_UNITS == True):
        df_OUT_date_filtered_PERIOD_1 = pd.concat(
            [df_OUT[0:1], df_OUT_date_filtered_PERIOD_1])
        df_OUT_date_filtered_PERIOD_2 = pd.concat(
            [df_OUT[0:1], df_OUT_date_filtered_PERIOD_2])


    # Now save the data to the output data file. Before that, reset the index again.
    # PERIOD_1
    df_OUT_date_filtered_PERIOD_1.set_index(
        keys=DATE_COLUMN_NAME, drop=True, inplace=True, verify_integrity=True)
    # Add new meteo columns for each period
    df_IN_METEO_PER1 = pd.read_excel(IN_METEO_FILE_NAME_PERIOD_1)
    df_IN_METEO_PER1.set_index(DATE_COLUMN_NAME, inplace=True)
    # df_OUT_date_filtered_PERIOD_1=df_OUT_date_filtered_PERIOD_1.join(df_IN_METEO_PER1)
    df_OUT_date_filtered_PERIOD_1 = pd.merge(
        df_OUT_date_filtered_PERIOD_1, df_IN_METEO_PER1, on='Fecha', how='left')
    # df_OUT_date_filtered_PERIOD_1.drop_duplicates(keep=False,inplace=True)
    df_OUT_date_filtered_PERIOD_1.to_csv(
        OUT_DATA_FILE_NAME_PERIOD_1, sep=',', encoding='latin-1', decimal='.')

    # Create Meteo PERIOD 2 files
    df_METEO = create_meteo_df(UNITS, YEAR_FOLDERS, YEAR_MONTHS,
                            COLUMN_NAMES, IN_METEO_DATA_FILE_DIR, DATA_FILE_NAMES)

    ## Check for new live data ##
    last_timestamp = df_METEO.index[-1].to_pydatetime().date() # Obtain last stored timestamp
    today = datetime.now().date() # Obtain today timestamp
    remaining_timestamps = pd.date_range(start=last_timestamp+timedelta(days=1), end=today, freq='d') # Compute remaining days to be compleated with live file

    # Obtain latest METEO_LIVE df
    df_meteo_live = pd.read_excel(IN_METEO_LIVE_FILE,
                              usecols=['day','month','year']+list(COLUMN_NAMES_METEO_LIVE.values()),
                              parse_dates={'Fecha':['year','month','day']})
    df_meteo_live.set_index('Fecha', inplace=True)

    # Convert METEO_LIVE units to destiny units
    df_meteo_live_units = df_meteo_live.copy()
    df_meteo_live_units[COLUMN_NAMES_METEO_LIVE['P24']] = df_meteo_live[COLUMN_NAMES_METEO_LIVE['P24']] * 10 # Convert precipitation [cm -> mm]
    df_meteo_live_units[COLUMN_NAMES_METEO_LIVE['TMED']] = df_meteo_live[COLUMN_NAMES_METEO_LIVE['TMED']] * 10 # Convert temperature [°C -> (1/10)°C]
    df_meteo_live_units[COLUMN_NAMES_METEO_LIVE['PRES']] = df_meteo_live[COLUMN_NAMES_METEO_LIVE['PRES']] * 100 # Convert pressure [kPa -> hPa]

    # Build dataframe with required format to add
    columns_inverted = {v: k for k, v in COLUMN_NAMES_METEO_LIVE.items()}
    df_new_data = df_meteo_live_units.loc[df_meteo_live_units.index.intersection(remaining_timestamps)].rename(columns=columns_inverted)
    df_new_data = df_new_data.assign(PRES00=df_new_data['PRES'], PRES07=df_new_data['PRES'], PRES13=df_new_data['PRES'], PRES18=df_new_data['PRES'])
    df_new_data = df_new_data.drop(['PRES'], axis=1)
    
    # Add new data to PERIOD_2
    df_METEO = df_METEO.append(df_new_data)
    df_METEO.to_excel(OUT_METEO_DATA_FILE_NAME_PERIOD_2,
                    sheet_name=METEO_SHEET_NAME_PERIOD_2)
    ## End live data ##

    # PERIOD_2
    df_OUT_date_filtered_PERIOD_2.set_index(
        keys=DATE_COLUMN_NAME, drop=True, inplace=True, verify_integrity=True)
    # Add new meteo columns for each period
    df_IN_METEO_PER2 = pd.read_excel(IN_METEO_FILE_NAME_PERIOD_2)
    df_IN_METEO_PER2.set_index(DATE_COLUMN_NAME, inplace=True)
    # df_OUT_date_filtered_PERIOD_2=df_OUT_date_filtered_PERIOD_2.join(df_IN_METEO_PER2)
    df_OUT_date_filtered_PERIOD_2 = pd.merge(
        df_OUT_date_filtered_PERIOD_2, df_IN_METEO_PER2, on='Fecha', how='left')
    # df_OUT_date_filtered_PERIOD_2.drop_duplicates(keep=False,inplace=True)
    df_OUT_date_filtered_PERIOD_2.to_csv(
        OUT_DATA_FILE_NAME_PERIOD_2, sep=',', encoding='latin-1', decimal='.')
