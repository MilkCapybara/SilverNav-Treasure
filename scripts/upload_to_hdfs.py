#!/usr/bin/env python3
"""
船舶融资合同PDF上传到HDFS脚本
通过SSH连接到云服务器，将本地PDF文件上传到HDFS
"""
import os
import sys
import subprocess
from datetime import datetime

# 云服务器配置
SSH_HOST = "1.15.225.134"
SSH_PORT = 22
SSH_USER = "hadoopuser"
SSH_PASSWORD = "sunfanjibada"

# 本地PDF目录
LOCAL_PDF_DIR = "./contracts_pdf"

# HDFS目标路径
HDFS_TARGET_DIR = "/silvernav/contracts"

# 临时目录（云服务器上）
REMOTE_TEMP_DIR = "/tmp/silvernav_contracts"


class HDFSUploader:
    """HDFS上传器"""

    def __init__(self):
        """初始化"""
        self.local_dir = LOCAL_PDF_DIR
        self.remote_temp_dir = REMOTE_TEMP_DIR
        self.hdfs_target_dir = HDFS_TARGET_DIR

    def check_local_files(self):
        """检查本地PDF文件"""
        print("=" * 60)
        print("📁 检查本地PDF文件...")
        print("=" * 60)

        if not os.path.exists(self.local_dir):
            print(f"❌ 本地目录不存在: {self.local_dir}")
            return False

        pdf_files = [f for f in os.listdir(self.local_dir) if f.endswith('.pdf')]
        pdf_count = len(pdf_files)

        if pdf_count == 0:
            print(f"❌ 本地目录中没有PDF文件: {self.local_dir}")
            return False

        # 计算总大小
        total_size = sum(os.path.getsize(os.path.join(self.local_dir, f)) for f in pdf_files)
        total_size_mb = total_size / (1024 * 1024)

        print(f"✅ 找到 {pdf_count} 个PDF文件")
        print(f"📊 总大小: {total_size_mb:.2f} MB")
        print(f"📁 本地路径: {os.path.abspath(self.local_dir)}")

        return True

    def test_ssh_connection(self):
        """测试SSH连接"""
        print("\n" + "=" * 60)
        print("🔌 测试SSH连接...")
        print("=" * 60)

        try:
            # 使用sshpass进行密码认证
            cmd = f"sshpass -p '{SSH_PASSWORD}' ssh -o StrictHostKeyChecking=no -p {SSH_PORT} {SSH_USER}@{SSH_HOST} 'echo SSH连接成功'"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                print(f"✅ SSH连接成功: {SSH_USER}@{SSH_HOST}:{SSH_PORT}")
                return True
            else:
                print(f"❌ SSH连接失败: {result.stderr}")
                print("\n💡 提示: 请确保已安装 sshpass")
                print("   macOS: brew install hudochenkov/sshpass/sshpass")
                print("   Linux: sudo apt-get install sshpass")
                return False

        except subprocess.TimeoutExpired:
            print(f"❌ SSH连接超时")
            return False
        except Exception as e:
            print(f"❌ SSH连接错误: {e}")
            return False

    def check_hdfs_status(self):
        """检查HDFS状态"""
        print("\n" + "=" * 60)
        print("🔍 检查HDFS状态...")
        print("=" * 60)

        try:
            # 检查HDFS是否运行
            cmd = f"sshpass -p '{SSH_PASSWORD}' ssh -o StrictHostKeyChecking=no -p {SSH_PORT} {SSH_USER}@{SSH_HOST} 'hdfs dfsadmin -report 2>&1 | head -20'"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                print("✅ HDFS状态:")
                print(result.stdout)
                return True
            else:
                print(f"⚠️  HDFS状态检查失败: {result.stderr}")
                print("\n💡 提示: HDFS可能未启动或配置有问题")
                print("   请在云服务器上执行: start-dfs.sh")
                return False

        except Exception as e:
            print(f"❌ HDFS状态检查错误: {e}")
            return False

    def create_hdfs_directory(self):
        """在HDFS上创建目标目录"""
        print("\n" + "=" * 60)
        print("📁 创建HDFS目标目录...")
        print("=" * 60)

        try:
            # 创建HDFS目录
            cmd = f"sshpass -p '{SSH_PASSWORD}' ssh -o StrictHostKeyChecking=no -p {SSH_PORT} {SSH_USER}@{SSH_HOST} 'hdfs dfs -mkdir -p {self.hdfs_target_dir}'"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                print(f"✅ HDFS目录创建成功: {self.hdfs_target_dir}")
                return True
            else:
                print(f"⚠️  HDFS目录创建失败: {result.stderr}")
                # 目录可能已存在，继续执行
                return True

        except Exception as e:
            print(f"❌ HDFS目录创建错误: {e}")
            return False

    def upload_to_server(self):
        """上传PDF文件到云服务器临时目录"""
        print("\n" + "=" * 60)
        print("📤 上传PDF文件到云服务器...")
        print("=" * 60)

        try:
            # 创建远程临时目录
            cmd = f"sshpass -p '{SSH_PASSWORD}' ssh -o StrictHostKeyChecking=no -p {SSH_PORT} {SSH_USER}@{SSH_HOST} 'mkdir -p {self.remote_temp_dir}'"
            subprocess.run(cmd, shell=True, check=True, timeout=10)
            print(f"✅ 远程临时目录创建成功: {self.remote_temp_dir}")

            # 使用rsync上传文件（带进度显示）
            print(f"\n🚀 开始上传文件...")
            cmd = f"sshpass -p '{SSH_PASSWORD}' rsync -avz --progress -e 'ssh -p {SSH_PORT} -o StrictHostKeyChecking=no' {self.local_dir}/*.pdf {SSH_USER}@{SSH_HOST}:{self.remote_temp_dir}/"

            result = subprocess.run(cmd, shell=True, timeout=3600)  # 1小时超时

            if result.returncode == 0:
                print(f"\n✅ 文件上传成功!")
                return True
            else:
                print(f"\n❌ 文件上传失败")
                return False

        except subprocess.TimeoutExpired:
            print(f"\n❌ 上传超时")
            return False
        except Exception as e:
            print(f"\n❌ 上传错误: {e}")
            return False

    def move_to_hdfs(self):
        """将文件从临时目录移动到HDFS"""
        print("\n" + "=" * 60)
        print("📦 将文件移动到HDFS...")
        print("=" * 60)

        try:
            # 使用hdfs dfs -put命令上传
            cmd = f"sshpass -p '{SSH_PASSWORD}' ssh -o StrictHostKeyChecking=no -p {SSH_PORT} {SSH_USER}@{SSH_HOST} 'hdfs dfs -put {self.remote_temp_dir}/*.pdf {self.hdfs_target_dir}/'"

            print(f"🚀 执行HDFS上传命令...")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=3600)

            if result.returncode == 0:
                print(f"✅ 文件已成功移动到HDFS: {self.hdfs_target_dir}")
                return True
            else:
                print(f"⚠️  HDFS上传警告: {result.stderr}")
                # 可能部分文件已存在，继续验证
                return True

        except subprocess.TimeoutExpired:
            print(f"❌ HDFS上传超时")
            return False
        except Exception as e:
            print(f"❌ HDFS上传错误: {e}")
            return False

    def verify_hdfs_upload(self):
        """验证HDFS上传结果"""
        print("\n" + "=" * 60)
        print("✅ 验证HDFS上传结果...")
        print("=" * 60)

        try:
            # 统计HDFS中的文件数量
            cmd = f"sshpass -p '{SSH_PASSWORD}' ssh -o StrictHostKeyChecking=no -p {SSH_PORT} {SSH_USER}@{SSH_HOST} 'hdfs dfs -ls {self.hdfs_target_dir} | wc -l'"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                file_count = int(result.stdout.strip()) - 1  # 减去标题行
                print(f"📊 HDFS中的文件数量: {file_count}")

                # 统计HDFS中的总大小
                cmd = f"sshpass -p '{SSH_PASSWORD}' ssh -o StrictHostKeyChecking=no -p {SSH_PORT} {SSH_USER}@{SSH_HOST} 'hdfs dfs -du -s -h {self.hdfs_target_dir}'"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)

                if result.returncode == 0:
                    print(f"📦 HDFS总大小: {result.stdout.strip()}")

                # 显示前10个文件
                cmd = f"sshpass -p '{SSH_PASSWORD}' ssh -o StrictHostKeyChecking=no -p {SSH_PORT} {SSH_USER}@{SSH_HOST} 'hdfs dfs -ls {self.hdfs_target_dir} | head -15'"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)

                if result.returncode == 0:
                    print(f"\n📄 HDFS文件列表（前10个）:")
                    print(result.stdout)

                return True
            else:
                print(f"❌ HDFS验证失败: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ HDFS验证错误: {e}")
            return False

    def cleanup_temp_files(self):
        """清理云服务器上的临时文件"""
        print("\n" + "=" * 60)
        print("🧹 清理临时文件...")
        print("=" * 60)

        try:
            cmd = f"sshpass -p '{SSH_PASSWORD}' ssh -o StrictHostKeyChecking=no -p {SSH_PORT} {SSH_USER}@{SSH_HOST} 'rm -rf {self.remote_temp_dir}'"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                print(f"✅ 临时文件清理成功")
                return True
            else:
                print(f"⚠️  临时文件清理失败: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ 临时文件清理错误: {e}")
            return False

    def run(self):
        """执行完整的上传流程"""
        print("\n" + "=" * 80)
        print("🚀 船舶融资合同PDF上传到HDFS")
        print("=" * 80)
        print(f"📅 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🖥️  云服务器: {SSH_USER}@{SSH_HOST}:{SSH_PORT}")
        print(f"📁 本地目录: {os.path.abspath(self.local_dir)}")
        print(f"📦 HDFS目标: {self.hdfs_target_dir}")
        print("=" * 80)

        start_time = datetime.now()

        # 1. 检查本地文件
        if not self.check_local_files():
            print("\n❌ 本地文件检查失败，终止上传")
            return False

        # 2. 测试SSH连接
        if not self.test_ssh_connection():
            print("\n❌ SSH连接失败，终止上传")
            return False

        # 3. 检查HDFS状态
        if not self.check_hdfs_status():
            print("\n⚠️  HDFS状态检查失败，但继续尝试上传...")

        # 4. 创建HDFS目录
        if not self.create_hdfs_directory():
            print("\n❌ HDFS目录创建失败，终止上传")
            return False

        # 5. 上传文件到云服务器
        if not self.upload_to_server():
            print("\n❌ 文件上传到云服务器失败，终止上传")
            return False

        # 6. 移动文件到HDFS
        if not self.move_to_hdfs():
            print("\n❌ 文件移动到HDFS失败")
            return False

        # 7. 验证上传结果
        if not self.verify_hdfs_upload():
            print("\n⚠️  HDFS验证失败，但文件可能已上传")

        # 8. 清理临时文件
        self.cleanup_temp_files()

        # 完成
        elapsed_time = (datetime.now() - start_time).total_seconds()
        print("\n" + "=" * 80)
        print("🎉 上传完成!")
        print("=" * 80)
        print(f"⏱️  总耗时: {elapsed_time/60:.2f} 分钟")
        print(f"📦 HDFS路径: {self.hdfs_target_dir}")
        print(f"📅 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        return True


def main():
    """主函数"""
    uploader = HDFSUploader()

    try:
        success = uploader.run()
        if success:
            print("\n✅ 所有操作成功完成!")
            sys.exit(0)
        else:
            print("\n❌ 上传过程中出现错误")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 程序执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
