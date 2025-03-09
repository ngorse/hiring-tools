import os
import requests
import json
import subprocess
from dotenv import load_dotenv
import phonenumbers
from phonenumbers import geocoder

load_dotenv()
TOKEN = os.getenv("TOKEN")
OWNER = os.getenv("OWNER")
PIPELINE = os.getenv("PIPELINE")
STAGE = os.getenv("STAGE")
LIMIT = os.getenv("LIMIT")

BASE_URL = "https://api.hubapi.com/crm/v3"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# ----------------------------------------------------------------------------------
def get_owner_id(name=OWNER):
    response = requests.get(f"{BASE_URL}/owners/?limit=100", headers=HEADERS)
    data = response.json()
    for owner in data.get("results", []):
        if name.lower() in owner.get("email", "").lower():
            return owner.get("id")
    return None


# ----------------------------------------------------------------------------------
def get_pipeline_id(pipeline_name):
    response = requests.get(f"{BASE_URL}/pipelines/deals", headers=HEADERS)
    data = response.json()
    for pipeline in data.get("results", []):
        if pipeline_name.lower() in pipeline.get("label", "").lower():
            return pipeline.get("id")
    return None


# ----------------------------------------------------------------------------------
def get_hiring_stage_id(stage=STAGE):
    response = requests.get(f"{BASE_URL}/pipelines/deals", headers=HEADERS)
    data = response.json()
    for pipeline in data.get("results", []):
        for stage_data in pipeline.get("stages", []):
            if stage.lower() in stage_data.get("label", "").lower():
                return stage_data.get("id")
    return None


# ----------------------------------------------------------------------------------
def get_deals_for_pipeline(owner_id, pipeline_id, stage_id, job, limit):
    payload = {
        "filterGroups": [{
            "filters": [
                {"propertyName": "hubspot_owner_id", "operator": "EQ", "value": owner_id},
                {"propertyName": "pipeline", "operator": "EQ", "value": pipeline_id},
                {"propertyName": "dealstage", "operator": "EQ", "value": stage_id},
                {"propertyName": "dealname", "operator": "CONTAINS_TOKEN", "value": job}
            ]
        }],
        "properties": ["dealname", "dealstage", "hubspot_owner_id"],
        "limit": limit
    }
    response = requests.post(f"{BASE_URL}/objects/deals/search", headers=HEADERS, json=payload)

    if response.status_code == 200:
        deals = response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")
        deals = {}

    return deals


# ----------------------------------------------------------------------------------
def get_associated_contact(deal_id):
    response = requests.get(f"{BASE_URL}/objects/deals/{deal_id}/associations/contacts", headers=HEADERS)
    data = response.json()
    return data.get("results", [{}])[0].get("id")


# ----------------------------------------------------------------------------------
def get_contact_property(contact_id, info):
    response = requests.get(f"{BASE_URL}/objects/contacts/{contact_id}?properties={info}", headers=HEADERS)
    data = response.json()
    return data.get("properties", {}).get(info)


# ----------------------------------------------------------------------------------
def download_resume(job, deal, url):
    os.makedirs("resumes", exist_ok=True)
    outfile = f"resumes/{job}-{deal}-{url.split('/')[-1]}"
    response = requests.get(url, headers=HEADERS, stream=True)
    with open(outfile, 'wb') as f:
        for chunk in response.iter_content(1024):
            f.write(chunk)
    print(f"Resume downloaded: {outfile}")
    return outfile


# ----------------------------------------------------------------------------------
def analyze_resume(job, pdf):
    txt = pdf.replace(".pdf", ".txt")
    subprocess.run(["pdftotext", pdf, txt])
    analysis = pdf.replace(".pdf", ".analysis")
    cmd = f'echo "Analyze job {job} vs resume {txt}" | ollama run hr-agent'
    #with open(analysis, "w") as f:
    #    subprocess.run(cmd, shell=True, stdout=f)
    #print(f"Analysis saved: {analysis}")


# ----------------------------------------------------------------------------------
def print_all_job_types(owner_id, pipeline_id, stage_id, limit):
    deals = get_deals_for_pipeline(owner_id, pipeline_id, stage_id, '*', limit)
    deal_names = set()
    for deal in deals.get("results", []):
        deal_names.add(deal.get("properties").get("dealname").split(' - ')[1])
    print(f'Where available job types is one of:\n    {"\n    ".join(deal_names)}')


# ----------------------------------------------------------------------------------
def get_country_by_phone_number(phone_number):
    try:
        parsed_number = phonenumbers.parse(phone_number)
        country = geocoder.description_for_number(parsed_number, "en")
        return country
    except phonenumbers.phonenumberutil.NumberParseException:
        return "?"


# ----------------------------------------------------------------------------------
def main(owner_id, pipeline_id, stage_id, job_type):
    data = get_deals_for_pipeline(owner_id, pipeline_id, stage_id, job_type, LIMIT)
    amount = data.get("total", 0)
    deals = data.get("results", [])
    print(f'Found {amount} deals for job type "job_type"\n')
    for deal in deals:
        print(f'{deal.get("properties").get("dealname").split(' - ')[0]}')
        contact_id = get_associated_contact(deal.get("id"))
        phone = get_contact_property(contact_id, 'phone')
        country = get_country_by_phone_number(phone)
        print(f'    {phone} - {country}')
        print(f'    {get_contact_property(contact_id, "email")}')
        print()

#    for deal in get_deals(owner_id, stage_id, job):
#        contact = get_associated_contact(deal)
#        resume_url = get_contact_property(contact, 'resume')
#        print(f'Deal ID: {deal.get("id")}')
#        if resume_url:
#            pdf_path = download_resume(job, deal, resume_url)
#            if pdf_path.endswith(".pdf"):
#                analyze_resume(job, pdf_path)
#            else:
#                print(f"Manual review required: {pdf_path}")

if __name__ == "__main__":
    import sys
    owner_id = get_owner_id()
    pipeline_id = get_pipeline_id(PIPELINE)
    stage_id = get_hiring_stage_id()

    if len(sys.argv) != 2:
        print("Usage: python script.py <job_type>")
        print_all_job_types(owner_id, pipeline_id, stage_id, LIMIT)
        sys.exit(1)
    else:
        main(owner_id, pipeline_id, stage_id, sys.argv[1])
