from django.core.management.base import BaseCommand
from django_python_job_board import models
import BeautifulSoup
import requests
from datetime import datetime
import re
from collections import defaultdict
import HTMLParser

from django.conf import settings
from django_python_job_board.models import JobListing

board_url = getattr(settings, 'PYTHON_JOB_BOARD_URL', 
                    'http://www.python.org/community/jobs/index.html')

job_listing_sections = {'Job Description',
                        'Requirements',
                        'About the company',
                        'Contact Info:',
                        'Python is used'
                        
                        }

contact_info_types = {'contact_name':'Contact',
                      'contact_email':'(E-mail|email)',
                      'contact_other': 'Other',
                      'contact_web': 'Web',
                       }


class Command(BaseCommand):
    
    def handle(self, *args, **options):
        r = requests.get(board_url)
        soup = BeautifulSoup.BeautifulSoup(r.text)
        
        job_divs = soup.findAll('div', {'class':'section'})
        
        for div in job_divs:
            job_info = {}
            job_info['original_id'] = div.attrMap['id']
            head = div.find('h2')
            anchor = head.find('a')
            if anchor:
                job_info['company_url'] = dict(anchor.attrs)['href'] #for some reason this doesn't have an attrMap
                job_info['company_name'] = anchor.text
                anchor.extract() #discard it so the remainder is location
                job_info['job_location'] = head.text.strip('() ') #remove parens and spaces at ends
            else: #no url in header, try a regex
                m = re.match("^(.*) \((.*)\)$", head.text)
                if m:
                    job_info['company_name'] = m.groups()[0]
                    job_info['job_location'] = m.groups()[1]
            
            
            job_posted_str = div.findAll('em')[0].text
            job_posted_str = job_posted_str.replace('Posted ', '')
            try:
                job_info['date_posted'] = datetime.strptime(job_posted_str, '%d-%B-%Y')
            except ValueError:
                print "Can't make a date out of: ", job_posted_str
            descriptions = defaultdict(list)
            
            #find and parse the job descriptions
            job_description_head = div.find('p', text=re.compile('Job Description'))
            if job_description_head:
                jdp = job_description_head.findParent('p') #back to <p><strong>Job Description</strong></p>
                for sibling in jdp.findNextSiblings():
                    text = sibling.text
                    if text in job_listing_sections:
                        break #done, we hit another section
                    m = re.match('(.*?) \((.*)\)$', text) #try to parse:  Job Title (City, Country)
                    if m:
                        job_info['job_title'] = m.groups()[0]
                    else: #not the job title/location
                        descriptions['job_description'].append(text)

            #find and parse the job requirements
            requirements_head = div.find('p', text=re.compile('Requirements'))
            if requirements_head:
                rp = requirements_head.findParent('p')
                requirements = rp.findNextSibling()
                if requirements.find('li'):
                    for item in requirements.findAll('li'):
                        descriptions['requirements'].append(item.text)
                else:
                    descriptions['requirements'] = [requirements.text]
            #find and parse company description
            about_company_head = div.find('p', text=re.compile('About the company'))
            if about_company_head:
                acp = about_company_head.findParent('p')
                for sibling in acp.findNextSiblings():
                    text = sibling.text
                    if text in job_listing_sections:
                        break
                    descriptions['company_description'].append(text)
            
            #find and parse contact list
            contact_head = div.find('p', text=re.compile('Contact Info'))
            if contact_head:
                chp = contact_head.findParent('p')
                contact_list = chp.findNextSibling('ul')
                for contact_type, contact_regex in contact_info_types.items():
                    contact_strong = contact_list.find('strong', text=re.compile(contact_regex))
                    if not contact_strong:
                        continue
                    cp = contact_strong.findParent('li')
                    if not cp:
                        continue
                    contact_strong.extract() #remove the <strong> contents
                    try:
                        contact_text = cp.text
                        contact_text.lstrip(' :') #remove any leading spaces or colons
                        job_info[contact_type] = html_entity_decode(contact_text).strip(': ')
                    except AttributeError:
                        print "%s has no text?" % cp

            
            for desc_name, desc_value in descriptions.items():
#                print desc_name, desc_value
                desc_value = [xml_encode(v) for v in desc_value]
                job_info[desc_name] = list_to_csv(desc_value)
            
            #create or replace
            try:
                job = JobListing.objects.get(original_id=job_info['original_id'])
                for k,v in job_info.items():
                    setattr(job, k, v)
                job.save()
            except JobListing.DoesNotExist:
                job = JobListing(**job_info)
                job.save()

#quick helper to convert a list of strings to a csv-delimited string                    
import csv
from StringIO import StringIO
def list_to_csv(data):
    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(data)
    return buf.getvalue()

def xml_encode(string):
    res = string.encode('ascii', 'xmlcharrefreplace')
    #dumb quotes
    res.replace('&#226;&#128;&#153', "'")
    return res

def html_entity_decode(string):
    h = HTMLParser.HTMLParser()
    return h.unescape(string)
            