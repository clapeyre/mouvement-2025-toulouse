import pandas as pd

# Read the CSV file with the correct separator
df = pd.read_csv('schools_with_addresses.csv', sep=';', encoding='utf-8')

# Remove any extra whitespace from string columns
for col in df.columns:
    if df[col].dtype == 'object':
        df[col] = df[col].str.strip()

# Convert latitude and longitude to float, handling any errors
df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')

# Save the cleaned data
df.to_csv('schools_with_addresses_clean.csv', sep=';', index=False, encoding='utf-8') 