"""
Entry point for field stability-based update management.
This script checks which fields in each roaster record need updating based on stability category.
NOTE: Uses row-level updated_at timestamp for all fields (field-level timestamps not implemented).
"""

from db.supabase import supabase
from field_stability.utils import should_update_field
from field_stability.mapping import ROASTER_FIELD_STABILITY
from db.models import Roaster

def check_roaster_fields():
    roasters = supabase.list_all(Roaster)
    for roaster in roasters:
        print(f"Checking roaster: {roaster.name}")
        last_updated = getattr(roaster, 'updated_at', None)
        for field in ROASTER_FIELD_STABILITY.keys():
            needs_update = should_update_field(field, last_updated, db_type='roaster')
            print(f"  {field}: {'update' if needs_update else 'up-to-date'} (last updated: {last_updated})")

if __name__ == "__main__":
    check_roaster_fields()
