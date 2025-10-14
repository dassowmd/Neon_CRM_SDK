"""Migration tools for Neon CRM resources.

This package provides resource-specific migration managers for handling
custom field migrations and bulk operations.
"""

from .base import (
    BaseMigrationManager,
    MigrationStrategy,
    MigrationMapping,
    MigrationPlan,
    MigrationResult,
    ConflictReport,
)
from .bulk_migration import (
    BulkMigrationManager,
    PerformanceMetrics,
    BulkOperationResult,
)
from .plan_serializer import MigrationPlanSerializer, ExportOptions
from .fast_discovery import (
    FastDiscoveryManager,
    DiscoveryReport,
    MigrationOpportunity,
    FieldDiscoveryResult,
)
from .universal_field_manager import (
    UniversalFieldManager,
    FieldType,
    FieldMetadata,
    UniversalFieldValue,
)
from .mapping_validator import (
    MappingDictionaryValidator,
    MappingValidationResult,
    ValidationSeverity,
    ValidationIssue,
)
from .accounts import AccountsMigrationManager
from .activities import ActivitiesMigrationManager
from .campaigns import CampaignsMigrationManager
from .donations import DonationsMigrationManager
from .events import EventsMigrationManager
from .memberships import MembershipsMigrationManager
from .volunteers import VolunteersMigrationManager

__all__ = [
    "BaseMigrationManager",
    "BulkMigrationManager",
    "FastDiscoveryManager",
    "UniversalFieldManager",
    "MappingDictionaryValidator",
    "MigrationStrategy",
    "MigrationMapping",
    "MigrationPlan",
    "MigrationResult",
    "ConflictReport",
    "PerformanceMetrics",
    "BulkOperationResult",
    "DiscoveryReport",
    "MigrationOpportunity",
    "FieldDiscoveryResult",
    "FieldType",
    "FieldMetadata",
    "UniversalFieldValue",
    "MappingValidationResult",
    "ValidationSeverity",
    "ValidationIssue",
    "MigrationPlanSerializer",
    "ExportOptions",
    "AccountsMigrationManager",
    "ActivitiesMigrationManager",
    "CampaignsMigrationManager",
    "DonationsMigrationManager",
    "EventsMigrationManager",
    "MembershipsMigrationManager",
    "VolunteersMigrationManager",
]
