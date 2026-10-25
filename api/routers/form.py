"""
api/routers/form.py — Form correction endpoints for all workout types.
"""
from fastapi import APIRouter, HTTPException
from features.coach.form_corrections import get_form_correction, get_all_activities, FORM_CORRECTIONS

router = APIRouter(prefix="/api/v1/form", tags=["form"])


@router.get("/activities")
async def list_activities():
    """List all activities with form correction data available."""
    return {"activities": get_all_activities()}


@router.get("/{activity}")
async def get_correction(activity: str):
    """Get detailed form correction data for a specific activity."""
    data = get_form_correction(activity)
    if not data:
        raise HTTPException(
            status_code=404,
            detail=f"No form data for '{activity}'. Available: {get_all_activities()}"
        )
    return {"activity": activity, **data}
