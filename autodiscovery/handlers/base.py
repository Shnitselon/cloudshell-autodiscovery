from cloudshell.api.cloudshell_api import AttributeNameValue
from cloudshell.api.cloudshell_api import ResourceAttributesUpdateRequest
from cloudshell.api.common_cloudshell_api import CloudShellAPIError

from autodiscovery.cli_sessions import SSHDiscoverySession
from autodiscovery.cli_sessions import TelnetDiscoverySession
from autodiscovery.common.consts import CloudshellAPIErrorCodes
from autodiscovery.exceptions import ReportableException


class AbstractHandler(object):
    def __init__(self, logger):
        """

        :param logging.Logger logger:
        """
        self.logger = logger

    def discover(self, entry, vendor, cli_credentials):
        """Discover device attributes

        :param autodiscovery.reports.base.Entry entry:
        :param autodiscovery.models.vendor.BaseVendorDefinition vendor:
        :param autodiscovery.models.CLICredentialsCollection cli_credentials:
        :rtype: autodiscovery.reports.base.Entry
        """
        raise NotImplementedError("Class {} must implement method 'discover'".format(type(self)))

    def upload(self, entry, vendor, cs_session):
        """Upload discovered device on the CloudShell

        :param autodiscovery.reports.base.Entry entry:
        :param autodiscovery.models.vendor.BaseVendorDefinition vendor:
        :param cloudshell.api.cloudshell_api.CloudShellAPISession cs_session:
        :return:
        """
        raise NotImplementedError("Class {} must implement method 'upload'".format(type(self)))

    def _add_resource_driver(self, cs_session, resource_name, driver_name):
        """Add appropriate driver to the created CloudShell resource

        :param cloudshell.api.cloudshell_api.CloudShellAPISession cs_session:
        :param str resource_name:
        :param str driver_name:
        :return:
        """
        try:
            cs_session.UpdateResourceDriver(resourceFullPath=resource_name,
                                            driverName=driver_name)
        except CloudShellAPIError as e:
            if e.code == CloudshellAPIErrorCodes.UNABLE_TO_LOCATE_DRIVER:
                self.logger.exception("Unable to locate driver {}".format(driver_name))
                raise ReportableException("Shell {} is not installed on the CloudShell".format(driver_name))
            raise

    def _create_cs_resource(self, cs_session, resource_name, resource_family, resource_model, driver_name, device_ip,
                            attributes, attribute_prefix=""):
        """Create Resource on CloudShell with appropriate attributes

        :param cloudshell.api.cloudshell_api.CloudShellAPISession cs_session:
        :param str resource_name:
        :param str resource_family:
        :param str resource_model:
        :param str driver_name:
        :param str device_ip:
        :param dict attributes:
        :param str attribute_prefix:
        :return: name for the created Resource
        :rtype: str
        """
        try:
            cs_session.CreateResource(resourceFamily=resource_family,
                                      resourceModel=resource_model,
                                      resourceName=resource_name,
                                      resourceAddress=device_ip)
        except CloudShellAPIError as e:
            if e.code == CloudshellAPIErrorCodes.RESOURCE_ALREADY_EXISTS:
                resource_name = "{}-1".format(resource_name)
                cs_session.CreateResource(resourceFamily=resource_family,
                                          resourceModel=resource_model,
                                          resourceName=resource_name,
                                          resourceAddress=device_ip)
            else:
                self.logger.exception("Unable to locate Shell with Resource Family/Name: {}/{}"
                                      .format(resource_family, resource_model))
                raise

        attributes = [AttributeNameValue("{}{}".format(attribute_prefix, key), value)
                      for key, value in attributes.iteritems()]

        cs_session.SetAttributesValues([ResourceAttributesUpdateRequest(resource_name, attributes)])

        self._add_resource_driver(cs_session=cs_session,
                                  resource_name=resource_name,
                                  driver_name=driver_name)

        return resource_name

    def _get_cli_credentials(self, vendor, cli_credentials, device_ip):
        """

        :param autodiscovery.models.VendorDefinition vendor:
        :param autodiscovery.models.CLICredentialsCollection cli_credentials:
        :param str device_ip:
        :return:
        """
        vendor_cli_creds = cli_credentials.get_creds_by_vendor(vendor)

        if vendor_cli_creds:
            for session in (SSHDiscoverySession(device_ip), TelnetDiscoverySession(device_ip)):
                try:
                    valid_creds = session.check_credentials(cli_credentials=vendor_cli_creds,
                                                            default_prompt=vendor.default_prompt,
                                                            enable_prompt=vendor.enable_prompt,
                                                            logger=self.logger)
                except Exception:
                    self.logger.warning("{} Credentials aren't valid for the device with IP {}"
                                        .format(session.SESSION_TYPE, device_ip), exc_info=True)
                else:
                    vendor_cli_creds.update_valid_creds(valid_creds)
                    return valid_creds
