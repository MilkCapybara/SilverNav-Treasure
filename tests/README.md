# 测试文件目录 / Tests Directory

本目录包含项目的所有测试脚本和测试文件。

## 文件说明

### API 测试
- `test_credit_api.py` - 信用评估 API 测试
- `test_behavior_fix.py` - 船舶行为分析 API 测试
- `test_ml_prediction.py` - 机器学习预测 API 测试

### 集成测试
- `test_redis_integration.py` - Redis 缓存集成测试
- `test_redis_connection.py` - Redis 连接测试
- `test_kafka_connection.py` - Kafka 连接测试
- `test_pg.py` - PostgreSQL 数据库连接测试

### 功能测试
- `test_all_fixes.py` - 综合功能修复测试
- `test_final_fixes.py` - 最终修复验证测试
- `test_fixes.py` - 功能修复测试
- `test_sci_fi_select.py` - 科技风格选择器测试
- `test_dashboard_migration.py` - Dashboard 迁移测试

### 其他
- `test_main.http` - HTTP 请求测试文件
- `test_monitor_api.sh` - API 监控测试脚本

## 运行测试

```bash
# 运行单个测试文件
python tests/test_credit_api.py

# 运行所有测试（如果配置了 pytest）
pytest tests/
```
