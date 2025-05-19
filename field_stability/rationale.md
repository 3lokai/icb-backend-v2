# Field Stability Rationale

This document explains the rationale for assigning stability categories to each field in the roaster and coffee product databases. Assignments are based on expected frequency of change and business importance.

Refer to docs/roaster_db.md and docs/coffee_db.md for detailed field descriptions and update strategies.

## Categories
- **Highly Stable**: Annual check, rarely changes (e.g., name, founded_year)
- **Moderately Stable**: Quarterly check, occasional updates (e.g., logo_url, description)
- **Variable**: Monthly check, marketing or operational changes (e.g., contact info, tags)
- **Highly Variable**: Weekly check, stock/availability (e.g., is_available)

## Field Assignments
See mapping.py for code mapping and the docs for full field descriptions.
