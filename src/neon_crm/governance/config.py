"""Configuration system for permissions and access control."""

from typing import Dict, Set, Optional, Any, Callable
import json
import os
from pathlib import Path

from .permissions import Permission, ResourceType, Role, UserPermissions, ROLE_PERMISSIONS, create_user_permissions


class PermissionConfig:
    """Configuration manager for the governance system."""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize the permission configuration.
        
        Args:
            config_file: Path to JSON configuration file (optional)
        """
        self.custom_permissions: Dict[ResourceType, Dict[str, Set[Permission]]] = {}
        self.user_permissions: Dict[str, UserPermissions] = {}
        self.role_overrides: Dict[Role, Dict[ResourceType, Set[Permission]]] = {}
        self.resource_specific_rules: Dict[ResourceType, Callable] = {}
        
        if config_file and os.path.exists(config_file):
            self.load_from_file(config_file)
    
    def load_from_file(self, config_file: str):
        """Load permission configuration from a JSON file.
        
        Args:
            config_file: Path to the configuration file
        """
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            self._load_role_overrides(config_data.get('role_overrides', {}))
            self._load_user_permissions(config_data.get('users', {}))
            self._load_custom_permissions(config_data.get('custom_permissions', {}))
            
        except Exception as e:
            raise ValueError(f"Error loading permission config from {config_file}: {e}")
    
    def _load_role_overrides(self, overrides_data: Dict[str, Any]):
        """Load role permission overrides from configuration."""
        for role_name, resources in overrides_data.items():
            try:
                role = Role(role_name)
                role_perms = {}
                
                for resource_name, permissions in resources.items():
                    resource = ResourceType(resource_name)
                    perms = {Permission(p) for p in permissions}
                    role_perms[resource] = perms
                
                self.role_overrides[role] = role_perms
                
            except ValueError as e:
                print(f"Warning: Invalid role or resource in config: {e}")
    
    def _load_user_permissions(self, users_data: Dict[str, Any]):
        """Load individual user permissions from configuration."""
        for user_id, user_config in users_data.items():
            try:
                role = Role(user_config.get('role', 'viewer'))
                custom_overrides = {}
                
                # Load custom resource permissions for this user
                if 'permissions' in user_config:
                    for resource_name, permissions in user_config['permissions'].items():
                        resource = ResourceType(resource_name)
                        perms = {Permission(p) for p in permissions}
                        custom_overrides[resource] = perms
                
                user_permissions = create_user_permissions(user_id, role, custom_overrides)
                self.user_permissions[user_id] = user_permissions
                
            except ValueError as e:
                print(f"Warning: Invalid user configuration for {user_id}: {e}")
    
    def _load_custom_permissions(self, custom_data: Dict[str, Any]):
        """Load custom permission rules from configuration."""
        for resource_name, rules in custom_data.items():
            try:
                resource = ResourceType(resource_name)
                if resource not in self.custom_permissions:
                    self.custom_permissions[resource] = {}
                
                for rule_name, permissions in rules.items():
                    perms = {Permission(p) for p in permissions}
                    self.custom_permissions[resource][rule_name] = perms
                    
            except ValueError as e:
                print(f"Warning: Invalid custom permission rule: {e}")
    
    def save_to_file(self, config_file: str):
        """Save current configuration to a JSON file.
        
        Args:
            config_file: Path to save the configuration
        """
        config_data = {
            'role_overrides': {
                role.value: {
                    resource.value: [p.value for p in permissions]
                    for resource, permissions in resource_perms.items()
                }
                for role, resource_perms in self.role_overrides.items()
            },
            'users': {
                user_id: {
                    'role': user_perms.role,
                    'permissions': {
                        resource.value: [p.value for p in permissions]
                        for resource, permissions in user_perms.resource_permissions.items()
                    }
                }
                for user_id, user_perms in self.user_permissions.items()
            },
            'custom_permissions': {
                resource.value: {
                    rule_name: [p.value for p in permissions]
                    for rule_name, permissions in rules.items()
                }
                for resource, rules in self.custom_permissions.items()
            }
        }
        
        # Create directory if it doesn't exist
        Path(config_file).parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def add_user(self, user_id: str, role: Role, custom_permissions: Dict[ResourceType, Set[Permission]] = None) -> UserPermissions:
        """Add a user with specified role and optional custom permissions.
        
        Args:
            user_id: Unique identifier for the user
            role: Base role for the user
            custom_permissions: Optional resource-specific permission overrides
            
        Returns:
            UserPermissions object for the user
        """
        # Start with role-based permissions
        base_permissions = ROLE_PERMISSIONS.get(role, {}).copy()
        
        # Apply role overrides if configured
        if role in self.role_overrides:
            for resource, permissions in self.role_overrides[role].items():
                base_permissions[resource] = permissions
        
        # Apply custom permissions
        if custom_permissions:
            base_permissions.update(custom_permissions)
        
        user_perms = UserPermissions(
            user_id=user_id,
            role=role.value,
            resource_permissions=base_permissions
        )
        
        self.user_permissions[user_id] = user_perms
        return user_perms
    
    def get_user_permissions(self, user_id: str) -> Optional[UserPermissions]:
        """Get permissions for a specific user.
        
        Args:
            user_id: The user identifier
            
        Returns:
            UserPermissions object or None if user not found
        """
        return self.user_permissions.get(user_id)
    
    def remove_user(self, user_id: str):
        """Remove a user from the configuration.
        
        Args:
            user_id: The user identifier to remove
        """
        self.user_permissions.pop(user_id, None)
    
    def update_role_permissions(self, role: Role, resource: ResourceType, permissions: Set[Permission]):
        """Update the default permissions for a role on a specific resource.
        
        Args:
            role: The role to update
            resource: The resource type
            permissions: New set of permissions for this role/resource combination
        """
        if role not in self.role_overrides:
            self.role_overrides[role] = {}
        
        self.role_overrides[role][resource] = permissions
        
        # Update all existing users with this role
        for user_perms in self.user_permissions.values():
            if user_perms.role == role.value:
                user_perms.resource_permissions[resource] = permissions
    
    def get_effective_permissions(self, user_id: str, resource: ResourceType) -> Set[Permission]:
        """Get the effective permissions for a user on a specific resource.
        
        Args:
            user_id: The user identifier
            resource: The resource type
            
        Returns:
            Set of effective permissions
        """
        user_perms = self.get_user_permissions(user_id)
        if not user_perms:
            return set()
        
        return user_perms.resource_permissions.get(resource, set())
    
    def list_users_with_permission(self, resource: ResourceType, permission: Permission) -> list[str]:
        """List all users who have a specific permission on a resource.
        
        Args:
            resource: The resource type
            permission: The permission to check for
            
        Returns:
            List of user IDs who have the permission
        """
        users_with_permission = []
        
        for user_id, user_perms in self.user_permissions.items():
            if user_perms.has_permission(resource, permission):
                users_with_permission.append(user_id)
        
        return users_with_permission


# Default permission matrix for quick setup
default_permission_matrix = PermissionConfig()

# Add some example users for demonstration
default_permission_matrix.add_user("admin_user", Role.ADMIN)
default_permission_matrix.add_user("fundraiser_user", Role.FUNDRAISER)
default_permission_matrix.add_user("event_manager_user", Role.EVENT_MANAGER)
default_permission_matrix.add_user("volunteer_coordinator_user", Role.VOLUNTEER_COORDINATOR)
default_permission_matrix.add_user("readonly_user", Role.VIEWER)

# Example of custom permissions for a specific user
default_permission_matrix.add_user(
    "special_editor", 
    Role.EDITOR, 
    custom_permissions={
        ResourceType.WEBHOOKS: {Permission.READ, Permission.WRITE, Permission.UPDATE},
        ResourceType.CUSTOM_FIELDS: {Permission.READ, Permission.WRITE, Permission.UPDATE, Permission.DELETE}
    }
)