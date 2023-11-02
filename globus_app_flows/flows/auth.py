import logging
import time
import typing as t
import globus_sdk
from django.conf import settings
from django.contrib.auth.models import User
from globus_app_flows.models import Flow, FlowAuthorization

log = logging.getLogger(__name__)


def get_flows_client(
    authorization: FlowAuthorization, user: User
) -> globus_sdk.FlowsClient:
    scopes = [globus_sdk.FlowsClient.scopes.run_status]
    authorizer = confidential_client_authorization(
        "flows.globus.org", scopes, authorization, user
    )
    return globus_sdk.FlowsClient(authorizer=authorizer)


def get_specific_flow_client(
    flow: Flow, authorization: FlowAuthorization, user: User
) -> globus_sdk.SpecificFlowClient:
    auth_func = get_authorization_function(authorization)
    authorizer = auth_func(flow.flow_id, [flow.flow_scope], authorization, user)
    return globus_sdk.SpecificFlowClient(flow.flow_id, authorizer=authorizer)


def get_authorization_function(authorization: FlowAuthorization):
    auth_types = {"CONFIDENTIAL_CLIENT": confidential_client_authorization}
    atype_auth = auth_types.get(authorization.authorization_key)
    if atype_auth is None:
        raise ValueError(
            "Unable to authorize {flow}, invalid authorizor key {authorization.authorization_key} for flow authorizer {authorization}"
        )
    return atype_auth


def refresh_tokens(
    resource_server, flow_scopes, authorization: FlowAuthorization
) -> t.Mapping[str, dict]:
    cc_creds = settings.GLOBUS_APP_FLOWS_AUTHORIZATIONS["confidential_client"][
        authorization.authorization_key
    ]
    app = globus_sdk.ConfidentialAppAuthClient(
        cc_creds["client_id"], cc_creds["client_secret"]
    )

    response = app.oauth2_client_credentials_tokens(requested_scopes=flow_scopes)
    tokens = response.by_resource_server
    authorization.update_cache(tokens)
    log.debug(f"New tokens cached for {authorization}")
    return tokens


def _tokens_expired(tokens: dict) -> bool:
    expired = time.time() >= tokens["expires_at_seconds"]
    log.debug(
        f'Tokens have expired for resource server {tokens["resource_server"]}: {expired}'
    )
    return expired


def _scopes_mismatch(tokens: dict, requested_scopes: t.List[str]) -> bool:
    mismatch = bool(set(requested_scopes).difference(set(tokens["scope"].split())))
    log.debug(f'Mismatch for resource server {tokens["resource_server"]}: {mismatch}')
    return mismatch


def confidential_client_authorization(
    resource_server, flow_scopes, authorization: FlowAuthorization, user=None
):
    cache = authorization.cache
    tokens = cache.get(resource_server)
    if (
        tokens is None
        or _tokens_expired(tokens)
        or _scopes_mismatch(tokens, flow_scopes)
    ):
        log.info(
            f"Fetching new tokens for scopes {flow_scopes} under user {user} for authorization {authorization}"
        )
        tokens = refresh_tokens(resource_server, flow_scopes, authorization)

    authorizer = globus_sdk.AccessTokenAuthorizer(tokens["access_token"])
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
