from pprint import pprint
import app.route_53 as r53

domains_to_delete = r53.return_domains_by_comment("HostedZone created by Route53 Registrar")

for domain in domains_to_delete:
    resp = r53.list_resource_record_sets(domain['Id'])
    for record in resp['ResourceRecordSets']:
        if record['Type'] not in ['SOA','NS']:
            #r53.update_dns_record(domain['Id'],record,'DELETE')
    #r53.delete_dns_zone(domain['Id'])
    print("Deleting: %s" % domain['Name'])