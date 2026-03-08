#!/usr/bin/env python3
"""
修复HDFS环境并上传PDF文件
"""
import subprocess
import sys

SSH_HOST = "1.15.225.134"
SSH_PORT = 22
SSH_USER = "hadoopuser"
SSH_PASSWORD = "sunfanjibada"
REMOTE_TEMP_DIR = "/tmp/silvernav_contracts"
HDFS_TARGET_DIR = "/silvernav/contracts"


def run_ssh_command(command, description=""):
    """执行SSH命令"""
    if description:
        print(f"\n🔧 {description}")

    full_cmd = f"sshpass -p '{SSH_PASSWORD}' ssh -o StrictHostKeyChecking=no -p {SSH_PORT} {SSH_USER}@{SSH_HOST} '{command}'"

    try:
        result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=300)
        return result
    except Exception as e:
        print(f"❌ 命令执行失败: {e}")
        return None


def main():
    print("=" * 80)
    print("🔧 HDFS环境修复与文件上传")
    print("=" * 80)

    # 1. 查找Hadoop安装路径
    print("\n📍 步骤1: 查找Hadoop安装路径...")
    result = run_ssh_command("find /usr/local /opt /home -name 'hadoop' -type d 2>/dev/null | head -5")
    if result and result.stdout:
        print("找到的Hadoop路径:")
        print(result.stdout)

    # 2. 检查常见的Hadoop路径
    print("\n📍 步骤2: 检查常见Hadoop路径...")
    common_paths = [
        "/usr/local/hadoop",
        "/opt/hadoop",
        "/home/hadoopuser/hadoop",
        "~/hadoop",
        "/usr/local/hadoop-3.3.6",
    ]

    hadoop_home = None
    for path in common_paths:
        result = run_ssh_command(f"test -d {path} && echo 'EXISTS' || echo 'NOT_FOUND'")
        if result and "EXISTS" in result.stdout:
            print(f"✅ 找到Hadoop: {path}")
            hadoop_home = path
            break
        else:
            print(f"❌ 不存在: {path}")

    if not hadoop_home:
        print("\n⚠️  未找到Hadoop安装目录，尝试使用默认路径...")
        hadoop_home = "/usr/local/hadoop"

    # 3. 检查HDFS命令
    print(f"\n📍 步骤3: 测试HDFS命令 (HADOOP_HOME={hadoop_home})...")
    result = run_ssh_command(f"export HADOOP_HOME={hadoop_home} && export PATH=$HADOOP_HOME/bin:$PATH && hdfs version")
    if result and result.returncode == 0:
        print("✅ HDFS命令可用:")
        print(result.stdout[:500])
    else:
        print("❌ HDFS命令仍然不可用")
        print(f"错误: {result.stderr if result else 'Unknown'}")

        # 尝试直接使用完整路径
        print("\n🔄 尝试使用完整路径...")
        result = run_ssh_command(f"{hadoop_home}/bin/hdfs version")
        if result and result.returncode == 0:
            print("✅ 使用完整路径成功!")
            print(result.stdout[:500])
        else:
            print("❌ 完整路径也失败")
            print("\n💡 建议: 请在云服务器上手动执行以下命令:")
            print(f"   ssh {SSH_USER}@{SSH_HOST}")
            print(f"   which hdfs")
            print(f"   echo $HADOOP_HOME")
            return False

    # 4. 检查临时文件
    print("\n📍 步骤4: 检查临时目录中的PDF文件...")
    result = run_ssh_command(f"ls {REMOTE_TEMP_DIR} | wc -l")
    if result and result.stdout:
        file_count = int(result.stdout.strip())
        print(f"✅ 临时目录中有 {file_count} 个文件")

        if file_count == 0:
            print("❌ 临时目录为空，需要重新上传")
            return False

    # 5. 创建HDFS目录
    print("\n📍 步骤5: 创建HDFS目录...")
    result = run_ssh_command(
        f"export HADOOP_HOME={hadoop_home} && export PATH=$HADOOP_HOME/bin:$PATH && hdfs dfs -mkdir -p {HDFS_TARGET_DIR}",
        "创建HDFS目录"
    )
    if result:
        if result.returncode == 0 or "File exists" in result.stderr:
            print(f"✅ HDFS目录已就绪: {HDFS_TARGET_DIR}")
        else:
            print(f"⚠️  创建目录警告: {result.stderr}")

    # 6. 上传文件到HDFS
    print("\n📍 步骤6: 上传文件到HDFS...")
    print("🚀 开始上传 (这可能需要几分钟)...")

    result = run_ssh_command(
        f"export HADOOP_HOME={hadoop_home} && export PATH=$HADOOP_HOME/bin:$PATH && hdfs dfs -put {REMOTE_TEMP_DIR}/*.pdf {HDFS_TARGET_DIR}/",
        "上传PDF到HDFS"
    )

    if result:
        if result.returncode == 0:
            print("✅ 文件上传到HDFS成功!")
        elif "File exists" in result.stderr:
            print("⚠️  部分文件已存在，跳过...")
        else:
            print(f"❌ 上传失败: {result.stderr}")
            return False

    # 7. 验证HDFS上传
    print("\n📍 步骤7: 验证HDFS上传结果...")

    # 统计文件数量
    result = run_ssh_command(
        f"export HADOOP_HOME={hadoop_home} && export PATH=$HADOOP_HOME/bin:$PATH && hdfs dfs -ls {HDFS_TARGET_DIR} | wc -l",
        "统计HDFS文件数量"
    )
    if result and result.stdout:
        file_count = int(result.stdout.strip()) - 1  # 减去标题行
        print(f"📊 HDFS中的文件数量: {file_count}")

    # 统计总大小
    result = run_ssh_command(
        f"export HADOOP_HOME={hadoop_home} && export PATH=$HADOOP_HOME/bin:$PATH && hdfs dfs -du -s -h {HDFS_TARGET_DIR}",
        "统计HDFS总大小"
    )
    if result and result.stdout:
        print(f"📦 HDFS总大小: {result.stdout.strip()}")

    # 显示前10个文件
    result = run_ssh_command(
        f"export HADOOP_HOME={hadoop_home} && export PATH=$HADOOP_HOME/bin:$PATH && hdfs dfs -ls {HDFS_TARGET_DIR} | head -15",
        "显示HDFS文件列表"
    )
    if result and result.stdout:
        print(f"\n📄 HDFS文件列表（前10个）:")
        print(result.stdout)

    # 8. 清理临时文件
    print("\n📍 步骤8: 清理临时文件...")
    result = run_ssh_command(f"rm -rf {REMOTE_TEMP_DIR}", "删除临时目录")
    if result and result.returncode == 0:
        print("✅ 临时文件清理成功")

    print("\n" + "=" * 80)
    print("🎉 HDFS上传完成!")
    print("=" * 80)
    print(f"📦 HDFS路径: {HDFS_TARGET_DIR}")
    print(f"🖥️  云服务器: {SSH_HOST}")
    print("=" * 80)

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
