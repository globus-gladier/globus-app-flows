import logging
import globus_sdk
from django.conf import settings
from django.contrib.auth.models import User
from globus_app_flows.models import Flow, FlowAuthorization

log = logging.getLogger(__name__)

CC_SPECIFIC_FLOW_AUTHORIZATION_CACHE = {}
CC_FLOWS_AUTHORIZATION_CACHE = {}


def get_flows_client(
    authorization: FlowAuthorization, user: User
) -> globus_sdk.FlowsClient:
    auth_types = {"CONFIDENTIAL_CLIENT": confidential_client_authorization}

    scopes = [globus_sdk.FlowsClient.scopes.run_status]
    authorizer = auth_types[authorization.authorization_type](
        "flows.globus.org", scopes, authorization.authorization_key, user
    )
    return globus_sdk.FlowsClient(authorizer=authorizer)


def get_specific_flow_client(
    flow: Flow, authorization: FlowAuthorization, user: User
) -> globus_sdk.SpecificFlowClient:
    auth_types = {"CONFIDENTIAL_CLIENT": confidential_client_authorization}
    authorizer = CC_SPECIFIC_FLOW_AUTHORIZATION_CACHE.get(
        authorization.authorization_key, None
    )
    authorizer = authorizer or auth_types[authorization.authorization_type](
        flow.flow_id, [flow.flow_scope], authorization.authorization_key, user
    )
    return globus_sdk.SpecificFlowClient(flow.flow_id, authorizer=authorizer)


def confidential_client_authorization(
    resource_server, flow_scopes, auth_key, user=None
):
    log.critical(
        "TOKEN CACHE NOT USED, IMPLEMENT THIS FEATURE BEFORE LARGE SCALE RUNS!"
    )
    cc_creds = settings.GLOBUS_APP_FLOWS_AUTHORIZATIONS["confidential_client"][auth_key]
    app = globus_sdk.ConfidentialAppAuthClient(
        cc_creds["client_id"], cc_creds["client_secret"]
    )

    response = app.oauth2_client_credentials_tokens(requested_scopes=flow_scopes)
    tokens = response.by_resource_server
    authorizer = globus_sdk.AccessTokenAuthorizer(
        tokens[resource_server]["access_token"]
    )
    return authorizer


# def get_authorized_flow(flow_id, flow_scope, authorization):
#     atype = authorization['type']
#     log.info(f'Authorizing XPCS Reprocessing flow {flow_id} with type {atype}')
#     if atype == 'app':
#         app = globus_sdk.ConfidentialAppAuthClient(authorization['uuid'], authorization['client_secret'])
#         response = app.oauth2_client_credentials_tokens(requested_scopes=[flow_scope])
#         tokens = response.by_resource_server
#         authorizer = globus_sdk.AccessTokenAuthorizer(tokens[flow_id]['access_token'])
#     elif atype == 'token':
#         client = globus_sdk.NativeAppAuthClient(authorization['client_id'])
#         tokens = authorization['tokens'][flow_scope]
#         # authorizer = globus_sdk.RefreshTokenAuthorizer(tokens['refresh_token'], client, access_token=tokens['access_token'], expires_at=tokens['expiration_time'])
#         authorizer = globus_sdk.AccessTokenAuthorizer(tokens['access_token'])
#     else:
#         raise ValueError(f'Unable to authorize reprocessing flow {flow_scope}')
#     return globus_sdk.SpecificFlowClient(flow_id, authorizer=authorizer)
