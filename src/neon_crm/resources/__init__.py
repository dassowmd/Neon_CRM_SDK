"""Resource classes for the Neon CRM SDK."""

from .accounts import AccountsResource
from .activities import ActivitiesResource
from .addresses import AddressesResource
from .base import BaseResource
from .campaigns import CampaignsResource
from .custom_fields import CustomFieldsResource
from .custom_objects import CustomObjectsResource
from .donations import DonationsResource
from .events import EventsResource
from .grants import GrantsResource
from .households import HouseholdsResource
from .memberships import MembershipsResource
from .online_store import OnlineStoreResource
from .orders import OrdersResource
from .payments import PaymentsResource
from .pledges import PledgesResource
from .properties import PropertiesResource
from .recurring_donations import RecurringDonationsResource
from .soft_credits import SoftCreditsResource
from .volunteers import VolunteersResource
from .webhooks import WebhooksResource

__all__ = [
    "BaseResource",
    "AccountsResource",
    "AddressesResource",
    "DonationsResource",
    "EventsResource",
    "MembershipsResource",
    "ActivitiesResource",
    "CampaignsResource",
    "CustomFieldsResource",
    "CustomObjectsResource",
    "GrantsResource",
    "HouseholdsResource",
    "OnlineStoreResource",
    "OrdersResource",
    "PaymentsResource",
    "PledgesResource",
    "PropertiesResource",
    "RecurringDonationsResource",
    "SoftCreditsResource",
    "VolunteersResource",
    "WebhooksResource",
]
