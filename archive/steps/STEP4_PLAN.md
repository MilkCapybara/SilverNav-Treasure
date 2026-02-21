# Step 4 开发计划：船舶资产风险页（vessels）

## 📋 任务概述

开发船舶资产风险详情页，展示船舶风险评估数据，包括船舶列表、风险评分排名、船龄分布、船型统计等功能。

## 🎯 核心功能

### 1. 统计卡片（4个指标）
- **总船舶数**：活跃船舶总数
- **高风险船舶**：风险等级为high的船舶数量
- **平均船龄**：所有船舶的平均船龄（年）
- **平均风险评分**：所有船舶的平均风险评分

### 2. 船舶风险排行榜
- 显示风险评分最高的Top 20船舶
- 表格列：排名、船舶名称、IMO编号、船型、船龄、所属企业、风险评分、风险等级
- 按风险评分降序排列
- 支持风险等级徽章显示（高/中/低）

### 3. 船龄分布图表
- 按船龄区间统计船舶数量
- 区间划分：
  - 0-5年（新船）
  - 5-10年（青年船）
  - 10-15年（中年船）
  - 15-20年（老龄船）
  - 20年以上（超龄船）
- 柱状图可视化展示

### 4. 船型分布图表
- 按船型统计船舶数量
- 主要船型：
  - Bulk Carrier（散货船）
  - Tanker（油轮）
  - Container Ship（集装箱船）
  - General Cargo（杂货船）
  - Other（其他）
- 柱状图可视化展示

## 📊 数据来源

### 主要数据表
1. **vessels**：船舶基本信息表
   - vessel_name：船舶名称
   - imo_number：IMO编号
   - vessel_type：船型
   - built_year：建造年份
   - asset_risk_score：资产风险评分
   - risk_level：风险等级
   - owner_company_id：所属企业ID

2. **companies**：企业信息表
   - company_name：企业名称

3. **vessel_risk_history**：船舶风险历史评估表（可选）
   - assessment_date：评估日期
   - risk_score：风险评分
   - risk_level：风险等级

## 🔧 技术实现

### 后端API开发

#### API端点
```
POST /api/detail/vessels
```

#### 请求参数
```json
{
  "currency": "CNY",
  "unit": "万元",
  "time_range": "30d"
}
```

#### 响应数据结构
```json
{
  "success": true,
  "base_date": "2026-02-19",
  "range": "today",
  "currency": "CNY",
  "stats": {
    "total_vessels": 1234,
    "high_risk_vessels": 56,
    "avg_vessel_age": 12.5,
    "avg_risk_score": 45.3
  },
  "vessel_ranking": [
    {
      "rank": 1,
      "vessel_name": "MV Ocean Star",
      "imo_number": "IMO1234567",
      "vessel_type": "Bulk Carrier",
      "vessel_age": 15,
      "company_name": "Company ABC",
      "risk_score": 85.5,
      "risk_level": "high"
    }
    // ... 更多记录
  ],
  "age_distribution": [
    {"range": "0-5年", "count": 234},
    {"range": "5-10年", "count": 345},
    {"range": "10-15年", "count": 456},
    {"range": "15-20年", "count": 123},
    {"range": "20年以上", "count": 76}
  ],
  "type_distribution": [
    {"type": "Bulk Carrier", "count": 456},
    {"type": "Tanker", "count": 345},
    {"type": "Container Ship", "count": 234},
    {"type": "General Cargo", "count": 123},
    {"type": "Other", "count": 76}
  ]
}
```

### SQL查询设计

#### 1. 统计数据查询
```sql
SELECT
    COUNT(*) AS total_vessels,
    COUNT(CASE WHEN risk_level = 'high' THEN 1 END) AS high_risk_vessels,
    AVG(EXTRACT(YEAR FROM CURRENT_DATE) - built_year) AS avg_vessel_age,
    AVG(asset_risk_score) AS avg_risk_score
FROM vessels
WHERE is_active = TRUE
```

#### 2. 船舶风险排行榜查询
```sql
SELECT
    v.vessel_name,
    v.imo_number,
    v.vessel_type,
    EXTRACT(YEAR FROM CURRENT_DATE) - v.built_year AS vessel_age,
    c.company_name,
    v.asset_risk_score AS risk_score,
    v.risk_level
FROM vessels v
LEFT JOIN companies c ON c.id = v.owner_company_id
WHERE v.is_active = TRUE
  AND v.asset_risk_score IS NOT NULL
ORDER BY v.asset_risk_score DESC
LIMIT 20
```

#### 3. 船龄分布查询
```sql
SELECT
    CASE
        WHEN vessel_age < 5 THEN '0-5年'
        WHEN vessel_age < 10 THEN '5-10年'
        WHEN vessel_age < 15 THEN '10-15年'
        WHEN vessel_age < 20 THEN '15-20年'
        ELSE '20年以上'
    END AS range,
    COUNT(*) AS count
FROM (
    SELECT EXTRACT(YEAR FROM CURRENT_DATE) - built_year AS vessel_age
    FROM vessels
    WHERE is_active = TRUE
) t
GROUP BY range
ORDER BY range
```

#### 4. 船型分布查询
```sql
SELECT
    vessel_type AS type,
    COUNT(*) AS count
FROM vessels
WHERE is_active = TRUE
GROUP BY vessel_type
ORDER BY count DESC
```

### 前端开发

#### 1. 扩展fetchDetailData()函数
```javascript
// 在fetchDetailData()中添加vessels类型支持
if (Detail.type === "credit" || Detail.type === "alerts" || Detail.type === "vessels") {
    // ... API调用逻辑
    if (Detail.type === "vessels") {
        renderVesselsData(data);
    }
}
```

#### 2. 实现renderVesselsData()函数
```javascript
function renderVesselsData(data) {
    const { stats, vessel_ranking, age_distribution, type_distribution, unit } = data;

    // 1. 更新统计卡片
    updateVesselsStats(stats);

    // 2. 渲染船龄分布图表
    renderAgeDistributionChart(age_distribution);

    // 3. 渲染船型分布图表
    renderTypeDistributionChart(type_distribution);

    // 4. 渲染船舶风险排行榜表格
    renderVesselRankingTable(vessel_ranking);
}
```

#### 3. 实现数据渲染函数
- `updateVesselsStats()` - 更新统计卡片
- `renderAgeDistributionChart()` - 渲染船龄分布柱状图
- `renderTypeDistributionChart()` - 渲染船型分布柱状图
- `renderVesselRankingTable()` - 渲染船舶排行榜表格

#### 4. 更新renderVesselsDetail()函数
添加统计卡片、图表容器和表格容器的HTML结构。

## 📝 开发步骤

### 第一阶段：后端API开发（30分钟）
1. 在main.py中添加 `/api/detail/vessels` API端点
2. 实现4个核心SQL查询
3. 添加详细的调试日志
4. 实现错误处理机制

### 第二阶段：SQL查询测试（30分钟）
5. 创建测试脚本 `test_vessels_api.py`
6. 独立测试每个SQL查询
7. 验证数据完整性和准确性
8. 性能测试（确保查询时间<300ms）

### 第三阶段：前端开发（1小时）
9. 扩展 `fetchDetailData()` 函数支持vessels类型
10. 实现 `renderVesselsData()` 函数
11. 实现4个数据渲染函数
12. 更新 `renderVesselsDetail()` 函数

### 第四阶段：集成测试（30分钟）
13. API集成测试（使用curl命令）
14. 浏览器端功能测试
15. 验证数据展示正确性
16. 性能测试和优化

## ✅ 验收标准

- [ ] 创建 `/api/detail/vessels` API端点
- [ ] 实现4个核心SQL查询
- [ ] SQL查询独立测试通过
- [ ] API集成测试通过
- [ ] 扩展 `fetchDetailData()` 支持vessels类型
- [ ] 实现 `renderVesselsData()` 函数
- [ ] 实现4个数据渲染函数
- [ ] 更新 `renderVesselsDetail()` 函数
- [ ] 浏览器端功能测试通过
- [ ] 性能测试通过（API响应<500ms）

## 📊 预期成果

### 代码统计
| 文件 | 新增行数 | 功能 |
|------|---------|------|
| main.py | ~120 | 后端API端点 |
| static/js/detail.js | ~150 | 前端数据加载和渲染 |
| test_vessels_api.py | ~200 | 测试脚本 |
| **总计** | **~470** | **船舶资产风险页完整功能** |

### 功能特性
1. **多维度数据展示**：统计卡片、图表、表格
2. **船龄分布可视化**：5个年龄段柱状图
3. **船型分布可视化**：主要船型柱状图
4. **风险排行榜**：Top 20高风险船舶
5. **风险等级标识**：高/中/低风险徽章
6. **响应式布局**：支持桌面端和移动端

## 🎯 技术亮点

1. **复用成功经验**：
   - 使用Step 2和Step 3的API结构
   - 复用数据渲染函数（formatAmount）
   - 统一的错误处理机制
   - 详细的调试日志

2. **SQL查询优化**：
   - 使用LEFT JOIN关联企业信息
   - 使用CASE WHEN进行数据分组
   - 使用子查询计算船龄
   - 合理使用索引提升性能

3. **数据可视化**：
   - 柱状图展示船龄分布
   - 柱状图展示船型分布
   - 表格展示船舶排行榜
   - 颜色编码区分风险等级

## 📈 项目进度

- ✅ Phase 0：MVP基础功能（登录认证 + 数据大屏）
- ✅ Step 1：详情页面路由逻辑
- ✅ Step 2：授信详情页（100%完成）
- ✅ Step 3：高风险预警详情页（100%完成）
- 📋 **Step 4：船舶资产风险页（待开发）**
- 📋 Step 5：不良资产明细页（待开发）
- 📋 Step 6：风险趋势分析页（待开发）
- 📋 Step 7：风险因子拆解页（待开发）
- 📋 Step 8：风险等级分布详情页（待开发）
- 📋 Step 9：总体风险敞口详情页（待开发）

## 🚀 开始时间

预计开始时间：下次工作会话
预计完成时间：1-2天
开发优先级：高

---

**创建时间**: 2026-02-20 00:50
**创建者**: Claude (Sonnet 4.5)
**状态**: 待开发
**依赖**: Step 2和Step 3的成功经验
