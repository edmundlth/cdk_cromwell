#!/usr/bin/env python3

from aws_cdk import core

from cdk_cromwell.cdk_cromwell_stack import CdkCromwellStack


app = core.App()
CdkCromwellStack(app, "cdk-cromwell")

app.synth()
