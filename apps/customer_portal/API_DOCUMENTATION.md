# Customer Portal API Documentation

## Overview
This document provides detailed information about the API endpoints available in the Customer Portal application of RS Wind Repair Systems. These APIs are primarily used to retrieve data for the interactive visualizations and to support various customer-facing functionalities.

## Authentication
All API endpoints require authentication. The APIs use Django's session-based authentication, and users must be logged in as a valid customer user to access these endpoints. Unauthorized requests will be redirected to the login page.

## API Endpoints

### 1. Unit Repair Data API

**Endpoint**: `/customer/api/unit-repair-data/`

**Method**: GET

**Description**: Retrieves repair counts for each unit associated with the logged-in customer's account.

**Request Parameters**: None

**Response Format**:
```json
[
  {
    "unit_number": "A123",
    "repair_count": 8
  },
  {
    "unit_number": "B456",
    "repair_count": 5
  },
  ...
]
```

**Status Codes**:
- 200: Successful request
- 302: Redirect to login if not authenticated
- 404: Customer profile not found

**Usage Example**:
```javascript
fetch('/customer/api/unit-repair-data/')
  .then(response => response.json())
  .then(data => {
    // Process unit repair data
    console.log(data);
  })
  .catch(error => {
    console.error('Error fetching unit repair data:', error);
  });
```

### 2. Repair Frequency Data API

**Endpoint**: `/customer/api/repair-cost-data/`

**Method**: GET

**Description**: Retrieves repair frequency over time, grouped by month, for the logged-in customer's account.

**Request Parameters**: None

**Response Format**:
```json
[
  {
    "date": "2023-01",
    "count": 3
  },
  {
    "date": "2023-02",
    "count": 7
  },
  ...
]
```

**Status Codes**:
- 200: Successful request
- 302: Redirect to login if not authenticated
- 404: Customer profile not found

**Usage Example**:
```javascript
fetch('/customer/api/repair-cost-data/')
  .then(response => response.json())
  .then(data => {
    // Process repair frequency data
    console.log(data);
  })
  .catch(error => {
    console.error('Error fetching repair frequency data:', error);
  });
```

### 3. Repair Status Data

**Note**: This data is not provided via a separate API endpoint but is included directly in the context of the dashboard template.

**Data Structure**:
```json
{
  "repair_status_counts": [
    {
      "status": "REQUESTED",
      "count": 5
    },
    {
      "status": "PENDING",
      "count": 3
    },
    {
      "status": "APPROVED",
      "count": 2
    },
    {
      "status": "IN_PROGRESS",
      "count": 4
    },
    {
      "status": "COMPLETED",
      "count": 12
    },
    {
      "status": "DENIED",
      "count": 1
    }
  ]
}
```

**Usage**: This data is accessed directly in the dashboard template and passed to the JavaScript functions that generate the pie chart.

## Implementation Details

### Backend Code

The API endpoints are implemented in `views.py`:

```python
@login_required
def unit_repair_data_api(request):
    try:
        customer_user = CustomerUser.objects.get(user=request.user)
        customer = customer_user.customer
        
        # Get unit repair counts
        unit_repair_counts = UnitRepairCount.objects.filter(customer=customer)
        data = [
            {"unit_number": unit.unit_number, "repair_count": unit.repair_count}
            for unit in unit_repair_counts
        ]
        
        return JsonResponse(data, safe=False)
    except CustomerUser.DoesNotExist:
        return JsonResponse({"error": "Customer profile not found"}, status=404)
        
@login_required
def repair_cost_data_api(request):
    try:
        customer_user = CustomerUser.objects.get(user=request.user)
        customer = customer_user.customer
        
        # Get repair frequency data by month
        repairs = Repair.objects.filter(customer=customer)
        
        # Group by month and count
        from django.db.models import Count
        from django.db.models.functions import TruncMonth
        
        repair_data = (
            repairs.annotate(month=TruncMonth('repair_date'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )
        
        # Format data for chart
        data = [
            {"date": item['month'].strftime('%Y-%m'), "count": item['count']}
            for item in repair_data
        ]
        
        return JsonResponse(data, safe=False)
    except CustomerUser.DoesNotExist:
        return JsonResponse({"error": "Customer profile not found"}, status=404)
```

### URL Configuration

The API endpoints are configured in `urls.py`:

```python
from django.urls import path
from . import views

urlpatterns = [
    # ... other URL patterns ...
    path('api/unit-repair-data/', views.unit_repair_data_api, name='unit_repair_data_api'),
    path('api/repair-cost-data/', views.repair_cost_data_api, name='repair_cost_data_api'),
]
```

## Error Handling

The API endpoints include error handling for common scenarios:

1. **User Not Authenticated**: Django's `@login_required` decorator redirects to the login page.
2. **Customer Profile Not Found**: Returns a 404 status with an error message.
3. **Server Error**: Standard Django error handling applies; 500 status is returned.

## Best Practices for API Usage

1. **Error Handling**: Always include error handling in your API calls.
2. **Loading States**: Show loading indicators while waiting for API responses.
3. **Caching**: Consider caching API responses if they are used frequently.
4. **Rate Limiting**: Be mindful of how frequently you call the APIs, especially in loops or intervals.
5. **Authentication**: Ensure users are authenticated before attempting to access the APIs.

## Future API Extensions

Potential future API endpoints that may be implemented:

1. **Repair Details API**: Get detailed information about a specific repair.
2. **Repair Status Update API**: Allow customers to update repair statuses via API.
3. **Repair Request API**: Submit new repair requests programmatically.
4. **Customer Profile API**: Retrieve and update customer profile information. 