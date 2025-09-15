"""Type definitions for the Neon CRM SDK."""

from enum import Enum
from typing import Any, Dict, List, Literal, Union

from typing_extensions import TypedDict


class UserType(str, Enum):
    """Account user type enumeration."""

    INDIVIDUAL = "INDIVIDUAL"
    COMPANY = "COMPANY"


class CustomFieldCategory(str, Enum):
    """Custom field category enumeration."""

    ACCOUNT = "Account"
    DONATION = "Donation"
    EVENT = "Event"
    ATTENDEE = "Attendee"
    INDIVIDUAL = "Individual"
    COMPANY = "Company"
    ACTIVITY = "Activity"
    MEMBERSHIP = "Membership"
    PRODUCT = "Product"
    PROSPECT = "Prospect"
    GRANT = "Grant"


class SearchOperator(str, Enum):
    """Search operator enumeration."""

    EQUAL = "EQUAL"
    NOT_EQUAL = "NOT_EQUAL"
    BLANK = "BLANK"
    NOT_BLANK = "NOT_BLANK"
    LESS_THAN = "LESS_THAN"
    GREATER_THAN = "GREATER_THAN"
    LESS_AND_EQUAL = "LESS_AND_EQUAL"
    GREATER_AND_EQUAL = "GREATER_AND_EQUAL"
    IN_RANGE = "IN_RANGE"
    NOT_IN_RANGE = "NOT_IN_RANGE"
    CONTAIN = "CONTAIN"
    NOT_CONTAIN = "NOT_CONTAIN"


class PaginationParams(TypedDict, total=False):
    """Parameters for paginated requests."""

    currentPage: int
    pageSize: int


class SearchField(TypedDict):
    """A search field specification."""

    field: str
    operator: Union[SearchOperator, str]
    value: Union[str, int, float, bool, List[Any]]


class SearchRequest(TypedDict, total=False):
    """Request structure for search endpoints."""

    searchFields: List[SearchField]
    outputFields: List[str]
    pagination: PaginationParams


class PaginatedResponse(TypedDict):
    """Structure of paginated API responses."""

    pagination: Dict[str, Any]
    searchResults: List[Dict[str, Any]]


class IndividualAccount(TypedDict, total=False):
    """Individual account data structure."""

    accountType: str  # Required: "INDIVIDUAL"
    firstName: str  # Required
    lastName: str  # Required
    middleName: str
    prefix: str
    suffix: str
    salutation: str
    preferredName: str
    email: str  # Highly recommended
    phone: str
    website: str
    jobTitle: str
    gender: str
    dateOfBirth: str  # ISO format: "YYYY-MM-DD"
    deceased: bool
    # Primary contact information
    primaryContact: Dict[str, Any]
    # Multiple email/phone support
    email1: str
    email2: str
    email3: str
    phone1: str
    phone2: str
    phone3: str
    phone1Type: str
    phone2Type: str
    phone3Type: str
    fax: str


class CompanyAccount(TypedDict, total=False):
    """Company account data structure."""

    accountType: str  # Required: "COMPANY"
    name: str  # Required (company name)
    companyName: str  # Alias for name
    organizationType: str
    email: str  # Highly recommended
    phone: str
    website: str
    fax: str
    # Multiple contact support
    email1: str
    email2: str
    email3: str
    phone1: str
    phone2: str
    phone3: str
    phone1Type: str
    phone2Type: str
    phone3Type: str


class AccountResponse(TypedDict, total=False):
    """Account response structure from API."""

    accountId: str
    firstName: str
    lastName: str
    companyName: str
    email: str
    userType: str  # "INDIVIDUAL" or "COMPANY"


class AccountListResponse(TypedDict):
    """Response structure for GET /accounts."""

    accounts: List[AccountResponse]
    pagination: "PaginationInfo"


class PaginationInfo(TypedDict):
    """Pagination information structure."""

    currentPage: int
    pageSize: int
    sortColumn: str
    sortDirection: str  # "ASC" or "DESC"
    totalPages: int
    totalResults: int


class Source(TypedDict, total=False):
    """Source tracking information."""

    sourceId: int
    sourceName: str


class Timestamps(TypedDict, total=False):
    """Custom timestamp information."""

    createdDateTime: str  # ISO format: "2024-01-01T00:00:00Z"


class AccountData(TypedDict, total=False):
    """Account creation data."""

    individualAccount: IndividualAccount
    companyAccount: CompanyAccount
    loginName: str  # For portal access
    source: Source
    timestamps: Timestamps
    addresses: List["Address"]
    consent: Dict[str, Any]  # Consent preferences
    customFields: List[Dict[str, Any]]  # Custom field values


class Address(TypedDict, total=False):
    """Address data structure."""

    addressId: str
    addressType: str  # "Home", "Work", "Billing", "Mailing", etc.
    streetAddress1: str
    streetAddress2: str
    addressLine1: str  # Alias for streetAddress1
    addressLine2: str  # Alias for streetAddress2
    addressLine3: str
    addressLine4: str
    city: str
    state: str
    zipCode: str
    postalCode: str  # Alias for zipCode
    country: str
    isPrimaryAddress: bool


class Contact(TypedDict, total=False):
    """Contact data structure for company accounts."""

    contactId: str
    firstName: str
    lastName: str
    email: str
    phone: str
    title: str
    isPrimaryContact: bool


class DonationData(TypedDict, total=False):
    """Donation data structure."""

    amount: float
    date: str
    campaign: Dict[str, Any]
    fund: Dict[str, Any]
    purpose: Dict[str, Any]
    acknowledgee: Dict[str, Any]
    tribute: Dict[str, Any]
    anonymousType: str
    note: str


class EventData(TypedDict, total=False):
    """Event data structure."""

    name: str
    summary: str
    description: str
    eventDates: Dict[str, str]
    publishEvent: bool
    archived: bool
    category: Dict[str, Any]


class MembershipData(TypedDict, total=False):
    """Membership data structure."""

    membershipType: Dict[str, Any]
    enrollmentDate: str
    expirationDate: str
    membershipLevel: Dict[str, Any]
    status: str


# Environment types
Environment = Literal["production", "trial"]

# Response data types
ResponseData = Dict[str, Any]
ListResponseData = List[Dict[str, Any]]


# Account creation payloads
class CreateIndividualAccountPayload(TypedDict):
    """Payload for creating an individual account."""

    individualAccount: IndividualAccount


class CreateCompanyAccountPayload(TypedDict):
    """Payload for creating a company account."""

    companyAccount: CompanyAccount


# Complete account creation with all optional fields
class CompleteAccountPayload(TypedDict, total=False):
    """Complete account creation payload with all optional fields."""

    individualAccount: IndividualAccount
    companyAccount: CompanyAccount
    addresses: List["Address"]
    source: Source
    timestamps: Timestamps
    loginName: str
    consent: Dict[str, Any]
    customFields: List[Dict[str, Any]]
