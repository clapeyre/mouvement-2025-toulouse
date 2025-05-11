from flask import Flask, render_template
import pandas as pd
import json
import os
import re
import logging
import urllib.parse
import csv
import requests
import time
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def get_directions_url(destination_address):
    """
    Generate a Google Maps directions URL for cycling from a fixed starting point
    to the destination address.
    """
    base_url = "https://www.google.com/maps/dir/"
    start_address = "15 rue de la chaussée, 31000 toulouse"
    
    # URL encode the addresses
    start_encoded = urllib.parse.quote(start_address)
    dest_encoded = urllib.parse.quote(destination_address)
    
    # Add cycling mode parameter
    return f"{base_url}{start_encoded}/{dest_encoded}/?mode=bicycling"

def download_schools_data():
    """
    Download schools data from the education.gouv.fr API and convert it to our format
    """
    cache_file = Path('schools_data_cache.json')
    cache_duration = 24 * 60 * 60  # 24 hours in seconds
    
    # Check if we have a valid cache
    if cache_file.exists():
        cache_age = time.time() - cache_file.stat().st_mtime
        if cache_age < cache_duration:
            logger.info("Using cached schools data")
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    logger.info("Downloading fresh schools data from API")
    try:
        # Download data from API
        url = "https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets/fr-en-annuaire-education/exports/json?lang=fr&timezone=Europe%2FBerlin"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Convert to our format
        schools_dict = {}
        for school in data:
            uai = school.get('identifiant_de_l_etablissement')
            if uai:
                # Convert UAI to uppercase for consistency
                uai = uai.upper()
                # Combine address fields, handling None values
                address_parts = []
                for i in range(1, 4):
                    addr = school.get(f'adresse_{i}')
                    if addr and addr != 'None':
                        address_parts.append(addr)
                
                # Get and validate coordinates
                try:
                    lat = float(school.get('latitude', ''))
                    lon = float(school.get('longitude', ''))
                    # Basic validation of coordinates for France
                    if not (41 <= lat <= 52 and -5 <= lon <= 10):
                        lat, lon = None, None
                except (ValueError, TypeError):
                    lat, lon = None, None
                
                schools_dict[uai] = {
                    'address': ' '.join(address_parts),
                    'postal_code': school.get('code_postal', ''),
                    'commune': school.get('nom_commune', ''),
                    'type': school.get('type_etablissement', ''),
                    'name': school.get('nom_etablissement', ''),
                    'latitude': lat,
                    'longitude': lon
                }
        
        # Save to cache
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(schools_dict, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Downloaded and processed {len(schools_dict)} schools")
        return schools_dict
        
    except Exception as e:
        logger.error(f"Error downloading schools data: {str(e)}")
        # If we have a cache file, use it even if it's old
        if cache_file.exists():
            logger.info("Using old cache due to download error")
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

def load_schools():
    try:
        # Read the CSV file with the correct headers
        headers = [
            "Numéro du poste", "Commune", "Etablissement", "Type de poste",
            "Nature de support", "Spécialité / Nb classes",
            "Nb de postes vacants", "Nb de postes susceptibles d'être vacants"
        ]
        
        logger.debug("Attempting to read mouvement_complet_clean.csv")
        # First read the original CSV to get the list data
        df_list = pd.read_csv('mouvement_complet_clean.csv', sep=';', encoding='utf-8', header=None)
        df_list.columns = headers
        logger.debug(f"Successfully loaded mouvement_complet_clean.csv with {len(df_list)} rows")
        
        logger.debug("Attempting to read schools_with_addresses.csv")
        # Then read the CSV with addresses and coordinates
        df = pd.read_csv('schools_with_addresses.csv', sep=';', encoding='utf-8')
        logger.debug(f"Successfully loaded schools_with_addresses.csv with {len(df)} rows")
        
        # Download schools data from API
        schools_dict = download_schools_data()
        
        # Convert DataFrame to list of dictionaries
        schools = df.to_dict('records')
        
        # Convert to GeoJSON format for the map
        geojson = {
            "type": "FeatureCollection",
            "features": []
        }
        
        # Statistics tracking
        stats = {
            'total': len(schools),
            'found': 0,
            'not_found': 0,
            'error': 0
        }
        
        # Create a dictionary to group schools by coordinates
        location_groups = {}
        
        total_schools = len(schools)
        processed = 0
        
        for school in schools:
            processed += 1
            logger.debug(f"Processing school {processed}/{total_schools}: {school['school_name']}")
            
            try:
                # Extract UAI code from school name
                uai_match = re.search(r'\(([0-9A-Za-z]+)\)', school['school_name'])
                if uai_match:
                    uai = uai_match.group(1).upper()
                    
                    # Get school data from API data
                    school_data = schools_dict.get(uai)
                    if school_data and school_data['latitude'] is not None and school_data['longitude'] is not None:
                        # Create a unique key for this school's location
                        coord_key = (float(school_data['latitude']), float(school_data['longitude']))
                        
                        # Initialize the location group if it doesn't exist
                        if coord_key not in location_groups:
                            location_groups[coord_key] = {
                                'coordinates': [float(school_data['longitude']), float(school_data['latitude'])],
                                'schools': []
                            }
                        
                        # Find all corresponding rows in df_list for this school
                        school_rows = df_list[df_list['Etablissement'].str.contains(uai, na=False)]
                        
                        # Create a list to store all positions for this school
                        positions = []
                        
                        # Process each position for this school
                        for _, row in school_rows.iterrows():
                            # Calculate the ratio
                            vacants = row['Nb de postes vacants']
                            susceptibles = row["Nb de postes susceptibles d'être vacants"]
                            total = vacants + susceptibles
                            ratio = f"{vacants}/{total}" if total > 0 else "N/A"
                            
                            # Add position details
                            positions.append({
                                "type": row['Type de poste'],
                                "specialization": row['Nature de support'],
                                "ratio": ratio
                            })
                        
                        # Add school to the location group with all its positions
                        location_groups[coord_key]['schools'].append({
                            "name": school['school_name'],
                            "city": school_data['commune'],
                            "address": school_data['address'],
                            "positions": positions,
                            "directions_url": get_directions_url(school_data['address'])
                        })
                        stats['found'] += 1
                    else:
                        logger.debug(f"No coordinates found for school: {school['school_name']}")
                        stats['not_found'] += 1
                else:
                    logger.debug(f"No UAI code found for school: {school['school_name']}")
                    stats['not_found'] += 1
            except Exception as e:
                logger.error(f"Error processing school {school['school_name']}: {str(e)}")
                stats['error'] += 1
        
        # Create GeoJSON features from location groups
        for coord_key, group in location_groups.items():
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": group['coordinates']
                },
                "properties": {
                    "schools": group['schools']
                }
            }
            geojson["features"].append(feature)
        
        # Print statistics
        logger.info("\nSchool Processing Statistics:")
        logger.info(f"Total schools: {stats['total']}")
        logger.info(f"Schools with coordinates: {stats['found']}")
        logger.info(f"Schools without coordinates: {stats['not_found']}")
        logger.info(f"Errors: {stats['error']}")
        
        return geojson, stats, None
        
    except Exception as e:
        logger.error(f"Error loading schools data: {str(e)}")
        return {"type": "FeatureCollection", "features": []}, {"total": 0, "found": 0, "not_found": 0, "error": 1}, None

def load_rep_schools():
    """Load the list of REP schools from REP_Toulouse.csv"""
    try:
        rep_schools = []
        
        # Try different encodings
        encodings = ['utf-8', 'latin1']
        for encoding in encodings:
            try:
                with open('REP_Toulouse.csv', 'r', encoding=encoding) as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        rne = row.get('RNE', '').strip().upper()
                        if rne:  # Only add non-empty RNE codes
                            rep_schools.append(rne)
                break  # If we successfully read the file, break the loop
            except UnicodeDecodeError:
                continue
        
        # Log details about the processing
        logger.info(f"Total number of RNE codes: {len(rep_schools)}")
        logger.info("All RNE codes:")
        for code in rep_schools:
            logger.info(f"  {code}")
        
        return rep_schools
    except Exception as e:
        logger.error(f"Error loading REP schools: {str(e)}")
        return []

@app.route('/')
def index():
    schools, stats, table_html = load_schools()
    rep_schools = load_rep_schools()
    return render_template('index.html', 
                         schools=json.dumps(schools),
                         stats=stats,
                         table_html=table_html,
                         rep_schools=json.dumps(rep_schools))

if __name__ == '__main__':
    app.run(debug=True) 
