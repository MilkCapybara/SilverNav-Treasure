"""
Kafka 配置和工具函数
"""
from typing import Dict, Any, Optional
from kafka import KafkaProducer, KafkaConsumer
from kafka.admin import KafkaAdminClient, NewTopic
import json
from .config import settings

# Kafka Topic 定义
KAFKA_TOPICS = {
    'ais.raw': {
        'num_partitions': 6,
        'replication_factor': 1,  # 单节点设置为1
        'config': {
            'retention.ms': '86400000',  # 1天
            'compression.type': 'gzip'
        },
        'description': 'AIS原始轨迹数据'
    },
    'risk.events': {
        'num_partitions': 3,
        'replication_factor': 1,
        'config': {
            'retention.ms': '604800000',  # 7天
            'compression.type': 'gzip'
        },
        'description': '风险事件（高风险区域、异常行为等）'
    },
    'alerts.realtime': {
        'num_partitions': 3,
        'replication_factor': 1,
        'config': {
            'retention.ms': '2592000000',  # 30天
            'compression.type': 'gzip'
        },
        'description': '实时告警消息'
    },
    'metrics.updates': {
        'num_partitions': 2,
        'replication_factor': 1,
        'config': {
            'retention.ms': '3600000',  # 1小时
            'compression.type': 'gzip'
        },
        'description': 'Dashboard指标实时更新'
    }
}


def create_kafka_producer() -> Optional[KafkaProducer]:
    """创建 Kafka Producer"""
    try:
        producer = KafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',
            retries=3,
            max_in_flight_requests_per_connection=1
        )
        print(f"✅ Kafka Producer 创建成功: {settings.kafka_bootstrap_servers}")
        return producer
    except Exception as e:
        print(f"❌ Kafka Producer 创建失败: {e}")
        return None


def create_kafka_consumer(topic: str, group_id: str) -> Optional[KafkaConsumer]:
    """创建 Kafka Consumer"""
    try:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            enable_auto_commit=True
        )
        print(f"✅ Kafka Consumer 创建成功: {topic} (group: {group_id})")
        return consumer
    except Exception as e:
        print(f"❌ Kafka Consumer 创建失败: {e}")
        return None


def create_topics():
    """创建 Kafka Topics"""
    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            client_id='silvernav-admin'
        )

        # 获取现有 topics
        existing_topics = admin_client.list_topics()

        # 创建新 topics
        new_topics = []
        for topic_name, config in KAFKA_TOPICS.items():
            if topic_name not in existing_topics:
                new_topic = NewTopic(
                    name=topic_name,
                    num_partitions=config['num_partitions'],
                    replication_factor=config['replication_factor'],
                    topic_configs=config.get('config', {})
                )
                new_topics.append(new_topic)
                print(f"📝 准备创建 Topic: {topic_name}")

        if new_topics:
            admin_client.create_topics(new_topics=new_topics, validate_only=False)
            print(f"✅ 成功创建 {len(new_topics)} 个 Topics")
        else:
            print("ℹ️ 所有 Topics 已存在")

        admin_client.close()
        return True

    except Exception as e:
        print(f"❌ 创建 Topics 失败: {e}")
        return False


def send_message(producer: KafkaProducer, topic: str, message: Dict[Any, Any], key: Optional[str] = None):
    """发送消息到 Kafka"""
    try:
        future = producer.send(topic, value=message, key=key)
        record_metadata = future.get(timeout=10)
        print(f"✅ 消息已发送: {topic} (partition: {record_metadata.partition}, offset: {record_metadata.offset})")
        return True
    except Exception as e:
        print(f"❌ 消息发送失败: {e}")
        return False


# 全局 Producer 实例（可选）
_global_producer = None

def get_global_producer() -> Optional[KafkaProducer]:
    """获取全局 Producer 实例"""
    global _global_producer
    if _global_producer is None:
        _global_producer = create_kafka_producer()
    return _global_producer
