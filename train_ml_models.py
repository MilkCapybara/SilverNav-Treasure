"""
模型训练脚本
训练多个风险预测模型并保存
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_models.data_loader import DataLoader
from ml_models.risk_predictor import train_risk_model
import pandas as pd


def main():
    """主函数"""
    print("="*80)
    print("🚀 银航宝 - 机器学习模型训练")
    print("="*80)

    # 1. 加载数据
    print("\n📊 步骤1: 加载数据")
    loader = DataLoader()

    # 加载船舶数据（使用全部数据以获得更好的模型）
    print("\n正在加载船舶数据...")
    vessel_df = loader.load_vessel_features()  # 不限制数量，加载全部数据

    print(f"\n数据统计:")
    print(f"   总样本数: {len(vessel_df)}")
    print(f"   特征数量: {len(vessel_df.columns)}")
    print(f"\n风险等级分布:")
    print(vessel_df['risk_level'].value_counts())

    # 2. 准备特征
    print("\n🔧 步骤2: 特征工程")
    X, y, feature_names = loader.prepare_features(vessel_df, target_column='risk_level')

    print(f"\n特征列表 ({len(feature_names)}个):")
    for i, feat in enumerate(feature_names, 1):
        print(f"   {i:2d}. {feat}")

    # 3. 训练模型
    print("\n🤖 步骤3: 训练模型")

    # 训练RandomForest模型（默认，最稳定）
    print("\n" + "="*80)
    print("训练 Random Forest 模型")
    print("="*80)
    rf_predictor, rf_metrics = train_risk_model(
        X, y,
        model_type='random_forest',
        test_size=0.2
    )

    # 尝试训练XGBoost模型（如果可用）
    try:
        import xgboost
        print("\n" + "="*80)
        print("训练 XGBoost 模型")
        print("="*80)
        xgb_predictor, xgb_metrics = train_risk_model(
            X, y,
            model_type='xgboost',
            test_size=0.2
        )
    except ImportError:
        print("\n⚠️ XGBoost未安装，跳过XGBoost模型训练")
        print("   安装命令: pip install xgboost")

    # 尝试训练LightGBM模型（如果可用）
    try:
        import lightgbm
        print("\n" + "="*80)
        print("训练 LightGBM 模型")
        print("="*80)
        lgb_predictor, lgb_metrics = train_risk_model(
            X, y,
            model_type='lightgbm',
            test_size=0.2
        )
    except ImportError:
        print("\n⚠️ LightGBM未安装，跳过LightGBM模型训练")
        print("   安装命令: pip install lightgbm")

    # 4. 模型对比
    print("\n" + "="*80)
    print("📊 模型性能对比")
    print("="*80)

    comparison = pd.DataFrame({
        'Random Forest': {
            'Accuracy': rf_metrics['accuracy'],
            'Precision': rf_metrics['precision_macro'],
            'Recall': rf_metrics['recall_macro'],
            'F1-Score': rf_metrics['f1_macro']
        }
    })

    print("\n")
    print(comparison.T.to_string())

    # 5. 完成
    print("\n" + "="*80)
    print("✅ 模型训练完成!")
    print("="*80)
    print("\n模型文件保存在: ml_models/saved_models/")
    print("\n下一步:")
    print("   1. 运行 python ml_models/predict_api.py 启动预测API")
    print("   2. 或者运行 python test_ml_prediction.py 测试预测功能")

    loader.close()


if __name__ == '__main__':
    main()
