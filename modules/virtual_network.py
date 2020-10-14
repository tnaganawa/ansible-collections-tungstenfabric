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
    domain:
        description:
            - virtual-network subnet
        required: false
    project:
        description:
            - virtual-network subnet
        required: false

author:
    - Tatsuya Naganawa (@yourhandle)
'''

EXAMPLES = '''
# Pass in a message
- name: create virtual-network
  tungstenfabric_virtual_network:
    name: vn1
    controller_ip: x.x.x.x
    state: present

- name: delete virtual-network
  tungstenfabric_virtual_network:
    name: vn1
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
        subnet=dict(type='str', required=False, default=False)
        domain=dict(type='str', required=False, default='default-domain')
        project=dict(type='str', required=False, default='default-project')
        state=dict(type='str', required=False, default='present', choices=['absent', 'present'])
    )

    result = dict(
        changed=False,
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        module.exit_json(**result)

    ## begin: virtual-network
    config_api_url = 'http://' + controller_ip + ':8082/'
    web_api_url = 'https://' + controller_ip + ':8143/'
    vnc_api_headers= {"Content-Type": "application/json", "charset": "UTF-8"}
    failed = False

    ## check if the fqname exists
    response = json.loads(requests.post(config_api_url + 'fqname-to-id').content.decode('UTF-8'), headers=vnc_api_headers)
    if response.status_code == 200:
      update = True
      uuid = json.loads(response.text).get("uuid")
    else:
      update = False


    js=json.loads (
    """{"fq_name": ["%s", "%s", "%s"]
    "parent_type": "project"
    """ % (domain, project, name)
    }
    )
    if state == "present":
      if update:
        js["uuid"]=uuid
        response = json.loads(requests.post(web_api_url + 'api/tenants/config/create-config-object').content.decode('UTF-8'), data=json.dumps(js), headers=vnc_api_headers, verify=False)
      else:
        response = json.loads(requests.post(web_api_url + 'api/tenants/config/update-config-object').content.decode('UTF-8'), data=json.dumps(js), headers=vnc_api_headers, verify=False)
      message = response.text
    elif state == "absent":
      if update:
        js["uuid"]=uuid
        response = json.loads(requests.post(web_api_url + 'api/tenants/config/delete').content.decode('UTF-8'), data=json.dumps([{"type": "virtual-network", "deleteIDs": ["{}".format(uuid)]}]), headers=vnc_api_headers, verify=False)
      else:
        pass

    if response.status_code == 200:
      result['changed'] = True
    elif:
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
