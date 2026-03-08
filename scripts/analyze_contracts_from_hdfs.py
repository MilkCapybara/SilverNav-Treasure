#!/usr/bin/env python3
"""
从HDFS读取船舶融资合同PDF，进行风险分析，并将结果写入MongoDB
"""
import os
import sys
import re
import subprocess
from datetime import datetime
from typing import Dict, List, Optional
import tempfile

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from pymongo import MongoClient, UpdateOne
    from pymongo.errors import BulkWriteError
except ImportError:
    print("❌ 请安装pymongo: pip install pymongo")
    sys.exit(1)

try:
    import PyPDF2
except ImportError:
    print("❌ 请安装PyPDF2: pip install PyPDF2")
    sys.exit(1)

from app.config import settings


class ContractAnalyzer:
    """合同分析器"""

    def __init__(self, pdf_dir="./contracts_pdf"):
        """初始化"""
        self.mongo_client = None
        self.db = None
        self.collection = None

        # 本地PDF目录
        self.pdf_dir = pdf_dir

        # 风险关键词
        self.risk_keywords = {
            'high': ['违约', '逾期', '罚息', '诉讼', '仲裁', '抵押物处置', '强制执行'],
            'medium': ['担保', '保证金', '质押', '抵押', '风险', '损失', '赔偿'],
            'low': ['利率调整', '提前还款', '展期', '续期']
        }

    def connect_mongo(self, use_local=False):
        """连接MongoDB"""
        try:
            if use_local:
                # 使用本地MongoDB
                mongo_uri = "mongodb://localhost:27017/"
                self.mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
                self.db = self.mongo_client['silvernav']
                print(f"✅ 成功连接到本地MongoDB: localhost:27017/silvernav")
            else:
                # 使用云服务器MongoDB
                mongo_uri = f"mongodb://{settings.mongo_user}:{settings.mongo_password}@{settings.mongo_host}:{settings.mongo_port}/{settings.mongo_db}?authSource={settings.mongo_auth_source}"
                self.mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10000)
                self.db = self.mongo_client[settings.mongo_db]
                print(f"✅ 成功连接到MongoDB: {settings.mongo_host}:{settings.mongo_port}/{settings.mongo_db}")

            self.collection = self.db['contracts']

            # 创建索引
            self.collection.create_index('contract_id', unique=True)
            self.collection.create_index('vessel_imo')
            self.collection.create_index('risk_score')
            self.collection.create_index('analyzed_at')

        except Exception as e:
            print(f"❌ MongoDB连接失败: {e}")
            raise

    def get_pdf_path(self, contract_id: str) -> Optional[str]:
        """获取本地PDF文件路径"""
        pdf_path = os.path.join(self.pdf_dir, f"{contract_id}.pdf")
        if os.path.exists(pdf_path):
            return pdf_path
        return None

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """从PDF提取文本"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                return text
        except Exception as e:
            print(f"❌ PDF文本提取失败: {e}")
            return ""

    def analyze_risk(self, text: str) -> Dict:
        """分析合同风险"""
        risk_analysis = {
            'high_risk_count': 0,
            'medium_risk_count': 0,
            'low_risk_count': 0,
            'high_risk_keywords': [],
            'medium_risk_keywords': [],
            'low_risk_keywords': [],
            'risk_score': 0,
            'risk_level': 'LOW'
        }

        # 统计风险关键词
        for keyword in self.risk_keywords['high']:
            count = text.count(keyword)
            if count > 0:
                risk_analysis['high_risk_count'] += count
                risk_analysis['high_risk_keywords'].append({'keyword': keyword, 'count': count})

        for keyword in self.risk_keywords['medium']:
            count = text.count(keyword)
            if count > 0:
                risk_analysis['medium_risk_count'] += count
                risk_analysis['medium_risk_keywords'].append({'keyword': keyword, 'count': count})

        for keyword in self.risk_keywords['low']:
            count = text.count(keyword)
            if count > 0:
                risk_analysis['low_risk_count'] += count
                risk_analysis['low_risk_keywords'].append({'keyword': keyword, 'count': count})

        # 计算风险评分 (0-100)
        risk_score = (
            risk_analysis['high_risk_count'] * 10 +
            risk_analysis['medium_risk_count'] * 5 +
            risk_analysis['low_risk_count'] * 2
        )
        risk_score = min(risk_score, 100)  # 最高100分
        risk_analysis['risk_score'] = risk_score

        # 确定风险等级
        if risk_score >= 70:
            risk_analysis['risk_level'] = 'HIGH'
        elif risk_score >= 40:
            risk_analysis['risk_level'] = 'MEDIUM'
        else:
            risk_analysis['risk_level'] = 'LOW'

        return risk_analysis

    def extract_contract_info(self, text: str, contract_id: str) -> Dict:
        """提取合同信息"""
        info = {
            'contract_id': contract_id,
            'contract_number': contract_id,
            'contract_type': None,
            'contract_date': None,
            'maturity_date': None,
            'vessel_imo': None,
            'vessel_name': None,
            'vessel_type': None,
            'build_year': None,
            'flag_country': None,
            'company_name': None,
            'company_type': None,
            'registration_country': None,
            'credit_score': None,
            'institution_name': None,
            'principal_amount': None,
            'interest_rate': None,
            'risk_level': None,
            'asset_risk_score': None,
            'text_length': len(text)
        }

        # 提取Contract Type
        contract_type_match = re.search(r'Contract Type[:\s]+([^\n]+)', text, re.IGNORECASE)
        if contract_type_match:
            info['contract_type'] = contract_type_match.group(1).strip()

        # 提取Contract Date
        contract_date_match = re.search(r'Contract Date[:\s]+(\d{4}-\d{2}-\d{2})', text, re.IGNORECASE)
        if contract_date_match:
            info['contract_date'] = contract_date_match.group(1)

        # 提取Maturity Date
        maturity_date_match = re.search(r'Maturity Date[:\s]+(\d{4}-\d{2}-\d{2})', text, re.IGNORECASE)
        if maturity_date_match:
            info['maturity_date'] = maturity_date_match.group(1)

        # 提取IMO Number
        imo_match = re.search(r'IMO Number[:\s]+(\d{7})', text, re.IGNORECASE)
        if imo_match:
            info['vessel_imo'] = imo_match.group(1)

        # 提取Vessel Name
        vessel_match = re.search(r'Vessel Name[:\s]+([^\n]+)', text, re.IGNORECASE)
        if vessel_match:
            info['vessel_name'] = vessel_match.group(1).strip()

        # 提取Vessel Type
        vessel_type_match = re.search(r'Vessel Type[:\s]+([^\n]+)', text, re.IGNORECASE)
        if vessel_type_match:
            info['vessel_type'] = vessel_type_match.group(1).strip()

        # 提取Build Year
        build_year_match = re.search(r'Build Year[:\s]+(\d{4})', text, re.IGNORECASE)
        if build_year_match:
            info['build_year'] = int(build_year_match.group(1))

        # 提取Flag Country
        flag_match = re.search(r'Flag Country[:\s]+([^\n]+)', text, re.IGNORECASE)
        if flag_match:
            info['flag_country'] = flag_match.group(1).strip()

        # 提取Company Name (Borrower)
        company_match = re.search(r'Company Name[:\s]+([^\n]+)', text, re.IGNORECASE)
        if company_match:
            info['company_name'] = company_match.group(1).strip()

        # 提取Company Type
        company_type_match = re.search(r'Company Type[:\s]+([^\n]+)', text, re.IGNORECASE)
        if company_type_match:
            info['company_type'] = company_type_match.group(1).strip()

        # 提取Registration Country
        reg_country_match = re.search(r'Registration Country[:\s]+([^\n]+)', text, re.IGNORECASE)
        if reg_country_match:
            info['registration_country'] = reg_country_match.group(1).strip()

        # 提取Credit Score
        credit_score_match = re.search(r'Credit Score[:\s]+([\d.]+)', text, re.IGNORECASE)
        if credit_score_match:
            info['credit_score'] = float(credit_score_match.group(1))

        # 提取Institution Name (Lender)
        institution_match = re.search(r'Institution Name[:\s]+([^\n]+)', text, re.IGNORECASE)
        if institution_match:
            info['institution_name'] = institution_match.group(1).strip()

        # 提取Principal Amount (支持多种格式)
        # 格式1: Principal Amount CNY 3,327,382.00
        # 格式2: Principal Amount: $5,000,000
        amount_match = re.search(r'Principal Amount[:\s]+(?:CNY|USD|EUR|GBP|HKD)?\s*([\d,]+(?:\.\d+)?)', text, re.IGNORECASE)
        if amount_match:
            amount_str = amount_match.group(1).replace(',', '')
            info['principal_amount'] = float(amount_str)

        # 提取Interest Rate
        rate_match = re.search(r'Interest Rate[:\s]+([\d.]+)%', text, re.IGNORECASE)
        if rate_match:
            info['interest_rate'] = float(rate_match.group(1))

        # 提取Risk Level
        risk_level_match = re.search(r'Risk Level[:\s]+([A-Z]+)', text, re.IGNORECASE)
        if risk_level_match:
            info['risk_level'] = risk_level_match.group(1).upper()

        # 提取Asset Risk Score
        asset_risk_match = re.search(r'Asset Risk Score[:\s]+([\d.]+)', text, re.IGNORECASE)
        if asset_risk_match:
            info['asset_risk_score'] = float(asset_risk_match.group(1))

        return info

    def analyze_contract(self, contract_id: str) -> Optional[Dict]:
        """分析单个合同"""
        try:
            # 获取本地PDF路径
            pdf_path = self.get_pdf_path(contract_id)
            if not pdf_path:
                return None

            # 提取文本
            text = self.extract_text_from_pdf(pdf_path)
            if not text:
                return None

            # 提取合同信息
            contract_info = self.extract_contract_info(text, contract_id)

            # 分析风险
            risk_analysis = self.analyze_risk(text)

            # 合并结果
            result = {
                **contract_info,
                **risk_analysis,
                'analyzed_at': datetime.utcnow(),
                'text_preview': text[:500] if len(text) > 500 else text
            }

            return result

        except Exception as e:
            print(f"❌ 分析合同失败 {contract_id}: {e}")
            return None

    def save_to_mongo(self, contracts: List[Dict]):
        """批量保存到MongoDB"""
        if not contracts:
            return

        try:
            operations = [
                UpdateOne(
                    {'contract_id': contract['contract_id']},
                    {'$set': contract},
                    upsert=True
                )
                for contract in contracts
            ]

            result = self.collection.bulk_write(operations, ordered=False)
            print(f"✅ 保存到MongoDB: {result.upserted_count} 新增, {result.modified_count} 更新")

        except BulkWriteError as e:
            print(f"⚠️  部分写入失败: {e.details}")
        except Exception as e:
            print(f"❌ MongoDB写入失败: {e}")

    def analyze_all_contracts(self, start_id: int = 1, end_id: int = 20000, batch_size: int = 100):
        """分析所有合同"""
        print(f"\n开始分析合同 {start_id} 到 {end_id}...")
        print(f"批次大小: {batch_size}")

        total = end_id - start_id + 1
        processed = 0
        success = 0
        failed = 0

        batch = []

        for i in range(start_id, end_id + 1):
            contract_id = f"SN-2026-{i:06d}"

            result = self.analyze_contract(contract_id)

            if result:
                batch.append(result)
                success += 1
            else:
                failed += 1

            processed += 1

            # 批量保存
            if len(batch) >= batch_size:
                self.save_to_mongo(batch)
                batch = []

            # 进度显示
            if processed % 100 == 0:
                progress = (processed / total) * 100
                print(f"进度: {processed}/{total} ({progress:.1f}%) - 成功: {success}, 失败: {failed}")

        # 保存剩余的
        if batch:
            self.save_to_mongo(batch)

        print(f"\n✅ 分析完成!")
        print(f"总计: {total}")
        print(f"成功: {success}")
        print(f"失败: {failed}")

    def get_statistics(self):
        """获取统计信息"""
        try:
            total = self.collection.count_documents({})
            high_risk = self.collection.count_documents({'risk_level': 'HIGH'})
            medium_risk = self.collection.count_documents({'risk_level': 'MEDIUM'})
            low_risk = self.collection.count_documents({'risk_level': 'LOW'})

            avg_score = list(self.collection.aggregate([
                {'$group': {'_id': None, 'avg_score': {'$avg': '$risk_score'}}}
            ]))

            print(f"\n📊 统计信息:")
            print(f"总合同数: {total}")
            print(f"高风险: {high_risk} ({high_risk/total*100:.1f}%)")
            print(f"中风险: {medium_risk} ({medium_risk/total*100:.1f}%)")
            print(f"低风险: {low_risk} ({low_risk/total*100:.1f}%)")
            if avg_score:
                print(f"平均风险评分: {avg_score[0]['avg_score']:.2f}")

        except Exception as e:
            print(f"❌ 获取统计信息失败: {e}")

    def close(self):
        """关闭连接"""
        if self.mongo_client:
            self.mongo_client.close()
            print("✅ MongoDB连接已关闭")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='分析本地合同PDF文件')
    parser.add_argument('--pdf-dir', type=str, default='./contracts_pdf', help='PDF文件目录')
    parser.add_argument('--start', type=int, default=1, help='起始合同编号')
    parser.add_argument('--end', type=int, default=20000, help='结束合同编号')
    parser.add_argument('--batch', type=int, default=100, help='批次大小')
    parser.add_argument('--stats-only', action='store_true', help='仅显示统计信息')
    parser.add_argument('--local-mongo', action='store_true', help='使用本地MongoDB')

    args = parser.parse_args()

    analyzer = ContractAnalyzer(pdf_dir=args.pdf_dir)

    try:
        analyzer.connect_mongo(use_local=args.local_mongo)

        if args.stats_only:
            analyzer.get_statistics()
        else:
            analyzer.analyze_all_contracts(args.start, args.end, args.batch)
            analyzer.get_statistics()

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        analyzer.close()


if __name__ == "__main__":
    main()
