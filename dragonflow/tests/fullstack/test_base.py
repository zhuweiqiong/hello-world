#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os_client_config
from oslo_config import cfg
from oslo_utils import importutils

from neutron.common import config as common_config
from neutronclient.neutron import client

from dragonflow.common import common_params
from dragonflow.db import api_nb
from dragonflow.tests import base


cfg.CONF.register_opts(common_params.df_opts, 'df')


def get_cloud_config(cloud='devstack-admin'):
    return os_client_config.OpenStackConfig().get_one_cloud(cloud=cloud)


def credentials(cloud='devstack-admin'):
    """Retrieves credentials to run functional tests"""
    return get_cloud_config(cloud=cloud).get_auth_args()


class DFTestBase(base.BaseTestCase):

    def setUp(self):
        super(DFTestBase, self).setUp()
        creds = credentials()
        tenant_name = creds['project_name']
        auth_url = creds['auth_url'] + "/v2.0"
        self.neutron = client.Client('2.0', username=creds['username'],
             password=creds['password'], auth_url=auth_url,
             tenant_name=tenant_name)
        self.neutron.format = 'json'
        common_config.init(['--config-file', '/etc/neutron/neutron.conf'])

        db_driver_class = importutils.import_class(cfg.CONF.df.nb_db_class)
        self.nb_api = api_nb.NbApi(db_driver_class())
        self.nb_api.initialize(db_ip=cfg.CONF.df.remote_db_ip,
            db_port=cfg.CONF.df.remote_db_port)
        self.local_ip = cfg.CONF.df.local_ip
        self.__objects_to_close = []

    def store(self, obj, close_func=None):
        close_func = close_func if close_func else obj.close
        self.__objects_to_close.append(close_func)
        return obj

    def tearDown(self):
        for close_func in reversed(self.__objects_to_close):
            close_func()
        super(DFTestBase, self).tearDown()
