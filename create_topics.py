from kafka.admin import KafkaAdminClient, NewTopic
import os

admin_client = KafkaAdminClient(
    bootstrap_servers=os.environ.get('KAFKA_BOOTSTRAP_SERVERS'),
    security_protocol=os.environ.get('KAFKA_SECURITY_PROTOCOL'),
    sasl_mechanism=os.environ.get('KAFKA_SASL_MECHANISM'),
    sasl_plain_username=os.environ.get('KAFKA_SASL_USERNAME'),
    sasl_plain_password=os.environ.get('KAFKA_SASL_PASSWORD'),
    ssl_check_hostname=False
)

topics = ['build.queued', 'build.status', 'deployment.status']
new_topics = [NewTopic(name=t, num_partitions=1, replication_factor=1) for t in topics]

try:
    admin_client.create_topics(new_topics=new_topics, validate_only=False)
    print('Topics created successfully')
except Exception as e:
    print('Error creating topics:', type(e), e)
