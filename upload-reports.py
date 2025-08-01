import requests
import sys
from datetime import datetime

# --- Configuration ---
# Replace with your DefectDojo URL and API Token
DEFECTDOJO_URL = 'https://demo.defectdojo.org'
API_TOKEN = 'ca679219925d52d40b438f197ceedfc1b9772491'
# Replace with the ID of the product you want to create the engagement in
PRODUCT_ID = 1

# --- Scan Type Mapping ---
# Maps a keyword in the filename to the DefectDojo 'scan_type'
SCAN_TYPE_MAPPING = {
    'gitleaks': 'Gitleaks Scan',
    'njsscan': 'SARIF',
    'semgrep': 'Semgrep JSON Report',
    'retire': 'Retire.js Scan',
    'trivy': 'Trivy Scan'
}

# --- Script ---
if len(sys.argv) < 2:
    print("Usage: python upload_reports.py <file1> <file2> ...")
    sys.exit(1)

headers = {
    'Authorization': f'Token {API_TOKEN}'
}

def create_engagement(product_id):
    """Creates a new engagement in DefectDojo and returns its ID."""
    engagement_url = f'{DEFECTDOJO_URL}/api/v2/engagements/'
    now = datetime.now()
    engagement_name = f'Automated Scan - {now.strftime("%Y-%m-%d %H:%M:%S")}'
    
    data = {
        'name': engagement_name,
        'product': product_id,
        'target_start': now.strftime("%Y-%m-%d"),
        'target_end': now.strftime("%Y-%m-%d"),
        'engagement_type': 'CI/CD' # Optional: specify the type of engagement
    }
    
    try:
        response = requests.post(engagement_url, headers=headers, json=data)
        response.raise_for_status()  # Raise an exception for bad status codes
        engagement_id = response.json().get('id')
        print(f"Successfully created engagement '{engagement_name}' with ID: {engagement_id}")
        return engagement_id
    except requests.exceptions.RequestException as e:
        print(f"Error creating engagement: {e}")
        print(f"Response content: {response.content.decode('utf-8')}")
        return None

def upload_scan(file_path, engagement_id):
    """Uploads a single scan report to the specified engagement."""
    import_url = f'{DEFECTDOJO_URL}/api/v2/import-scan/'
    
    # Determine scan type from filename
    scan_type = None
    for key, value in SCAN_TYPE_MAPPING.items():
        if key in file_path.lower():
            scan_type = value
            break
            
    if not scan_type:
        print(f"Warning: Could not determine scan type for '{file_path}'. Skipping.")
        return

    data = {
        'active': True,
        'verified': True,
        'scan_type': scan_type,
        'minimum_severity': 'Low',
        'engagement': engagement_id
    }
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(import_url, headers=headers, data=data, files=files)
            response.raise_for_status()
            print(f"Successfully imported '{file_path}' as '{scan_type}'.")
    except FileNotFoundError:
        print(f"Error: File not found at '{file_path}'.")
    except requests.exceptions.RequestException as e:
        print(f"Failed to import scan results for '{file_path}': {e}")
        print(f"Response content: {response.content.decode('utf-8')}")


# --- Main execution ---
if __name__ == "__main__":
    new_engagement_id = create_engagement(PRODUCT_ID)
    
    if new_engagement_id:
        scan_files = sys.argv[1:]
        print(f"\nUploading {len(scan_files)} scan file(s) to engagement ID {new_engagement_id}...")
        for file_name in scan_files:
            upload_scan(file_name, new_engagement_id)
        print("\nScript finished.")
