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
module: logical_router

short_description: create tungstenfabirc logical-router

version_added: "2.10"

description:
    - "create / delete tungstenfabric logical-router"

options:
    name:
        description:
            - logical-router name
        required: true
    controller_ip:
        description:
            - tungstenfabric controller ip
        required: true
    domain:
        description:
            - logical-router subnet
        required: false
    project:
        description:
            - logical-router subnet
        required: false

author:
    - Tatsuya Naganawa (@tnaganawa)
'''

EXAMPLES = '''
# Pass in a message
- name: create logical-router
  tungstenfabric_logical_router:
    name: lr1
    controller_ip: x.x.x.x
    state: present

- name: delete logical-router
  tungstenfabric_logical_router:
    name: lr1
    controller_ip: x.x.x.x
    state: absent

'''

RETURN = '''
message:
    description: The output message that this module generates
    type: str
    returned: always
'''

import json
import requests
from ansible.module_utils.basic import AnsibleModule

def run_module():
    module_args = dict(
        name=dict(type='str', required=True),
        controller_ip=dict(type='str', required=True),
        username=dict(type='str', required=False, default='admin'),
        password=dict(type='str', required=False, default='contrail123'),
        state=dict(type='str', required=False, default='present', choices=['absent', 'present']),
        uuid=dict(type='str', required=False),
        domain=dict(type='str', required=False, default='default-domain'),
        project=dict(type='str', required=False, default='default-project'),
        router_type=dict(type='str', required=False, choices=['snat-routing', 'vxlan-routing'])
        connected_networks=dict(type='list', required=False)
    )
    result = dict(
        changed=False,
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    name = module.params.get("name")
    controller_ip = module.params.get("controller_ip")
    username = module.params.get("username")
    password = module.params.get("password")
    state = module.params.get("state")
    domain = module.params.get("domain")
    project = module.params.get("project")
    router_type = module.params.get("router_type")
    connected_networks = module.params.get("connected_networks")

    if module.check_mode:
        module.exit_json(**result)

    ## begin: logical-router
    config_api_url = 'http://' + controller_ip + ':8082/'
    web_api_url = 'https://' + controller_ip + ':8143/'
    vnc_api_headers= {"Content-Type": "application/json", "charset": "UTF-8"}
    failed = False

    ## check if the fqname exists
    response = requests.post(config_api_url + 'fqname-to-id', data='{"type": "logical_router", "fq_name": ["%s", "%s", "%s"]}' % (domain, project, name), headers=vnc_api_headers)
    if response.status_code == 200:
      update = True
      uuid = json.loads(response.text).get("uuid")
    else:
      update = False

    ## login to web API
    client = requests.session()
    response = client.post(web_api_url + 'authenticate', data=json.dumps({"username": username, "password": password}), headers=vnc_api_headers, verify=False)
    print (client.cookies)
    csrftoken=client.cookies['_csrf']
    vnc_api_headers["x-csrf-token"]=csrftoken

    ## create payload and call API
    js=json.loads (
    '''
    { "logical-router":
      {
        "fq_name": ["%s", "%s", "%s"],
        "parent_type": "project"
      }
    }
    ''' % (domain, project, name)
    )

    #if subnet:
    #  js ["logical-router"]["network_ipam_refs"]=[
    #    {"to": ["default-domain", "default-project", "default-network-ipam"],
    #    "attr": {"ipam_subnets": [{"subnet": {"ip_prefix": subnet, "ip_prefix_len": subnet_prefix}}]}
    #    }
    #  ]


    if state == "present":
      if update:
        print ("update object")
        js["logical-router"]["uuid"]=uuid
        response = client.post(web_api_url + 'api/tenants/config/update-config-object', data=json.dumps(js), headers=vnc_api_headers, verify=False)
      else:
        print ("create object")
        response = client.post(web_api_url + 'api/tenants/config/create-config-object', data=json.dumps(js), headers=vnc_api_headers, verify=False)
    elif (state == "absent"):
      if update:
        print ("delete object {}".format(uuid))
        response = client.post(web_api_url + 'api/tenants/config/delete', data=json.dumps([{"type": "logical-router", "deleteIDs": ["{}".format(uuid)]}]), headers=vnc_api_headers, verify=False)
      else:
        failed = True
    message = response.text

    if response.status_code == 200:
      result['changed'] = True
    else:
      result['changed'] = False
      failed = True

    result['message'] = message

    ## end: logical-router

    if failed:
        module.fail_json(msg='failure message', **result)

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
