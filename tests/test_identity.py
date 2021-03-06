# coding: utf-8
# Copyright (c) 2016, 2017, Oracle and/or its affiliates. All rights reserved.

import json
import random
import unittest
from . import command_coverage_validator
from . import util
import oraclebmc_cli


class TestIdentity(unittest.TestCase):

    def setUp(self):
        util.set_admin_pass_phrase()

    @command_coverage_validator.CommandCoverageValidator(oraclebmc_cli.identity_cli.identity_group, expected_not_called_count=3)
    def test_all_operations(self, validator):
        """Successfully calls every operation with basic options.  Exceptions are region list, region-subscription list region-subscription create"""
        self.validator = validator

        self.subtest_availability_domain_operations()
        self.subtest_compartment_operations()
        self.subtest_user_operations()
        self.subtest_group_operations()
        self.subtest_user_group_membership_operations()
        self.subtest_api_key_operations()
        self.subtest_ui_password_operations()
        self.subtest_swift_password_operations()
        self.subtest_policy_operations()
        self.subtest_cleanup()

    def subtest_availability_domain_operations(self):
        result = self.invoke(['availability-domain', 'list', '--compartment-id', util.TENANT_ID])
        self.validate_response(result)

    def subtest_compartment_operations(self):
        # We don't want to call compartment create with every run, so just call help to
        # make sure the command is at least there.
        result = self.invoke(['compartment', 'create', '--help'])
        self.validate_response(result, json_response_expected=False)

        result = self.invoke(['compartment', 'list', '--compartment-id', util.TENANT_ID, '--limit', '1000'])
        self.validate_response(result)

        result = self.invoke(['compartment', 'get', '--compartment-id', util.COMPARTMENT_ID])
        self.validate_response(result, expect_etag=True)

        update_description = 'Compartment used by CLI integration tests. ' + str(random.randint(0, 1000000))
        result = self.invoke(
            ['compartment', 'update', '--compartment-id', util.COMPARTMENT_ID, '--description', update_description])
        self.validate_response(result, expect_etag=True)
        self.assertEquals(update_description, json.loads(result.output)['data']['description'])

    def subtest_user_operations(self):
        self.user_name = util.random_name('cli_test_user')
        self.user_description = 'Created by CLI identity tests.'

        result = self.invoke(['user', 'create', '--compartment-id', util.TENANT_ID, '--name', self.user_name, '--description', self.user_description])
        self.user_ocid = util.find_id_in_response(result.output)
        self.validate_response(result, extra_validation=self.validate_user, expect_etag=True)

        result = self.invoke(['user', 'list', '--compartment-id', util.TENANT_ID, '--limit', '1000'])
        self.validate_response(result, extra_validation=self.validate_user)
        assert "opc-next-page" in result.output

        # Call again with debug data for extra validation.
        result = self.invoke(['user', 'list', '--compartment-id', util.TENANT_ID, '--limit', '1000'], debug=True)
        self.validate_response(result, extra_validation=self.validate_user, includes_debug_data=True)

        self.user_description = 'UPDATED ' + self.user_description
        result = self.invoke(['user', 'update', '--user-id', self.user_ocid, '--description', self.user_description])
        self.validate_response(result, extra_validation=self.validate_user, expect_etag=True)

        result = self.invoke(['user', 'update-user-state', '--user-id', self.user_ocid, '--blocked', 'false'])
        self.validate_response(result, extra_validation=self.validate_user, expect_etag=True)

        result = self.invoke(['user', 'get', '--user-id', self.user_ocid])
        self.validate_response(result, extra_validation=self.validate_user, expect_etag=True)

    def subtest_group_operations(self):
        self.group_name = util.random_name('cli_test_group')
        self.group_description = 'Created by CLI identity tests.'

        result = self.invoke(
            ['group', 'create', '--compartment-id', util.TENANT_ID, '--name', self.group_name, '--description',
             self.group_description])
        self.group_ocid = util.find_id_in_response(result.output)
        self.validate_response(result, extra_validation=self.validate_group, expect_etag=True)

        result = self.invoke(['group', 'list', '--compartment-id', util.TENANT_ID, '--limit', '1000'])
        self.validate_response(result, extra_validation=self.validate_group)

        self.group_description = 'UPDATED ' + self.user_description
        result = self.invoke(['group', 'update', '--group-id', self.group_ocid, '--description', self.group_description])
        self.validate_response(result, extra_validation=self.validate_group, expect_etag=True)

        result = self.invoke(['group', 'get', '--group-id', self.group_ocid])
        self.validate_response(result, extra_validation=self.validate_group, expect_etag=True)

    def subtest_user_group_membership_operations(self):
        result = self.invoke(
            ['group', 'add-user', '--user-id', self.user_ocid, '--group-id', self.group_ocid])
        self.validate_response(result, expect_etag=True)

        result = self.invoke(
            ['group', 'list-users', '--compartment-id', util.TENANT_ID, '--group-id', self.group_ocid])
        self.validate_response(result)
        assert len(json.loads(result.output)['data']) == 1

        result = self.invoke(
            ['user', 'list-groups', '--compartment-id', util.TENANT_ID, '--user-id', self.user_ocid])
        self.validate_response(result)
        assert len(json.loads(result.output)['data']) == 1

        result = self.invoke(
            ['group', 'remove-user', '--compartment-id', util.TENANT_ID, '--user-id', self.user_ocid, '--group-id', self.group_ocid, '--force'])
        self.validate_response(result)

        result = self.invoke(
            ['group', 'list-users', '--compartment-id', util.TENANT_ID, '--group-id', self.group_ocid])
        self.validate_response(result)
        assert len(result.output) == 0

    def subtest_api_key_operations(self):
        public_key = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA0j0c6GtzuzSBGCT8D/nj
yFtYIl5hsySErWQt/+eSm9bhSMpPBXdNNw/4StMfdtyDlJS6jNDwPAOXXTOU149m
j+CQKiqphy1gawtgMc7riDNA8ufLZ3TisCeXcaC5N/InR7OfERovi2jckB78luXm
jA9txdv1xDcd1akKoHiq7RPlmZnLlPfXzUA0LdppAM0t5poZeeR0l6t/ytWgSxQt
wy9vTSr5jUrHkY1QgKjNmgcRHvIjMSJxOozBiPmFuckuJtOfh+r8jctoLmykB0JY
P8ZM9xRukuJ4bnPTe8olOFB8UCCkAEmkUxtZI4vF90HvDKDOV0KY4OH5YESY6apH
3QIDAQAB
-----END PUBLIC KEY-----"""

        result = self.invoke(
            ['user', 'api-key', 'upload', '--user-id', self.user_ocid, '--key', public_key])
        self.validate_response(result)

        result = self.invoke(
            ['user', 'api-key', 'list', '--user-id', self.user_ocid])
        self.validate_response(result)
        json_response = json.loads(result.output)
        assert len(json_response['data']) == 1
        fingerprint = json_response['data'][0]['fingerprint']

        result = self.invoke(
            ['user', 'api-key', 'delete', '--user-id', self.user_ocid, '--fingerprint', fingerprint, '--force'])
        self.validate_response(result)

    def subtest_ui_password_operations(self):
        result = self.invoke(
            ['user', 'ui-password', 'create-or-reset', '--user-id', self.user_ocid])
        self.validate_response(result)
        password = json.loads(result.output)['data']['password']
        assert len(password) > 5

        # Get a new password, verify that it has changed.
        result = self.invoke(
            ['user', 'ui-password', 'create-or-reset', '--user-id', self.user_ocid])
        self.validate_response(result)
        assert password != json.loads(result.output)['data']['password']

    def subtest_swift_password_operations(self):
        description = "Password created by CLI integration tests."
        result = self.invoke(
            ['user', 'swift-password', 'create', '--user-id', self.user_ocid, '--description', description])
        self.validate_response(result, expect_etag=True)
        json_result = json.loads(result.output, )
        password_ocid = json_result['data']['id']
        password = json_result['data']['password']
        assert len(password) > 5
        self.assertEquals(description, json_result['data']['description'])

        description = description + " UPDATED"
        result = self.invoke(
            ['user', 'swift-password', 'update', '--user-id', self.user_ocid, '--swift-password-id', password_ocid, '--description', description])
        self.validate_response(result, expect_etag=True)
        json_result = json.loads(result.output)
        self.assertEquals(description, json_result['data']['description'])

        result = self.invoke(
            ['user', 'swift-password', 'list', '--user-id', self.user_ocid])
        self.validate_response(result)
        json_result = json.loads(result.output)
        self.assertEquals(1, len(json_result['data']))

        result = self.invoke(
            ['user', 'swift-password', 'delete', '--user-id', self.user_ocid, '--swift-password-id', password_ocid, '--force'])
        self.validate_response(result)

    def subtest_policy_operations(self):
        policy_name = util.random_name('cli_test_policy')
        policy_description = 'Created by CLI identity tests.'

        statement_a = "Allow group {group_name} to inspect volume-family in compartment {compartment_name}".format(group_name=self.group_name, compartment_name=util.COMPARTMENT_NAME)
        statement_b = "Allow group {group_name} to inspect virtual-network-family in compartment {compartment_name}".format(
            group_name=self.group_name, compartment_name=util.COMPARTMENT_NAME)

        result = self.invoke(
            ['policy',
             'create',
             '--name', policy_name,
             '--compartment-id', util.TENANT_ID,
             '--description', policy_description,
             '--statements', '["{statement}"]'.format(statement=statement_a)])
        policy_ocid = util.find_id_in_response(result.output)
        self.validate_response(result, expect_etag=True)
        assert statement_a in result.output

        # Update description only.
        policy_description = policy_description + "UPDATED!"
        result = self.invoke(
            ['policy',
             'update',
             '--policy-id', policy_ocid,
             '--description', policy_description])
        self.validate_response(result, expect_etag=True)
        assert statement_a in result.output

        statements = '["{statement_a}", "{statement_b}"]'.format(statement_a=statement_a, statement_b=statement_b)
        version_date = "2016-01-01"

        # Try to update statements only - should fail.
        result = self.invoke(
            ['policy',
             'update',
             '--policy-id', policy_ocid,
             '--statements', statements])
        assert result.exit_code != 0

        # Try to update statements only - should fail.
        result = self.invoke(
            ['policy',
             'update',
             '--policy-id', policy_ocid,
             '--statements', statements])
        assert result.exit_code != 0

        # Update statements and version_date, but don't confirm.
        result = self.invoke(
            ['policy',
             'update',
             '--policy-id', policy_ocid,
             '--statements', statements,
             '--version-date', version_date])
        assert result.exit_code != 0

        # Update statements and version_date
        result = self.invoke(
            ['policy',
             'update',
             '--policy-id', policy_ocid,
             '--statements', statements,
             '--version-date', version_date,
             '--force'])
        self.validate_response(result, expect_etag=True)
        assert statement_a in result.output
        assert statement_b in result.output
        assert version_date in result.output

        etag = json.loads(result.output)['etag']
        # Set incorrect etag when updating statements
        result = self.invoke(
            ['policy',
             'update',
             '--policy-id', policy_ocid,
             '--statements', statements,
             '--version-date', version_date,
             '--if-match', 'incorrect_etag'
             '--force'])
        assert result.exit_code != 0

        # Set incorrect etag when updating description
        policy_description = policy_description + " updated again"
        result = self.invoke(
            ['policy',
             'update',
             '--policy-id', policy_ocid,
             '--description', policy_description,
             '--if-match', 'incorrect_etag'])
        assert result.exit_code != 0

        # Set correct etag when updating statements.
        # Remove statement a, clear the version date
        statements = '["{statement_b}"]'.format(statement_b=statement_b)
        result = self.invoke(
            ['policy',
             'update',
             '--policy-id', policy_ocid,
             '--statements', statements,
             '--version-date', "",
             '--if-match', etag,
             '--force'])
        self.validate_response(result, expect_etag=True)
        assert statement_a not in result.output
        assert statement_b in result.output
        assert version_date not in result.output

        # Set correct etag when updating description
        etag = json.loads(result.output)['etag']
        policy_description = policy_description + " updated again"
        result = self.invoke(
            ['policy',
             'update',
             '--policy-id', policy_ocid,
             '--description', policy_description,
             '--if-match', etag])
        self.validate_response(result, expect_etag=True)
        assert policy_description in result.output
        assert statement_a not in result.output
        assert statement_b in result.output
        assert version_date not in result.output

        # Get policy
        result = self.invoke(['policy', 'get', '--policy-id', policy_ocid])
        self.validate_response(result, expect_etag=True)
        assert policy_description in result.output
        assert statement_a not in result.output
        assert statement_b in result.output
        assert version_date not in result.output

        # List policies
        result = self.invoke(['policy', 'list', '--compartment-id', util.TENANT_ID, '--limit', '1000'])
        self.validate_response(result)
        assert policy_description in result.output
        assert statement_a not in result.output
        assert statement_b in result.output

        result = self.invoke(['policy', 'list', '--compartment-id', util.TENANT_ID, '--limit', '1'])
        self.validate_response(result)
        assert len(json.loads(result.output)['data']) == 1

        # Delete policy
        result = self.invoke(['policy', 'delete', '--policy-id', policy_ocid, '--force'])
        self.validate_response(result)

    def subtest_cleanup(self):
        result = self.invoke(['user', 'delete', '--user-id', self.user_ocid], input='n')
        assert result.exit_code != 0

        result = self.invoke(['user', 'delete', '--user-id', self.user_ocid], input='y')
        self.validate_response(result, json_response_expected=False)

        result = self.invoke(['user', 'list', '--compartment-id', util.TENANT_ID, '--limit', '1000'])
        self.validate_response(result)
        assert self.user_ocid not in result.output

        result = self.invoke(['group', 'delete', '--group-id', self.group_ocid, '--force'])
        self.validate_response(result)

    def validate_group(self, result):
        assert self.group_ocid in result.output
        assert self.group_name in result.output
        assert self.group_description in result.output

    def validate_user(self, result):
        assert self.user_ocid in result.output
        assert self.user_name in result.output
        assert self.user_description in result.output

    def validate_response(self, result, extra_validation=None, expect_etag=False, ** args):
        def common_validation(result):
            if expect_etag:
                assert "etag" in result.output

            if extra_validation:
                extra_validation(result)

        util.validate_response(result, extra_validation=common_validation, ** args)

    def invoke(self, params, debug=False, ** args):
        commands = ['iam'] + params
        self.validator.register_call(commands)

        if debug is True:
            commands = ['--debug'] + commands

        return util.invoke_command_as_admin(commands, ** args)


if __name__ == '__main__':
    unittest.main()
