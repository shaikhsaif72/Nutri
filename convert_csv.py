import pandas as pd

# Read your existing CSV
df = pd.read_csv('data/nutrition_data.csv', encoding='latin-1')

print(f"Original columns: {list(df.columns)}")
print(f"Total rows: {len(df)}")

# Rename columns to match what app expects
column_mapping = {
    'food_name': 'name',
    'energy_kcal': 'calories',
    'protein_g': 'protein',
    'carb_g': 'carbs',
    'fat_g': 'fat'
}

# Select only the columns we need and rename them
df_simple = df[['food_name', 'energy_kcal', 'protein_g', 'carb_g', 'fat_g']].copy()
df_simple.columns = ['name', 'calories', 'protein', 'carbs', 'fat']

# Add category column (set all to General for now)
df_simple['category'] = 'General'

# Clean up - remove any rows with missing data
df_simple = df_simple.dropna()

# Save converted CSV
df_simple.to_csv('data/nutrition_data_converted.csv', index=False, encoding='utf-8')

print(f"\n✓ Converted {len(df_simple)} foods")
print(f"✓ Saved to: data/nutrition_data_converted.csv")
print("\nFirst 5 foods:")
print(df_simple.head())