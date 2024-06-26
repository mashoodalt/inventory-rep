# example/st_app.py

import streamlit as st
from streamlit_gsheets import GSheetsConnection

import pandas as pd

import requests

def send_email_via_postmark(subject, body, recipient):
    url = "https://api.postmarkapp.com/email"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Postmark-Server-Token": "b4458825-787c-48b7-8a80-2ee3405d60a0"
    }
    data = {
        "From": "mashood@altventures.co",  # This must be a verified sender signature in Postmark
        "To": recipient, #recipient
        "Subject": subject,
        "TextBody": body
    }
    response = requests.post(url, headers=headers, json=data)
    return response.status_code, response.text


url = "https://docs.google.com/spreadsheets/d/1NwKMHFMklbu-fRvTjv1e7-XlN34SzckWJoSGd6mTwoI/edit?gid=0#gid=0"

st.set_page_config(layout="wide")

email_mapping = {
    "Athara Hazari": "muhammmadmashood23@gmail.com",
    "Bhowana": "mashood@altventures.co",
    "Chund Bharwana": "muhammmadmashood23@gmail.com",
    "Garh Maharaja": "mashood@altventures.co",
    "Lallian": "muhammmadmashood23@gmail.com",
    "Hafizabad": "mashood@altventures.co",
    "KDuakaan": "mashood@altventures.co",
    "TTS/Stock": "muhammmadmashood23@gmail.com",
    "Purchase": "mashood@altventures.co",
}


def generate_recommendations(df):
    recommendations = []
    transfer_aggregation = {}
    my_data = {
        "Product": [],
        "Source": [],
        "Destination": [],
        "Amount": [],
        "Person Responsible": []
    }
    
    # Convert columns to numeric inside the function to avoid any typing issues
    for column in df.columns:
        if column != 'product':
            df[column] = pd.to_numeric(df[column], errors='coerce')

    for index, row in df.iterrows():
        product = row['product']
        
        # surplus_warehouses = {col: val for col, val in row.items() if pd.notna(val) and val > 0 and col != 'product'}
        # deficit_warehouses = {col: abs(val) for col, val in row.items() if pd.notna(val) and val < 0 and col != 'product'}

        # Use dictionary comprehension to filter surplus and deficit warehouses
        surplus_warehouses = {col: val for col, val in row.items() if isinstance(val, (int, float)) and val > 0}
        deficit_warehouses = {col: abs(val) for col, val in row.items() if isinstance(val, (int, float)) and val < 0}

        # Calculate remaining deficits after possible transfers
        # for d_warehouse, d_amount in list(deficit_warehouses.items()):
        #     for s_warehouse, s_amount in list(surplus_warehouses.items()):
        #         if s_amount == 0:
        #             continue
        #         transfer_amount = min(d_amount, s_amount)
        #         if transfer_amount > 0:
        #             recommendations.append(f"Transfer {transfer_amount} units of {product} from {s_warehouse} to {d_warehouse}.")
        #             surplus_warehouses[s_warehouse] -= transfer_amount
        #             deficit_warehouses[d_warehouse] -= transfer_amount
        #             if deficit_warehouses[d_warehouse] <= 0:
        #                 break

        for d_warehouse, d_amount in deficit_warehouses.items():
            for s_warehouse, s_amount in surplus_warehouses.items():
                transfer_amount = min(d_amount, s_amount)
                if transfer_amount > 0:
                    key = (s_warehouse, d_warehouse, product)
                    if key not in transfer_aggregation:
                        transfer_aggregation[key] = 0
                    transfer_aggregation[key] += transfer_amount
                    surplus_warehouses[s_warehouse] -= transfer_amount
                    d_amount -= transfer_amount
                    if d_amount <= 0:
                        break
    
    for (source, dest, product), amount in transfer_aggregation.items():
        recommendations.append(f"Transfer {amount} units of {product} from {source} to {dest}.")
        my_data["Product"].append(product)
        my_data["Source"].append(source)
        my_data["Destination"].append(dest)
        my_data["Amount"].append(amount)
        my_data["Person Responsible"].append(email_mapping.get(source, "No email found"))

        #Check any remaining deficit
        # remaining_deficit = sum(value for value in deficit_warehouses.values() if value > 0)
        # if remaining_deficit > 0:
        #     recommendations.append(f"Purchase {remaining_deficit} more units of {product} to meet the demand.")

    df_transfers = pd.DataFrame(my_data)
    
    return recommendations, df_transfers




conn = st.connection("gsheets", type=GSheetsConnection)

data = conn.read(spreadsheet=url, usecols=range(0,9))

def load_inventory_data():
    data = conn.read(spreadsheet=url, worksheet="1092163554")
    return data

def load_advanced_orders():
    #1125866982
    data = conn.read(spreadsheet=url, worksheet="1125866982")
    return data

# Load data (placeholders for demonstration)
inventory_data = load_inventory_data()  # This would be your actual function call
advanced_orders = load_advanced_orders()  # This would be your actual function call



df = pd.DataFrame(data)

# st.dataframe(df)

# df['Total'] = df.iloc[:, 1:].sum(axis=1)

# Calculate totals for each column (excluding the 'Product' column)
# column_totals = df.iloc[:, 1:].sum().rename('Total')

# Append this row to the DataFrame
# df = df.append(column_totals)



# Assuming you know the columns that represent warehouses
warehouse_columns = ['Athara Hazari', 'Bhowana', 'Chund Bharwana', "Garrh Maharaja", "Lallian", "Hafizabad", "KDukaan", "TTS/Stock"]  # Add all your warehouse columns here

# User Inputs for Demand Multipliers
with open("logo.svg", "r") as file:
    svg = file.read()

# Display SVG
st.sidebar.markdown(svg, unsafe_allow_html=True)
# st.sidebar.header("Inventory Helper")
# st.sidebar.divider()
st.sidebar.header("Set Benchmark Quantities for Each Product")

product_demands = {}
for product in df['product']:
    product_demands[product] = st.sidebar.number_input(f"Demand for {product}", min_value=0, value=10)

st.sidebar.header("Set Demand Constants for Each Warehouse")
warehouse_demands = {}
for column in warehouse_columns:
    warehouse_demands[column] = st.sidebar.number_input(f"Demand in {column}", min_value=0, value=1)

# Calculate and Update DataFrame for Display
for column in warehouse_columns:
    df[column] = df.applymap(lambda row: (row[column] - (product_demands[row['product']] * warehouse_demands[column])), axis=1)

# Apply Conditional Formatting
def color_negative(val):
    color = 'orange' if val < 0 else 'black'
    return f'color: {color}'

# st.header("Available Quantity")

# st.dataframe(df.style.applymap(color_negative_red, subset=warehouse_columns))

# Displaying available quantity of inventory
st.header("Available Quantity of Inventory")
st.dataframe(inventory_data)  # Display your inventory DataFrame here

# Displaying advanced orders
st.header("Advanced Orders")
st.dataframe(advanced_orders)  # Display your advanced orders DataFrame here

# Display current table under a new heading
st.header("Quantity - Advanced Orders - Benchmark")
# Assuming 'df' is the DataFrame you're currently displaying

df['Total Inventory'] = df.iloc[:, 1:].sum(axis=1)  # Sum across rows starting from the second column

st.dataframe(df)
# st.dataframe(df.style.map(color_negative, subset=warehouse_columns))


recs, df_transfers = generate_recommendations(df)

# st.header("Recommendations:")

# print(df.dtypes)

deficit_products = df[df['Total Inventory'] < 0]

# Generate purchase recommendations
recommendations = []
for index, row in deficit_products.iterrows():
    product = row['product']
    needed_units = -row['Total Inventory']  # Calculate how many units are needed to reach zero
    recommendations.append(f"Purchase {needed_units} more units of {product} to meet the demand.")



st.markdown("### Recommendations")
with st.expander("See Recommendations"):
    st.markdown(f"### Warehouse Transfers ({len(df_transfers)})")
    st.dataframe(df_transfers)
    # for rec in recs:
    #     if "Purchase" in rec:
    #         st.markdown(f"<span style='color:yellow'>{rec}</span>", unsafe_allow_html=True)
    #     else:
    #         st.markdown(f"<span style='color:gray'>{rec}</span>", unsafe_allow_html=True)
    st.markdown(f"### Purchase Required ({len(recommendations)})")
    
    
    for rec in recommendations:
        st.write(rec)
        
if st.button('Send Emails'):
    success = True
    for rec in recommendations:
        subject = f"Purchase Recommendation"
        body = rec
        recipient = email_mapping["Purchase"]  # Each recommendation could have a different recipient
        status_code, response_text = send_email_via_postmark(subject, body, recipient)
        if status_code != 200:
            success = False
            st.error(f"Failed to send email: {response_text}")
            
    for index, row in df_transfers.iterrows():
        product = row['Product']
        source = row['Source']
        destination = row['Destination']
        amount = row['Amount']
        recipient = row['Person Responsible']
        
        # Construct the email details
        subject = f"Transfer Notification for {product}"
        body = f"Please be advised to transfer {amount} units of {product} from {source} to {destination}."
        
        # Send the email
        status_code, response_text = send_email_via_postmark(subject, body, recipient)
        
        # Display the status in Streamlit (you can also use print if not using Streamlit)
        if status_code != 200:
            success = False
            st.error(f"Failed to send email: {response_text}")
    
    if success:
        st.success("All emails sent successfully!")
        
st.write("Sends emails to all responsible people for transfers & purchases")
