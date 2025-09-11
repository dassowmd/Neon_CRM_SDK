"""Permission types and role definitions."""

from enum import Enum
from typing import Set, Dict, List
from dataclasses import dataclass


class Permission(Enum):
    """Available permission levels."""
    
    READ = "read"
    WRITE = "write"  # Create new resources
    UPDATE = "update"  # Modify existing resources
    DELETE = "delete"
    ADMIN = "admin"  # Full access including sensitive operations


class ResourceType(Enum):
    """Available resource types in the system."""
    
    ACCOUNTS = "accounts"
    ACTIVITIES = "activities"
    CAMPAIGNS = "campaigns"
    CUSTOM_FIELDS = "custom_fields"
    CUSTOM_OBJECTS = "custom_objects"
    DONATIONS = "donations"
    EVENTS = "events"
    GRANTS = "grants"
    HOUSEHOLDS = "households"
    MEMBERSHIPS = "memberships"
    ONLINE_STORE = "online_store"
    ORDERS = "orders"
    PAYMENTS = "payments"
    PLEDGES = "pledges"
    PROPERTIES = "properties"
    RECURRING_DONATIONS = "recurring_donations"
    SOFT_CREDITS = "soft_credits"
    VOLUNTEERS = "volunteers"
    WEBHOOKS = "webhooks"


@dataclass
class UserPermissions:
    """User's permissions for the system."""
    
    user_id: str
    role: str
    resource_permissions: Dict[ResourceType, Set[Permission]]
    custom_permissions: Dict[str, Set[Permission]] = None
    
    def __post_init__(self):
        if self.custom_permissions is None:
            self.custom_permissions = {}
    
    def has_permission(self, resource: ResourceType, permission: Permission) -> bool:
        """Check if user has a specific permission for a resource."""
        resource_perms = self.resource_permissions.get(resource, set())
        
        # Admin permission grants all access
        if Permission.ADMIN in resource_perms:
            return True
            
        return permission in resource_perms
    
    def has_any_permission(self, resource: ResourceType, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions for a resource."""
        return any(self.has_permission(resource, perm) for perm in permissions)


class Role(Enum):
    """Pre-defined user roles with standard permission sets."""
    
    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN = "admin"
    FUNDRAISER = "fundraiser"
    EVENT_MANAGER = "event_manager"
    VOLUNTEER_COORDINATOR = "volunteer_coordinator"


# Standard role definitions
ROLE_PERMISSIONS: Dict[Role, Dict[ResourceType, Set[Permission]]] = {
    Role.VIEWER: {
        # Viewers can only read most resources
        ResourceType.ACCOUNTS: {Permission.READ},
        ResourceType.ACTIVITIES: {Permission.READ},
        ResourceType.CAMPAIGNS: {Permission.READ},
        ResourceType.DONATIONS: {Permission.READ},
        ResourceType.EVENTS: {Permission.READ},
        ResourceType.GRANTS: {Permission.READ},
        ResourceType.HOUSEHOLDS: {Permission.READ},
        ResourceType.MEMBERSHIPS: {Permission.READ},
        ResourceType.ONLINE_STORE: {Permission.READ},
        ResourceType.ORDERS: {Permission.READ},
        ResourceType.PAYMENTS: {Permission.READ},
        ResourceType.PLEDGES: {Permission.READ},
        ResourceType.VOLUNTEERS: {Permission.READ},
        # Limited access to system configuration
        ResourceType.CUSTOM_FIELDS: {Permission.READ},
        ResourceType.CUSTOM_OBJECTS: {Permission.READ},
        ResourceType.PROPERTIES: {Permission.READ},
    },
    
    Role.EDITOR: {
        # Editors can read and modify most resources
        ResourceType.ACCOUNTS: {Permission.READ, Permission.WRITE, Permission.UPDATE},
        ResourceType.ACTIVITIES: {Permission.READ, Permission.WRITE, Permission.UPDATE},
        ResourceType.CAMPAIGNS: {Permission.READ, Permission.WRITE, Permission.UPDATE},
        ResourceType.DONATIONS: {Permission.READ, Permission.WRITE, Permission.UPDATE},
        ResourceType.EVENTS: {Permission.READ, Permission.WRITE, Permission.UPDATE},
        ResourceType.GRANTS: {Permission.READ, Permission.WRITE, Permission.UPDATE},
        ResourceType.HOUSEHOLDS: {Permission.READ, Permission.WRITE, Permission.UPDATE},
        ResourceType.MEMBERSHIPS: {Permission.READ, Permission.WRITE, Permission.UPDATE},
        ResourceType.ONLINE_STORE: {Permission.READ, Permission.WRITE, Permission.UPDATE},
        ResourceType.ORDERS: {Permission.READ, Permission.UPDATE},  # Can't create orders directly
        ResourceType.PAYMENTS: {Permission.READ, Permission.UPDATE},  # Can't create payments directly
        ResourceType.PLEDGES: {Permission.READ, Permission.WRITE, Permission.UPDATE},
        ResourceType.RECURRING_DONATIONS: {Permission.READ, Permission.WRITE, Permission.UPDATE},
        ResourceType.SOFT_CREDITS: {Permission.READ, Permission.WRITE, Permission.UPDATE},
        ResourceType.VOLUNTEERS: {Permission.READ, Permission.WRITE, Permission.UPDATE},
        # Read-only access to system configuration
        ResourceType.CUSTOM_FIELDS: {Permission.READ},
        ResourceType.CUSTOM_OBJECTS: {Permission.READ},
        ResourceType.PROPERTIES: {Permission.READ},
        ResourceType.WEBHOOKS: {Permission.READ},
    },
    
    Role.ADMIN: {
        # Admins have full access to all resources
        resource: {Permission.ADMIN}
        for resource in ResourceType
    },
    
    Role.FUNDRAISER: {
        # Fundraisers focus on donation-related activities
        ResourceType.ACCOUNTS: {Permission.READ, Permission.WRITE, Permission.UPDATE},
        ResourceType.DONATIONS: {Permission.READ, Permission.WRITE, Permission.UPDATE},
        ResourceType.CAMPAIGNS: {Permission.READ, Permission.WRITE, Permission.UPDATE},
        ResourceType.PLEDGES: {Permission.READ, Permission.WRITE, Permission.UPDATE},
        ResourceType.RECURRING_DONATIONS: {Permission.READ, Permission.WRITE, Permission.UPDATE},
        ResourceType.SOFT_CREDITS: {Permission.READ, Permission.WRITE, Permission.UPDATE},
        ResourceType.GRANTS: {Permission.READ, Permission.WRITE, Permission.UPDATE},
        ResourceType.ACTIVITIES: {Permission.READ, Permission.WRITE, Permission.UPDATE},
        ResourceType.HOUSEHOLDS: {Permission.READ},
        ResourceType.MEMBERSHIPS: {Permission.READ},
        ResourceType.EVENTS: {Permission.READ},
        ResourceType.VOLUNTEERS: {Permission.READ},
        ResourceType.PAYMENTS: {Permission.READ},
        ResourceType.ORDERS: {Permission.READ},
    },
    
    Role.EVENT_MANAGER: {
        # Event managers focus on event-related activities
        ResourceType.EVENTS: {Permission.READ, Permission.WRITE, Permission.UPDATE, Permission.DELETE},
        ResourceType.ACCOUNTS: {Permission.READ, Permission.WRITE, Permission.UPDATE},
        ResourceType.ACTIVITIES: {Permission.READ, Permission.WRITE, Permission.UPDATE},
        ResourceType.ORDERS: {Permission.READ},
        ResourceType.PAYMENTS: {Permission.READ},
        ResourceType.VOLUNTEERS: {Permission.READ, Permission.WRITE, Permission.UPDATE},
        ResourceType.DONATIONS: {Permission.READ},
        ResourceType.HOUSEHOLDS: {Permission.READ},
        ResourceType.MEMBERSHIPS: {Permission.READ},
    },
    
    Role.VOLUNTEER_COORDINATOR: {
        # Volunteer coordinators manage volunteer activities
        ResourceType.VOLUNTEERS: {Permission.READ, Permission.WRITE, Permission.UPDATE, Permission.DELETE},
        ResourceType.ACCOUNTS: {Permission.READ, Permission.WRITE, Permission.UPDATE},
        ResourceType.ACTIVITIES: {Permission.READ, Permission.WRITE, Permission.UPDATE},
        ResourceType.EVENTS: {Permission.READ},
        ResourceType.HOUSEHOLDS: {Permission.READ},
        ResourceType.DONATIONS: {Permission.READ},
        ResourceType.MEMBERSHIPS: {Permission.READ},
    },
}


def create_user_permissions(user_id: str, role: Role, custom_overrides: Dict[ResourceType, Set[Permission]] = None) -> UserPermissions:
    """Create a UserPermissions object with a standard role and optional overrides."""
    base_permissions = ROLE_PERMISSIONS.get(role, {}).copy()
    
    if custom_overrides:
        for resource, permissions in custom_overrides.items():
            base_permissions[resource] = permissions
    
    return UserPermissions(
        user_id=user_id,
        role=role.value,
        resource_permissions=base_permissions
    )