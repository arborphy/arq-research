import csv
import json
import os
import requests
import time
from bs4 import BeautifulSoup

def get_traits(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    traits = {}
    
    full_descriptions = soup.select('ul.full-description div.characteristics.full dl')
    
    if not full_descriptions:
        full_descriptions = soup.select('div.characteristics dl')
        
    for dl in full_descriptions:
        dt = dl.find('dt')
        dd = dl.find('dd')
        
        if dt and dd:
            key = dt.get_text(strip=True)
            
            ul = dd.find('ul')
            if ul:
                values = [li.get_text(strip=True) for li in ul.find_all('li')]
                value = values
            else:
                value = dd.get_text(strip=True)
                if value == "NA":
                    value = None
            
            traits[key] = value
            
    return traits

def main():
    observations_file = 'data/observations.csv'
    traits_dir = 'data/traits'
    failures_file = 'data/failed_exports.csv'
    
    # Ensure output directory exists
    os.makedirs(traits_dir, exist_ok=True)
    
    # Initialize failures file if it doesn't exist
    if not os.path.exists(failures_file):
        with open(failures_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['scientific_name', 'url', 'error'])

    # 1. Get unique species
    unique_species = set()
    try:
        with open(observations_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                scientific_name = row.get('scientific_name')
                if scientific_name:
                    unique_species.add(scientific_name)
    except FileNotFoundError:
        print(f"Error: {observations_file} not found.")
        return

    print(f"Found {len(unique_species)} unique species.")
    
    # 2. Process each species
    for i, species in enumerate(unique_species):
        # Generate filename
        safe_name = species.replace(' ', '_').replace('/', '-')
        output_path = os.path.join(traits_dir, f"{safe_name}.json")
        
        # Skip if already exists
        if os.path.exists(output_path):
            # print(f"Skipping {species} (already exists)")
            continue

        parts = species.split()
        if len(parts) >= 2:
            genus = parts[0].lower()
            spec = parts[1].lower()
            
            url = f"https://gobotany.nativeplanttrust.org/species/{genus}/{spec}/"
            
            # Local file check (specifically for the provided example or others)
            local_filename = f"{genus}{spec}.html"
            
            html_content = None
            source = "web"
            
            if os.path.exists(local_filename):
                print(f"[{i+1}/{len(unique_species)}] Processing {species} from local file...")
                try:
                    with open(local_filename, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    source = "local"
                except Exception as e:
                    print(f"Error reading local file {local_filename}: {e}")
            
            if not html_content:
                print(f"[{i+1}/{len(unique_species)}] Fetching {species} from {url}...")
                try:
                    response = requests.get(url)
                    if response.status_code == 200:
                        html_content = response.text
                        time.sleep(1) # Be polite
                    else:
                        print(f"Failed to fetch {url}: {response.status_code}")
                        with open(failures_file, 'a', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow([species, url, f"HTTP {response.status_code}"])
                        continue
                except Exception as e:
                    print(f"Error fetching {url}: {e}")
                    with open(failures_file, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow([species, url, str(e)])
                    continue

            # Extract and Save
            if html_content:
                try:
                    traits = get_traits(html_content)
                    traits['scientific_name'] = species
                    traits['url'] = url
                    traits['source'] = source
                    
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(traits, f, indent=2)
                    # print(f"Saved {output_path}")
                except Exception as e:
                    print(f"Error parsing/saving {species}: {e}")
                    with open(failures_file, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow([species, url, f"Parse/Save Error: {str(e)}"])

if __name__ == "__main__":
    main()
