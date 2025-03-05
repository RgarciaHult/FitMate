import pandas as pd
import sqlite3
import os

DATABASE = 'database/fitmate.db'

def import_meals_from_excel(file_path):
    # Read the Excel file into a DataFrame
    df = pd.read_excel(file_path)
    
    # Normalize column names: strip whitespace and convert to lowercase
    df.columns = df.columns.str.strip().str.lower()
    
    # Debug: print the column names so you can verify they match expected names
    print("Excel columns:", df.columns.tolist())
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Loop through each row and insert data into the meals table
    for index, row in df.iterrows():
        try:
            meal_type = row['type'] 
            name = row['meal name']  
            identifier = row['identifier']
            categories = row['categories']
            prep_time = int(row['preptime'])
            # Accept various forms for overnight (boolean)
            overnight = 1 if row['overnight'] in [True, 1, 'true', 'TRUE'] else 0
            equipment = row['equipment']
            ingredients = row['ingredients']
            instructions = row['instructions']
        except KeyError as e:
            print(f"Column not found: {e}")
            continue

        cursor.execute('''
            INSERT OR IGNORE INTO meals 
            (type, name, identifier, categories, prep_time, overnight, equipment, ingredients, instructions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (meal_type, name, identifier, categories, prep_time, overnight, equipment, ingredients, instructions))
    
    conn.commit()
    conn.close()
    print("Meals imported successfully.")

if __name__ == "__main__":
    import_meals_from_excel("data/meals.xlsx")