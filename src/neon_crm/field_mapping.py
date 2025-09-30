"""Field name mapping utilities for the Neon CRM SDK.

This module provides utilities to map between different field name formats:
- API camelCase format (e.g., "firstName", "accountId")
- Display name format (e.g., "First Name", "Account ID")
- Legacy field names from older SDK versions

This ensures backward compatibility while supporting the correct API field names.
"""

from typing import Dict, List, Optional, Set


class FieldNameMapper:
    """Maps between different field name formats for Neon CRM API."""

    # Mapping from display names to API field names
    DISPLAY_TO_API_MAP = {
        # Account fields
        "Account ID": "accountId",
        "First Name": "firstName",
        "Last Name": "lastName",
        "Email 1": "email1",
        "Email 2": "email2",
        "Email 3": "email3",
        "Phone 1": "phone1",
        "Phone 2": "phone2",
        "Phone 3": "phone3",
        "Account Type": "accountType",
        "Company Name": "companyName",
        "Date Created": "dateCreated",
        "Date Modified": "dateModified",
        "Source": "source",
        "Login Name": "loginName",
        "Address Line 1": "addressLine1",
        "Address Line 2": "addressLine2",
        "City": "city",
        "State": "stateProvince",
        "State/Province": "stateProvince",
        "Zip Code": "zipCode",
        "Country": "country",
        "Gender": "gender",
        "Date of Birth": "dateOfBirth",
        "Preferred Name": "preferredName",
        "Account Created Date/Time": "dateCreated",
        "Account Last Modified Date/Time": "dateModified",
        # Donation fields
        "Donation ID": "id",
        "Donation Amount": "amount",
        "Amount": "amount",
        "Donation Date": "date",
        "Date": "date",
        "Campaign": "campaign",
        "Campaign Name": "name",
        "Campaign ID": "id",
        "Fund": "fund",
        "Purpose": "purpose",
        "Payment Method": "paymentMethod",
        "Check Number": "checkNumber",
        "Transaction Fee": "transactionFee",
        "Anonymous Type": "anonymousType",
        "Tribute Type": "tributeType",
        "Acknowledgee": "acknowledgee",
        "Note": "note",
        "Tender Type": "paymentMethod",
        # Event fields
        "Event ID": "id",
        "Event Name": "name",
        "Start Date": "startDate",
        "End Date": "endDate",
        "Category": "category",
        "Status": "status",
        "Published": "publishEvent",
        "Archived": "archived",
        "Registration Start Date": "registrationStartDate",
        "Registration End Date": "registrationEndDate",
        "Maximum Attendees": "maximumAttendees",
        "Current Attendees": "currentAttendees",
        "Summary": "summary",
        "Description": "description",
        # Activity fields
        "Activity ID": "id",
        "Activity Type": "activityType",
        "Subject": "subject",
        "Priority": "priority",
        "Assigned To": "assignedTo",
        "Created By": "createdBy",
        # Membership fields
        "Membership ID": "id",
        "Membership Type": "membershipType",
        "Enrollment Date": "enrollmentDate",
        "Expiration Date": "expirationDate",
        "Auto Renew": "autoRenew",
        "Term": "term",
        "Transaction ID": "transactionId",
        # Campaign fields
        "Campaign ID": "id",
        "Campaign Code": "code",
        "Campaign Goal": "goal",
        "Campaign Start Date": "startDate",
        "Campaign End Date": "endDate",
        "Campaign Type": "type",
        "Campaign Status": "status",
    }

    # Reverse mapping from API names to display names
    # Note: Where multiple display names map to same API name, use the most specific one
    API_TO_DISPLAY_MAP = {
        # Account fields
        "accountId": "Account ID",
        "firstName": "First Name",
        "lastName": "Last Name",
        "email1": "Email 1",
        "email2": "Email 2",
        "email3": "Email 3",
        "phone1": "Phone 1",
        "phone2": "Phone 2",
        "phone3": "Phone 3",
        "accountType": "Account Type",
        "companyName": "Company Name",
        "dateCreated": "Date Created",
        "dateModified": "Date Modified",
        "source": "Source",
        "loginName": "Login Name",
        "addressLine1": "Address Line 1",
        "addressLine2": "Address Line 2",
        "city": "City",
        "stateProvince": "State/Province",
        "zipCode": "Zip Code",
        "country": "Country",
        "gender": "Gender",
        "dateOfBirth": "Date of Birth",
        "preferredName": "Preferred Name",
        # Donation fields
        "id": "ID",  # Generic ID field
        "amount": "Donation Amount",  # Prefer "Donation Amount" over "Amount"
        "date": "Date",
        "campaign": "Campaign Name",  # Prefer "Campaign Name" over "Campaign ID"
        "fund": "Fund",
        "purpose": "Purpose",
        "paymentMethod": "Payment Method",
        "checkNumber": "Check Number",
        "transactionFee": "Transaction Fee",
        "anonymousType": "Anonymous Type",
        "tributeType": "Tribute Type",
        "acknowledgee": "Acknowledgee",
        "note": "Note",
        # Event fields
        "name": "Event Name",  # Context-dependent
        "startDate": "Start Date",
        "endDate": "End Date",
        "category": "Category",
        "status": "Status",
        "publishEvent": "Published",
        "archived": "Archived",
        "registrationStartDate": "Registration Start Date",
        "registrationEndDate": "Registration End Date",
        "maximumAttendees": "Maximum Attendees",
        "currentAttendees": "Current Attendees",
        "summary": "Summary",
        "description": "Description",
        # Activity fields
        "activityType": "Activity Type",
        "subject": "Subject",
        "priority": "Priority",
        "assignedTo": "Assigned To",
        "createdBy": "Created By",
        # Membership fields
        "membershipType": "Membership Type",
        "enrollmentDate": "Enrollment Date",
        "expirationDate": "Expiration Date",
        "autoRenew": "Auto Renew",
        "term": "Term",
        "transactionId": "Transaction ID",
        # Campaign fields
        "code": "Campaign Code",
        "goal": "Campaign Goal",
        "type": "Campaign Type",
    }

    @classmethod
    def to_api_field_name(cls, display_name: str) -> str:
        """Convert display name to API field name.

        Args:
            display_name: Field name in display format (e.g., "First Name")

        Returns:
            API field name in camelCase format (e.g., "firstName")

        Example:
            >>> FieldNameMapper.to_api_field_name("First Name")
            "firstName"
            >>> FieldNameMapper.to_api_field_name("Account ID")
            "accountId"
        """
        # If it's already an API field name, return as-is
        if display_name in cls.API_TO_DISPLAY_MAP:
            return display_name

        # Look up in mapping
        api_name = cls.DISPLAY_TO_API_MAP.get(display_name)
        if api_name:
            return api_name

        # If not found, return the original (might be already correct)
        return display_name

    @classmethod
    def to_display_field_name(cls, api_name: str) -> str:
        """Convert API field name to display name.

        Args:
            api_name: Field name in API format (e.g., "firstName")

        Returns:
            Display field name (e.g., "First Name")

        Example:
            >>> FieldNameMapper.to_display_field_name("firstName")
            "First Name"
            >>> FieldNameMapper.to_display_field_name("accountId")
            "Account ID"
        """
        # Look up in reverse mapping
        display_name = cls.API_TO_DISPLAY_MAP.get(api_name)
        if display_name:
            return display_name

        # If not found, return the original
        return api_name

    @classmethod
    def convert_search_fields(cls, search_fields: List[Dict]) -> List[Dict]:
        """Convert search fields from display names to API names.

        Args:
            search_fields: List of search field dictionaries with "field" key

        Returns:
            List of search fields with API field names

        Example:
            >>> fields = [{"field": "First Name", "operator": "EQUAL", "value": "John"}]
            >>> FieldNameMapper.convert_search_fields(fields)
            [{"field": "firstName", "operator": "EQUAL", "value": "John"}]
        """
        converted_fields = []

        for field_def in search_fields:
            if isinstance(field_def, dict) and "field" in field_def:
                converted_field = field_def.copy()
                converted_field["field"] = cls.to_api_field_name(field_def["field"])
                converted_fields.append(converted_field)
            else:
                converted_fields.append(field_def)

        return converted_fields

    @classmethod
    def convert_output_fields(cls, output_fields: List[str]) -> List[str]:
        """Convert output fields from display names to API names.

        Args:
            output_fields: List of output field names

        Returns:
            List of API field names

        Example:
            >>> fields = ["Account ID", "First Name", "Last Name"]
            >>> FieldNameMapper.convert_output_fields(fields)
            ["accountId", "firstName", "lastName"]
        """
        return [cls.to_api_field_name(field) for field in output_fields]

    @classmethod
    def convert_search_request(cls, search_request: Dict) -> Dict:
        """Convert entire search request to use API field names.

        Args:
            search_request: Search request dictionary

        Returns:
            Search request with API field names
        """
        converted_request = search_request.copy()

        # Convert search fields
        if "searchFields" in converted_request:
            converted_request["searchFields"] = cls.convert_search_fields(
                converted_request["searchFields"]
            )

        # Convert output fields
        if "outputFields" in converted_request:
            converted_request["outputFields"] = cls.convert_output_fields(
                converted_request["outputFields"]
            )

        return converted_request

    @classmethod
    def get_suggested_fields(
        cls, invalid_field: str, available_fields: List[str]
    ) -> List[str]:
        """Get suggested field names for an invalid field.

        Args:
            invalid_field: The invalid field name
            available_fields: List of available field names

        Returns:
            List of suggested field names
        """
        suggestions = []

        # Try converting to API format
        api_field = cls.to_api_field_name(invalid_field)
        if api_field != invalid_field and api_field in available_fields:
            suggestions.append(api_field)

        # Try converting to display format
        display_field = cls.to_display_field_name(invalid_field)
        if display_field != invalid_field:
            api_equivalent = cls.to_api_field_name(display_field)
            if api_equivalent in available_fields:
                suggestions.append(api_equivalent)

        # Look for similar field names (basic fuzzy matching)
        lower_invalid = invalid_field.lower().replace(" ", "").replace("_", "")
        for field in available_fields:
            lower_field = field.lower().replace(" ", "").replace("_", "")
            if lower_invalid in lower_field or lower_field in lower_invalid:
                if field not in suggestions:
                    suggestions.append(field)

        return suggestions[:5]  # Return top 5 suggestions

    @classmethod
    def is_valid_field_format(cls, field_name: str) -> bool:
        """Check if a field name is in valid API format.

        Args:
            field_name: Field name to check

        Returns:
            True if field name is in API format, False otherwise
        """
        # API field names are typically camelCase with no spaces
        return (
            " " not in field_name
            and field_name.islower()
            or (field_name[0].islower() and any(c.isupper() for c in field_name[1:]))
        )
