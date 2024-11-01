import psycopg2
import json
import configparser
import difflib
import os

# Load conif file 
config = configparser.ConfigParser()
config.read('config.ini')

# Funktion on load db
def connect_to_db(db_name):
    try:
        db_config = config[db_name]
        connection = psycopg2.connect(
            host=db_config['host'],
            database=db_config['dbname'],
            user=db_config['user'],
            password=db_config['password']
        )
        return connection
    except Exception as error:
        print(f"ERor with connection in db: {error}")
        return None

# funktion for load JSON file
def load_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"ERor for loading data: {file_path}: {e}")
        return None

# Funktion for get JSOn file of db
def get_db_json_data(cursor, row_id):
    cursor.execute("SELECT data FROM template WHERE id = %s", (row_id,))
    result = cursor.fetchone()
    if result:
        return result[0]  # give JSON file
    else:
        print(f"line with id {row_id} not found.")
        return None

# funktion for mark differences between JSOn files
def highlight_differences(json1, json2):
    json1_str = json.dumps(json1, indent=4, sort_keys=True)
    json2_str = json.dumps(json2, indent=4, sort_keys=True)
    
    diff = difflib.unified_diff(json1_str.splitlines(), json2_str.splitlines(), lineterm='', fromfile='Databáze', tofile='Soubor')
    
    return '\n'.join(diff)

# Funktion for update db
def update_db_json(cursor, row_id, new_data):
    try:
        cursor.execute("UPDATE template SET data = %s WHERE id = %s", (json.dumps(new_data), row_id))
    except Exception as e:
        print(f"Eror for actualization db {row_id}: {e}")

# Main funktion script
def main(file_path, db_name, row_id):
    # Connect to db
    connection = connect_to_db(db_name)
    if connection is None:
        return
    
    cursor = connection.cursor()

    # Load Json file
    file_json_data = load_json_file(file_path)
    if file_json_data is None:
        return

    # get data from json 
    db_json_data = get_db_json_data(cursor, row_id)
    if db_json_data is None:
        return

    # comper between data
    if db_json_data != file_json_data:
        print("Rozdíly nalezeny:")
        diff = highlight_differences(db_json_data, file_json_data)
        print(diff)

        # Ask user, if he want to rewrite data in db
        user_input = input("Do you want to rewrite data in db? (yes/no): ")
        if user_input.lower() == "yes":
            update_db_json(cursor, row_id, file_json_data)
            connection.commit()
            print(f"line {row_id} was succesfully update.")
        else:
            print("Aktualization hase been closed.")
    else:
        print("Data is identical,no uppdate needed.")

    # Close connection
    cursor.close()
    connection.close()

# Run script
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Aktualization templates in db")
    parser.add_argument("file_path", help="Way to JSON file")
    parser.add_argument("db_name", help="Name db (testovaci nebo produkční)")
    parser.add_argument("row_id", help="ID line in db", type=int)
    
    args = parser.parse_args()
    main(args.file_path, args.db_name, args.row_id)
