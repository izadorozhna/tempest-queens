# Copyright (c) 2014 The Johns Hopkins University/Applied Physics Laboratory
# All Rights Reserved.
#
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

import testtools

from tempest.common import utils
from tempest import config
from tempest.lib import decorators
from tempest.scenario import manager

CONF = config.CONF


class TestEncryptedCinderVolumes(manager.EncryptionScenarioTest):

    """The test suite for encrypted cinder volumes

    This test is for verifying the functionality of encrypted cinder volumes.

    For both LUKS and cryptsetup encryption types, this test performs
    the following:
        * Creates an image in Glance
        * Boots an instance from the image
        * Creates an encryption type (as admin)
        * Creates a volume of that encryption type (as a regular user)
        * Attaches and detaches the encrypted volume to the instance
    """

    @classmethod
    def skip_checks(cls):
        super(TestEncryptedCinderVolumes, cls).skip_checks()
        if not CONF.compute_feature_enabled.attach_encrypted_volume:
            raise cls.skipException('Encrypted volume attach is not supported')

    def launch_instance(self):
        image = self.glance_image_create()
        keypair = self.create_keypair()

        return self.create_server(image_id=image, key_name=keypair['name'])

    def attach_detach_volume(self, server, volume):
        attached_volume = self.nova_volume_attach(server, volume)
        self.nova_volume_detach(server, attached_volume)

    @decorators.idempotent_id('79165fb4-5534-4b9d-8429-97ccffb8f86e')
    @decorators.attr(type='slow')
    @testtools.skipIf(getattr(CONF.service_available, 'barbican', False),
                      'Image Signature Verification enabled')
    @testtools.skipUnless(
        'luks' in CONF.volume_feature_enabled.supported_crypto_providers,
        'Cryptoprovider is not supported.')
    @utils.services('compute', 'volume', 'image')
    def test_encrypted_cinder_volumes_luks(self):
        server = self.launch_instance()
        volume = self.create_encrypted_volume('nova.volume.encryptors.'
                                              'luks.LuksEncryptor',
                                              volume_type='luks')
        self.attach_detach_volume(server, volume)

    @decorators.idempotent_id('cbc752ed-b716-4717-910f-956cce965722')
    @decorators.attr(type='slow')
    @testtools.skipIf(getattr(CONF.service_available, 'barbican', False),
                      'Image Signature Verification enabled')
    @testtools.skipUnless(
        'plain' in CONF.volume_feature_enabled.supported_crypto_providers,
        'Cryptoprovider is not supported.')
    @utils.services('compute', 'volume', 'image')
    def test_encrypted_cinder_volumes_cryptsetup(self):
        server = self.launch_instance()
        volume = self.create_encrypted_volume('nova.volume.encryptors.'
                                              'cryptsetup.CryptsetupEncryptor',
                                              volume_type='cryptsetup')
        self.attach_detach_volume(server, volume)
