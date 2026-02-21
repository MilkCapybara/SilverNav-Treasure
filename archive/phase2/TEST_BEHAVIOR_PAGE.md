# 船舶行为分析页面测试指南

## 🚀 快速测试

### 1. 启动服务

```bash
cd /Users/sunfanmacpro/Desktop/SilverNav-Treasure
python3 main.py
```

### 2. 访问页面

打开浏览器访问：http://localhost:8000/behavior

### 3. 登录（如果需要）

- 账号：`root`
- 密码：`sunfannb0307SF?`

---

## ✅ 功能测试清单

### 基础功能测试

- [ ] 页面加载成功
- [ ] 顶部导航栏显示正常
- [ ] 时钟实时更新
- [ ] 三栏布局显示正常
- [ ] 地图加载成功

### 数据概览测试

- [ ] 总轨迹点数显示
- [ ] 船舶数量显示
- [ ] 异常停泊数显示
- [ ] 数据时间跨度显示
- [ ] 船舶类型分布图显示

### 船舶查询测试

- [ ] 输入IMO编号：`IMO9000001`
- [ ] 选择时间范围：`近30天`
- [ ] 点击"查询轨迹"按钮
- [ ] 地图上显示轨迹线
- [ ] 显示起点和终点标记
- [ ] 点击标记显示详细信息
- [ ] 右侧显示船舶信息

### 异常停泊测试

- [ ] 右侧面板显示异常列表
- [ ] 点击异常记录
- [ ] 地图定位到异常位置
- [ ] 显示异常详细信息

### 地理围栏测试

- [ ] 选择区域：`上海港周边`
- [ ] 地图显示区域边界
- [ ] 点击"查询区域船舶"
- [ ] 显示区域内船舶标记
- [ ] 点击船舶标记查看信息

### Spark分析测试

- [ ] 点击"运行轨迹分析"按钮
- [ ] 显示确认对话框
- [ ] 状态指示器变为"运行中"
- [ ] 显示Toast提示
- [ ] 状态恢复为"就绪"

### 地图控制测试

- [ ] 点击"适应边界"按钮
- [ ] 点击"清除轨迹"按钮
- [ ] 点击"热力图"按钮（显示开发中提示）

### 图表测试

- [ ] 船舶类型分布图显示数据
- [ ] 速度分布图显示数据
- [ ] 图表可以交互

### 响应式测试

- [ ] 缩小浏览器窗口
- [ ] 检查布局是否适应
- [ ] 检查移动端显示

---

## 🐛 常见问题排查

### 问题1：页面无法访问

**症状**：浏览器显示"无法访问此网站"

**解决方案**：
1. 检查服务是否启动：`ps aux | grep python3`
2. 检查端口是否被占用：`lsof -i :8000`
3. 重新启动服务：`python3 main.py`

### 问题2：地图不显示

**症状**：地图区域空白

**解决方案**：
1. 检查网络连接（需要加载Leaflet.js CDN）
2. 打开浏览器控制台查看错误信息
3. 检查JavaScript是否加载成功

### 问题3：数据不显示

**症状**：统计卡片显示"-"

**解决方案**：
1. 检查MongoDB连接：
   ```bash
   python3 -c "from app.database import get_mongo_db; db = get_mongo_db(); print('连接成功')"
   ```
2. 检查数据是否存在：
   ```bash
   python3 -c "from pymongo import MongoClient; from app.config import settings; client = MongoClient(f'mongodb://{settings.mongo_user}:{settings.mongo_password}@{settings.mongo_host}:{settings.mongo_port}/{settings.mongo_db}?authSource={settings.mongo_auth_source}'); print(f'记录数: {client[settings.mongo_db][\"ais_tracks\"].count_documents({})}'); client.close()"
   ```

### 问题4：查询无结果

**症状**：点击查询后没有显示轨迹

**解决方案**：
1. 检查IMO编号是否正确（例如：IMO9000001）
2. 检查时间范围是否有数据
3. 打开浏览器控制台查看API响应

### 问题5：Spark按钮无反应

**症状**：点击Spark按钮没有反应

**解决方案**：
1. 这是正常的，Spark作业需要在服务器端手动运行
2. 前端按钮仅用于演示和状态显示
3. 实际运行Spark作业：`./run_spark_analysis.sh`

---

## 📊 性能测试

### API响应时间测试

```bash
# 测试数据概览API
time curl -X GET http://localhost:8000/api/behavior/summary

# 测试轨迹查询API
time curl -X POST http://localhost:8000/api/behavior/tracks \
  -H "Content-Type: application/json" \
  -d '{"imo_number": "IMO9000001", "limit": 100}'

# 测试异常查询API
time curl -X POST http://localhost:8000/api/behavior/anomalies \
  -H "Content-Type: application/json" \
  -d '{"limit": 20}'
```

### 预期性能指标

- 数据概览API：< 200ms
- 轨迹查询API（100条）：< 500ms
- 异常查询API（20条）：< 300ms
- 地理围栏查询API（100条）：< 500ms

---

## 📝 测试报告模板

```
测试日期：____________________
测试人员：____________________

基础功能：
- 页面加载：[ ] 通过 [ ] 失败
- 地图显示：[ ] 通过 [ ] 失败
- 数据概览：[ ] 通过 [ ] 失败

查询功能：
- 船舶查询：[ ] 通过 [ ] 失败
- 异常查询：[ ] 通过 [ ] 失败
- 地理围栏：[ ] 通过 [ ] 失败

性能测试：
- API响应时间：________ms
- 地图渲染时间：________ms
- 数据加载时间：________ms

问题记录：
1. ____________________
2. ____________________
3. ____________________

总体评价：
[ ] 优秀 [ ] 良好 [ ] 一般 [ ] 需改进
```

---

**创建时间**: 2026-02-21
**测试版本**: v1.0
