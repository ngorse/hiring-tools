import subprocess
import hubspot_resume_functions as hs
import getch
import os

# ----------------------------------------------------------------------------------
def main(owner_id, pipeline_id, stage_id, job_type):
    data = hs.get_deals_for_pipeline(owner_id, pipeline_id, stage_id, job_type, hs.LIMIT)
    amount = data.get('total', 0)
    deals = data.get('results', [])
    rejected = hs.get_stage_id("Rejected")
    interview = hs.get_stage_id("Interview")
    print(f'Found {amount} deals for job type {job_type}\n')
    for deal in deals:
        name = deal.get('properties').get('dealname').split(' - ')[0]
        contact_id = hs.get_associated_contact(deal.get('id'))
        phone = hs.get_contact_property(contact_id, 'phone')
        country = hs.get_country_by_phone_number(phone)
        print(f'{name} ({deal.get('id')})')
        print(f'    {phone} - {country}')
        print(f'    {hs.get_contact_property(contact_id, 'email')}')
        path, pdf_path = hs.get_resume_path(job_type, name, country, hs.get_contact_property(contact_id, 'linkedin'))
        summary = pdf_path.replace('.pdf', '.summary.txt')
        highlighted = pdf_path.replace('.pdf', '.highlighted.pdf')
        if os.path.exists(highlighted):
            cmd = f'open "{highlighted}"'
            print(cmd)
            subprocess.run(cmd, shell=True)
        if os.path.exists(summary):
            with open(summary) as f:
                print(f'    {f.read()}')
        char = ''
        deal_id = deal.get('id')
        print(f'    (i)nterview    (r)eject    (s)kip')
        while char not in ['i', 'r', 's']:
            char = getch.getch()
            if char == 'i':
                hs.move_deal_to_stage(deal_id, interview, "Interview", path, hs.INTERVIEWPATH)
            elif char == 'r':
                hs.move_deal_to_stage(deal_id, rejected, "Rejected", path, hs.REJECTPATH)
            else:
                print('Skipped')
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
