import camelot
import pandas as pd
import re

def clean_etablissement(text):
    """Clean school names while preserving institution codes"""
    return re.sub(r'\s+', ' ', text).strip()

def process_pdf_to_csv(pdf_path, csv_path):
    # Extract tables using lattice mode (best for bordered LaTeX tables)
    tables = camelot.read_pdf(
        pdf_path,
        pages='all',
        flavor='lattice',
        strip_text='\n',
        suppress_stdout=True
    )
    
    # Combine all tables into one DataFrame
    df = pd.concat([table.df for table in tables], ignore_index=True)
    
    # Clean headers from multi-line fragments
    df.columns = [
        "Rang", "Numéro du poste", "Commune", "Etablissement",
        "Type de poste", "Nature de support", "Spécialité / Nb classes",
        "Nb de postes vacants", "Nb de postes susceptibles d'être vacants"
    ]
    
    # Remove duplicate header rows
    df = df[df['Rang'] != 'Rang'].reset_index(drop=True)
    
    # Clean data
    df['Etablissement'] = df['Etablissement'].apply(clean_etablissement)
    df['Type de poste'] = 'E'  # All values are 'E' based on the document
    
    # Convert numerical columns to integers
    int_cols = ['Rang', 'Nb de postes vacants', 'Nb de postes susceptibles d\'être vacants']
    df[int_cols] = df[int_cols].apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)
    
    # Save to CSV
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"Successfully exported {len(df)} rows to {csv_path}")

if __name__ == "__main__":
    input_pdf = "Celia-Voeu-Groupe-51822-April-18-2025.pdf"
    output_csv = "mouvement_complet.csv"
    process_pdf_to_csv(input_pdf, output_csv)


