'''
Created on Sep 26, 2016

@author: castulo
'''
from tempest.api.compute import base
from tempest.common.dynamic_creds import DynamicCredentialProvider
from tempest.common.cred_provider import TestResources
from tempest.common.utils.linux import remote_client
from tempest import config
from tempest import test

import pickle

CONF = config.CONF


# Monkey patch the method for creating new credentials to use existing
# credentials instead
def _use_existing_creds(self, admin):
    """Create credentials with an existing user.

    :return: Readonly Credentials with network resources
    """
    # Read the files that have the existing persistent resources
    with open('persistent.resource', 'rb') as f:
        resources = pickle.load(f)
    user = {'name': resources['username'], 'id': resources['user_id']}
    project = {'name': resources['tenant_name'], 'id': resources['tenant_id']}
    user_password = resources['password']
    creds = self.creds_client.get_credentials(user, project, user_password)
    return TestResources(creds)

DynamicCredentialProvider._create_creds = _use_existing_creds


class VerifyComputePersistentResources(base.BaseV2ComputeTest):

    @classmethod
    def resource_setup(cls):
        super(VerifyComputePersistentResources, cls).resource_setup()
        # Read the files that have the existing persistent resources
        with open('persistent.resource', 'rb') as f:
            cls.resources = pickle.load(f)
        cls.validation_resources = cls.resources['validation_resources']

    @classmethod
    def resource_cleanup(cls):
        # Override the parent's method to avoid deleting the resources at
        # the end of the test.
        pass

    @classmethod
    def clear_credentials(cls):
        # Override the parent's method to avoid deleting the credentials
        # at the end of the test.
        pass

    @test.attr(type='upgrade-verify')
    def test_verify_persistent_servers(self):
        servers = self.resources['servers']
        for server in servers:
            fetched_server = self.servers_client.show_server(
                server['id'])['server']
            self.assertEqual(server['id'], fetched_server['id'])
            if CONF.validation.run_validation:
                linux_client = remote_client.RemoteClient(
                    self.get_server_ip(fetched_server),
                    self.ssh_user,
                    CONF.validation.image_ssh_password,
                    self.validation_resources['keypair']['private_key'],
                    server=fetched_server,
                    servers_client=self.servers_client)
                linux_client.validate_authentication()
