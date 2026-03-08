#!/usr/bin/env python3
"""
完整的PDF上传到HDFS脚本（包含环境配置）
"""
import os
import subprocess
import sys
from datetime import datetime

# 配置
SSH_HOST = "1.15.225.134"
SSH_PORT = 22
SSH_USER = "hadoopuser"
SSH_PASSWORD = "sunfanjibada"
LOCAL_PDF_DIR = "./contracts_pdf"
REMOTE_TEMP_DIR = "/tmp/silvernav_contracts_upload"
HDFS_TARGET_DIR = "/silvernav/contracts"
HADOOP_HOME = "/usr/local/hadoop"


def run_ssh_command(command, description="", timeout=300):
    """执行SSH命令"""
    if description:
        print(f"🔧 {description}")

    # 添加Hadoop环境变量
    env_setup = f"export HADOOP_HOME={HADOOP_HOME} && export PATH=$HADOOP_HOME/bin:$PATH && "
    full_command = env_setup + command

    full_cmd = f"sshpass -p '{SSH_PASSWORD}' ssh -o StrictHostKeyChecking=no -p {SSH_PORT} {SSH_USER}@{SSH_HOST} '{full_command}'"

    try:
        result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result
    except subprocess.TimeoutExpired:
        print(f"❌ 命令超时")
        return None
    except Exception as e:
        print(f"❌ 命令执行失败: {e}")
        return None


def main():
    print("=" * 80)
    print("🚀 船舶融资合同PDF完整上传到HDFS")
    print("=" * 80)
    print(f"📅 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🖥️  云服务器: {SSH_USER}@{SSH_HOST}")
    print(f"📁 本地目录: {os.path.abspath(LOCAL_PDF_DIR)}")
    print(f"📦 HDFS目标: {HDFS_TARGET_DIR}")
    print(f"🔧 Hadoop路径: {HADOOP_HOME}")
    print("=" * 80)

    start_time = datetime.now()

    # 1. 检查本地文件
    print("\n📍 步骤1: 检查本地PDF文件...")
    if not os.path.exists(LOCAL_PDF_DIR):
        print(f"❌ 本地目录不存在: {LOCAL_PDF_DIR}")
        return False

    pdf_files = [f for f in os.listdir(LOCAL_PDF_DIR) if f.endswith('.pdf')]
    pdf_count = len(pdf_files)
    total_size = sum(os.path.getsize(os.path.join(LOCAL_PDF_DIR, f)) for f in pdf_files)
    total_size_mb = total_size / (1024 * 1024)

    print(f"✅ 找到 {pdf_count} 个PDF文件")
    print(f"📊 总大小: {total_size_mb:.2f} MB")

    # 2. 测试SSH和HDFS
    print("\n📍 步骤2: 测试HDFS连接...")
    result = run_ssh_command("hdfs version | head -3", "测试HDFS命令")
    if not result or result.returncode != 0:
        print("❌ HDFS命令不可用")
        return False
    print("✅ HDFS连接正常")
    print(result.stdout)

    # 3. 创建远程临时目录
    print("\n📍 步骤3: 创建远程临时目录...")
    result = run_ssh_command(f"mkdir -p {REMOTE_TEMP_DIR}", "创建临时目录")
    if result and result.returncode == 0:
        print(f"✅ 临时目录创建成功: {REMOTE_TEMP_DIR}")
    else:
        print("❌ 临时目录创建失败")
        return False

    # 4. 上传文件到云服务器
    print("\n📍 步骤4: 上传PDF到云服务器...")
    print("🚀 开始上传 (这可能需要几分钟)...")

    cmd = f"sshpass -p '{SSH_PASSWORD}' rsync -avz --progress -e 'ssh -p {SSH_PORT} -o StrictHostKeyChecking=no' {LOCAL_PDF_DIR}/*.pdf {SSH_USER}@{SSH_HOST}:{REMOTE_TEMP_DIR}/"

    result = subprocess.run(cmd, shell=True, timeout=3600)

    if result.returncode != 0:
        print("❌ 文件上传失败")
        return False

    print("✅ 文件上传到云服务器成功!")

    # 5. 验证上传的文件
    print("\n📍 步骤5: 验证上传的文件...")
    result = run_ssh_command(f"ls {REMOTE_TEMP_DIR} | wc -l", "统计文件数量")
    if result and result.stdout:
        uploaded_count = int(result.stdout.strip())
        print(f"✅ 云服务器上有 {uploaded_count} 个文件")

        if uploaded_count != pdf_count:
            print(f"⚠️  文件数量不匹配: 本地{pdf_count} vs 远程{uploaded_count}")

    # 6. 创建HDFS目录
    print("\n📍 步骤6: 创建HDFS目录...")
    result = run_ssh_command(f"hdfs dfs -mkdir -p {HDFS_TARGET_DIR}", "创建HDFS目录")
    if result:
        if result.returncode == 0 or "File exists" in result.stderr:
            print(f"✅ HDFS目录已就绪: {HDFS_TARGET_DIR}")
        else:
            print(f"⚠️  HDFS目录创建警告: {result.stderr}")

    # 7. 上传到HDFS
    print("\n📍 步骤7: 上传文件到HDFS...")
    print("🚀 开始上传到HDFS (这可能需要几分钟)...")

    result = run_ssh_command(
        f"hdfs dfs -put {REMOTE_TEMP_DIR}/*.pdf {HDFS_TARGET_DIR}/",
        "上传PDF到HDFS",
        timeout=3600
    )

    if result:
        if result.returncode == 0:
            print("✅ 文件上传到HDFS成功!")
        elif "File exists" in result.stderr:
            print("⚠️  部分文件已存在，尝试覆盖上传...")
            # 尝试使用 -f 强制覆盖
            result = run_ssh_command(
                f"hdfs dfs -put -f {REMOTE_TEMP_DIR}/*.pdf {HDFS_TARGET_DIR}/",
                "强制覆盖上传",
                timeout=3600
            )
            if result and result.returncode == 0:
                print("✅ 强制覆盖上传成功!")
            else:
                print(f"❌ 覆盖上传失败: {result.stderr if result else 'Unknown'}")
        else:
            print(f"❌ HDFS上传失败: {result.stderr}")
            return False

    # 8. 验证HDFS上传
    print("\n📍 步骤8: 验证HDFS上传结果...")

    # 统计文件数量
    result = run_ssh_command(
        f"hdfs dfs -ls {HDFS_TARGET_DIR} | wc -l",
        "统计HDFS文件数量"
    )
    if result and result.stdout:
        hdfs_file_count = int(result.stdout.strip()) - 1  # 减去标题行
        print(f"📊 HDFS中的文件数量: {hdfs_file_count}")

        if hdfs_file_count == pdf_count:
            print(f"✅ 文件数量匹配: {hdfs_file_count}/{pdf_count}")
        else:
            print(f"⚠️  文件数量不匹配: HDFS有{hdfs_file_count}个，本地有{pdf_count}个")

    # 统计总大小
    result = run_ssh_command(
        f"hdfs dfs -du -s -h {HDFS_TARGET_DIR}",
        "统计HDFS总大小"
    )
    if result and result.stdout:
        print(f"📦 HDFS总大小: {result.stdout.strip()}")

    # 显示前10个文件
    result = run_ssh_command(
        f"hdfs dfs -ls {HDFS_TARGET_DIR} | head -15",
        "显示HDFS文件列表"
    )
    if result and result.stdout:
        print(f"\n📄 HDFS文件列表（前10个）:")
        print(result.stdout)

    # 显示最后10个文件
    result = run_ssh_command(
        f"hdfs dfs -ls {HDFS_TARGET_DIR} | tail -10",
        "显示HDFS文件列表（最后10个）"
    )
    if result and result.stdout:
        print(f"\n📄 HDFS文件列表（最后10个）:")
        print(result.stdout)

    # 9. 清理临时文件
    print("\n📍 步骤9: 清理临时文件...")
    result = run_ssh_command(f"rm -rf {REMOTE_TEMP_DIR}", "删除临时目录")
    if result and result.returncode == 0:
        print("✅ 临时文件清理成功")

    # 完成
    elapsed_time = (datetime.now() - start_time).total_seconds()
    print("\n" + "=" * 80)
    print("🎉 HDFS上传完成!")
    print("=" * 80)
    print(f"⏱️  总耗时: {elapsed_time/60:.2f} 分钟")
    print(f"📦 HDFS路径: {HDFS_TARGET_DIR}")
    print(f"📊 文件数量: {pdf_count}")
    print(f"📁 文件大小: {total_size_mb:.2f} MB")
    print(f"🖥️  云服务器: {SSH_HOST}")
    print(f"📅 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # 10. 提供访问命令
    print("\n💡 访问HDFS文件的命令:")
    print(f"   ssh {SSH_USER}@{SSH_HOST}")
    print(f"   hdfs dfs -ls {HDFS_TARGET_DIR}")
    print(f"   hdfs dfs -cat {HDFS_TARGET_DIR}/SN-2026-000001.pdf | head -100")
    print(f"   hdfs dfs -get {HDFS_TARGET_DIR}/SN-2026-000001.pdf ./")

    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 程序执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
