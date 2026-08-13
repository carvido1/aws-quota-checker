import cachetools
import typing
import boto3

from aws_quota.exceptions import InstanceWithIdentifierNotFound, NotImplementedInFavourOfCloudWatch
from aws_quota.utils import get_paginated_results
from .quota_check import QuotaCheck, InstanceQuotaCheck, QuotaScope


@cachetools.cached(cache=cachetools.TTLCache(maxsize=1, ttl=60))
def get_rest_apis(session: boto3.Session) -> typing.List[dict]:
    return get_paginated_results(session, 'apigateway', 'get_rest_apis', 'items')


def get_rest_apis_by_endpoint_type(session: boto3.Session, endpoint_type: str) -> typing.List[dict]:
    return [
        api for api in get_rest_apis(session)
        if endpoint_type in api.get('endpointConfiguration', {}).get('types', [])
    ]


@cachetools.cached(cache=cachetools.TTLCache(maxsize=1, ttl=60))
def get_domain_names(session: boto3.Session) -> typing.List[dict]:
    return get_paginated_results(session, 'apigateway', 'get_domain_names', 'items')


@cachetools.cached(cache=cachetools.TTLCache(maxsize=1, ttl=60))
def get_usage_plans(session: boto3.Session) -> typing.List[dict]:
    return get_paginated_results(session, 'apigateway', 'get_usage_plans', 'items')


@cachetools.cached(cache=cachetools.TTLCache(maxsize=1, ttl=60))
def get_vpc_links(session: boto3.Session) -> typing.List[dict]:
    return get_paginated_results(session, 'apigateway', 'get_vpc_links', 'items')


@cachetools.cached(cache=cachetools.TTLCache(maxsize=1, ttl=60))
def get_v2_apis(session: boto3.Session) -> typing.List[dict]:
    return get_paginated_results(session, 'apigatewayv2', 'get_apis', 'Items')


def get_v2_apis_by_protocol(session: boto3.Session, protocol_type: str) -> typing.List[dict]:
    return [api for api in get_v2_apis(session) if api.get('ProtocolType') == protocol_type]


@cachetools.cached(cache=cachetools.TTLCache(maxsize=1, ttl=60))
def get_v2_vpc_links(session: boto3.Session) -> typing.List[dict]:
    # apigatewayv2's GetVpcLinks has no botocore paginator config, so page manually.
    client = session.client('apigatewayv2')
    items = []
    next_token = None
    while True:
        kwargs = {'NextToken': next_token} if next_token else {}
        response = client.get_vpc_links(**kwargs)
        items.extend(response['Items'])
        next_token = response.get('NextToken')
        if not next_token:
            return items


class RegionalApiCountCheck(QuotaCheck):
    key = "apigateway_regional_api_count"
    scope = QuotaScope.REGION
    service_code = 'apigateway'
    quota_code = 'L-AA0FF27B'
    description = "The maximum number of regional REST APIs per Region."

    @property
    def current(self):
        return len(get_rest_apis_by_endpoint_type(self.boto_session, 'REGIONAL'))


class EdgeOptimizedApiCountCheck(QuotaCheck):
    key = "apigateway_edge_optimized_api_count"
    scope = QuotaScope.REGION
    service_code = 'apigateway'
    quota_code = 'L-B97207D0'
    description = "The maximum number of edge-optimized REST APIs per Region."

    @property
    def current(self):
        return len(get_rest_apis_by_endpoint_type(self.boto_session, 'EDGE'))


class PrivateApiCountCheck(QuotaCheck):
    key = "apigateway_private_api_count"
    scope = QuotaScope.REGION
    service_code = 'apigateway'
    quota_code = 'L-A966AB5C'
    description = "The maximum number of private REST APIs per Region."

    @property
    def current(self):
        return len(get_rest_apis_by_endpoint_type(self.boto_session, 'PRIVATE'))


class CustomDomainNameCountCheck(QuotaCheck):
    key = "apigateway_custom_domain_name_count"
    scope = QuotaScope.REGION
    service_code = 'apigateway'
    quota_code = 'L-A93447B8'
    description = "The maximum number of custom domain names per Region."

    @property
    def current(self):
        return len([
            domain_name for domain_name in get_domain_names(self.boto_session)
            if 'PRIVATE' not in domain_name.get('endpointConfiguration', {}).get('types', [])
        ])


class PrivateCustomDomainNameCountCheck(QuotaCheck):
    key = "apigateway_private_custom_domain_name_count"
    scope = QuotaScope.REGION
    service_code = 'apigateway'
    quota_code = 'L-24E7E662'
    description = "The maximum number of private custom domain names per Region."

    @property
    def current(self):
        return len([
            domain_name for domain_name in get_domain_names(self.boto_session)
            if 'PRIVATE' in domain_name.get('endpointConfiguration', {}).get('types', [])
        ])


class ClientCertificateCountCheck(QuotaCheck):
    key = "apigateway_client_certificate_count"
    scope = QuotaScope.REGION
    service_code = 'apigateway'
    quota_code = 'L-824C9E42'
    description = "The maximum number of client certificates per Region."

    @property
    def current(self):
        return self.count_paginated_results('apigateway', 'get_client_certificates', 'items')


class ApiKeyCountCheck(QuotaCheck):
    key = "apigateway_api_key_count"
    scope = QuotaScope.REGION
    service_code = 'apigateway'
    quota_code = 'L-1D180A63'
    description = "The maximum number of API keys per Region."

    @property
    def current(self):
        return self.count_paginated_results('apigateway', 'get_api_keys', 'items')


class UsagePlanCountCheck(QuotaCheck):
    key = "apigateway_usage_plan_count"
    scope = QuotaScope.REGION
    service_code = 'apigateway'
    quota_code = 'L-E8693075'
    description = "The maximum number of usage plans per Region."

    @property
    def current(self):
        return len(get_usage_plans(self.boto_session))


class VpcLinkCountCheck(QuotaCheck):
    key = "apigateway_vpc_link_count"
    scope = QuotaScope.REGION
    service_code = 'apigateway'
    quota_code = 'L-A4C7274F'
    description = "The maximum number of VPC links per Region, for use with REST APIs."

    @property
    def current(self):
        return len(get_vpc_links(self.boto_session))


class VpcLinkV2CountCheck(QuotaCheck):
    key = "apigateway_vpc_link_v2_count"
    scope = QuotaScope.REGION
    service_code = 'apigateway'
    quota_code = 'L-608BDCD4'
    description = "The maximum number of VPC links per Region, for use with HTTP APIs."

    @property
    def current(self):
        return len(get_v2_vpc_links(self.boto_session))


class UsagePlansPerApiKeyCountCheck(InstanceQuotaCheck):
    key = "apigateway_usage_plans_per_api_key"
    service_code = 'apigateway'
    quota_code = 'L-985EB478'
    description = "The maximum number of usage plans per API key."
    instance_id = 'API Key ID'

    @staticmethod
    def get_all_identifiers(session: boto3.Session) -> typing.List[str]:
        return [key['id'] for key in get_paginated_results(session, 'apigateway', 'get_api_keys', 'items')]

    @property
    def current(self):
        return self.count_paginated_results('apigateway', 'get_usage_plans', 'items', {'keyId': self.instance_id})


class SubnetsPerVpcLinkV2CountCheck(InstanceQuotaCheck):
    key = "apigateway_subnets_per_vpc_link_v2"
    service_code = 'apigateway'
    quota_code = 'L-668C9B28'
    description = "The maximum number of subnets per VPC link, for use with HTTP APIs."
    instance_id = 'VPC Link ID'

    @staticmethod
    def get_all_identifiers(session: boto3.Session) -> typing.List[str]:
        return [vpc_link['VpcLinkId'] for vpc_link in get_v2_vpc_links(session)]

    @property
    def current(self):
        try:
            vpc_link = self.boto_session.client('apigatewayv2').get_vpc_link(VpcLinkId=self.instance_id)
        except self.boto_session.client('apigatewayv2').exceptions.NotFoundException as e:
            raise InstanceWithIdentifierNotFound(self) from e

        return len(vpc_link['SubnetIds'])


class ResourcesPerRestApiCountCheck(InstanceQuotaCheck):
    key = "apigateway_resources_per_rest_api"
    service_code = 'apigateway'
    quota_code = 'L-01C8A9E0'
    description = "The maximum number of resources per REST API."
    instance_id = 'REST API ID'

    @staticmethod
    def get_all_identifiers(session: boto3.Session) -> typing.List[str]:
        return [api['id'] for api in get_rest_apis(session)]

    @property
    def current(self):
        try:
            return self.count_paginated_results('apigateway', 'get_resources', 'items', {'restApiId': self.instance_id})
        except self.boto_session.client('apigateway').exceptions.NotFoundException as e:
            raise InstanceWithIdentifierNotFound(self) from e


class RoutesPerWebSocketApiCountCheck(InstanceQuotaCheck):
    key = "apigateway_routes_per_websocket_api"
    service_code = 'apigateway'
    quota_code = 'L-01C8A9E0'
    description = "The maximum number of routes per WebSocket API."
    instance_id = 'WebSocket API ID'

    @staticmethod
    def get_all_identifiers(session: boto3.Session) -> typing.List[str]:
        return [api['ApiId'] for api in get_v2_apis_by_protocol(session, 'WEBSOCKET')]

    @property
    def current(self):
        try:
            return self.count_paginated_results('apigatewayv2', 'get_routes', 'Items', {'ApiId': self.instance_id})
        except self.boto_session.client('apigatewayv2').exceptions.NotFoundException as e:
            raise InstanceWithIdentifierNotFound(self) from e


class RoutesPerHttpApiCountCheck(InstanceQuotaCheck):
    key = "apigateway_routes_per_http_api"
    service_code = 'apigateway'
    quota_code = 'L-65B5C802'
    description = "The maximum number of routes per HTTP API."
    instance_id = 'HTTP API ID'

    @staticmethod
    def get_all_identifiers(session: boto3.Session) -> typing.List[str]:
        return [api['ApiId'] for api in get_v2_apis_by_protocol(session, 'HTTP')]

    @property
    def current(self):
        try:
            return self.count_paginated_results('apigatewayv2', 'get_routes', 'Items', {'ApiId': self.instance_id})
        except self.boto_session.client('apigatewayv2').exceptions.NotFoundException as e:
            raise InstanceWithIdentifierNotFound(self) from e


class StagesPerRestApiCountCheck(InstanceQuotaCheck):
    key = "apigateway_stages_per_rest_api"
    service_code = 'apigateway'
    quota_code = 'L-379E48B0'
    description = "The maximum number of stages per REST API."
    instance_id = 'REST API ID'

    @staticmethod
    def get_all_identifiers(session: boto3.Session) -> typing.List[str]:
        return [api['id'] for api in get_rest_apis(session)]

    @property
    def current(self):
        try:
            return len(self.boto_session.client('apigateway').get_stages(restApiId=self.instance_id)['item'])
        except self.boto_session.client('apigateway').exceptions.NotFoundException as e:
            raise InstanceWithIdentifierNotFound(self) from e


class StagesPerV2ApiCountCheck(InstanceQuotaCheck):
    key = "apigateway_stages_per_v2_api"
    service_code = 'apigateway'
    quota_code = 'L-379E48B0'
    description = "The maximum number of stages per HTTP or WebSocket API."
    instance_id = 'API ID'

    @staticmethod
    def get_all_identifiers(session: boto3.Session) -> typing.List[str]:
        return [api['ApiId'] for api in get_v2_apis(session)]

    @property
    def current(self):
        try:
            return self.count_paginated_results('apigatewayv2', 'get_stages', 'Items', {'ApiId': self.instance_id})
        except self.boto_session.client('apigatewayv2').exceptions.NotFoundException as e:
            raise InstanceWithIdentifierNotFound(self) from e


class ApiStageThrottlesPerUsagePlanCountCheck(InstanceQuotaCheck):
    key = "apigateway_api_stage_throttles_per_usage_plan"
    service_code = 'apigateway'
    quota_code = 'L-A9DBC573'
    description = "The maximum number of API stages that can be associated with a usage plan, per Region."
    instance_id = 'Usage Plan ID'

    @staticmethod
    def get_all_identifiers(session: boto3.Session) -> typing.List[str]:
        return [usage_plan['id'] for usage_plan in get_usage_plans(session)]

    @property
    def current(self):
        matching_usage_plans = [
            usage_plan for usage_plan in get_usage_plans(self.boto_session)
            if usage_plan['id'] == self.instance_id
        ]

        if not matching_usage_plans:
            raise InstanceWithIdentifierNotFound(self)

        return len(matching_usage_plans[0].get('apiStages', []))


class ThrottleRateCheck(QuotaCheck):
    key = "apigateway_throttle_rate"
    scope = QuotaScope.REGION
    service_code = 'apigateway'
    quota_code = 'L-8A5B8E43'
    description = "The maximum steady-state request rate limit per account per Region."

    @property
    def current(self):
        ## Current usage can be found in CloudWatch under:
        ## [ "AWS/Usage", "CallCount", "Type", "API", "Resource", "GetResources", "Service", "AWS API Gateway", "Class", "None" ]
        raise NotImplementedInFavourOfCloudWatch(self)


class ThrottleBurstRateCheck(QuotaCheck):
    key = "apigateway_throttle_burst_rate"
    scope = QuotaScope.REGION
    service_code = 'apigateway'
    quota_code = 'L-CDF5615A'
    description = "The maximum burst request rate limit per account per Region."

    @property
    def current(self):
        ## Current usage can be found in CloudWatch under:
        ## [ "AWS/Usage", "CallCount", "Type", "API", "Resource", "GetResources", "Service", "AWS API Gateway", "Class", "None" ]
        raise NotImplementedInFavourOfCloudWatch(self)
