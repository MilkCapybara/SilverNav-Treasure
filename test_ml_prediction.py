"""
测试机器学习预测功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ml_models.data_loader import DataLoader
from ml_models.risk_predictor import RiskPredictor
import pandas as pd
import numpy as np


def test_single_prediction():
    """测试单个船舶预测"""
    print("="*80)
    print("🧪 测试单个船舶风险预测")
    print("="*80)

    # 加载模型
    model_path = 'ml_models/saved_models/random_forest_latest.pkl'

    if not os.path.exists(model_path):
        print(f"❌ 模型文件不存在: {model_path}")
        print("   请先运行: python train_ml_models.py")
        return

    predictor = RiskPredictor()
    predictor.load_model(model_path)

    # 加载数据
    loader = DataLoader()
    vessel_df = loader.load_vessel_features(limit=10)

    # 准备特征
    X, y, features = loader.prepare_features(vessel_df)

    # 预测
    predictions = predictor.predict(X)
    probabilities = predictor.predict_proba(X)

    # 显示结果
    risk_level_map = {0: 'low', 1: 'medium', 2: 'high'}

    print(f"\n预测结果:")
    for i in range(len(predictions)):
        vessel_name = vessel_df.iloc[i]['vessel_name']
        actual = risk_level_map[y.iloc[i]]
        predicted = risk_level_map[predictions[i]]
        prob = probabilities[i]

        print(f"\n船舶 {i+1}: {vessel_name}")
        print(f"   实际风险等级: {actual}")
        print(f"   预测风险等级: {predicted}")
        print(f"   预测概率: Low={prob[0]:.2%}, Medium={prob[1]:.2%}, High={prob[2]:.2%}")
        print(f"   预测{'✅ 正确' if actual == predicted else '❌ 错误'}")

    loader.close()


def test_batch_prediction():
    """测试批量预测"""
    print("\n" + "="*80)
    print("🧪 测试批量风险预测")
    print("="*80)

    # 加载模型
    model_path = 'ml_models/saved_models/random_forest_latest.pkl'

    if not os.path.exists(model_path):
        print(f"❌ 模型文件不存在: {model_path}")
        return

    predictor = RiskPredictor()
    predictor.load_model(model_path)

    # 加载数据
    loader = DataLoader()
    vessel_df = loader.load_vessel_features(limit=100)

    # 准备特征
    X, y, features = loader.prepare_features(vessel_df)

    # 批量预测
    predictions = predictor.predict(X)

    # 统计准确率
    accuracy = (predictions == y).sum() / len(y)

    print(f"\n批量预测结果:")
    print(f"   样本数量: {len(predictions)}")
    print(f"   预测准确率: {accuracy:.2%}")

    # 统计各风险等级的预测情况
    risk_level_map = {0: 'low', 1: 'medium', 2: 'high'}

    print(f"\n风险等级分布:")
    for level in [0, 1, 2]:
        actual_count = (y == level).sum()
        predicted_count = (predictions == level).sum()
        correct_count = ((y == level) & (predictions == level)).sum()

        print(f"   {risk_level_map[level].upper():8s}: 实际={actual_count:3d}, 预测={predicted_count:3d}, 正确={correct_count:3d}")

    loader.close()


def test_feature_importance():
    """测试特征重要性"""
    print("\n" + "="*80)
    print("🧪 测试特征重要性分析")
    print("="*80)

    # 加载模型
    model_path = 'ml_models/saved_models/random_forest_latest.pkl'

    if not os.path.exists(model_path):
        print(f"❌ 模型文件不存在: {model_path}")
        return

    predictor = RiskPredictor()
    predictor.load_model(model_path)

    # 获取特征重要性
    importance_df = predictor.get_feature_importance(top_n=15)

    if importance_df is not None:
        print(f"\nTop 15 最重要特征:")
        print(importance_df.to_string(index=False))


if __name__ == '__main__':
    # 运行所有测试
    test_single_prediction()
    test_batch_prediction()
    test_feature_importance()

    print("\n" + "="*80)
    print("✅ 所有测试完成!")
    print("="*80)
