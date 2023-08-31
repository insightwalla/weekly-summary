import pandas as pd
import streamlit as st
st.set_page_config(layout="wide")

bartenders_type = [
    'Bartenders - Head Bartender',
    'Bartenders - Deputy Head Bartender',
    'Bartenders - Bar Shift Leader',
    'Bartenders - Barback',
    'Bartender',
]
servers_type = [
    'Server',
    'Servers - Head Server',
    'FOH - Training - Trainee Server',
]
runners_type = [
    'Food Runner',
    'Expeditor',
    'Runners - Head Runner',
    'FOH - Training - Trainee Runner'
    
]
hosts_type = [
    'Host',
    'Host - Head Host',
    'Host - Deputy Head Host',
    'FOH - Training - Trainee Host',

]
boh_type = [
    'BOH - Demi Chef de Partie',
    'BOH - Senior Chef de Partie',
    'BOH - Chef de Partie',
    'Management - BOH - Junior Sous Chef',
    'Management - BOH - Sous Chef',
    'Management - BOH - Head Chef',
    'BOH'
]
management_type = [
    'Management - FOH - General Manager',
    'Management - FOH - Assistant General Manager',
    'Management - FOH',
    'Management - FOH - Supervisor',
]
dict_map = {
    'Bartenders': bartenders_type,
    'Servers': servers_type,
    'Runners': runners_type,
    'Hosts': hosts_type,
    'BOH': boh_type,
    'Management': management_type,
}

def process_data(df):
    #st.write(df)
    unique_id = df['ID'].unique()
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    checkbox = st.sidebar.checkbox('Show Shifts data')
    # Perform this for each user
    # add a shift type for absence
    final_df = pd.DataFrame()
    final_empty_space = st.container()

    for i, id in enumerate(unique_id):
        data = df[df['ID'] == id] # filter the data for each user
        name = data['Name'].unique()[0] # get the name of the user
        departments_attributions = data['Shift type'].unique() # get the departments attributions
        departments_attributions = [x for x in departments_attributions if str(x) != 'nan'] # remove nan values 
        empty_space = st.container()
        general_dep = data['Department (attribution)'].unique()
        general_dep = [x for x in general_dep if str(x) != 'nan']
        general_dep = general_dep[0] if len(general_dep) > 0 else 'No department'
        days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        unique_shifts_type = data['Shift type'].unique()
        unique_shifts_type = [x for x in unique_shifts_type if str(x) != 'nan']
        general_shift_type = unique_shifts_type[0] if len(unique_shifts_type) > 0 else 'No shift type'
        # replace empty shift type with general shift type
        data.loc[data['Shift type'].isnull(), 'Shift type'] = general_shift_type


        shift_data = data.copy()
        # if there is a absence in the data the shift type is None, but we need to replace it with the majority department

        # case 1: employee has only one department
        if len(departments_attributions) <= 1:
            if checkbox:
                st.write(data)
            dep = departments_attributions[0] if len(departments_attributions) == 1 else general_dep
            # check that we don't have duplicates
            day_s = data['Dayname'].value_counts()
            
            if len(day_s[day_s > 1]) > 0:
                day_ = day_s[day_s > 1].index[0]
                unique_events_type = data[data['Dayname'] == day_]['Event type'].unique()
                list_unique_events_type = unique_events_type.tolist()
                is_absence = 'Absence' in unique_events_type
                data = data[data['Event type'] == 'Shift']
                # if we still have duplicates we sum the paid hours
                day_s = data['Dayname'].value_counts()
                if len(day_s[day_s > 1]) > 0:
                    double = True
                    # need first start and last finish of that day
                    start_double = data[data['Dayname'] == day_]['Start'].min()
                    end_double = data[data['Dayname'] == day_]['Finish'].max()
                    sum_paid_hours = data.groupby('Dayname')['Paid hours'].sum()
                    data = data.drop_duplicates(subset = ['Dayname'])
                    data = data.set_index('Dayname')
                    data.loc[day_, 'Paid hours'] = sum_paid_hours[day_]
                    data = data.reset_index()
                else:
                    double = False
                    start_double = None
                    end_double = None
            else:
                is_absence = False
                double = False
                start_double = None
                end_double = None

            # need to se thte
            missing_days = list(set(days_of_week) - set(data['Dayname'].unique()))
            #st.write(missing_days)
            if len(missing_days) > 0:
                for day in missing_days:
                    data = pd.concat([data, pd.DataFrame({'ID': [id], 'Start': [None], 'Finish': [None], 'Event type': ['Off'], 'Dayname': [day], 'Name': [name], 'Paid hours': [0], 'Site (appointment)': [None], 'Shift type': [None]})])

            data = data.set_index('Dayname')
            data = data.reindex(days_of_week)
            # replace Paid hours = 0 to Event type value
            data.loc[data['Paid hours'] == 0, 'Paid hours'] = data.loc[data['Paid hours'] == 0, 'Event type']
            columns_to_keep = ['Name', 'Site (appointment)', 'Event type', 'Paid hours', 'Department (attribution)' ]
            data = data[columns_to_keep]
            # rename paid hours column as department
            data = data.rename(columns = {'Paid hours': f'{dep}'})
            data = data.T
            # keep only index 'Paid hours'
            data = data[data.index == f'{dep}']
            # get a list with all the values in the row
            values = data.values.tolist()[0]
            values_numeric = [x for x in values if str(x) != 'nan' and x != 'Off' and x != 'Absence']
            sum_hours = sum(values_numeric)
            # round to 2 decimals
            message = f"**({i}) {name} - Total paid hours: {round(sum_hours,2)}**"
            if is_absence:
                message = message + f" (FOUND **ABSENCE** and **PAID HOURS** on: {day_})"
            with empty_space.expander(message):
                # working on adding shift inside the day column if not Absence
                # filter the data keeping only the shift type
                shift_data = shift_data[shift_data['Event type'] == 'Shift']
                # keep start and finish and day
                shift_data = shift_data[['Start', 'Finish', 'Dayname']]
                if double:
                    shift_data.loc[shift_data['Dayname'] == day_, 'Start'] = start_double
                    shift_data.loc[shift_data['Dayname'] == day_, 'Finish'] = end_double
                # keep only time and take off date
                shift_data['Start'] = shift_data['Start'].dt.time
                shift_data['Finish'] = shift_data['Finish'].dt.time
                # take off seconds assigning format
                shift_data['Start'] = shift_data['Start'].apply(lambda x: x.strftime('%H:%M'))
                shift_data['Finish'] = shift_data['Finish'].apply(lambda x: x.strftime('%H:%M'))
                #st.write(shift_data)
                # add the time to the day column inside the data dataframe
                for _, row in shift_data.iterrows():
                    day_ = row['Dayname']
                    start_ = row['Start']
                    finish_ = row['Finish']
                    # transform the start and finish as times
                    start_ = pd.to_datetime(start_, format = '%H:%M')
                    finish_ = pd.to_datetime(finish_, format = '%H:%M')
                    if finish_ < start_:
                        finish_ = finish_ + pd.DateOffset(days = 1)
                    difference_start_finish = finish_ - start_
                    start_ = start_.strftime('%H:%M')
                    finish_ = finish_.strftime('%H:%M')
                    # difference in hours only
                    difference_start_finish = difference_start_finish.total_seconds() / 3600
                    # if difference >= 6 hrs we add a break of 20 min
                    if difference_start_finish >= 6 and difference_start_finish <= 10:
                        difference_start_finish = difference_start_finish - 0.3333333333333333
                    elif difference_start_finish > 10 and difference_start_finish <= 14:
                        difference_start_finish = difference_start_finish - 1
                    elif difference_start_finish > 14:
                        difference_start_finish = difference_start_finish - 3

                    # as a markdown
                    data.loc[f'{dep}', f'{day_}'] = f'{start_} - {finish_}\n({round(difference_start_finish, 2)} hrs)'

                    # add department columns and replace add the name to the beginning of the index
                data = data.reset_index()
                data = data.rename(columns = {'index': 'Department'})
                data['Name'] = data['Department'].apply(lambda x: f'{name} - {x}')
                data = data.set_index('Name')
                # add to the final dataframe
                # add total column using sum_hours
                data['Total'] = sum_hours
                final_df = pd.concat([final_df, data])
                st.dataframe(data, use_container_width=True)

        # case 2: employee has more than one department
        else:
            #st.write('Employee has more than one department')
            all_data = pd.DataFrame()
            first_dep = departments_attributions[0]
            # if shift type is nan we replace it with the first department
            data.loc[data['Shift type'].isnull(), 'Shift type'] = first_dep
            if checkbox:
                st.write(data)
            
            # Create a row for each department in the data for each of the users
            for dep in departments_attributions:
                # filter the data keeping only the department we want
                data_ = data[data['Shift type'] == dep]
                # check that we don't have duplicates in the dayname column (It might be for sicknesses or double shifts)
                day_s = data_['Dayname'].value_counts()
                if len(day_s[day_s > 1]) > 0:
                    day_ = day_s[day_s > 1].index[0]
                    #st.write(f"Duplicate day: {day_}")
                    #st.write(data_[data_['Dayname'] == day_])
                    unique_events_type = data[data['Dayname'] == day_]['Event type'].unique()
                    list_unique_events_type = unique_events_type.tolist()
                    is_absence = 'Absence' in list_unique_events_type
                    # AS a first thing we can keep the shift rather than the absence -
                    data_ = data_[data_['Event type'] == 'Shift']

                    # if we still have duplicates we sum the paid hours and keep only one row
                    day_s = data_['Dayname'].value_counts()
                    if len(day_s[day_s > 1]) > 0:
                        sum_paid_hours = data_.groupby('Dayname')['Paid hours'].sum()
                        data_ = data_.drop_duplicates(subset = ['Dayname'])
                        data_ = data_.set_index('Dayname')
                        data_.loc[day_, 'Paid hours'] = sum_paid_hours[day_]
                        data_ = data_.reset_index()
                else:
                    is_absence = False
                # Now that we cannot have duplicates we can check if we have missing days and add them as days off
                missing_days = list(set(days_of_week) - set(data_['Dayname'].unique()))
                if len(missing_days) > 0:
                    for day in missing_days:
                        data_ = pd.concat([data_, pd.DataFrame({'ID': [id], 'Start': [None], 'Finish': [None], 'Event type': ['Off'], 'Dayname': [day], 'Name': [name], 'Paid hours': [0], 'Site (appointment)': [None], 'Shift type': [None]})])
                    
                data_ = data_.set_index('Dayname')
                data_ = data_.reindex(days_of_week)
                # replace Paid hours = 0 to Event type value

                data_.loc[data_['Paid hours'] == 0, 'Paid hours'] = data_.loc[data_['Paid hours'] == 0, 'Event type']
                columns_to_keep = ['Name', 'Site (appointment)', 'Event type', 'Paid hours', 'Department (attribution)' ]
                data_ = data_[columns_to_keep]
                # rename paid hours column as department
                data_ = data_.rename(columns = {'Paid hours': f'{dep}'})
                data_ = data_.T
                # keep only index 'Paid hours'
                data_ = data_[data_.index == f'{dep}']
                all_data = pd.concat([all_data, data_])

            # Reformat the data in a better form
            days_ = all_data.columns
            for col in days_:
                # if the column contains 'Absence' all that column should be 'Absence'
                if 'Absence' in all_data[col].unique():
                    all_data[col] = 'Absence'
                # count how many off there are for each column, if there are as many as len then take off the off and keep 0
                if len(all_data[all_data[col] == 'Off']) == len(all_data):
                    all_data[col] = 'Off'
                else:
                    all_data[col] = all_data[col].replace('Off', 0)

            # Get the Total Hours
            total_hours = []
            for _, row in all_data.iterrows():
                values = row.values.tolist()
                values_numeric = [x for x in values if str(x) != 'nan' and x != 'Off' and x != 'Absence']
                total_hours.append(sum(values_numeric))

            totals_ = sum(total_hours)
            # round to 2 decimals
            message = f"**({i}) {name} - Total paid hours: {round(totals_,2)}**"
            if is_absence:
                message = message + f" (FOUND **ABSENCE** and **PAID HOURS** on: {day_})"
            with empty_space.expander(message):
                for dep in departments_attributions:
                    shift_data_ = shift_data[shift_data['Shift type'] == dep]
                    # working on adding shift inside the day column if not Absence
                    # filter the data keeping only the shift type
                    shift_data_ = shift_data_[shift_data_['Event type'] == 'Shift']
                    # keep start and finish and day
                    shift_data_ = shift_data_[['Start', 'Finish', 'Dayname']]
                    # keep only time and take off date
                    shift_data_['Start'] = shift_data_['Start'].dt.time
                    shift_data_['Finish'] = shift_data_['Finish'].dt.time
                    # take off seconds assigning format
                    shift_data_['Start'] = shift_data_['Start'].apply(lambda x: x.strftime('%H:%M'))
                    shift_data_['Finish'] = shift_data_['Finish'].apply(lambda x: x.strftime('%H:%M'))
                    #st.write(shift_data)
                    # add the time to the day column inside the data dataframe
                    for _, row in shift_data_.iterrows():
                        day_ = row['Dayname']
                        start_ = row['Start']
                        finish_ = row['Finish']
                        # transform the start and finish as times 
                        start_ = pd.to_datetime(start_, format = '%H:%M')
                        finish_ = pd.to_datetime(finish_, format = '%H:%M')
                        if finish_ < start_:
                            finish_ = finish_ + pd.DateOffset(days = 1)
                        difference_start_finish = finish_ - start_
                        start_ = start_.strftime('%H:%M')
                        finish_ = finish_.strftime('%H:%M')
                        # difference in hours only  
                        difference_start_finish = difference_start_finish.total_seconds() / 3600 
                        # if difference >= 6 hrs we add a break of 20 min
                        if difference_start_finish >= 6 and difference_start_finish <= 10:
                            difference_start_finish = difference_start_finish - 0.3333333333333333
                        elif difference_start_finish > 10:
                            difference_start_finish = difference_start_finish - 1

                        all_data.loc[f'{dep}', f'{day_}'] = f'{start_} - {finish_}\n({round(difference_start_finish, 2)} hrs)'
                        
                # add department columns and replace add the name to the beginning of the index
                all_data = all_data.reset_index()
                all_data = all_data.rename(columns = {'index': 'Department'})
                all_data['Name'] = all_data['Department'].apply(lambda x: f'{name} - {x}')
                all_data = all_data.set_index('Name')
                all_data['Total'] = total_hours if len(total_hours) > 1 else total_hours[0]
                # add to the final dataframe
                final_df = pd.concat([final_df, all_data])
                # add total column using sum_hours
                st.dataframe(all_data, use_container_width=True)

        #st.stop()
    # show the data
    # make total column
    # get type of total column
    total_column_type = final_df['Total'].dtype
    # round to 2 decimals and transform it to string
    # transform it to string
    final_df['Total'] = final_df['Total'].apply(lambda x: str(round(x, 2)))
    final_df = final_df[['Total'] + days_of_week]
    final_df = final_df[~final_df.index.str.contains('BOH')]

    # highlight off days in red
    def highlight_off(s):
        is_off = s == 'Off'
        return ['background-color: lightblue' if v else '' for v in is_off]
    
    def highlight_absence(s):
        is_absence = s == 'Absence'
        return ['background-color: lightyellow' if v else '' for v in is_absence] # lightgreen, lightblue, lightyellow, lightred, lightgrey
    
    
    final_df = final_df.style.apply(highlight_off)
    final_df = final_df.apply(highlight_absence)
    # set size of the text inside the table
    final_df = final_df.set_properties(**{'font-size': '8pt'})
    # take off the index that contains 'BOH'
    final_empty_space.table(final_df, use_container_width=True)

if __name__ == '__main__':
    # upload a file
    uploaded_file = st.sidebar.file_uploader("Choose a file")

    # if file is uploaded
    if uploaded_file is not None:
        # read the file
        df = pd.read_excel(uploaded_file)
        unique_users = df['ID'].unique()
        
        # take off all boh users
        df = df[~df['Shift type'].isin(boh_type)]

        # get unique departments    
        unique_departments = df['Department (attribution)'].unique()
        # create a filter for the departments
        options = dict_map.keys()
        # take off BOH
        options = [x for x in options if x != 'BOH']
        department_filter = st.sidebar.multiselect('Department', options)

        if len(department_filter) > 0:
            # filter the data 
            #df = df[df['Department (attribution)'].isin(department_filter)]
            # get values from the dictionary
            values = [dict_map[x] for x in department_filter]
            # flatten the list
            values = [item for sublist in values for item in sublist]
            # filter the data
            df = df[df['Shift type'].isin(values)]
        
        # Keep only the events that we need (take off salary events)
        df = df[df['Event type'] != 'Salary']
        absences_df = df[df['Event type'] == 'Absence']
        shifts_df = df[df['Event type'] == 'Shift']

        # Start and Finish needs to be processed as datetime
        absences_df['Start'] = pd.to_datetime(absences_df['Start'], format = '%d/%m/%Y')
        absences_df['Finish'] = pd.to_datetime(absences_df['Finish'], format = '%d/%m/%Y')

        shifts_df['Start'] = pd.to_datetime(shifts_df['Start'], format = '%d/%m/%Y %H:%M')
        shifts_df['Finish'] = pd.to_datetime(shifts_df['Finish'], format = '%d/%m/%Y %H:%M')

        concatenated = pd.concat([absences_df, shifts_df])
        # add a dayname column
        concatenated['Dayname'] = concatenated['Start'].dt.day_name()
        concatenated['Name'] = concatenated['First name'] + ' ' + concatenated['Last name']
        # drop the first and last name columns
        concatenated = concatenated.drop(['First name', 'Last name'], axis = 1)
        
        #get unique names
        unique_names = concatenated['Name'].unique()
        #st.write(len(unique_names))
        # take off useless columns
        useless_columns = [
            'Base pay', 'Accrued holiday', 'Taxes', 'Wage uplift', 'Total cost'
        ]
        concatenated = concatenated.drop(useless_columns, axis = 1)
        #st.write(concatenated)
        # filter out boh
        process_data(concatenated)
