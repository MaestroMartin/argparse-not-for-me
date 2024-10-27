import psycopg2
import json
import configparser
import difflib
import os

# Načti konfigurační soubor
config = configparser.ConfigParser()
config.read('config.ini')

# Funkce pro připojení k databázi
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
        print(f"Chyba při připojení k databázi: {error}")
        return None

# Funkce pro načtení JSON souboru
def load_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"Chyba při načítání souboru {file_path}: {e}")
        return None

# Funkce pro získání JSON dat z databáze
def get_db_json_data(cursor, row_id):
    cursor.execute("SELECT data FROM template WHERE id = %s", (row_id,))
    result = cursor.fetchone()
    if result:
        return result[0]  # Vrací JSON data z databáze
    else:
        print(f"Řádek s id {row_id} nebyl nalezen.")
        return None

# Funkce pro zvýraznění rozdílů mezi dvěma JSONy
def highlight_differences(json1, json2):
    json1_str = json.dumps(json1, indent=4, sort_keys=True)
    json2_str = json.dumps(json2, indent=4, sort_keys=True)
    
    diff = difflib.unified_diff(json1_str.splitlines(), json2_str.splitlines(), lineterm='', fromfile='Databáze', tofile='Soubor')
    
    return '\n'.join(diff)

# Funkce pro aktualizaci databáze
def update_db_json(cursor, row_id, new_data):
    try:
        cursor.execute("UPDATE template SET data = %s WHERE id = %s", (json.dumps(new_data), row_id))
    except Exception as e:
        print(f"Chyba při aktualizaci řádku {row_id}: {e}")

# Hlavní funkce skriptu
def main(file_path, db_name, row_id):
    # Připojení k databázi
    connection = connect_to_db(db_name)
    if connection is None:
        return
    
    cursor = connection.cursor()

    # Načtení JSON souboru
    file_json_data = load_json_file(file_path)
    if file_json_data is None:
        return

    # Získání dat z databáze
    db_json_data = get_db_json_data(cursor, row_id)
    if db_json_data is None:
        return

    # Porovnání dat
    if db_json_data != file_json_data:
        print("Rozdíly nalezeny:")
        diff = highlight_differences(db_json_data, file_json_data)
        print(diff)

        # Zeptat se uživatele, zda chce přepsat data v databázi
        user_input = input("Chcete přepsat hodnotu v databázi? (ano/ne): ")
        if user_input.lower() == "ano":
            update_db_json(cursor, row_id, file_json_data)
            connection.commit()
            print(f"Řádek {row_id} byl úspěšně aktualizován.")
        else:
            print("Aktualizace byla zrušena.")
    else:
        print("Data jsou identická, není potřeba žádná aktualizace.")

    # Uzavřít připojení
    cursor.close()
    connection.close()

# Spuštění skriptu
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Aktualizace šablony v databázi")
    parser.add_argument("file_path", help="Cesta k JSON souboru")
    parser.add_argument("db_name", help="Název databáze (testovací nebo produkční)")
    parser.add_argument("row_id", help="ID řádku v databázi", type=int)
    
    args = parser.parse_args()
    main(args.file_path, args.db_name, args.row_id)
