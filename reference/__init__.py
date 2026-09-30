"""M4.4-D stage D2: immutable ERA5 secondary rain reference from the Copernicus Climate Data Store.

Specification: docs/M4.4-D2_PLAN.md (revision 3, frozen at 781d2e8). This package is isolated from the live BWI
application (CORE, api-v2, web): it only retrieves ERA5 total precipitation for the 36 archive points, builds monthly
reference files, and publishes immutable `ref-era5-YYYY-MM` releases with append-only archive-index provenance.
"""
