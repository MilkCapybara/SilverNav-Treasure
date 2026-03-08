"""
快速启动脚本 - 机器学习模块
一键完成：安装依赖 → 训练模型 → 测试预测
"""
import subprocess
import sys
import os


def run_command(cmd, description):
    """运行命令并显示进度"""
    print(f"\n{'='*80}")
    print(f"🚀 {description}")
    print(f"{'='*80}")
    print(f"执行命令: {cmd}\n")

    result = subprocess.run(cmd, shell=True)

    if result.returncode != 0:
        print(f"\n❌ {description} 失败")
        return False

    print(f"\n✅ {description} 完成")
    return True


def main():
    """主函数"""
    print("="*80)
    print("🎯 银航宝 - 机器学习模块快速启动")
    print("="*80)
    print("\n本脚本将自动完成以下步骤:")
    print("   1. 检查并安装依赖包")
    print("   2. 训练机器学习模型")
    print("   3. 测试预测功能")
    print("   4. 启动预测API")

    input("\n按回车键开始...")

    # 步骤1: 安装依赖
    if not run_command(
        "pip install -r requirements-ml.txt",
        "步骤1: 安装机器学习依赖包"
    ):
        print("\n⚠️ 依赖安装失败，但可以继续尝试...")

    # 步骤2: 训练模型
    if not run_command(
        "python train_ml_models.py",
        "步骤2: 训练机器学习模型"
    ):
        print("\n❌ 模型训练失败，无法继续")
        return

    # 步骤3: 测试预测
    if not run_command(
        "python test_ml_prediction.py",
        "步骤3: 测试预测功能"
    ):
        print("\n⚠️ 测试失败，但模型可能已经训练成功")

    # 完成
    print("\n" + "="*80)
    print("✅ 机器学习模块启动完成!")
    print("="*80)
    print("\n下一步:")
    print("   1. 启动主应用: python main.py")
    print("   2. 访问预测API: http://localhost:8000/api/ml/health")
    print("   3. 查看API文档: http://localhost:8000/docs")


if __name__ == '__main__':
    main()
