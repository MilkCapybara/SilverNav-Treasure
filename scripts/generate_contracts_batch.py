#!/usr/bin/env python3
"""
船舶融资合同PDF批量生成脚本（自动模式）
从PostgreSQL的vessels和companies表读取数据，生成20000份PDF合同文件
"""
import os
import sys
from datetime import datetime, timedelta
import random
from decimal import Decimal

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import psycopg2
from psycopg2.extras import RealDictCursor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 导入配置
from app.config import settings


class ContractGenerator:
    """合同生成器"""

    def __init__(self, output_dir="./contracts_pdf"):
        """初始化"""
        self.output_dir = output_dir
        self.conn = None
        self.vessels = []
        self.companies = []

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        # 注册中文字体
        self._register_fonts()

    def _register_fonts(self):
        """注册中文字体"""
        try:
            font_paths = [
                '/System/Library/Fonts/STHeiti Light.ttc',
                '/System/Library/Fonts/PingFang.ttc',
                '/Library/Fonts/Arial Unicode.ttf',
            ]

            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('Chinese', font_path))
                        print(f"✅ 成功注册中文字体: {font_path}")
                        return
                    except Exception as e:
                        continue

            print("⚠️  未找到中文字体，将使用默认字体")
        except Exception as e:
            print(f"❌ 字体注册错误: {e}")

    def connect_db(self):
        """连接数据库"""
        try:
            self.conn = psycopg2.connect(
                host=settings.db_host,
                port=settings.db_port,
                database=settings.db_name,
                user=settings.admin_user,
                password=settings.admin_password,
                options=f'-c search_path={settings.db_schema}'
            )
            print(f"✅ 成功连接到数据库: {settings.db_host}:{settings.db_port}/{settings.db_name}")
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            raise

    def load_data(self):
        """从数据库加载船舶和企业数据"""
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)

            # 加载船舶数据
            cursor.execute("""
                SELECT v.id, v.imo_number, v.vessel_name, v.vessel_type,
                       v.build_year, v.flag_country, v.owner_company_id,
                       v.asset_risk_score, v.risk_level
                FROM vessels v
                WHERE v.is_active = TRUE
                ORDER BY v.id
            """)
            self.vessels = cursor.fetchall()
            print(f"✅ 加载了 {len(self.vessels)} 条船舶数据")

            # 加载企业数据
            cursor.execute("""
                SELECT c.id, c.company_name, c.registration_country,
                       c.company_type, c.credit_score, c.risk_level
                FROM companies c
                WHERE c.is_active = TRUE
                ORDER BY c.id
            """)
            self.companies = cursor.fetchall()
            print(f"✅ 加载了 {len(self.companies)} 条企业数据")

            cursor.close()

            if not self.vessels or not self.companies:
                raise ValueError("数据库中没有足够的船舶或企业数据")

        except Exception as e:
            print(f"❌ 数据加载失败: {e}")
            raise

    def generate_contract_data(self, index):
        """生成单个合同数据"""
        vessel = random.choice(self.vessels)
        company = random.choice(self.companies)

        contract_no = f"SN-{datetime.now().year}-{index:06d}"
        start_date = datetime.now() - timedelta(days=random.randint(0, 365))
        maturity_date = start_date + timedelta(days=random.randint(365, 3650))
        principal_amount = Decimal(random.randint(1000000, 50000000))
        interest_rate = Decimal(random.uniform(3.0, 8.0))
        currency = random.choice(['CNY', 'USD', 'EUR', 'HKD'])
        asset_type = random.choice(['loan', 'mortgage', 'leasing', 'guarantee'])
        risk_level = random.choice(['low', 'medium', 'high'])

        return {
            'contract_no': contract_no,
            'vessel': vessel,
            'company': company,
            'asset_type': asset_type,
            'principal_amount': principal_amount,
            'currency': currency,
            'interest_rate': interest_rate,
            'start_date': start_date,
            'maturity_date': maturity_date,
            'risk_level': risk_level,
            'generated_date': datetime.now()
        }

    def create_pdf(self, contract_data, filename):
        """创建PDF合同文件"""
        try:
            doc = SimpleDocTemplate(
                filename,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )

            story = []
            styles = getSampleStyleSheet()

            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor('#0A1F3F'),
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName='Chinese' if 'Chinese' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'
            )

            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#123A63'),
                spaceAfter=12,
                fontName='Chinese' if 'Chinese' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'
            )

            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=10,
                leading=14,
                alignment=TA_JUSTIFY,
                fontName='Chinese' if 'Chinese' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
            )

            # 标题
            story.append(Paragraph("SHIPPING FINANCE CONTRACT", title_style))
            story.append(Paragraph("船舶融资合同", title_style))
            story.append(Spacer(1, 0.5*cm))

            # 合同编号
            story.append(Paragraph(f"<b>Contract No.:</b> {contract_data['contract_no']}", normal_style))
            story.append(Spacer(1, 0.3*cm))

            # 合同基本信息表格
            basic_info = [
                ['Contract Type', self._get_asset_type_name(contract_data['asset_type'])],
                ['Contract Date', contract_data['start_date'].strftime('%Y-%m-%d')],
                ['Maturity Date', contract_data['maturity_date'].strftime('%Y-%m-%d')],
                ['Principal Amount', f"{contract_data['currency']} {contract_data['principal_amount']:,.2f}"],
                ['Interest Rate', f"{contract_data['interest_rate']:.2f}%"],
                ['Risk Level', contract_data['risk_level'].upper()],
            ]

            basic_table = Table(basic_info, colWidths=[6*cm, 10*cm])
            basic_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8F4F8')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))

            story.append(basic_table)
            story.append(Spacer(1, 0.5*cm))

            # 甲方信息（企业）
            story.append(Paragraph("PARTY A (Borrower / 甲方-借款方)", heading_style))
            company_info = [
                ['Company Name', contract_data['company']['company_name']],
                ['Company Type', contract_data['company']['company_type'] or 'N/A'],
                ['Registration Country', contract_data['company']['registration_country'] or 'N/A'],
                ['Credit Score', f"{contract_data['company']['credit_score']:.2f}" if contract_data['company']['credit_score'] else 'N/A'],
                ['Risk Level', contract_data['company']['risk_level'] or 'N/A'],
            ]

            company_table = Table(company_info, colWidths=[6*cm, 10*cm])
            company_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#FFF8E1')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))

            story.append(company_table)
            story.append(Spacer(1, 0.5*cm))

            # 乙方信息（银行/金融机构）
            story.append(Paragraph("PARTY B (Lender / 乙方-贷款方)", heading_style))
            lender_info = [
                ['Institution Name', 'SilverNav Financial Services Ltd.'],
                ['Registration No.', 'SNFS-2020-001'],
                ['Address', 'Shanghai Free Trade Zone, China'],
                ['Contact', '+86 21 6888 8888'],
            ]

            lender_table = Table(lender_info, colWidths=[6*cm, 10*cm])
            lender_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8F5E9')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))

            story.append(lender_table)
            story.append(Spacer(1, 0.5*cm))

            # 抵押物信息（船舶）
            story.append(Paragraph("COLLATERAL (Vessel / 抵押物-船舶)", heading_style))
            vessel_info = [
                ['IMO Number', contract_data['vessel']['imo_number'] or 'N/A'],
                ['Vessel Name', contract_data['vessel']['vessel_name'] or 'N/A'],
                ['Vessel Type', contract_data['vessel']['vessel_type'] or 'N/A'],
                ['Build Year', str(contract_data['vessel']['build_year']) if contract_data['vessel']['build_year'] else 'N/A'],
                ['Flag Country', contract_data['vessel']['flag_country'] or 'N/A'],
                ['Asset Risk Score', f"{contract_data['vessel']['asset_risk_score']:.2f}" if contract_data['vessel']['asset_risk_score'] else 'N/A'],
            ]

            vessel_table = Table(vessel_info, colWidths=[6*cm, 10*cm])
            vessel_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E3F2FD')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))

            story.append(vessel_table)
            story.append(Spacer(1, 0.5*cm))

            # 合同条款
            story.append(Paragraph("TERMS AND CONDITIONS (合同条款)", heading_style))

            terms = [
                "1. The Borrower agrees to repay the principal amount plus interest according to the agreed schedule.",
                "2. The Vessel shall serve as collateral for this financing agreement.",
                "3. The Borrower shall maintain adequate insurance coverage for the Vessel.",
                "4. In case of default, the Lender has the right to seize and auction the collateral.",
                "5. This contract is governed by the laws of the People's Republic of China.",
                "6. Any disputes shall be resolved through arbitration in Shanghai.",
            ]

            for term in terms:
                story.append(Paragraph(term, normal_style))
                story.append(Spacer(1, 0.2*cm))

            story.append(Spacer(1, 0.5*cm))

            # 签名区域
            signature_data = [
                ['PARTY A (Borrower)', 'PARTY B (Lender)'],
                ['', ''],
                ['Signature: _______________', 'Signature: _______________'],
                ['Date: _______________', 'Date: _______________'],
            ]

            signature_table = Table(signature_data, colWidths=[8*cm, 8*cm])
            signature_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('LINEABOVE', (0, 2), (-1, 2), 1, colors.grey),
            ]))

            story.append(signature_table)
            story.append(Spacer(1, 0.5*cm))

            # 页脚
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_CENTER,
            )
            story.append(Paragraph(
                f"Generated by SilverNav Treasure System | {contract_data['generated_date'].strftime('%Y-%m-%d %H:%M:%S')}",
                footer_style
            ))

            doc.build(story)

        except Exception as e:
            raise Exception(f"PDF生成失败: {e}")

    def _get_asset_type_name(self, asset_type):
        """获取资产类型名称"""
        type_map = {
            'loan': 'Vessel Loan (船舶贷款)',
            'mortgage': 'Vessel Mortgage (船舶抵押)',
            'leasing': 'Vessel Leasing (船舶租赁)',
            'guarantee': 'Vessel Guarantee (船舶担保)',
        }
        return type_map.get(asset_type, asset_type)

    def generate_contracts(self, count=20000):
        """批量生成合同PDF"""
        print(f"\n🚀 开始生成 {count} 份合同PDF...")
        print(f"📁 输出目录: {os.path.abspath(self.output_dir)}")

        success_count = 0
        failed_count = 0
        start_time = datetime.now()

        for i in range(1, count + 1):
            try:
                contract_data = self.generate_contract_data(i)
                filename = os.path.join(
                    self.output_dir,
                    f"{contract_data['contract_no']}.pdf"
                )
                self.create_pdf(contract_data, filename)
                success_count += 1

                # 进度显示
                if i % 500 == 0:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    speed = i / elapsed if elapsed > 0 else 0
                    remaining = (count - i) / speed if speed > 0 else 0
                    print(f"✅ 进度: {i}/{count} ({i*100/count:.1f}%) | "
                          f"速度: {speed:.1f} 份/秒 | "
                          f"预计剩余: {remaining/60:.1f} 分钟")

            except Exception as e:
                failed_count += 1
                if failed_count <= 10:  # 只显示前10个错误
                    print(f"❌ 合同 #{i} 生成失败: {e}")
                continue

        elapsed_time = (datetime.now() - start_time).total_seconds()
        print(f"\n🎉 合同生成完成!")
        print(f"✅ 成功: {success_count} 份")
        print(f"❌ 失败: {failed_count} 份")
        print(f"⏱️  总耗时: {elapsed_time/60:.2f} 分钟")
        print(f"📊 平均速度: {success_count/elapsed_time:.2f} 份/秒")
        print(f"📁 输出目录: {os.path.abspath(self.output_dir)}")

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            print("✅ 数据库连接已关闭")


def main():
    """主函数"""
    print("=" * 60)
    print("船舶融资合同PDF批量生成工具")
    print("SilverNav Treasure - Contract Generator")
    print("=" * 60)

    generator = ContractGenerator(output_dir="./contracts_pdf")

    try:
        generator.connect_db()
        generator.load_data()
        generator.generate_contracts(count=20000)

    except Exception as e:
        print(f"\n❌ 程序执行失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        generator.close()


if __name__ == "__main__":
    main()
