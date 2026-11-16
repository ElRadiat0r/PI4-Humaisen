
# HUMAISEN – Agenda and Matching API

## 1. Overview

This API manages expert availability, appointments and expert matching.

Base URL:
`http://127.0.0.1:8000/api/`

Authentication is required for all endpoints.

## 2. Availability endpoints

### GET /availability/

Returns the list of availability slots.

Optional query parameter:
- `expert_id`: filter slots by expert.

Example:
`GET /api/availability/?expert_id=1`

### POST /availability/

Creates an availability slot.

Request:
```json
{
  "expert_id": 1,
  "starts_at": "2026-12-01T10:00:00+01:00",
  "ends_at": "2026-12-01T11:00:00+01:00",
  "is_available": true,
  "note": "Morning availability"
}
```

### POST /availability/{id}/block/

Blocks an availability slot.

A booked slot cannot be blocked.

### POST /availability/{id}/unblock/

Makes a previously blocked slot available again.

## 3. Appointment endpoints

### GET /appointments/

Returns appointments.

Optional query parameters:
- `expert_id`
- `project_id`

### POST /appointments/

Creates an appointment.

Request:
```json
{
  "project_id": 10,
  "expert_id": 1,
  "consultation_id": 5,
  "slot": 1
}
```

The selected slot must:
- Exist.
- Be available.
- Belong to the selected expert.
- Not already have a confirmed appointment.

Success: `201 Created`

Conflict: `409 Conflict`

### POST /appointments/{id}/cancel/

Cancels a confirmed appointment.

Request:
```json
{
  "reason": "The client is unavailable"
}
```

### POST /appointments/{id}/reschedule/

Changes the appointment's time slot.

Request:
```json
{
  "slot_id": 2
}
```

The new slot must be available and belong to the same expert.

## 4. Matching V1

### POST /matching/

Ranks experts according to required skills, availability, verification and experience.

Request:
```json
{
  "required_skills": ["Python", "Django"],
  "starts_at": "2026-12-01T10:00:00+01:00",
  "ends_at": "2026-12-01T11:00:00+01:00",
  "candidates": [
    {
      "expert_id": 1,
      "skills": ["Python", "Django", "SQL"],
      "is_verified": true,
      "experience_years": 5
    },
    {
      "expert_id": 2,
      "skills": ["Python"],
      "is_verified": true,
      "experience_years": 3
    }
  ]
}
```

### Mandatory filters

An expert is selected only if:
- They have all the required skills.
- They have an available slot covering the requested period.

### Weighted score

| Criterion | Points |
|---|---:|
| Required skills match | 70 |
| Verified expert | 20 |
| Experience | Up to 10 |
| Maximum | 100 |

Experts are sorted by descending score.

The API returns an explanation for each selected expert.

Example response:
```json
{
  "results": [
    {
      "expert_id": 1,
      "score": 95,
      "justification": "All required skills match; availability confirmed; expert verified."
    }
  ]
}
```

## 5. HTTP status codes

| Status | Meaning |
|---|---|
| 200 | Request successful |
| 201 | Resource created |
| 400 | Invalid request |
| 401 | Authentication required |
| 404 | Resource not found |
| 409 | Booking conflict |

## 6. Important implementation notes

- All endpoints require authentication.
- Appointment creation checks availability on the server.
- A database constraint prevents multiple confirmed appointments for the same slot.
- The current Matching V1 receives candidate profiles in the request.
- Expert, project and consultation IDs are temporary integer references pending integration with the shared team models.
