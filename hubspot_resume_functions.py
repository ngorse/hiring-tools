import os
import json
import magic
import shutil
import requests
import subprocess
import phonenumbers
from dotenv import load_dotenv
from phonenumbers import geocoder
from pdf_transformations import highlight_words_in_pdf, pdf_to_txt


# ----------------------------------------------------------------------------------
load_dotenv()
TOKEN = os.getenv('TOKEN')
OWNER = os.getenv('OWNER')
PIPELINE = os.getenv('PIPELINE')
STAGE = os.getenv('STAGE')
LIMIT = os.getenv('LIMIT')
KEYWORDS = os.getenv('KEYWORDS')
SAVEPATH = os.getenv('SAVEPATH')
REJECTPATH = os.getenv('REJECTPATH')
INTERVIEWPATH = os.getenv('INTERVIEWPATH')

BASE_URL = 'https://api.hubapi.com/crm/v3'
HEADERS = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json'
}


# ----------------------------------------------------------------------------------
def get_owner_id(name=OWNER):
    response = requests.get(f'{BASE_URL}/owners/?limit=100', headers=HEADERS)
    data = response.json()
    for owner in data.get('results', []):
        if name.lower() in owner.get('email', '').lower():
            return owner.get('id')
    return None


# ----------------------------------------------------------------------------------
def get_pipeline_id(pipeline_name):
    response = requests.get(f'{BASE_URL}/pipelines/deals', headers=HEADERS)
    data = response.json()
    for pipeline in data.get('results', []):
        if pipeline_name.lower() in pipeline.get('label', '').lower():
            return pipeline.get('id')
    return None


# ----------------------------------------------------------------------------------
def get_stage_id(stage=STAGE):
    response = requests.get(f'{BASE_URL}/pipelines/deals', headers=HEADERS)
    data = response.json()
    for pipeline in data.get('results', []):
        for stage_data in pipeline.get('stages', []):
            if stage.lower() in stage_data.get('label', '').lower():
                return stage_data.get('id')
    return None


# ----------------------------------------------------------------------------------
def get_deals_for_pipeline(owner_id, pipeline_id, stage_id, job_type, limit):
    payload = {
        'filterGroups': [{
            'filters': [
                {'propertyName': 'hubspot_owner_id', 'operator': 'EQ', 'value': owner_id},
                {'propertyName': 'pipeline', 'operator': 'EQ', 'value': pipeline_id},
                {'propertyName': 'dealstage', 'operator': 'EQ', 'value': stage_id},
                {'propertyName': 'dealname', 'operator': 'CONTAINS_TOKEN', 'value': job_type}
            ]
        }],
        'properties': ['dealname', 'dealstage', 'hubspot_owner_id'],
        'limit': limit
    }
    response = requests.post(f'{BASE_URL}/objects/deals/search', headers=HEADERS, json=payload)

    if response.status_code == 200:
        deals = response.json()
    else:
        print(f'Error {response.status_code}: {response.text}')
        deals = {}

    return deals


# ----------------------------------------------------------------------------------
def get_associated_contact(deal_id):
    response = requests.get(f'{BASE_URL}/objects/deals/{deal_id}/associations/contacts', headers=HEADERS)
    data = response.json()
    return data.get('results', [{}])[0].get('id')


# ----------------------------------------------------------------------------------
def get_contact_property(contact_id, info):
    response = requests.get(f'{BASE_URL}/objects/contacts/{contact_id}?properties={info}', headers=HEADERS)
    data = response.json()
    return data.get('properties', {}).get(info)


# ----------------------------------------------------------------------------------
def move_deal_to_stage(deal_id, stage_id, stage_name, path, stage_path):
    url = f"{BASE_URL}/objects/deals/{deal_id}"
    payload = {
        "properties": {
            "dealstage": stage_id
        }
    }
    response = requests.patch(url, headers=HEADERS, json=payload)

    if response.status_code == 200:
        _, dir_name = os.path.split(path)
        print(f'    Moved to {stage_name}, {stage_path}/{dir_name}')
        os.makedirs(stage_path, exist_ok=True)
        shutil.move(path, f'{stage_path}/{dir_name}')
    else:
        print(f"Error {response.status_code}: {response.text}")


# ----------------------------------------------------------------------------------
def send_email_via_hubspot(deal_id, subject, body):
    to_email = get_associated_contact(deal_id)

    url = "https://api.hubapi.com/marketing/v3/transactional/single-email/send"
    payload = {
        "emailId": "nico@secretsaucepartners.com",
        "message": {
            "to": to_email,
            "subject": subject,
            "html": body
        }
    }
    response = requests.post(url, headers=HEADERS, data=json.dumps(payload))

    if response.status_code == 200:
        email_data = response.json()
        print("    Email sent successfully")
        if email_data.get('id'):
            attach_email_to_deal(deal_id, email_data.get('id'))
        else:
            print("    Failed to attach email to deal")
    else:
        print(f"Error {response.status_code}: {response.text}")


# ----------------------------------------------------------------------------------
def attach_email_to_deal(deal_id, email_id):
    url = f"https://api.hubapi.com/crm/v3/objects/deals/{deal_id}/associations/emails/{email_id}"
    response = requests.put(url, headers=HEADERS)

    if response.status_code == 200:
        print(f"    Email {email_id} attached to deal {deal_id} successfully")
    else:
        print(f"    Error {response.status_code}: {response.text}")


# ----------------------------------------------------------------------------------
def get_country_by_phone_number(phone_number):
    try:
        parsed_number = phonenumbers.parse(phone_number)
        country = geocoder.country_name_for_number(parsed_number, 'en')
        if not country:
            country = geocoder.region_code_for_number(parsed_number)
        return country
    except Exception:
        return 'UnknownCountry'


# ----------------------------------------------------------------------------------
def get_resume_path(job_type, name, country, url):
    name_ = name.replace(' ', '_').replace('\'', '')
    savepath = f'{SAVEPATH}/{job_type}-{country}-{name_}'
    outfile = f'{savepath}/{job_type}-{country}-{name_}.pdf'
    return savepath, outfile


# ----------------------------------------------------------------------------------
def download_resume(job_type, name, country, url):
    savepath, outfile = get_resume_path(job_type, name, country, url)
    os.makedirs(savepath, exist_ok=True)
    if os.path.exists(outfile):
        print('    Already processed, skipping\n')
        return None

    response = requests.get(url, headers=HEADERS)
    with open(outfile, 'wb') as f:
        for chunk in response.iter_content(1024):
            f.write(chunk)
    file_magic = magic.Magic()
    file_type = file_magic.from_file(outfile)
    if 'Word' in file_type:
        os.rename(outfile, outfile.replace('.pdf', '.docx')) 
        outfile = outfile.replace('.pdf', '.docx')
    return outfile


# ----------------------------------------------------------------------------------
def analyze_resume(txt_path):
    analysis_path = txt_path.replace('.txt', '.summary.txt')
    cmd = f'echo "summarize this resume without giving any explanation: `cat {txt_path.replace(" ", "\\ ")}`" | ollama run llama3.2'
    with open(analysis_path, 'w') as f:
        subprocess.run(cmd, shell=True, stdout=f)
    print(f'    {analysis_path}')


# ----------------------------------------------------------------------------------
def print_all_job_types(owner_id, pipeline_id, stage_id, limit):
    deals = get_deals_for_pipeline(owner_id, pipeline_id, stage_id, '*', limit)
    deal_names = set()
    for deal in deals.get('results', []):
        deal_names.add(deal.get('properties').get('dealname').split(' - ')[1])
    print(f'Where available job types is one of:\n    {'\n    '.join(deal_names)}')

