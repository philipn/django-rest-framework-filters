#!/bin/bash

set -x
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-"367316522684"}
AWS_CODE_ARTIFACT_DOMAIN=${AWS_CODE_ARTIFACT_DOMAIN:-"ubidots"}
AWS_CODE_ARTIFACT_REPOSITORY=${AWS_CODE_ARTIFACT_REPOSITORY:-"ubidots"}
AWS_REGION=${AWS_REGION:-"us-east-2"}
AWS_PROFILE=${AWS_PROFILE:-"ubidots_code_artifact_admin"}

aws codeartifact login \
--tool twine \
--repository "${AWS_CODE_ARTIFACT_REPOSITORY}" \
--domain "${AWS_CODE_ARTIFACT_DOMAIN}" \
--domain-owner "${AWS_ACCOUNT_ID}" \
--region "${AWS_REGION}" \
--profile "${AWS_PROFILE}"
