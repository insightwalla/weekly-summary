import pandas as pd
import streamlit as st
st.set_page_config(layout="wide")


def process_data(df):
    #st.write(df)

    unique_id = df['ID'].unique()
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    checkbox = st.sidebar.checkbox('Show Shifts data')
    for i, id in enumerate(unique_id):
        data = df[df['ID'] == id]
        name = data['Name'].unique()[0]
        departments_attributions = data['Shift type'].unique()
        departments_attributions = [x for x in departments_attributions if str(x) != 'nan']
        empty_subheader = st.empty()
        general_dep = data['Department (attribution)'].unique()
        general_dep = [x for x in general_dep if str(x) != 'nan']
        general_dep = general_dep[0] if len(general_dep) > 0 else 'No department'
        days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        # case 1: employee has only one department
        if len(departments_attributions) <= 1:
            if checkbox:
                st.write(data)
            dep = departments_attributions[0] if len(departments_attributions) == 1 else general_dep
            # check that we don't have duplicates
            day_s = data['Dayname'].value_counts()
            if len(day_s[day_s > 1]) > 0:
                day_ = day_s[day_s > 1].index[0]
                data = data[data['Event type'] == 'Shift']

                # if we still have duplicates we sum the paid hours
                day_s = data['Dayname'].value_counts()
                if len(day_s[day_s > 1]) > 0:
                    sum_paid_hours = data.groupby('Dayname')['Paid hours'].sum()
                    data = data.drop_duplicates(subset = ['Dayname'])
                    data = data.set_index('Dayname')
                    data.loc[day_, 'Paid hours'] = sum_paid_hours[day_]
                    data = data.reset_index()

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
            st.dataframe(data, use_container_width=True)
            # get a list with all the values in the row
            values = data.values.tolist()[0]
            values_numeric = [x for x in values if str(x) != 'nan' and x != 'Off' and x != 'Absence']
            sum_hours = sum(values_numeric)
            empty_subheader.write(f"**{name} - Total paid hours: {round(sum_hours, 2)}**")
        
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
            empty_subheader.write(f"**{name} - Total paid hours: {round(totals_, 2)}**")
            st.dataframe(all_data, use_container_width=True)


if __name__ == '__main__':
    # upload a file
    uploaded_file = st.sidebar.file_uploader("Choose a file")

    # if file is uploaded
    if uploaded_file is not None:
        # read the file
        df = pd.read_excel(uploaded_file)

        # get unique departments    
        unique_departments = df['Department (attribution)'].unique()
        # create a filter for the departments
        department_filter = st.sidebar.multiselect('Department', unique_departments)
        if len(department_filter) > 0:
            df = df[df['Department (attribution)'].isin(department_filter)]

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
        process_data(concatenated)
