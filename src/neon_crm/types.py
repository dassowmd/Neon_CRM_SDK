"""Type definitions for the Neon CRM SDK."""

from typing import Any, Dict, List, Literal, Union

from typing_extensions import TypedDict


class PaginationParams(TypedDict, total=False):
    """Parameters for paginated requests."""

    currentPage: int
    pageSize: int


class SearchField(TypedDict):
    """A search field specification."""

    field: str
    operator: str
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

    accountType: str
    firstName: str
    lastName: str
    email: str
    phone: str
    website: str
    jobTitle: str
    suffix: str
    prefix: str
    middleName: str
    preferredName: str
    gender: str
    dateOfBirth: str


class CompanyAccount(TypedDict, total=False):
    """Company account data structure."""

    accountType: str
    name: str
    email: str
    phone: str
    website: str
    fax: str


class AccountData(TypedDict, total=False):
    """Account creation data."""

    individualAccount: IndividualAccount
    companyAccount: CompanyAccount
    loginName: str
    source: Dict[str, Any]
    timestamps: Dict[str, str]


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
