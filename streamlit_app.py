import streamlit as st

# Create the SQL connection to inventory_db as specified in your secrets file.
conn = st.connection('inventory_db', type='sql')

# Query and display the data you inserted
pet_owners = conn.query('select * from inventory')
st.dataframe(pet_owners)