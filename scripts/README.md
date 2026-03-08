# 脚本目录 / Scripts Directory

本目录包含项目的各类脚本工具。

## 目录结构

### migration/
数据迁移相关脚本
- `migrate_all_data.py` - 全量数据迁移脚本
- `migrate_large_tables.py` - 大表迁移脚本
- `migrate_large_tables_v2.py` - 大表迁移脚本 v2
- `check_migration_progress.py` - 迁移进度检查
- `check_progress.sh` - 进度检查 Shell 脚本
- `migration_status.sh` - 迁移状态查看脚本

### ml/
机器学习模型训练脚本
- `train_ml_models.py` - 基础模型训练脚本
- `train_ml_batch.py` - 批量模型训练脚本
- `train_ml_real_features.py` - 真实特征模型训练
- `quickstart_ml.py` - 机器学习快速启动脚本

## 根目录脚本

### 启动脚本
- `start_app.sh` - 应用启动脚本
- `start_server.sh` - 服务器启动脚本

### 环境配置
- `setup_redis_kafka.sh` - Redis + Kafka 环境配置
- `setup_redis_only.sh` - Redis 环境配置

### 数据生成
- `generate_ais_data_linked.py` - AIS 数据生成脚本
- `run_data_generation.sh` - 数据生成运行脚本

### 验证工具
- `verify_real_data.py` - 真实数据验证脚本
- `test_mongo_connection.py` - MongoDB 连接测试

## 使用说明

```bash
# 启动应用
./scripts/start_app.sh

# 配置 Redis 环境
./scripts/setup_redis_only.sh

# 训练机器学习模型
python scripts/ml/train_ml_models.py

# 执行数据迁移
python scripts/migration/migrate_all_data.py
```
