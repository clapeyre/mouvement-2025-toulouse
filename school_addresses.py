import pandas as pd
import json
import re

def extract_uai(school_name):
    """
    Extract the UAI code from the school name
    """
    # Look for pattern like (0310160f) or 0310160f at the end of the name
    match = re.search(r'[(\s]([0-9]{7}[A-Za-z])[)\s]?', school_name)
    if match:
        return match.group(1)
    return None

def load_schools_data():
    """
    Load the schools data from the GeoJSON file
    """
    print("Loading schools data from GeoJSON file...")
    with open('fr-en-annuaire-education.geojson', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Create a dictionary for quick lookup by UAI code
    schools_dict = {}
    for feature in data['features']:
        properties = feature['properties']
        uai = properties.get('identifiant_de_l_etablissement')
        if uai:
            # Convert UAI to uppercase for consistency
            uai = uai.upper()
            # Combine address fields, handling None values
            address_parts = []
            for i in range(1, 4):
                addr = properties.get(f'adresse_{i}')
                if addr and addr != 'None':
                    address_parts.append(addr)
            
            # Get and validate coordinates
            try:
                lat = float(properties.get('latitude', ''))
                lon = float(properties.get('longitude', ''))
                # Basic validation of coordinates for France
                if not (41 <= lat <= 52 and -5 <= lon <= 10):
                    lat, lon = None, None
            except (ValueError, TypeError):
                lat, lon = None, None
            
            schools_dict[uai] = {
                'address': ' '.join(address_parts),
                'postal_code': properties.get('code_postal', ''),
                'commune': properties.get('nom_commune', ''),
                'type': properties.get('type_etablissement', ''),
                'name': properties.get('nom_etablissement', ''),
                'latitude': lat,
                'longitude': lon
            }
    
    print(f"Loaded {len(schools_dict)} schools")
    return schools_dict

def get_school_data(school_name, schools_dict):
    """
    Get the school data from the loaded data
    """
    try:
        # Extract UAI code
        uai = extract_uai(school_name)
        if not uai:
            print(f"  No UAI code found in: {school_name}")
            return None
            
        print(f"  Looking for UAI: {uai}")
        
        # Convert UAI to uppercase for comparison
        uai = uai.upper()
        
        # Look up the school in our dictionary (try both upper and lower case)
        school_data = schools_dict.get(uai) or schools_dict.get(uai.lower())
        if school_data:
            print(f"  Found school: {school_data['name']}")
            print(f"  Type: {school_data['type']}")
            if school_data['latitude'] is not None and school_data['longitude'] is not None:
                print(f"  Coordinates: {school_data['latitude']}, {school_data['longitude']}")
            else:
                print("  No valid coordinates found")
            return school_data
        
        print("  No matching school found with this UAI")
        return None
    
    except Exception as e:
        print(f"  Error occurred: {str(e)}")
        return None

def main():
    # Load the schools data
    schools_dict = load_schools_data()
    
    # Read the CSV file without headers
    # Note: The file uses semicolon as separator
    df = pd.read_csv('mouvement_complet_clean.csv', sep=';', encoding='utf-8', header=None)
    
    # Rename columns to meaningful names
    df.columns = ['code', 'city', 'school_name', 'type', 'nature',
                  'specialization', 'num_vacant', 'num_potential']
    
    # Create new columns for school data
    df['address'] = ''
    df['latitude'] = pd.NA
    df['longitude'] = pd.NA
    df['school_type'] = ''
    
    # Statistics tracking
    stats = {
        'total': len(df),
        'found': 0,
        'found_with_coords': 0,
        'not_found': 0,
        'error': 0,
        'no_uai': 0
    }
    
    # Process all rows
    for index, row in df.iterrows():
        school_name = row['school_name']
        city = row['city']
        
        print(f"\nProcessing: {school_name} in {city}")
        
        # Get school data
        school_data = get_school_data(school_name, schools_dict)
        
        if school_data:
            # Update statistics
            stats['found'] += 1
            
            # Store the data
            df.at[index, 'address'] = f"{school_data['address']}, {school_data['postal_code']} {school_data['commune']}"
            
            # Only store coordinates if they are valid
            if school_data['latitude'] is not None and school_data['longitude'] is not None:
                df.at[index, 'latitude'] = school_data['latitude']
                df.at[index, 'longitude'] = school_data['longitude']
                stats['found_with_coords'] += 1
            
            df.at[index, 'school_type'] = school_data['type']
        else:
            if extract_uai(school_name) is None:
                stats['no_uai'] += 1
            else:
                stats['not_found'] += 1
    
    # Save results to a new CSV file
    df.to_csv('schools_with_addresses.csv', sep=';', index=False, encoding='utf-8')
    
    # Print statistics
    print("\nSchool Finding Statistics:")
    print(f"Total schools processed: {stats['total']}")
    print(f"Successfully found schools: {stats['found']}")
    print(f"Schools with valid coordinates: {stats['found_with_coords']}")
    print(f"Schools not found: {stats['not_found']}")
    print(f"Schools without UAI code: {stats['no_uai']}")
    print(f"Errors: {stats['error']}")
    print(f"\nSuccess rate: {(stats['found'] / stats['total'] * 100):.1f}%")
    print(f"Coordinates success rate: {(stats['found_with_coords'] / stats['total'] * 100):.1f}%")
    
    print("\nProcessing complete! Results saved to 'schools_with_addresses.csv'")

if __name__ == "__main__":
    main() 
