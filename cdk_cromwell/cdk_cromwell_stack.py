from aws_cdk import (
    core,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_iam as iam,
    aws_ecr as ecr,
    aws_batch as batch,
    aws_autoscaling as autoscaling
)

CROMWELL_REPOSITORY_NAME = "cromwell"

CROMWELL_IMAGE_TAG = "efs"
CROMWELL_PORT_NUMBER = 8000


class CdkCromwellStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # EC2 Vpc construct

        vpc = ec2.Vpc(
            self,
            id="cromwell_server_vpc",
            max_azs=2
        )

        # ECS Cluster construct
        cluster = ecs.Cluster(
            self,
            id="cromwell_cluster",
            vpc=vpc
        )

        # IAM roles
        ecstaskexecutionrole = iam.Role.from_role_arn(
            self,
            "ecstaskexecutionrole",
            role_arn="arn:aws:iam::562965587442:role/ecsTaskExecutionRole"
        )

        batch_service_role = iam.Role.from_role_arn(
            self,
            "batchservicerole",
            role_arn="arn:aws:iam::562965587442:role/AWSBatchServiceRole"
        )

        fargate_cromwell_role = iam.Role.from_role_arn(
            self,
            "fargate_cromwell_role",
            role_arn="arn:aws:iam::562965587442:role/fargate_cromwell_role"
        )

        # Cromwell docker image from ECR
        container_img = ecr.Repository.from_repository_name(
            self,
            "cromwell_docker_image",
            repository_name=CROMWELL_REPOSITORY_NAME
        )

        # ECS task definition construct
        task_def = ecs.TaskDefinition(
            self,
            "cromwell_server_task",
            execution_role=ecstaskexecutionrole,
            task_role=fargate_cromwell_role,
            compatibility=ecs.Compatibility.FARGATE,
            cpu="1024",
            memory_mib="4096"
        )

        # ECS container definition construct
        container_def = ecs.ContainerDefinition(
            self,
            "cromwell_container",
            task_definition=task_def,
            image=ecs.ContainerImage.from_ecr_repository(
                repository=container_img,
                tag=CROMWELL_IMAGE_TAG
            ),
            command=["bash", "run_cromwell_server.sh"],
            cpu=1,
            health_check=None,
            working_directory='/',
            logging=ecs.LogDriver.aws_logs(
                stream_prefix="cromwell_logs",
                datetime_format=None,
                log_group=None,
                log_retention=None,
                multiline_pattern=None
            )
        )
        container_def.add_port_mappings(
            ecs.PortMapping(
                container_port=CROMWELL_PORT_NUMBER,
                host_port=CROMWELL_PORT_NUMBER,
                protocol=ecs.Protocol.TCP
            )
        )

        # EC2 Security Group construct
        security_group = ec2.SecurityGroup(
            self,
            "cromwell_server_security_group",
            vpc=vpc,
            allow_all_outbound=True,
            security_group_name="cromwell_server_security_group",
            description="This is the security group assigned to the cromwell server running as a Fargate service.",
        )
        security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port(protocol=ecs.Protocol.TCP,
                                from_port=CROMWELL_PORT_NUMBER,
                                to_port=CROMWELL_PORT_NUMBER,
                                string_representation="cromwell_server_port"),
            remote_rule=None
        )

        # ECS Fargate Service construct
        service = ecs.FargateService(
            self,
            "cromwell_service",
            task_definition=task_def,
            cluster=cluster,
            service_name="cromwell_server_service",
            assign_public_ip=True,
            desired_count=1,
            security_group=security_group
        )


        # Batch resources
        # Reference:
        # https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-batch-computeenvironment-computeresources.html
        # https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-ec2-launchtemplate-launchtemplatedata.html
        # with open("lib/aws_batch_launch_template_user_data.txt", 'r') as user_data_file:
        #     user_data = user_data_file.read()
        #
        # ec2_user_data = ec2.UserData.custom(content=user_data)
        # ec2_instance =ec2.Instance(
        #     self,
        #     "ec2Instance",
        #     instance_type=ec2.InstanceType("t2.small"),
        #     machine_image=ec2.AmazonLinuxImage(),
        #     vpc=vpc,
        #     user_data=ec2_user_data
        # )

        # launch_template_data = core.CfnResource(
        #     self,
        #     "cromwell_launch_template_data",
        #     type="AWS::EC2::LaunchTemplate.LaunchTemplateData",
        #     properties={
        #         "UserData": user_data
        #     }
        # )
        #
        # launch_template = ec2.CfnLaunchTemplate(
        #     self,
        #     "cromwell_launch_template",
        #     launch_template_name="cromwell_launch_template",
        #     launch_template_data=launch_template_data,
        # )
        #
        # compute_resources = core.CfnResource(
        #     self,
        #     "cromwell_compute_resources",
        #     type="AWS::Batch::ComputeEnvironment.ComputeResources",
        #     properties={
        #       "DesiredvCpus": 256,
        #       "Ec2KeyPair": "genovic-qc-eddev",
        #       "InstanceRole": "arn:aws:iam::562965587442:role/ecsInstanceRole",
        #       "InstanceTypes": ["optimal"],
        #       "LaunchTemplate": launch_template.launch_template_name,
        #       "MaxvCpus": 256,
        #       "MinvCpus": 0,
        #       "SecurityGroupIds": [vpc.vpc_default_security_group],
        #       "Subnets": [subnet.subnet_id for subnet in vpc.public_subnets],
        #       "Tags": "cromwell_compute_resource",
        #       "Type": "EC2"
        #     }
        # )
        #
        # compute_env = batch.CfnComputeEnvironment(
        #     self,
        #     "cromwell_compute_env",
        #     service_role=batch_service_role,
        #     compute_environment_name="cromwell_compute_env",
        #     type="MANAGED",
        #     state="ENABLED",
        #     compute_resources=compute_resources
        # )
        #
        # queue = batch.CfnJobQueue(
        #     self,
        #     "cromwell_queue",
        #     compute_environment_order=compute_env,
        #     priority=1,
        #     job_queue_name="cromwell_queue",
        #     state="ENABLED"
        # )
        #
        # core.CfnOutput(
        #     self,
        #     "cromwell_queue_name",
        #     value=queue.job_queue_name
        # )

        core.CfnOutput(
            self,
            "FargateCromwellServiceArn",
            value=service.service_arn
        )
