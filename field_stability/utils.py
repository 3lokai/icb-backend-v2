from datetime import datetime, timedelta
from .categories import FieldStability
from .mapping import ROASTER_FIELD_STABILITY, COFFEE_FIELD_STABILITY

STABILITY_TO_DELTA = {
    FieldStability.HIGHLY_STABLE: None,  # 'never' update unless last_updated is None
    FieldStability.MODERATELY_STABLE: timedelta(days=90),
    FieldStability.VARIABLE: timedelta(days=30),
    FieldStability.HIGHLY_VARIABLE: timedelta(days=7),
}

def should_update_field(field_name, last_updated, db_type='roaster'):
    """
    Determine if a field should be updated based on its stability category and last updated timestamp.
    db_type: 'roaster' or 'coffee'
    """
    now = datetime.now()
    if db_type == 'roaster':
        stability = ROASTER_FIELD_STABILITY.get(field_name)
    else:
        stability = COFFEE_FIELD_STABILITY.get(field_name)
    if not stability or last_updated is None:
        return True  # Default: update if unknown or never updated
    delta = STABILITY_TO_DELTA.get(stability)
    if delta is None:
        # For HIGHLY_STABLE/'never', never update unless last_updated is None (already handled)
        return False
    return (now - last_updated) > delta
