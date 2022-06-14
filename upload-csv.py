#!/usr/bin/env python

import requests
import json
from datetime import datetime
import csv
import config


'''Reads in the metadata from your export CSV and readies it for import.'''
def process_csv(file):
    reader = csv.DictReader(file)
    processed_csv = []
    # TODO: determine if set or random prefix is used here.
    prefix = config.doiPrefix

    try:
        for row in reader:
            processed_csv.append({
                'id': row['context_key'],
                'creators': [
                    {
                        'name': row['creator1'],
                        'nameType': row['creator1_type'],
                        'givenName': row['creator1_given'],
                        'familyName': row['creator1_family']
                    },{
                        'name': row['creator2'],
                        'nameType': row['creator2_type'],
                        'givenName': row['creator2_given'],
                        'familyName': row['creator2_family']
                    }
                ],
                'year': row['date'],
                'uri': row['source'],
                'title': row['title'],
                'type': row['type'],
                'descriptions': [{
                    'description': row['description'],
                    'descriptionType': 'Abstract'
                }],
                'publisher': row['publisher'],
                'doi': '{0}/{1}'.format(prefix, row['context_key'])
            })
    except Exception as e:
        print(e)
        file.close()
        exit()

    return processed_csv


'''Process and submit DOIs to DataCite.'''
def submit_dois(dois):
    export = []

    for doi in dois:
        export_row = {}
        data = {
            'data': {
                'id': doi['doi'],
                'type': 'dois',
                'attributes': {
                    'event': 'publish',
                    'doi': doi['doi'],
                    'creators': doi['creators'],
                    'titles': [{
                        'title': doi['title']
                    }],
                    'publisher': doi['publisher'],
                    'publicationYear': doi['year'],
                    'descriptions': doi['descriptions'],
                    'types': {
                        'resourceTypeGeneral': 'Text',
                        'resourceType': doi['type']
                    },
                    'schemaVersion': 'http://datacite.org/schema/kernel-4',
                    'url': doi['uri']
                }
            }
        }

        json_data = json.dumps(data, ensure_ascii=False)
        response = requests.post(
            config.url,
            headers={'Content-Type': 'application/vnd.api+json'},
            data=json_data.encode('utf-8'),
            auth=(config.username, config.password)
        )
        print('{0} processed, response: {1}'.format(doi['doi'], response.status_code))
        export_row['id'] = doi['id']
        export_row['doi'] = 'https://doi.org/{0}'.format(doi['doi'])
        export_row['status'] = response.status_code
        export.append(export_row)

    return export


'''Saves a CSV file of the results.'''
def save_results(results):
    try:
        file = open('upload-report-{0}.csv'.format(datetime.now().strftime('%Y%m%d-%H%M%S')), 'w', newline='')
        fields = [
            'id',
            'doi',
            'status'
        ]
        writer = csv.DictWriter(file, fieldnames=fields)

        writer.writeheader()
        writer.writerows(results)
    except:
        print('Error saving report CSV.')
        exit()
    finally:
        file.close()



file_name = input('Please enter the name of your CSV file.\n')
try:
    file = open(file_name, newline='', errors='ignore')
except:
    print('Error reading file.')
    exit()

dois = process_csv(file)
file.close()
results = submit_dois(dois)
save_results(results)
