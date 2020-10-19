#!/usr/bin/python

# Copyright: (c) 2020, Tatsuya Naganawa <tatsuyan201101@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: virtual_network

short_description: create tungstenfabirc virtual-network

version_added: "2.10"

description:
    - "create / delete tungstenfabric virtual-network"

options:
    name:
        description:
            - virtual-network name
        required: true
    controller_ip:
        description:
            - tungstenfabric controller ip
        required: true
    subnet:
        description:
            - virtual-network subnet
        required: false
    subnet_prefix:
        description:
            - virtual-network subnet prefix
        required: false
    domain:
        description:
            - virtual-network subnet
        required: false
    project:
        description:
            - virtual-network subnet
        required: false
    forwarding_mode:
        description:
            - set forwarding mode (L2_L3, L2, L3)
        required: false
    rpf:
        description:
            - set rpf (enable or disable)
        required: false
    allow_transit:
        description:
            - set allow_transit (true or false)
        required: false
    vxlan_network_identifier:
        description:
            - set vni of this virtual-network
        required: false
    route_target_list:
        description:
            - list of route-target
        required: false
    import_route_target_list:
        description:
            - list of import route-target
        required: false
    export_route_target_list:
        description:
            - list of export route-target
        required: false
    network_policy_refs:
        description:
            - set network-policy (fq_name of network-policy)
        required: false

author:
    - Tatsuya Naganawa (@tnaganawa)
'''

EXAMPLES = '''
# Pass in a message
- name: create virtual-network
  tungstenfabric_virtual_network:
    name: vn1
    controller_ip: x.x.x.x
    state: present
    project: admin
    subnet: 10.0.1.0
    subnet_prefix: 24

- name: delete virtual-network
  tungstenfabric_virtual_network:
    name: vn1
    controller_ip: x.x.x.x
    state: absent
    project: admin

- name: create virtual-network with some parameters
  tungstenfabric_virtual_network:
    name: vn1
    controller_ip: x.x.x.x
    state: present
    project: admin
    subnet: 10.0.1.0
    subnet_prefix: 24
    rpf: enable
    vxlan_network_identifier: 101
    route_target_list: [target:64512:101, target:65501:101]
    network_policy_refs: [default-domain:admin:vn1-to-vn2]

'''

RETURN = '''
message:
    description: The output message that this module generates
    type: str
    returned: always
'''

import sys
import uuid as uuid_module
import json
import requests
from ansible.module_utils.basic import AnsibleModule
import ansible_collections.tungstenfabric.networking.plugins.module_utils.common

def run_module():
    module_args = dict(
        name=dict(type='str', required=True),
        controller_ip=dict(type='str', required=True),
        username=dict(type='str', required=False, default='admin'),
        password=dict(type='str', required=False, default='contrail123'),
        state=dict(type='str', required=False, default='present', choices=['absent', 'present']),
        global_object=dict(type='bool', required=False),
        uuid=dict(type='str', required=False),
        domain=dict(type='str', required=False, default='default-domain'),
        project=dict(type='str', required=False, default='default-project'),
        subnet=dict(type='str', required=False),
        subnet_prefix=dict(type='int', required=False),
        flood_unknown_unicast=dict(type='bool', required=False),
        ip_fabric_forwarding=dict(type='bool', required=False),
        fabric_snat=dict(type='bool', required=False),
        display_name=dict(type='str', required=False),
        igmp_enable=dict(type='bool', required=False),
        mac_learning_enabled=dict(type='bool', required=False),
        port_security_enabled=dict(type='bool', required=False),
        allow_transit=dict(type='bool', required=False),
        forwarding_mode=dict(type='str', required=False, choices=['default', 'l2_l3', 'l3', 'l2']),
        max_flows=dict(type='int', required=False),
        rpf=dict(type='str', required=False, choices=['enable', 'disable']),
        vxlan_network_identifier=dict(type='int', required=False),
        route_target_list=dict(type='list', required=False),
        import_route_target_list=dict(type='list', required=False),
        export_route_target_list=dict(type='list', required=False),
        network_policy_refs=dict(type='list', required=False)
    )
    result = dict(
        changed=False,
        message=''
    )

    required_if_args = [
      ["global_object", True, ["domain", "project", "name", "route_target_list", "vxlan_network_identifier"]]
    ]

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=required_if_args
    )

    name = module.params.get("name")
    controller_ip = module.params.get("controller_ip")
    username = module.params.get("username")
    password = module.params.get("password")
    state = module.params.get("state")
    domain = module.params.get("domain")
    project = module.params.get("project")
    subnet = module.params.get("subnet")
    subnet_prefix = module.params.get("subnet_prefix")
    flood_unknown_unicast = module.params.get("flood_unknown_unicast")
    ip_fabric_forwarding = module.params.get("ip_fabric_forwarding")
    fabric_snat = module.params.get("fabric_snat")
    rpf = module.params.get("rpf")
    allow_transit = module.params.get("allow_transit")
    forwarding_mode = module.params.get("forwarding_mode")
    vxlan_network_identifier = module.params.get("vxlan_network_identifier")
    route_target_list = module.params.get("route_target_list")
    import_route_target_list = module.params.get("import_route_target_list")
    export_route_target_list = module.params.get("export_route_target_list")
    network_policy_refs = module.params.get("network_policy_refs")

    if module.check_mode:
        module.exit_json(**result)

    ## begin: virtual-network
    config_api_url = 'http://' + controller_ip + ':8082/'
    web_api_url = 'https://' + controller_ip + ':8143/'
    vnc_api_headers= {"Content-Type": "application/json", "charset": "UTF-8"}
    failed = False

    ## check if the fqname exists
    response = requests.post(config_api_url + 'fqname-to-id', data='{"type": "virtual_network", "fq_name": ["%s", "%s", "%s"]}' % (domain, project, name), headers=vnc_api_headers)
    if response.status_code == 200:
      update = True
      uuid = json.loads(response.text).get("uuid")
    else:
      update = False

    ## login to web API
    client = requests.session()
    response = client.post(web_api_url + 'authenticate', data=json.dumps({"username": username, "password": password}), headers=vnc_api_headers, verify=False)
    #print (client.cookies)
    csrftoken=client.cookies['_csrf']
    vnc_api_headers["x-csrf-token"]=csrftoken

    if update and state=='present':
      response = client.post(web_api_url + 'api/tenants/config/get-config-objects', data=json.dumps({"data": [{"type": "virtual-network", "uuid": ["{}".format(uuid)]}]}), headers=vnc_api_headers, verify=False)
      js = json.loads(response.text)[0]
    else:
      ## create payload and call API
      js=json.loads (
      '''
      { "virtual-network":
        {
          "fq_name": ["%s", "%s", "%s"],
          "parent_type": "project"
        }
      }
      ''' % (domain, project, name)
      )

    if subnet:
      if (js["virtual-network"].get("network_ipam_refs")==None):
        js ["virtual-network"]["network_ipam_refs"]=[
          {"to": ["default-domain", "default-project", "default-network-ipam"],
          "attr": {"ipam_subnets": [{"subnet": {"ip_prefix": subnet, "ip_prefix_len": subnet_prefix}}]}
          }
        ]
        subnet_uuid=str(uuid_module.uuid4())
        js ["virtual-network"]["network_ipam_refs"][0]["attr"]["ipam_subnets"][0]["subnet_uuid"]=subnet_uuid
        js ["virtual-network"]["network_ipam_refs"][0]["attr"]["ipam_subnets"][0]["subnet_name"]=subnet_uuid
    if flood_unknown_unicast:
      js ["virtual-network"]["flood_unknown_unicast"]=True
    if ip_fabric_forwarding:
      js ["virtual-network"]["ip_fabric_forwarding"]=True
    if fabric_snat:
      js ["virtual-network"]["fabric_snat"]=True
    if network_policy_refs:
      # ["default-domain:admin:network-policy1"], []]
      network_policy_refs_list=[]
      for np_fqname in network_policy_refs:
        response = requests.post(config_api_url + 'fqname-to-id', data=json.dumps({"type": "network-policy", "fq_name": np_fqname.split(":")}), headers=vnc_api_headers)
        if not response.status_code == 200:
          module.fail_json(msg="network-policy specified doesn't exist", **result)
        np_uuid = json.loads(response.text).get("uuid")
        network_policy_refs_list.append ({"to": np_fqname.split(":"), "uuid": np_uuid, "attr": {"sequence": {"major": 0, "minor": 0}}})

      js ["virtual-network"]["network_policy_refs"]=network_policy_refs_list

    if js["virtual-network"].get("virtual_network_properties")==None:
      js ["virtual-network"]["virtual_network_properties"]={}
    if rpf:
      js ["virtual-network"]["virtual_network_properties"]["rpf"]=rpf
    if allow_transit:
      js ["virtual-network"]["virtual_network_properties"]["allow_transit"]=allow_transit
    if forwarding_mode:
      js ["virtual-network"]["virtual_network_properties"]["forwarding_mode"]=forwarding_mode
    if vxlan_network_identifier:
      js ["virtual-network"]["virtual_network_properties"]["vxlan_network_identifier"]=vxlan_network_identifier
    if route_target_list:
      js ["virtual-network"]["route_target_list"]={"route_target": route_target_list}
    if import_route_target_list:
      js ["virtual-network"]["import_route_target_list"]={"route_target": import_route_target_list}
    if export_route_target_list:
      js ["virtual-network"]["export_route_target_list"]={"route_target": export_route_target_list}


    if state == "present":
      if update:
        print ("update object")
        js["virtual-network"]["uuid"]=uuid
        response = client.post(web_api_url + 'api/tenants/config/update-config-object', data=json.dumps(js), headers=vnc_api_headers, verify=False)
      else:
        print ("create object")
        response = client.post(web_api_url + 'api/tenants/config/create-config-object', data=json.dumps(js), headers=vnc_api_headers, verify=False)
    elif (state == "absent"):
      if update:
        print ("delete object {}".format(uuid))
        response = client.post(web_api_url + 'api/tenants/config/delete', data=json.dumps([{"type": "virtual-network", "deleteIDs": ["{}".format(uuid)]}]), headers=vnc_api_headers, verify=False)
      else:
        failed = True
    message = response.text

    if response.status_code == 200:
      result['changed'] = True
    else:
      result['changed'] = False
      failed = True

    result['message'] = message

    ## end: virtual-network

    if failed:
        module.fail_json(msg='failure message', **result)

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
