import hubspot_resume_functions as hs
import os


# ----------------------------------------------------------------------------------
def main(owner_id, pipeline_id, stage_id, job_type):
    accepted_countries = hs.ACCEPTED_COUNTRIES.split(',')
    data = hs.get_deals_for_pipeline(owner_id, pipeline_id, stage_id, job_type, hs.LIMIT)
    amount = data.get('total', 0)
    deals = data.get('results', [])
    rejected = hs.get_stage_id("Rejected")
    print(f'Found {amount} deals for job type {job_type}\n')
    for deal in deals:
        name = deal.get('properties').get('dealname').split(' - ')[0]
        contact_id = hs.get_associated_contact(deal.get('id'))
        phone = hs.get_contact_property(contact_id, 'phone')
        country = hs.get_country_by_phone_number(phone)
        print(f'{name} ({deal.get('id')})')
        print(f'    {phone} - {country}')
        print(f'    {hs.get_contact_property(contact_id, 'email')}')
        if (country not in accepted_countries) or (country == 'Unknown'):
            print(f'    Candidates from {country} not accepted, rejecting')
            hs.move_deal_to_stage(deal.get('id'), rejected, "Rejected", None, hs.REJECTPATH)
            continue
        resume_url = hs.get_contact_property(contact_id, 'resume')
        if resume_url:
            pdf_path = hs.download_resume(job_type, name, country, resume_url)
            if not pdf_path:
                continue
            print(f'    {pdf_path}')
            if pdf_path.endswith('.pdf'):
                highlighted_path = hs.highlight_words_in_pdf(pdf_path, hs.KEYWORDS)
                if highlighted_path:
                    print(f'    {highlighted_path}')
                txt_path = hs.pdf_to_txt(pdf_path)
                print(f'    {txt_path}')
                hs.analyze_resume(txt_path)
            else:
                print(f'    Manual review required: {pdf_path}')
            print()


# ----------------------------------------------------------------------------------
if __name__ == '__main__':
    import sys
    owner_id = hs.get_owner_id()
    pipeline_id = hs.get_pipeline_id(hs.PIPELINE)
    stage_id = hs.get_stage_id()

    if len(sys.argv) != 2:
        print('Usage: python script.py <job_type>')
        hs.print_all_job_types(owner_id, pipeline_id, stage_id, hs.LIMIT)
        sys.exit(1)
    else:
        main(owner_id, pipeline_id, stage_id, sys.argv[1])
