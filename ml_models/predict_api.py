"""
机器学习预测API
集成到FastAPI中，提供实时预测接口
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from pathlib import Path

from ml_models.risk_predictor import RiskPredictor
from ml_models.data_loader import DataLoader


# 创建路由
router = APIRouter(prefix="/api/ml", tags=["Machine Learning"])

# 全局模型实例
_predictor = None
_loader = None


def get_predictor():
    """获取预测器实例"""
    global _predictor
    if _predictor is None:
        # 优先使用真实特征模型
        model_path = Path('ml_models/saved_models/random_forest_real_features.pkl')
        if not model_path.exists():
            # 如果不存在，尝试使用旧模型
            model_path = Path('ml_models/saved_models/random_forest_latest.pkl')

        if not model_path.exists():
            raise HTTPException(status_code=500, detail="模型未训练，请先运行 train_ml_real_features.py")

        _predictor = RiskPredictor()
        _predictor.load_model(model_path)

    return _predictor


def get_loader():
    """获取数据加载器实例"""
    global _loader
    if _loader is None:
        _loader = DataLoader()
    return _loader


class VesselPredictionRequest(BaseModel):
    """船舶预测请求"""
    vessel_imo: str


class BatchPredictionRequest(BaseModel):
    """批量预测请求"""
    vessel_imos: List[str]
    limit: Optional[int] = 100


class PredictionResponse(BaseModel):
    """预测响应"""
    vessel_imo: str
    vessel_name: str
    predicted_risk_level: str
    risk_probabilities: Dict[str, float]
    confidence: float
    top_risk_factors: List[Dict[str, Any]]


@router.get("/health")
async def ml_health_check():
    """机器学习模块健康检查"""
    try:
        predictor = get_predictor()
        return {
            "status": "healthy",
            "model_type": predictor.model_type,
            "model_loaded": predictor.model is not None,
            "feature_count": len(predictor.feature_names) if predictor.feature_names else 0
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.post("/predict/vessel", response_model=PredictionResponse)
async def predict_vessel_risk(request: VesselPredictionRequest):
    """
    预测单个船舶的风险等级

    Args:
        request: 包含vessel_imo的请求

    Returns:
        预测结果，包括风险等级、概率、置信度等
    """
    try:
        predictor = get_predictor()
        loader = get_loader()

        # 简化：直接从vessels表查询，不做复杂JOIN
        query = f"""
        SELECT
            v.imo_number as vessel_imo,
            v.vessel_name,
            v.vessel_type,
            v.build_year as built_year,
            v.flag_country,
            v.asset_risk_score,
            v.risk_level,
            v.owner_company_id,
            2026 - v.build_year as vessel_age
        FROM vessels v
        WHERE v.imo_number = '{request.vessel_imo}' AND v.is_active = 1
        LIMIT 1
        """

        result = loader.client.query(query)
        if not result.result_rows:
            raise HTTPException(status_code=404, detail=f"船舶 {request.vessel_imo} 不存在")

        vessel_data = pd.DataFrame(result.result_rows, columns=result.column_names)

        # 转换类型（但保留字符串字段）
        numeric_cols = ['built_year', 'asset_risk_score', 'vessel_age', 'owner_company_id']
        for col in numeric_cols:
            if col in vessel_data.columns:
                vessel_data[col] = pd.to_numeric(vessel_data[col], errors='coerce')

        # 准备真实特征（不使用模拟数据）
        # 编码分类变量
        vessel_data['vessel_type_encoded'] = pd.Categorical(vessel_data['vessel_type']).codes
        vessel_data['flag_country_encoded'] = pd.Categorical(vessel_data['flag_country']).codes

        # 归一化owner_company_id（使用全局统计值）
        # 注意：这里使用简单的归一化，实际应该使用训练时的统计值
        vessel_data['owner_company_normalized'] = (vessel_data['owner_company_id'] - 25000) / 15000

        # 选择特征（与训练时保持一致 - 6个真实特征）
        feature_columns = [
            'built_year',
            'asset_risk_score',
            'vessel_age',
            'vessel_type_encoded',
            'flag_country_encoded',
            'owner_company_normalized'
        ]

        X = vessel_data[feature_columns]

        # 预测
        prediction = predictor.predict(X)[0]
        probabilities = predictor.predict_proba(X)[0]

        # 映射风险等级
        risk_level_map = {0: 'low', 1: 'medium', 2: 'high'}
        predicted_risk = risk_level_map[prediction]

        # 计算置信度（最高概率）
        confidence = float(np.max(probabilities))

        # 获取特征重要性（Top 5风险因子）
        importance_df = predictor.get_feature_importance(top_n=5)
        top_factors = []
        if importance_df is not None and len(importance_df) > 0:
            for _, row in importance_df.iterrows():
                top_factors.append({
                    "factor": row['feature'],
                    "importance": float(row['importance'])
                })

        # 获取vessel_name，处理NaN情况
        vessel_name = vessel_data.iloc[0]['vessel_name']
        if pd.isna(vessel_name) or vessel_name == '':
            vessel_name = f"Vessel {request.vessel_imo}"

        return PredictionResponse(
            vessel_imo=request.vessel_imo,
            vessel_name=str(vessel_name),
            predicted_risk_level=predicted_risk,
            risk_probabilities={
                "low": float(probabilities[0]),
                "medium": float(probabilities[1]),
                "high": float(probabilities[2])
            },
            confidence=confidence,
            top_risk_factors=top_factors
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"预测失败: {str(e)}")


@router.post("/predict/batch")
async def predict_batch_risk(request: BatchPredictionRequest):
    """
    批量预测船舶风险等级（分批处理）

    Args:
        request: 包含vessel_imos列表的请求

    Returns:
        批量预测结果
    """
    try:
        predictor = get_predictor()
        loader = get_loader()

        # 分批读取，每次10w条
        batch_size = 100000
        limit = min(request.limit, 1000)  # 最多1000条用于展示

        all_results = []
        offset = 0

        # 只读取需要的数量
        query = f"""
        SELECT
            v.imo_number as vessel_imo,
            v.vessel_name,
            v.vessel_type,
            v.build_year as built_year,
            v.flag_country,
            v.asset_risk_score,
            v.risk_level,
            v.owner_company_id,
            2026 - v.build_year as vessel_age
        FROM vessels v
        WHERE v.is_active = 1
        ORDER BY v.asset_risk_score DESC
        LIMIT {limit}
        """

        result = loader.client.query(query)
        if not result.result_rows:
            raise HTTPException(status_code=404, detail="未找到匹配的船舶")

        vessel_df = pd.DataFrame(result.result_rows, columns=result.column_names)

        # 转换数值类型
        vessel_df['built_year'] = pd.to_numeric(vessel_df['built_year'], errors='coerce')
        vessel_df['asset_risk_score'] = pd.to_numeric(vessel_df['asset_risk_score'], errors='coerce')
        vessel_df['vessel_age'] = pd.to_numeric(vessel_df['vessel_age'], errors='coerce')
        vessel_df['owner_company_id'] = pd.to_numeric(vessel_df['owner_company_id'], errors='coerce')

        # 准备真实特征（不使用模拟数据）
        # 编码分类变量
        vessel_df['vessel_type_encoded'] = pd.Categorical(vessel_df['vessel_type']).codes
        vessel_df['flag_country_encoded'] = pd.Categorical(vessel_df['flag_country']).codes

        # 归一化owner_company_id
        vessel_df['owner_company_normalized'] = (vessel_df['owner_company_id'] - 25000) / 15000

        # 选择特征（与训练时保持一致 - 6个真实特征）
        feature_columns = [
            'built_year',
            'asset_risk_score',
            'vessel_age',
            'vessel_type_encoded',
            'flag_country_encoded',
            'owner_company_normalized'
        ]

        X = vessel_df[feature_columns]

        # 批量预测
        predictions = predictor.predict(X)
        probabilities = predictor.predict_proba(X)

        # 映射风险等级
        risk_level_map = {0: 'low', 1: 'medium', 2: 'high'}

        # 构建结果
        results = []
        for i in range(len(predictions)):
            vessel_imo = vessel_df.iloc[i]['vessel_imo']
            vessel_name = vessel_df.iloc[i]['vessel_name']

            # 处理NaN值
            if pd.isna(vessel_imo):
                vessel_imo = f"Unknown_{i}"
            if pd.isna(vessel_name):
                vessel_name = f"Vessel {vessel_imo}"

            results.append({
                "vessel_imo": str(vessel_imo),
                "vessel_name": str(vessel_name),
                "predicted_risk_level": risk_level_map[int(predictions[i])],
                "risk_probabilities": {
                    "low": float(probabilities[i][0]),
                    "medium": float(probabilities[i][1]),
                    "high": float(probabilities[i][2])
                },
                "confidence": float(np.max(probabilities[i]))
            })

        return {
            "total": len(results),
            "predictions": results
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"批量预测失败: {str(e)}")


@router.get("/model/info")
async def get_model_info():
    """获取模型信息"""
    try:
        predictor = get_predictor()

        return {
            "model_type": predictor.model_type,
            "feature_count": len(predictor.feature_names) if predictor.feature_names else 0,
            "feature_names": predictor.feature_names,
            "metrics": predictor.metrics
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型信息失败: {str(e)}")


@router.get("/model/feature-importance")
async def get_feature_importance(top_n: int = 20):
    """获取特征重要性"""
    try:
        predictor = get_predictor()

        # 确保特征重要性和特征名称都存在
        if predictor.feature_importance is None:
            import joblib
            model_path = 'ml_models/saved_models/random_forest_real_features.pkl'
            model = joblib.load(model_path)
            if hasattr(model, 'feature_importances_'):
                predictor.feature_importance = model.feature_importances_
            else:
                raise HTTPException(status_code=500, detail="模型不支持特征重要性")

        if predictor.feature_names is None or len(predictor.feature_names) == 0:
            raise HTTPException(status_code=500, detail="特征名称不可用")

        # 确保特征重要性和特征名称长度一致
        if len(predictor.feature_importance) != len(predictor.feature_names):
            raise HTTPException(
                status_code=500,
                detail=f"特征数量不匹配: importance={len(predictor.feature_importance)}, names={len(predictor.feature_names)}"
            )

        importance_df = predictor.get_feature_importance(top_n=min(top_n, len(predictor.feature_names)))

        if importance_df is None or len(importance_df) == 0:
            raise HTTPException(status_code=500, detail="特征重要性不可用")

        return {
            "features": importance_df.to_dict('records')
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取特征重要性失败: {str(e)}")


@router.get("/stats/risk-distribution")
async def get_risk_distribution():
    """获取风险分布统计"""
    try:
        loader = get_loader()

        # 简单查询，避免复杂操作
        query = """
        SELECT risk_level, COUNT(*) as count
        FROM vessels
        WHERE is_active = 1
        GROUP BY risk_level
        """

        result = loader.client.query(query)

        risk_counts = {}
        total_vessels = 0

        for row in result.result_rows:
            risk_level = row[0] if row[0] else 'unknown'
            count = int(row[1])
            risk_counts[risk_level] = count
            total_vessels += count

        return {
            "total_vessels": total_vessels,
            "risk_distribution": risk_counts
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取风险分布失败: {str(e)}")


@router.get("/vessels/list")
async def get_vessel_list(limit: int = 100, offset: int = 0):
    """
    获取船舶列表（分批加载）

    Args:
        limit: 每页数量，默认100
        offset: 偏移量，默认0

    Returns:
        船舶列表
    """
    try:
        loader = get_loader()

        # 限制最大每页数量
        limit = min(limit, 1000)

        query = f"""
        SELECT
            v.imo_number as vessel_imo,
            v.vessel_name,
            v.vessel_type,
            v.asset_risk_score,
            v.risk_level
        FROM vessels v
        WHERE v.is_active = 1
        ORDER BY v.asset_risk_score DESC
        LIMIT {limit} OFFSET {offset}
        """

        result = loader.client.query(query)

        vessels = []
        for row in result.result_rows:
            vessels.append({
                "vessel_imo": row[0],
                "vessel_name": row[1],
                "vessel_type": row[2],
                "asset_risk_score": float(row[3]) if row[3] else 0,
                "risk_level": row[4] if row[4] else 'unknown'
            })

        return {
            "total": len(vessels),
            "offset": offset,
            "limit": limit,
            "vessels": vessels
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取船舶列表失败: {str(e)}")
