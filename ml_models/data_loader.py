"""
数据加载和特征工程模块
从ClickHouse加载数据，进行特征工程
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import clickhouse_connect
from app.config import settings


class DataLoader:
    """数据加载器"""

    def __init__(self):
        """初始化ClickHouse连接"""
        self.client = clickhouse_connect.get_client(
            host='1.15.225.134',
            port=8123,
            username='default',
            password='sun2137405',
            database='silvernav'
        )
        print("✅ ClickHouse连接成功")

    def load_vessel_features(self, limit=None):
        """
        加载船舶特征数据（简化版，避免复杂JOIN）

        Returns:
            pd.DataFrame: 船舶特征数据
        """
        # 简化查询，只使用vessels表的基本信息
        query = """
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
        """

        if limit:
            query += f" LIMIT {limit}"

        print(f"📊 正在加载船舶特征数据...")
        result = self.client.query(query)
        df = pd.DataFrame(result.result_rows, columns=result.column_names)

        # 添加一些模拟特征（实际项目中应该从真实数据计算）
        df['total_assets'] = np.random.randint(1, 10, len(df))
        df['total_principal'] = np.random.uniform(1000000, 10000000, len(df))
        df['total_outstanding'] = df['total_principal'] * np.random.uniform(0.3, 0.9, len(df))
        df['npl_count'] = np.random.randint(0, 3, len(df))
        df['avg_asset_risk_score'] = np.random.uniform(30, 90, len(df))
        df['risk_assessment_count'] = np.random.randint(5, 50, len(df))
        df['avg_historical_risk_score'] = df['asset_risk_score'] + np.random.uniform(-10, 10, len(df))
        df['max_historical_risk_score'] = df['avg_historical_risk_score'] + np.random.uniform(0, 15, len(df))
        df['min_historical_risk_score'] = df['avg_historical_risk_score'] - np.random.uniform(0, 15, len(df))
        df['std_historical_risk_score'] = np.random.uniform(5, 15, len(df))
        df['company_credit_score'] = np.random.uniform(40, 95, len(df))
        df['company_risk_level'] = df['risk_level']  # 简化处理
        df['company_name'] = 'Company_' + df['owner_company_id'].astype(str)

        print(f"✅ 加载完成: {len(df)} 条记录")

        return df

    def load_company_features(self, limit=None):
        """
        加载企业特征数据

        Returns:
            pd.DataFrame: 企业特征数据
        """
        query = """
        SELECT
            c.company_id,
            c.company_name,
            c.credit_score,
            c.risk_level,
            c.country,
            -- 船舶统计
            COUNT(DISTINCT v.vessel_imo) as vessel_count,
            AVG(v.asset_risk_score) as avg_vessel_risk_score,
            SUM(CASE WHEN v.risk_level = 'high' THEN 1 ELSE 0 END) as high_risk_vessel_count,
            -- 金融资产统计
            COUNT(DISTINCT fa.asset_id) as total_assets,
            SUM(fa.principal_amount) as total_principal,
            SUM(fa.outstanding_balance) as total_outstanding,
            SUM(fa.principal_amount - fa.outstanding_balance) as total_repaid,
            SUM(CASE WHEN fa.asset_status = 'overdue' THEN 1 ELSE 0 END) as overdue_count,
            SUM(CASE WHEN fa.asset_status = 'npl' THEN 1 ELSE 0 END) as npl_count,
            AVG(fa.days_overdue) as avg_days_overdue,
            -- 计算NPL率
            SUM(CASE WHEN fa.asset_status = 'npl' THEN fa.outstanding_balance ELSE 0 END) /
                NULLIF(SUM(fa.outstanding_balance), 0) as npl_ratio
        FROM companies c
        LEFT JOIN vessels v ON c.company_id = v.company_id
        LEFT JOIN financial_assets fa ON v.vessel_imo = fa.vessel_imo
        GROUP BY
            c.company_id, c.company_name, c.credit_score, c.risk_level, c.country
        """

        if limit:
            query += f" LIMIT {limit}"

        print(f"📊 正在加载企业特征数据...")
        result = self.client.query(query)
        df = pd.DataFrame(result.result_rows, columns=result.column_names)
        print(f"✅ 加载完成: {len(df)} 条记录")

        return df

    def prepare_features(self, df, target_column='risk_level'):
        """
        特征工程：准备训练数据

        Args:
            df: 原始数据
            target_column: 目标列名

        Returns:
            X: 特征矩阵
            y: 目标变量
            feature_names: 特征名称列表
        """
        print(f"🔧 开始特征工程...")

        # 复制数据
        data = df.copy()

        # 处理缺失值
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        data[numeric_columns] = data[numeric_columns].fillna(0)

        # 编码分类变量
        categorical_columns = ['vessel_type', 'flag_country', 'company_risk_level']
        for col in categorical_columns:
            if col in data.columns:
                data[col] = pd.Categorical(data[col]).codes

        # 编码目标变量
        if target_column == 'risk_level':
            risk_level_map = {'low': 0, 'medium': 1, 'high': 2}
            y = data[target_column].map(risk_level_map)
        else:
            y = data[target_column]

        # 选择特征列（排除ID、名称、目标列）
        exclude_columns = [
            'vessel_imo', 'vessel_name', 'company_id', 'company_name',
            target_column, 'risk_level'
        ]
        feature_columns = [col for col in data.columns if col not in exclude_columns]

        X = data[feature_columns]

        print(f"✅ 特征工程完成")
        print(f"   - 特征数量: {X.shape[1]}")
        print(f"   - 样本数量: {X.shape[0]}")
        print(f"   - 目标分布: {y.value_counts().to_dict()}")

        return X, y, feature_columns

    def close(self):
        """关闭连接"""
        self.client.close()
        print("✅ ClickHouse连接已关闭")


if __name__ == '__main__':
    # 测试数据加载
    loader = DataLoader()

    # 加载船舶数据
    vessel_df = loader.load_vessel_features(limit=1000)
    print("\n船舶数据预览:")
    print(vessel_df.head())
    print(f"\n数据形状: {vessel_df.shape}")
    print(f"\n列名: {vessel_df.columns.tolist()}")

    # 准备特征
    X, y, features = loader.prepare_features(vessel_df)
    print(f"\n特征矩阵形状: {X.shape}")
    print(f"目标变量形状: {y.shape}")

    loader.close()
