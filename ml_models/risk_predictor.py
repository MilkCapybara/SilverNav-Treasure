"""
机器学习模型训练模块
支持多种模型：XGBoost、LightGBM、RandomForest
"""
import pandas as pd
import numpy as np
import joblib
import json
from datetime import datetime
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, roc_auc_score, roc_curve
)
import matplotlib.pyplot as plt
import seaborn as sns

# 尝试导入XGBoost和LightGBM
try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    print("⚠️ XGBoost未安装，将使用RandomForest")

try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False
    print("⚠️ LightGBM未安装，将使用RandomForest")


class RiskPredictor:
    """风险预测模型"""

    def __init__(self, model_type='random_forest'):
        """
        初始化模型

        Args:
            model_type: 模型类型 ('random_forest', 'xgboost', 'lightgbm', 'gradient_boosting')
        """
        self.model_type = model_type
        self.model = None
        self.feature_names = None
        self.feature_importance = None
        self.metrics = {}
        self.model_dir = Path('ml_models/saved_models')
        self.model_dir.mkdir(parents=True, exist_ok=True)

        print(f"🤖 初始化模型: {model_type}")

    def create_model(self):
        """创建模型"""
        if self.model_type == 'xgboost' and HAS_XGBOOST:
            self.model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1,
                eval_metric='mlogloss'
            )
        elif self.model_type == 'lightgbm' and HAS_LIGHTGBM:
            self.model = lgb.LGBMClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1,
                verbose=-1
            )
        elif self.model_type == 'gradient_boosting':
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                random_state=42
            )
        else:
            # 默认使用RandomForest
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )
            self.model_type = 'random_forest'

        print(f"✅ 模型创建成功: {self.model_type}")
        return self.model

    def train(self, X_train, y_train, X_val=None, y_val=None):
        """
        训练模型

        Args:
            X_train: 训练特征
            y_train: 训练标签
            X_val: 验证特征（可选）
            y_val: 验证标签（可选）
        """
        print(f"\n🚀 开始训练模型...")
        print(f"   训练集大小: {X_train.shape}")
        if X_val is not None:
            print(f"   验证集大小: {X_val.shape}")

        # 创建模型
        if self.model is None:
            self.create_model()

        # 保存特征名称
        if isinstance(X_train, pd.DataFrame):
            self.feature_names = X_train.columns.tolist()
            X_train = X_train.values
        if X_val is not None and isinstance(X_val, pd.DataFrame):
            X_val = X_val.values

        # 训练模型
        start_time = datetime.now()

        if self.model_type in ['xgboost', 'lightgbm'] and X_val is not None:
            # XGBoost和LightGBM支持早停
            self.model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                verbose=False
            )
        else:
            self.model.fit(X_train, y_train)

        training_time = (datetime.now() - start_time).total_seconds()

        print(f"✅ 训练完成，耗时: {training_time:.2f}秒")

        # 获取特征重要性
        if hasattr(self.model, 'feature_importances_'):
            self.feature_importance = self.model.feature_importances_

        return self.model

    def evaluate(self, X_test, y_test):
        """
        评估模型

        Args:
            X_test: 测试特征
            y_test: 测试标签

        Returns:
            dict: 评估指标
        """
        print(f"\n📊 评估模型性能...")

        if isinstance(X_test, pd.DataFrame):
            X_test = X_test.values

        # 预测
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)

        # 计算指标
        self.metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision_macro': precision_score(y_test, y_pred, average='macro', zero_division=0),
            'recall_macro': recall_score(y_test, y_pred, average='macro', zero_division=0),
            'f1_macro': f1_score(y_test, y_pred, average='macro', zero_division=0),
            'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
        }

        # 计算每个类别的指标
        report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
        self.metrics['classification_report'] = report

        # 计算AUC（多分类）
        try:
            if len(np.unique(y_test)) > 2:
                self.metrics['auc_ovr'] = roc_auc_score(
                    y_test, y_pred_proba, multi_class='ovr', average='macro'
                )
            else:
                self.metrics['auc'] = roc_auc_score(y_test, y_pred_proba[:, 1])
        except Exception as e:
            print(f"⚠️ AUC计算失败: {e}")

        # 打印结果
        print(f"\n✅ 评估完成:")
        print(f"   准确率 (Accuracy):  {self.metrics['accuracy']:.4f}")
        print(f"   精确率 (Precision): {self.metrics['precision_macro']:.4f}")
        print(f"   召回率 (Recall):    {self.metrics['recall_macro']:.4f}")
        print(f"   F1分数 (F1-Score):  {self.metrics['f1_macro']:.4f}")
        if 'auc_ovr' in self.metrics:
            print(f"   AUC (OVR):          {self.metrics['auc_ovr']:.4f}")

        return self.metrics

    def predict(self, X):
        """
        预测

        Args:
            X: 特征数据

        Returns:
            predictions: 预测结果
        """
        if isinstance(X, pd.DataFrame):
            X = X.values

        predictions = self.model.predict(X)
        return predictions

    def predict_proba(self, X):
        """
        预测概率

        Args:
            X: 特征数据

        Returns:
            probabilities: 预测概率
        """
        if isinstance(X, pd.DataFrame):
            X = X.values

        probabilities = self.model.predict_proba(X)
        return probabilities

    def get_feature_importance(self, top_n=20):
        """
        获取特征重要性

        Args:
            top_n: 返回前N个重要特征

        Returns:
            pd.DataFrame: 特征重要性
        """
        if self.feature_importance is None:
            print("⚠️ 特征重要性不可用")
            return None

        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.feature_importance
        }).sort_values('importance', ascending=False)

        return importance_df.head(top_n)

    def plot_feature_importance(self, top_n=20, save_path=None):
        """
        绘制特征重要性图

        Args:
            top_n: 显示前N个特征
            save_path: 保存路径
        """
        importance_df = self.get_feature_importance(top_n)

        if importance_df is None:
            return

        plt.figure(figsize=(10, 8))
        plt.barh(range(len(importance_df)), importance_df['importance'])
        plt.yticks(range(len(importance_df)), importance_df['feature'])
        plt.xlabel('Feature Importance')
        plt.title(f'Top {top_n} Feature Importance')
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✅ 特征重要性图已保存: {save_path}")
        else:
            plt.show()

        plt.close()

    def plot_confusion_matrix(self, y_test, y_pred, save_path=None):
        """
        绘制混淆矩阵

        Args:
            y_test: 真实标签
            y_pred: 预测标签
            save_path: 保存路径
        """
        cm = confusion_matrix(y_test, y_pred)

        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
        plt.xlabel('Predicted')
        plt.ylabel('Actual')
        plt.title('Confusion Matrix')
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✅ 混淆矩阵已保存: {save_path}")
        else:
            plt.show()

        plt.close()

    def save_model(self, model_name=None):
        """
        保存模型

        Args:
            model_name: 模型名称
        """
        if model_name is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            model_name = f"{self.model_type}_{timestamp}"

        model_path = self.model_dir / f"{model_name}.pkl"
        metadata_path = self.model_dir / f"{model_name}_metadata.json"

        # 保存模型
        joblib.dump(self.model, model_path)

        # 保存元数据
        metadata = {
            'model_type': self.model_type,
            'feature_names': self.feature_names,
            'metrics': self.metrics,
            'created_at': datetime.now().isoformat()
        }

        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"✅ 模型已保存:")
        print(f"   模型文件: {model_path}")
        print(f"   元数据: {metadata_path}")

        return model_path

    def load_model(self, model_path):
        """
        加载模型

        Args:
            model_path: 模型路径
        """
        model_path = Path(model_path)
        metadata_path = model_path.parent / f"{model_path.stem}_metadata.json"

        # 加载模型
        self.model = joblib.load(model_path)

        # 加载元数据
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                self.model_type = metadata.get('model_type')
                self.feature_names = metadata.get('feature_names')
                self.metrics = metadata.get('metrics', {})

        print(f"✅ 模型已加载: {model_path}")
        return self.model


def train_risk_model(X, y, model_type='random_forest', test_size=0.2):
    """
    训练风险预测模型的便捷函数

    Args:
        X: 特征数据
        y: 目标变量
        model_type: 模型类型
        test_size: 测试集比例

    Returns:
        model: 训练好的模型
        metrics: 评估指标
    """
    print(f"\n{'='*60}")
    print(f"训练风险预测模型")
    print(f"{'='*60}")

    # 分割数据
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )

    print(f"\n数据分割:")
    print(f"   训练集: {X_train.shape[0]} 样本")
    print(f"   测试集: {X_test.shape[0]} 样本")

    # 创建并训练模型
    predictor = RiskPredictor(model_type=model_type)
    predictor.train(X_train, y_train)

    # 评估模型
    metrics = predictor.evaluate(X_test, y_test)

    # 显示特征重要性
    print(f"\n📊 Top 10 特征重要性:")
    importance_df = predictor.get_feature_importance(top_n=10)
    if importance_df is not None:
        print(importance_df.to_string(index=False))

    # 保存模型
    model_path = predictor.save_model()

    return predictor, metrics


if __name__ == '__main__':
    # 测试模型训练
    from ml_models.data_loader import DataLoader

    print("🚀 开始测试机器学习模型...")

    # 加载数据
    loader = DataLoader()
    vessel_df = loader.load_vessel_features(limit=5000)

    # 准备特征
    X, y, features = loader.prepare_features(vessel_df)

    # 训练模型
    predictor, metrics = train_risk_model(X, y, model_type='random_forest')

    print(f"\n✅ 测试完成!")

    loader.close()
