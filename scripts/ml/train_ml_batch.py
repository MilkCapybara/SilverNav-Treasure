"""
分批训练脚本 - 避免一次性加载大量数据
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


def load_data_in_batches(batch_size=100000, max_batches=None):
    """
    分批加载数据

    Args:
        batch_size: 每批数据量（默认10万）
        max_batches: 最大批次数（None表示加载全部数据）

    Returns:
        合并后的DataFrame
    """
    print(f"📊 开始分批加载数据 (每批 {batch_size} 条)")
    if max_batches:
        print(f"   最多加载 {max_batches} 批")
    else:
        print(f"   加载全部数据直到结束")

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
        # 检查是否达到最大批次
        if max_batches and batch_num >= max_batches:
            print(f"\n⚠️ 已达到最大批次数 {max_batches}，停止加载")
            break

        offset = batch_num * batch_size

        print(f"\n批次 {batch_num + 1}: 加载 {offset} - {offset + batch_size} 条数据...")

        query = f"""
        SELECT
            v.imo_number as vessel_imo,
            v.vessel_name,
            v.vessel_type,
            v.build_year as built_year,
            v.flag_country,
            v.asset_risk_score,
            v.risk_level,
            v.owner_company_id,
            2026 - v.build_year as vessel_age
        FROM vessels v
        WHERE v.is_active = 1
        ORDER BY v.id
        LIMIT {batch_size} OFFSET {offset}
        """

        try:
            result = client.query(query)
            df_batch = pd.DataFrame(result.result_rows, columns=result.column_names)

            if len(df_batch) == 0:
                print(f"   ✅ 没有更多数据，已加载全部数据")
                break

            # 转换Decimal类型为float
            for col in df_batch.columns:
                if df_batch[col].dtype == 'object':
                    try:
                        df_batch[col] = pd.to_numeric(df_batch[col], errors='coerce')
                    except:
                        pass

            # 确保数值列为float类型
            numeric_cols = ['asset_risk_score', 'built_year', 'vessel_age', 'owner_company_id']
            for col in numeric_cols:
                if col in df_batch.columns:
                    df_batch[col] = df_batch[col].astype(float)

            # 添加模拟特征（避免复杂JOIN）
            np.random.seed(42 + batch_num)  # 每批使用不同的随机种子
            df_batch['total_assets'] = np.random.randint(1, 10, len(df_batch))
            df_batch['total_principal'] = np.random.uniform(1000000, 10000000, len(df_batch))
            df_batch['total_outstanding'] = df_batch['total_principal'] * np.random.uniform(0.3, 0.9, len(df_batch))
            df_batch['npl_count'] = np.random.randint(0, 3, len(df_batch))
            df_batch['avg_asset_risk_score'] = np.random.uniform(30, 90, len(df_batch))
            df_batch['risk_assessment_count'] = np.random.randint(5, 50, len(df_batch))
            df_batch['avg_historical_risk_score'] = df_batch['asset_risk_score'].astype(float) + np.random.uniform(-10, 10, len(df_batch))
            df_batch['max_historical_risk_score'] = df_batch['avg_historical_risk_score'] + np.random.uniform(0, 15, len(df_batch))
            df_batch['min_historical_risk_score'] = df_batch['avg_historical_risk_score'] - np.random.uniform(0, 15, len(df_batch))
            df_batch['std_historical_risk_score'] = np.random.uniform(5, 15, len(df_batch))
            df_batch['company_credit_score'] = np.random.uniform(40, 95, len(df_batch))
            df_batch['company_risk_level'] = df_batch['risk_level']
            df_batch['company_name'] = 'Company_' + df_batch['owner_company_id'].astype(int).astype(str)

            # 如果risk_level为空，根据asset_risk_score生成
            if df_batch['risk_level'].isna().any() or (df_batch['risk_level'] == '').any():
                print(f"   ⚠️ 检测到空的risk_level，根据asset_risk_score生成...")
                def assign_risk_level(score):
                    if pd.isna(score):
                        return 'medium'
                    score = float(score)
                    if score < 50:
                        return 'low'
                    elif score < 70:
                        return 'medium'
                    else:
                        return 'high'

                df_batch['risk_level'] = df_batch['asset_risk_score'].apply(assign_risk_level)
                df_batch['company_risk_level'] = df_batch['risk_level']

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


def prepare_features(df):
    """准备特征"""
    print(f"\n🔧 开始特征工程...")

    # 处理缺失值
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    df[numeric_columns] = df[numeric_columns].fillna(0)

    # 编码分类变量
    df['vessel_type_encoded'] = pd.Categorical(df['vessel_type']).codes
    df['flag_country_encoded'] = pd.Categorical(df['flag_country']).codes
    df['company_risk_level_encoded'] = pd.Categorical(df['company_risk_level']).codes

    # 编码目标变量
    risk_level_map = {'low': 0, 'medium': 1, 'high': 2}
    y = df['risk_level'].map(risk_level_map)

    # 选择特征列
    exclude_columns = [
        'vessel_imo', 'vessel_name', 'owner_company_id', 'company_name',
        'risk_level', 'vessel_type', 'flag_country', 'company_risk_level'
    ]
    feature_columns = [col for col in df.columns if col not in exclude_columns]

    X = df[feature_columns]

    print(f"✅ 特征工程完成")
    print(f"   - 特征数量: {X.shape[1]}")
    print(f"   - 样本数量: {X.shape[0]}")
    print(f"   - 目标分布: {y.value_counts().to_dict()}")

    return X, y, feature_columns


def main():
    """主函数"""
    print("="*80)
    print("🚀 银航宝 - 机器学习模型训练（分批加载版）")
    print("="*80)

    # 1. 分批加载数据
    print("\n📊 步骤1: 分批加载数据")
    try:
        # 加载全部数据，每批100000条
        vessel_df = load_data_in_batches(batch_size=100000, max_batches=None)
    except Exception as e:
        print(f"\n❌ 数据加载失败: {e}")
        return

    print(f"\n数据统计:")
    print(f"   总样本数: {len(vessel_df)}")
    print(f"   特征数量: {len(vessel_df.columns)}")
    print(f"\n风险等级分布:")
    print(vessel_df['risk_level'].value_counts())

    # 2. 准备特征
    print("\n🔧 步骤2: 特征工程")
    X, y, feature_names = prepare_features(vessel_df)

    print(f"\n特征列表 ({len(feature_names)}个):")
    for i, feat in enumerate(feature_names, 1):
        print(f"   {i:2d}. {feat}")

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

    # 创建并训练模型
    predictor = RiskPredictor(model_type='random_forest')
    predictor.feature_names = feature_names
    predictor.train(X_train, y_train, X_test, y_test)

    # 评估模型
    metrics = predictor.evaluate(X_test, y_test)

    # 显示特征重要性
    print(f"\n📊 Top 10 特征重要性:")
    importance_df = predictor.get_feature_importance(top_n=10)
    if importance_df is not None:
        print(importance_df.to_string(index=False))

    # 保存模型
    model_path = predictor.save_model('random_forest_latest')

    # 4. 完成
    print("\n" + "="*80)
    print("✅ 模型训练完成!")
    print("="*80)
    print("\n模型文件保存在: ml_models/saved_models/")
    print("\n下一步:")
    print("   1. 运行 python main.py 启动应用")
    print("   2. 访问 http://localhost:8000/ml-predict 查看机器学习页面")
    print("   3. 或者运行 python test_ml_prediction.py 测试预测功能")


if __name__ == '__main__':
    main()
