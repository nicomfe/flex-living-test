from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from sqlalchemy import text
from app.services.cache import get_revenue_summary
from app.core.auth import authenticate_request as get_current_user
from app.core.database_pool import DatabasePool

router = APIRouter()


@router.get("/dashboard/properties")
async def get_dashboard_properties(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    tenant_id = getattr(current_user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant ID not found for user")

    try:
        db_pool = DatabasePool()
        await db_pool.initialize()
        if not db_pool.session_factory:
            raise Exception("Database pool not available")

        async with db_pool.get_session() as session:
            query = text("""
                SELECT id, name
                FROM properties
                WHERE tenant_id = :tenant_id
                ORDER BY name
            """)
            result = await session.execute(query, {"tenant_id": tenant_id})
            rows = result.fetchall()
            properties = [{"id": row.id, "name": row.name} for row in rows]
            return {"properties": properties}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch properties: {str(e)}")

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    tenant_id = getattr(current_user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant ID not found for user")
    
    revenue_data = await get_revenue_summary(property_id, tenant_id)
    
    total_revenue_float = float(revenue_data['total'])
    
    return {
        "property_id": revenue_data['property_id'],
        "total_revenue": total_revenue_float,
        "currency": revenue_data['currency'],
        "reservations_count": revenue_data['count']
    }
