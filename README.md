# README

```
$ cat << EOF > mfcreds.json
{
      "MF_USERNAME": "mf_username",
      "MF_PASS": "mf_pass"
}
EOF

$ aws secretsmanager create-secret --name mfcreds --secret-string file://mfcreds.json
{
    "ARN": "arn:aws:secretsmanager:<REGION>:<ACCOUNT_ID>:secret:mfcreds-XXXXXX",
    "Name": "mfcreds",
    "VersionId": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}

$ aws ecr get-login-password | docker login --username AWS --password-stdin https://${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com
$ aws ecr create-repository --repository-name ${REPOSITORY_NAME}
```
