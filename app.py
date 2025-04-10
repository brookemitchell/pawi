import streamlit as st
import pandas as pd
from data_loader import load_inventory_data # Import the loading function

# Set the title of the Streamlit application
st.title("Veterinary Inventory PoC")

# Attempt to load the inventory data
# This happens on every script run in this step
inventory_df = load_inventory_data()

# Check if data loading was successful
if inventory_df is not None:
    # Display the loaded data in a table format
    st.dataframe(inventory_df)
else:
    # Display an error message if data loading failed
    st.error("Failed to load inventory data. Check database file and logs.")

# We will add state management and simulation logic later
