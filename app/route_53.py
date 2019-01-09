import boto3
import json
import random
import dns.resolver
import pprint

from botocore.exceptions import ClientError, ParamValidationError

boto_r53d    = boto3.client('route53domains')
boto_r53    = boto3.client('route53')

def return_zones(x_marker = None, x_max_items="300", hosted_zones=list()):

    response = boto_r53.list_hosted_zones(
        MaxItems=x_max_items
    ) if not x_marker else boto_r53.list_hosted_zones(
        Marker=x_marker,
        MaxItems=x_max_items
    )

    for zone in response['HostedZones']:
        zone['Id'] = zone['Id'].split('/')
        zone['Id'] = zone['Id'][int(len(zone['Id']) - 1)]
        hosted_zones.append(zone)

    if response['IsTruncated']:
        x_marker = response['NextMarker']
        return return_zones(x_marker,x_max_items,hosted_zones)

    return hosted_zones

def test_dns_answer(HostedZoneId,RecordName,RecordType='NS',ResolverIP='1.1.1.1'):
    response = boto_r53.test_dns_answer(
        HostedZoneId=HostedZoneId,
        RecordName=RecordName,
        RecordType=RecordType,
        ResolverIP=ResolverIP
    )
    return response

def get_assigned_nameservers(zone_id):
    response = boto_r53.get_hosted_zone(
        Id=zone_id
    )
    return response['DelegationSet']['NameServers']

def get_active_nameservers(domain):
    ns = list()
    try:
        response = dns.resolver.query(domain, 'NS')
    except dns.resolver.NXDOMAIN as ex:
        return ["not-registered"]

    for data in response:
        ns.append(data.to_text()[:-1])

    return ns

def list_resource_record_sets(Id):
    response = boto_r53.list_resource_record_sets(
        HostedZoneId=Id
    )

    return response

def update_dns_record(zone,record,action):
    resp = boto_r53.change_resource_record_sets(
        HostedZoneId=zone,
        ChangeBatch={
            'Changes': [
                {
                    'Action': action,
                    'ResourceRecordSet': record
                },
            ]
        })

    return resp

def delete_dns_zone(zone):
    while True:
        try:
            del_zone_resp = boto_r53.delete_hosted_zone(
                Id=zone
            )
        except boto_r53.exceptions.ClientError as ex:
            continue
        break

    return del_zone_resp

def return_non_pointed_domains(domain_limit = 500, x = None, zones_to_remove = list()):
    for domain in return_zones():
        x = 1 if not x else x + 1
        if x <= domain_limit:
            current_nameservers = get_active_nameservers(domain['DomainName'])
            assigned_nameservers = get_assigned_nameservers(domain['Id'])
            if not set(assigned_nameservers).intersection(current_nameservers):
                zones_to_remove.append(domain)

    return zones_to_remove

def return_domains_by_comment(comment, domain_limit = 500, x = None, zones_to_remove = list()):
    for domain in return_zones():
        x = 1 if not x else x + 1
        if x <= domain_limit:
            if 'Comment' in domain['Config']:
                if domain['Config']['Comment'] == comment:
                    zones_to_remove.append(domain)

    return zones_to_remove