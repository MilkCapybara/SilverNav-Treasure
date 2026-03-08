# 🚀 银航宝系统 - 快速启动指南

## 📋 前置要求

- Python 3.12+
- PostgreSQL 14.20 (已配置)
- MongoDB 7.0.29 (已配置)
- 依赖库已安装

## 🎯 快速启动（3步）

### 1. 启动应用

```bash
cd /Users/sunfanmacpro/Desktop/SilverNav-Treasure
python main.py
```

### 2. 验证功能（可选）

在另一个终端运行：

```bash
python verify_real_data.py
```

### 3. 访问页面

打开浏览器访问：

- **总览大屏**: http://localhost:8000/dashboard
- **实时监控大屏**: http://localhost:8000/monitor ⭐ 新增
- **数据质量监控**: http://localhost:8000/quality ⭐ 新增
- **船舶行为分析**: http://localhost:8000/behavior
- **船舶画像**: http://localhost:8000/profile
- **数据血缘**: http://localhost:8000/lineage

## 🎨 新增功能亮点

### ⚡ 实时监控大屏
- 系统资源监控（CPU/内存/磁盘）
- 数据库连接池状态（PostgreSQL + MongoDB）
- API调用统计
- 实时告警信息
- 数据流量监控

### 🎯 数据质量监控
- 四维质量评分（完整性/准确性/时效性/一致性）
- 数据表质量检查（5张核心表）
- 异常数据统计
- 质量规则检查
- 数据时效性监控
- 智能改进建议

## 📊 真实数据来源

所有监控数据都来自真实数据库：

| 数据项 | 来源 |
|-------|------|
| CPU/内存/磁盘 | psutil库 |
| PostgreSQL连接池 | pg_stat_activity |
| MongoDB连接池 | serverStatus |
| 数据质量指标 | vessels/companies/assets/risk_assessments/ais_tracks |
| 异常统计 | 数据库实时查询 |

## 🔧 故障排查

### 问题1: 应用启动失败

```bash
# 检查依赖
pip install fastapi uvicorn psycopg2-binary pymongo passlib[bcrypt] pydantic psutil

# 检查数据库连接
python scripts/test_mongo_connection.py
```

### 问题2: 页面显示"连接失败"

- 确认应用已启动（python main.py）
- 检查端口8000是否被占用
- 查看控制台错误信息

### 问题3: 数据不更新

- 检查数据库连接是否正常
- 查看浏览器控制台（F12）的网络请求
- 确认API返回数据正常

## 📚 相关文档

- **详细功能说明**: NEW_PAGES_README.md
- **真实数据集成**: REAL_DATA_INTEGRATION.md
- **完成报告**: COMPLETION_REPORT.md
- **项目路线图**: ROADMAP.md

## 💡 使用技巧

1. **页面导航**: 在dashboard页面右下角点击"页面导航"按钮，可以快速跳转到所有页面

2. **自动刷新**: 
   - 实时监控大屏：5秒自动刷新
   - 数据质量监控：10-60秒自动刷新

3. **返回大屏**: 所有子页面左上角都有"返回大屏"按钮

## 🎉 开始使用

```bash
# 一键启动
python main.py

# 然后访问
open http://localhost:8000/dashboard
```

**祝您使用愉快！** 🚀
