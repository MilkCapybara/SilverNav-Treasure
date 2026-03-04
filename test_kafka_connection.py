#!/usr/bin/env python3
"""
测试 Kafka 连接和基本功能
"""
import sys
sys.path.insert(0, '/Users/sunfanmacpro/Desktop/SilverNav-Treasure')

from app.kafka_config import (
    create_kafka_producer,
    create_kafka_consumer,
    create_topics,
    send_message,
    KAFKA_TOPICS
)
from datetime import datetime
import time

print("=" * 60)
print("Kafka 连接测试")
print("=" * 60)

# 1. 测试连接
print("\n1. 测试 Kafka 连接...")
producer = create_kafka_producer()

if not producer:
    print("❌ Kafka 连接失败")
    print("请检查:")
    print("1. Kafka 服务是否启动")
    print("2. 配置是否正确 (bootstrap_servers)")
    print("3. 防火墙是否开放 9092 端口")
    sys.exit(1)

# 2. 创建 Topics
print("\n2. 创建 Kafka Topics...")
if create_topics():
    print("✅ Topics 创建成功")
    print("\n已创建的 Topics:")
    for topic_name, config in KAFKA_TOPICS.items():
        print(f"  - {topic_name}: {config['description']}")
else:
    print("⚠️ Topics 创建失败，但可能已存在")

# 3. 测试发送消息
print("\n3. 测试发送消息...")
test_message = {
    'type': 'test',
    'timestamp': datetime.now().isoformat(),
    'data': {
        'vessel_imo': '9876543',
        'vessel_name': '测试船舶',
        'latitude': 30.5678,
        'longitude': 120.1234,
        'speed': 15.5,
        'course': 180
    }
}

if send_message(producer, 'ais.raw', test_message, key='test_vessel'):
    print("✅ 消息发送成功")
else:
    print("❌ 消息发送失败")

# 4. 测试接收消息
print("\n4. 测试接收消息...")
print("创建 Consumer，等待消息...")

consumer = create_kafka_consumer('ais.raw', 'test-group')

if consumer:
    print("等待 5 秒接收消息...")
    start_time = time.time()
    message_received = False

    while time.time() - start_time < 5:
        messages = consumer.poll(timeout_ms=1000)
        if messages:
            for topic_partition, records in messages.items():
                for record in records:
                    print(f"✅ 收到消息: {record.value}")
                    message_received = True
                    break
            if message_received:
                break

    if not message_received:
        print("⚠️ 未收到消息（可能因为 Consumer 从最新位置开始读取）")

    consumer.close()
else:
    print("❌ Consumer 创建失败")

# 5. 清理
producer.close()

print("\n" + "=" * 60)
print("✅ Kafka 测试完成")
print("=" * 60)
