"""
使用真实特征重新训练模型
只使用数据库中真实存在的字段，不使用模拟数据
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from pathlib import Path
from ml_models.risk_predictor import RiskPredictor
from sklearn.model_selection import train_test_split
import clickhouse_connect


def load_real_data(batch_size=100000, max_batches=None):
    """
    分批加载真实数据，只使用数据库中的真实字段

    Args:
        batch_size: 每批数据量
        max_batches: 最大批次数

    Returns:
        合并后的DataFrame
    """
    print(f"📊 开始分批加载真实数据 (每批 {batch_size} 条)")

    client = clickhouse_connect.get_client(
        host='1.15.225.134',
        port=8123,
        username='default',
        password='sun2137405',
        database='silvernav'
    )

    all_data = []
    batch_num = 0

    while True:
        if max_batches and batch_num >= max_batches:
            print(f"\n⚠️ 已达到最大批次数 {max_batches}，停止加载")
            break

        offset = batch_num * batch_size
        print(f"\n批次 {batch_num + 1}: 加载 {offset} - {offset + batch_size} 条数据...")

        # 只查询真实存在的字段
        query = f"""
        SELECT
            v.imo_number as vessel_imo,
            v.vessel_name,
            v.vessel_type,
            v.build_year,
            v.flag_country,
            v.asset_risk_score,
            v.risk_level,
            v.owner_company_id,
            2026 - v.build_year as vessel_age
        FROM vessels v
        WHERE v.is_active = 1
            AND v.risk_level IS NOT NULL
            AND v.risk_level != ''
        ORDER BY v.id
        LIMIT {batch_size} OFFSET {offset}
        """

        try:
            result = client.query(query)
            df_batch = pd.DataFrame(result.result_rows, columns=result.column_names)

            if len(df_batch) == 0:
                print(f"   ✅ 没有更多数据，已加载全部数据")
                break

            # 转换数值类型
            df_batch['build_year'] = pd.to_numeric(df_batch['build_year'], errors='coerce')
            df_batch['asset_risk_score'] = pd.to_numeric(df_batch['asset_risk_score'], errors='coerce')
            df_batch['vessel_age'] = pd.to_numeric(df_batch['vessel_age'], errors='coerce')
            df_batch['owner_company_id'] = pd.to_numeric(df_batch['owner_company_id'], errors='coerce')

            # 过滤掉risk_level为空的数据
            df_batch = df_batch[df_batch['risk_level'].notna()]
            df_batch = df_batch[df_batch['risk_level'] != '']

            all_data.append(df_batch)
            print(f"   ✅ 成功加载 {len(df_batch)} 条数据，累计 {sum(len(d) for d in all_data)} 条")

            batch_num += 1

        except Exception as e:
            print(f"   ❌ 加载失败: {e}")
            import traceback
            traceback.print_exc()
            break

    client.close()

    if not all_data:
        raise Exception("没有成功加载任何数据")

    # 合并所有批次
    df_combined = pd.concat(all_data, ignore_index=True)
    print(f"\n✅ 数据加载完成，共 {len(df_combined)} 条记录，分 {len(all_data)} 批加载")

    return df_combined


def prepare_real_features(df):
    """
    准备真实特征（不使用模拟数据）

    Args:
        df: 原始数据

    Returns:
        X: 特征矩阵
        y: 目标变量
        feature_names: 特征名称列表
    """
    print(f"\n🔧 开始特征工程（仅使用真实特征）...")

    data = df.copy()

    # 处理缺失值
    data['build_year'].fillna(data['build_year'].median(), inplace=True)
    data['asset_risk_score'].fillna(data['asset_risk_score'].median(), inplace=True)
    data['vessel_age'].fillna(data['vessel_age'].median(), inplace=True)
    data['owner_company_id'].fillna(0, inplace=True)

    # 编码分类变量
    data['vessel_type_encoded'] = pd.Categorical(data['vessel_type']).codes
    data['flag_country_encoded'] = pd.Categorical(data['flag_country']).codes

    # 对owner_company_id进行归一化（因为ID值可能很大）
    data['owner_company_normalized'] = (data['owner_company_id'] - data['owner_company_id'].mean()) / data['owner_company_id'].std()

    # 编码目标变量
    risk_level_map = {'low': 0, 'medium': 1, 'high': 2}
    y = data['risk_level'].map(risk_level_map)

    # 只使用真实特征（6个特征）
    feature_columns = [
        'build_year',           # 建造年份
        'asset_risk_score',     # 资产风险评分
        'vessel_age',           # 船龄
        'vessel_type_encoded',  # 船舶类型
        'flag_country_encoded', # 船旗国
        'owner_company_normalized'  # 归一化的公司ID
    ]

    X = data[feature_columns]

    print(f"✅ 特征工程完成")
    print(f"   - 特征数量: {X.shape[1]}")
    print(f"   - 样本数量: {X.shape[0]}")
    print(f"   - 目标分布:")
    for level, count in y.value_counts().sort_index().items():
        level_name = ['低风险', '中风险', '高风险'][level]
        print(f"     {level_name}: {count} ({count/len(y)*100:.1f}%)")

    return X, y, feature_columns


def main():
    """主函数"""
    print("="*80)
    print("🚀 银航宝 - 机器学习模型重新训练（使用真实特征）")
    print("="*80)

    # 1. 分批加载真实数据
    print("\n📊 步骤1: 分批加载真实数据")
    try:
        vessel_df = load_real_data(batch_size=100000, max_batches=None)
    except Exception as e:
        print(f"\n❌ 数据加载失败: {e}")
        return

    print(f"\n数据统计:")
    print(f"   总样本数: {len(vessel_df)}")
    print(f"   特征数量: {len(vessel_df.columns)}")
    print(f"\n风险等级分布:")
    print(vessel_df['risk_level'].value_counts())

    # 2. 准备真实特征
    print("\n🔧 步骤2: 特征工程（仅使用真实特征）")
    X, y, feature_names = prepare_real_features(vessel_df)

    print(f"\n特征列表 ({len(feature_names)}个):")
    for i, feat in enumerate(feature_names, 1):
        print(f"   {i}. {feat}")

    # 3. 训练模型
    print("\n🤖 步骤3: 训练模型")
    print("\n" + "="*80)
    print("训练 Random Forest 模型")
    print("="*80)

    # 分割数据
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"\n数据分割:")
    print(f"   训练集: {X_train.shape[0]} 样本")
    print(f"   测试集: {X_test.shape[0]} 样本")

    # 创建并训练模型（调整参数避免过拟合）
    predictor = RiskPredictor(model_type='random_forest')
    predictor.feature_names = feature_names

    # 使用更保守的参数
    from sklearn.ensemble import RandomForestClassifier
    predictor.model = RandomForestClassifier(
        n_estimators=100,
        max_depth=8,           # 限制深度避免过拟合
        min_samples_split=10,  # 增加最小分割样本数
        min_samples_leaf=5,    # 增加叶子节点最小样本数
        max_features='sqrt',   # 使用sqrt特征数
        random_state=42,
        n_jobs=-1,
        class_weight='balanced'  # 平衡类别权重
    )

    predictor.train(X_train, y_train, X_test, y_test)

    # 评估模型
    metrics = predictor.evaluate(X_test, y_test)

    # 显示特征重要性
    print(f"\n📊 特征重要性:")
    importance_df = predictor.get_feature_importance(top_n=10)
    if importance_df is not None:
        print(importance_df.to_string(index=False))

    # 保存模型
    model_path = predictor.save_model('random_forest_real_features')

    # 测试预测
    print(f"\n🧪 测试预测（随机抽取10个样本）:")
    test_indices = np.random.choice(len(X_test), 10, replace=False)
    X_test_sample = X_test.iloc[test_indices]
    y_test_sample = y_test.iloc[test_indices]

    predictions = predictor.predict(X_test_sample)
    probabilities = predictor.predict_proba(X_test_sample)

    risk_level_map = {0: '低风险', 1: '中风险', 2: '高风险'}
    for i in range(len(predictions)):
        actual = risk_level_map[y_test_sample.iloc[i]]
        predicted = risk_level_map[predictions[i]]
        confidence = np.max(probabilities[i]) * 100
        print(f"   样本{i+1}: 实际={actual}, 预测={predicted}, 置信度={confidence:.1f}%")

    # 4. 完成
    print("\n" + "="*80)
    print("✅ 模型训练完成!")
    print("="*80)
    print("\n模型文件保存在: ml_models/saved_models/")
    print("\n下一步:")
    print("   1. 重启应用: python main.py")
    print("   2. 访问 http://localhost:8000/ml-predict 查看预测结果")


if __name__ == '__main__':
    main()
