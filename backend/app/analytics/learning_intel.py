"""Volume 17 Section 12 — Learning intelligence."""

import json

from sqlalchemy.orm import Session

from app.models.learning import CampaignLearning, LearningCampaign


def get_learning_intelligence(db: Session, limit: int = 20) -> dict:
    learning_rows = db.query(CampaignLearning).order_by(CampaignLearning.learning_score.desc()).limit(limit).all()
    insight_rows = db.query(LearningCampaign).order_by(LearningCampaign.score.desc()).limit(limit).all()

    fa_values = [r.forecast_accuracy for r in learning_rows if r.forecast_accuracy is not None]
    ls_values = [r.learning_score for r in learning_rows if r.learning_score is not None]

    records = []
    for row in learning_rows:
        records.append({
            "learning_id": str(row.learning_id),
            "campaign_id": row.campaign_id,
            "forecast_accuracy": row.forecast_accuracy,
            "recommendation_accuracy": row.forecast_accuracy,
            "learning_score": row.learning_score,
            "revenue": row.revenue,
            "roi": row.roi,
            "campaign_improvement": round((row.learning_score or 0) - 50, 2),
            "segment_improvement": json.loads(row.ceragem_segment_distribution or "{}"),
            "created_at": row.created_at.isoformat() if row.created_at else None,
        })

    return {
        "learning_score": round(sum(ls_values) / len(ls_values), 2) if ls_values else None,
        "recommendation_accuracy": round(sum(fa_values) / len(fa_values), 4) if fa_values else None,
        "forecast_accuracy": round(sum(fa_values) / len(fa_values), 4) if fa_values else None,
        "campaign_improvement": round(sum(r.learning_score or 0 for r in learning_rows) / max(len(learning_rows), 1) - 50, 2),
        "customer_improvement": "stable",
        "segment_improvement": records[0]["segment_improvement"] if records else {},
        "records": records,
        "insights": [
            {
                "id": str(i.id),
                "campaign_id": i.campaign_id,
                "state": i.state,
                "product": i.product,
                "insight_summary": i.insight_summary,
                "recommendation": i.recommendation,
                "confidence_score": i.score,
            }
            for i in insight_rows
        ],
    }
