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
from .accounts import AccountsMigrationManager
from .activities import ActivitiesMigrationManager
from .campaigns import CampaignsMigrationManager
from .donations import DonationsMigrationManager
from .events import EventsMigrationManager
from .memberships import MembershipsMigrationManager
from .volunteers import VolunteersMigrationManager

__all__ = [
    "BaseMigrationManager",
    "MigrationStrategy",
    "MigrationMapping",
    "MigrationPlan",
    "MigrationResult",
    "ConflictReport",
    "AccountsMigrationManager",
    "ActivitiesMigrationManager",
    "CampaignsMigrationManager",
    "DonationsMigrationManager",
    "EventsMigrationManager",
    "MembershipsMigrationManager",
    "VolunteersMigrationManager",
]
