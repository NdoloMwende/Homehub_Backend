# HomeHub Backend API Testing Guide

## Prerequisites
- Flask app running on `http://127.0.0.1:5000`
- Use `curl`, Postman, or any HTTP client

---

## Step 1: Health Check
Verify the backend is running:

```bash
curl http://127.0.0.1:5000/
```

**Expected Response (200):**
```json
{
  "message": "HomeHub Backend is running",
  "status": "healthy",
  "version": "1.0.0"
}
```

---

## Step 2: Get API Information
```bash
curl http://127.0.0.1:5000/api
```

**Expected Response (200):**
```json
{
  "name": "HomeHub Backend API",
  "version": "1.0.0",
  "description": "Property rental management system",
  "endpoints": {
    "auth": "/api/auth",
    "users": "/api/users",
    "properties": "/api/properties",
    "units": "/api/units",
    "leases": "/api/leases",
    "rent_invoices": "/api/rent-invoices",
    "payments": "/api/payments",
    "maintenance": "/api/maintenance",
    "notifications": "/api/notifications"
  },
  "docs": "/apidocs"
}
```

---

## Step 3: Register Users

### 3a. Register Admin User
```bash
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "System Admin",
    "email": "admin@homehub.test",
    "password": "admin123",
    "role": "admin",
    "phone": "0700000000"
  }'
```

**Expected Response (201):**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": "uuid-here",
    "full_name": "System Admin",
    "email": "admin@homehub.test",
    "role": "admin",
    "phone": "0700000000",
    "is_active": true,
    "status": "approved",
    "comment": null,
    "created_at": "2026-01-03T...",
    "updated_at": "2026-01-03T..."
  }
}
```

**Save Admin ID for later use:**
```
ADMIN_ID = aef4166f-7b87-4d72-872f-ae63d37aba28
```

---

### 3b. Register Landlord User
```bash
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Landlord",
    "email": "landlord@homehub.test",
    "password": "landlord123",
    "role": "landlord",
    "phone": "0711111111"
  }'
```

**Save Landlord ID:**
```
LANDLORD_ID = <id from response>
```

---

### 3c. Register Tenant User
```bash
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Jane Tenant",
    "email": "tenant@homehub.test",
    "password": "tenant123",
    "role": "tenant",
    "phone": "0722222222"
  }'
```

**Save Tenant ID:**
```
TENANT_ID = <id from response>
```

---

## Step 4: Login Users

### 4a. Admin Login
```bash
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@homehub.test",
    "password": "admin123"
  }'
```

**Expected Response (200):**
```json
{
  "message": "Login successful",
  "access_token": "eyJ...",
  "user": { ... }
}
```

**Save Admin Token:**
```
ADMIN_TOKEN = <access_token from response>
```

---

### 4b. Landlord Login
```bash
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "landlord@homehub.test",
    "password": "landlord123"
  }'
```

**Save Landlord Token:**
```
LANDLORD_TOKEN = <access_token from response>
```

---

### 4c. Tenant Login
```bash
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "tenant@homehub.test",
    "password": "tenant123"
  }'
```

**Save Tenant Token:**
```
TENANT_TOKEN = <access_token from response>
```

---

## Step 5: Create Property (Landlord)

```bash
curl -X POST http://127.0.0.1:5000/api/properties \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer LANDLORD_TOKEN" \
  -d '{
    "name": "Emerald Residency",
    "address": "123 Ngong Road",
    "city": "Nairobi",
    "country": "Kenya",
    "description": "Luxury apartments",
    "lrn_no": "LR12345",
    "location": "Ngong Road"
  }'
```

**Expected Response (201):**
```json
{
  "message": "Property created successfully",
  "property": {
    "id": "prop-uuid",
    "landlord_id": "LANDLORD_ID",
    "name": "Emerald Residency",
    "address": "123 Ngong Road",
    "city": "Nairobi",
    "country": "Kenya",
    "status": "pending",
    "created_at": "2026-01-03T..."
  }
}
```

**Save Property ID:**
```
PROPERTY_ID = <id from response>
```

---

## Step 6: Approve Property (Admin)

```bash
curl -X POST http://127.0.0.1:5000/api/properties/PROPERTY_ID/approve \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "comment": "Property looks good and verified"
  }'
```

**Expected Response (200):**
```json
{
  "message": "Property approved successfully",
  "property": {
    "id": "PROPERTY_ID",
    "status": "approved",
    ...
  }
}
```

---

## Step 7: Create Unit (Landlord)

```bash
curl -X POST http://127.0.0.1:5000/api/units \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer LANDLORD_TOKEN" \
  -d '{
    "property_id": "PROPERTY_ID",
    "unit_number": "A1",
    "floor_number": "1",
    "rent_amount": 45000
  }'
```

**Expected Response (201):**
```json
{
  "message": "Unit created successfully",
  "unit": {
    "id": "unit-uuid",
    "property_id": "PROPERTY_ID",
    "unit_number": "A1",
    "floor_number": "1",
    "rent_amount": 45000,
    "status": "vacant"
  }
}
```

**Save Unit ID:**
```
UNIT_ID = <id from response>
```

---

## Step 8: Get All Units for Property

```bash
curl http://127.0.0.1:5000/api/units/property/PROPERTY_ID
```

**Expected Response (200):**
```json
[
  {
    "id": "UNIT_ID",
    "property_id": "PROPERTY_ID",
    "unit_number": "A1",
    "floor_number": "1",
    "rent_amount": 45000,
    "status": "vacant"
  }
]
```

---

## Step 9: Create Lease (Landlord)

```bash
curl -X POST http://127.0.0.1:5000/api/leases \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer LANDLORD_TOKEN" \
  -d '{
    "unit_id": "UNIT_ID",
    "tenant_id": "TENANT_ID",
    "start_date": "2026-01-03",
    "end_date": "2027-01-03",
    "monthly_rent": 45000,
    "deposit": 90000
  }'
```

**Expected Response (201):**
```json
{
  "message": "Lease created successfully",
  "lease": {
    "id": "lease-uuid",
    "unit_id": "UNIT_ID",
    "tenant_id": "TENANT_ID",
    "start_date": "2026-01-03",
    "end_date": "2027-01-03",
    "monthly_rent": 45000,
    "deposit": 90000,
    "status": "active"
  }
}
```

**Save Lease ID:**
```
LEASE_ID = <id from response>
```

---

## Step 10: Create Rent Invoice (Landlord)

```bash
curl -X POST http://127.0.0.1:5000/api/rent-invoices \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer LANDLORD_TOKEN" \
  -d '{
    "unit_id": "UNIT_ID",
    "landlord_id": "LANDLORD_ID",
    "tenant_id": "TENANT_ID",
    "lease_id": "LEASE_ID",
    "invoice_date": "2026-01-03",
    "invoice_amount": 45000,
    "status": "pending"
  }'
```

**Expected Response (201):**
```json
{
  "message": "Invoice created successfully",
  "invoice": {
    "id": "invoice-uuid",
    "unit_id": "UNIT_ID",
    "invoice_amount": 45000,
    "status": "pending",
    "invoice_date": "2026-01-03"
  }
}
```

**Save Invoice ID:**
```
INVOICE_ID = <id from response>
```

---

## Step 11: Create Payment

```bash
curl -X POST http://127.0.0.1:5000/api/payments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TENANT_TOKEN" \
  -d '{
    "lease_id": "LEASE_ID",
    "invoice_id": "INVOICE_ID",
    "amount": 45000,
    "due_date": "2026-02-03",
    "payment_reference": "MPESA123456",
    "payment_method": "mpesa"
  }'
```

**Expected Response (201):**
```json
{
  "message": "Payment created successfully",
  "payment": {
    "id": "payment-uuid",
    "amount": 45000,
    "status": "pending",
    "payment_method": "mpesa"
  }
}
```

**Save Payment ID:**
```
PAYMENT_ID = <id from response>
```

---

## Step 12: Create Maintenance Request (Tenant)

```bash
curl -X POST http://127.0.0.1:5000/api/maintenance \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TENANT_TOKEN" \
  -d '{
    "unit_id": "UNIT_ID",
    "title": "Leaking sink",
    "description": "Water leaking under sink in kitchen"
  }'
```

**Expected Response (201):**
```json
{
  "message": "Maintenance request created successfully",
  "request": {
    "id": "maint-uuid",
    "unit_id": "UNIT_ID",
    "tenant_id": "TENANT_ID",
    "title": "Leaking sink",
    "description": "Water leaking under sink in kitchen",
    "status": "pending"
  }
}
```

**Save Maintenance Request ID:**
```
MAINT_ID = <id from response>
```

---

## Step 13: Update Maintenance Status (Landlord)

```bash
curl -X PUT http://127.0.0.1:5000/api/maintenance/MAINT_ID \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer LANDLORD_TOKEN" \
  -d '{
    "status": "in-progress"
  }'
```

**Expected Response (200):**
```json
{
  "message": "Request updated successfully",
  "request": {
    "id": "MAINT_ID",
    "status": "in-progress"
  }
}
```

---

## Step 14: Send Notification (Landlord to Tenant)

```bash
curl -X POST http://127.0.0.1:5000/api/notifications \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer LANDLORD_TOKEN" \
  -d '{
    "recipient_user_id": "TENANT_ID",
    "message": "Your maintenance request is being handled"
  }'
```

**Expected Response (201):**
```json
{
  "message": "Notification sent successfully",
  "notification": {
    "id": "notif-uuid",
    "user_id": "LANDLORD_ID",
    "recipient_user_id": "TENANT_ID",
    "message": "Your maintenance request is being handled",
    "is_read": false
  }
}
```

---

## Step 15: Get Notifications (Tenant)

```bash
curl http://127.0.0.1:5000/api/notifications \
  -H "Authorization: Bearer TENANT_TOKEN"
```

**Expected Response (200):**
```json
[
  {
    "id": "notif-uuid",
    "message": "Your maintenance request is being handled",
    "is_read": false,
    "created_at": "2026-01-03T..."
  }
]
```

---

## Step 16: Mark Notification as Read (Tenant)

```bash
curl -X PUT http://127.0.0.1:5000/api/notifications/notif-uuid/read \
  -H "Authorization: Bearer TENANT_TOKEN"
```

**Expected Response (200):**
```json
{
  "message": "Notification marked as read",
  "notification": {
    "id": "notif-uuid",
    "is_read": true
  }
}
```

---

## Summary of Variables to Save

Keep track of these for testing:

```bash
ADMIN_ID = aef4166f-7b87-4d72-872f-ae63d37aba28
ADMIN_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc2NzQzNTA0OSwianRpIjoiYzViNDgyMTktZmQwYi00ZGYzLWFjNzgtZDhmODMyYWNmZjEzIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6ImFlZjQxNjZmLTdiODctNGQ3Mi04NzJmLWFlNjNkMzdhYmEyOCIsIm5iZiI6MTc2NzQzNTA0OSwiY3NyZiI6IjQ1M2ViOTNlLTI0YWMtNDI0OC1iYmYzLWJjZDk2NGEyYTFlYyIsImV4cCI6MTc2NzQzNTk0OX0.qgKDyEpukhoiVjrNtoSeEjRRX41QeQAaTrNn1dm6vYg"

LANDLORD_ID = "acfd1cc9-b77b-4def-87b0-59eb21432ea6"
LANDLORD_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc2NzQzNTEwMCwianRpIjoiNzg4MGMwMDktMjI5My00Mjg3LTlmNmYtMmUyYzc5ZGYxYjg3IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6ImFjZmQxY2M5LWI3N2ItNGRlZi04N2IwLTU5ZWIyMTQzMmVhNiIsIm5iZiI6MTc2NzQzNTEwMCwiY3NyZiI6ImFlYTJjMGQxLTk5OWQtNDA1Ni1hYmUyLTQxZDY0YjBjNDQ0MSIsImV4cCI6MTc2NzQzNjAwMH0.1JGXhFZkx05WScQSM8W-PY4tb692CvERGsVCNabskMU"

TENANT_ID = "0fcd1066-4c5f-489e-aab9-4f727c363106"
TENANT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc2NzQzNTEyOCwianRpIjoiZDYyZTMzOGItNTc1OC00MjU1LTk5ZTctMGJmNzgyNGQ1M2Q0IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjBmY2QxMDY2LTRjNWYtNDg5ZS1hYWI5LTRmNzI3YzM2MzEwNiIsIm5iZiI6MTc2NzQzNTEyOCwiY3NyZiI6ImU3MDFjYmFhLWQwMzktNGVhMy04NjNiLTA1YjUwMzJiOGFiMyIsImV4cCI6MTc2NzQzNjAyOH0.7nvSIu7MTg9N5CsARf2YygKSTQNcPgXaKFKMMTN3mWw"

PROPERTY_ID = ""
UNIT_ID = ""
LEASE_ID = ""
INVOICE_ID = ""
PAYMENT_ID = ""
MAINT_ID = ""
```

---

## Error Handling Examples

### 401 Unauthorized (Missing Token)
```bash
curl http://127.0.0.1:5000/api/properties -H "Content-Type: application/json"
```

### 403 Forbidden (Insufficient Permissions)
```bash
# Tenant trying to create property
curl -X POST http://127.0.0.1:5000/api/properties \
  -H "Authorization: Bearer TENANT_TOKEN" \
  -d '{"name": "Test", ...}'
```

### 404 Not Found
```bash
curl http://127.0.0.1:5000/api/properties/invalid-id
```

---

**Start from Step 1 and work through each step sequentially!**
