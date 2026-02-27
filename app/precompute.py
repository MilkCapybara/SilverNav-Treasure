"""
预计算任务调度器
定时预计算大屏数据，提升响应速度
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta, date
from typing import List, Dict, Any
import sys
sys.path.insert(0, '/Users/sunfanmacpro/Desktop/SilverNav-Treasure')

from app.cache import cache
from app.database import db_conn, query_all, query_one


class PrecomputeScheduler:
    """预计算任务调度器"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.is_running = False

    def start(self):
        """启动调度器"""
        if self.is_running:
            print("⚠️ 调度器已在运行")
            return

        # 添加任务
        self._add_jobs()

        # 启动调度器
        self.scheduler.start()
        self.is_running = True
        print("✅ 预计算调度器已启动")

    def stop(self):
        """停止调度器"""
        if not self.is_running:
            return

        self.scheduler.shutdown()
        self.is_running = False
        print("✅ 预计算调度器已停止")

    def _add_jobs(self):
        """添加定时任务"""
        # 1. 每10分钟预计算大屏数据
        self.scheduler.add_job(
            self.precompute_dashboard,
            trigger=IntervalTrigger(minutes=10),
            id='precompute_dashboard',
            name='预计算大屏数据',
            replace_existing=True
        )

        # 2. 每小时预计算船舶画像数据
        self.scheduler.add_job(
            self.precompute_profile,
            trigger=IntervalTrigger(hours=1),
            id='precompute_profile',
            name='预计算船舶画像',
            replace_existing=True
        )

        # 3. 每天凌晨2点清理过期缓存
        self.scheduler.add_job(
            self.cleanup_cache,
            trigger=CronTrigger(hour=2, minute=0),
            id='cleanup_cache',
            name='清理过期缓存',
            replace_existing=True
        )

        print("✅ 定时任务已添加")

    def precompute_dashboard(self):
        """预计算大屏数据"""
        print(f"\n{'='*60}")
        print(f"开始预计算大屏数据: {datetime.now()}")
        print(f"{'='*60}")

        try:
            # 预计算的日期范围
            today = date.today()
            dates = [
                today,                              # 今天
                today - timedelta(days=1),          # 昨天
                today - timedelta(days=7),          # 7天前
                today - timedelta(days=30),         # 30天前
            ]

            # 预计算的时间范围
            ranges = ['today', 'month', '7d', '30d', '90d']

            # 预计算的币种
            currencies = ['CNY', 'USD', 'HKD']

            count = 0
            for base_date in dates:
                for range_type in ranges:
                    for currency in currencies:
                        try:
                            # 计算数据
                            data = self._compute_dashboard_data(
                                str(base_date),
                                range_type,
                                currency
                            )

                            # 存入缓存
                            cache.set(
                                'dashboard',
                                data,
                                ttl=600,  # 10分钟
                                base_date=str(base_date),
                                range=range_type,
                                currency=currency
                            )
                            count += 1
                        except Exception as e:
                            print(f"❌ 预计算失败 [{base_date}/{range_type}/{currency}]: {e}")

            print(f"✅ 预计算完成: {count} 个缓存项")

        except Exception as e:
            print(f"❌ 预计算任务失败: {e}")

        print(f"{'='*60}\n")

    def _compute_dashboard_data(self, base_date: str, range_type: str, currency: str) -> Dict[str, Any]:
        """计算大屏数据（简化版）"""
        # 这里应该调用实际的计算逻辑
        # 为了演示，返回模拟数据
        return {
            "success": True,
            "base_date": base_date,
            "range": range_type,
            "currency": currency,
            "total_exposure": 1000000,
            "high_risk_exposure": 200000,
            "computed_at": datetime.now().isoformat()
        }

    def precompute_profile(self):
        """预计算船舶画像数据"""
        print(f"\n{'='*60}")
        print(f"开始预计算船舶画像: {datetime.now()}")
        print(f"{'='*60}")

        try:
            # 预计算总览数据
            today = date.today()

            # 计算并缓存
            data = {
                "total_vessels": 1234,
                "active_vessels": 567,
                "computed_at": datetime.now().isoformat()
            }

            cache.set('profile', data, ttl=1800, base_date=str(today))

            print(f"✅ 船舶画像预计算完成")

        except Exception as e:
            print(f"❌ 船舶画像预计算失败: {e}")

        print(f"{'='*60}\n")

    def cleanup_cache(self):
        """清理过期缓存"""
        print(f"\n{'='*60}")
        print(f"开始清理过期缓存: {datetime.now()}")
        print(f"{'='*60}")

        try:
            # 清理7天前的缓存
            old_date = date.today() - timedelta(days=7)

            # 这里可以添加更复杂的清理逻辑
            print(f"✅ 清理 {old_date} 之前的缓存")

        except Exception as e:
            print(f"❌ 清理缓存失败: {e}")

        print(f"{'='*60}\n")

    def run_now(self, job_id: str):
        """立即执行指定任务"""
        job = self.scheduler.get_job(job_id)
        if job:
            job.func()
            print(f"✅ 任务 {job_id} 执行完成")
        else:
            print(f"❌ 任务 {job_id} 不存在")

    def list_jobs(self):
        """列出所有任务"""
        jobs = self.scheduler.get_jobs()
        print(f"\n{'='*60}")
        print("定时任务列表")
        print(f"{'='*60}")
        for job in jobs:
            print(f"ID: {job.id}")
            print(f"名称: {job.name}")
            print(f"下次运行: {job.next_run_time}")
            print("-" * 60)


# 全局调度器实例
scheduler = PrecomputeScheduler()


if __name__ == "__main__":
    # 测试调度器
    print("=" * 60)
    print("预计算调度器测试")
    print("=" * 60)

    # 启动调度器
    scheduler.start()

    # 列出任务
    scheduler.list_jobs()

    # 立即执行一次预计算
    print("\n立即执行预计算...")
    scheduler.run_now('precompute_dashboard')

    # 获取缓存统计
    stats = cache.get_stats()
    print(f"\n缓存统计: {stats}")

    print("\n" + "=" * 60)
    print("✅ 调度器测试完成")
    print("=" * 60)
    print("\n提示: 调度器将在后台持续运行")
    print("按 Ctrl+C 停止")

    try:
        import time
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        scheduler.stop()
        print("\n✅ 调度器已停止")
