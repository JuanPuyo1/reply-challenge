# Scheduler Integration - Complete Implementation

## Overview
This document describes the integration of the `scheduler.py` agent into the appointment booking flow.

## Changes Made

### 1. New Form: `AvailabilityPreferenceForm` (`core/forms.py`)
Added a new form to collect user's availability preferences:
- **Time Preference**: Choice field with options for morning, afternoon, or evening
- **Is Urgent**: Boolean checkbox to indicate if the appointment is urgent

### 2. New Views (`core/views.py`)

#### `AvailabilityPreferenceView`
- **Purpose**: Display form to collect user's time preference and urgency
- **GET**: Shows the availability preference form with doctor information
- **POST**: Processes the form and stores preferences in session, then redirects to `AvailabilityView`

#### Updated `AvailabilityView`
- **Purpose**: Run the scheduler agent and display the best available appointment
- **Process**:
  1. Retrieves data from session (triage data, doctor recommendation, availability preference)
  2. Reads `mental_health_agent_result.json` for specialist schedule
  3. Builds doctor's schedule using `build_schedule()` from `scheduler.py`
  4. Prepares initial JSON for scheduler with:
     - Doctor name, email
     - Patient name (from email), symptoms
     - Doctor schedule, time preference, urgency
  5. Runs scheduler (currently using mock data as placeholder)
  6. Stores booking data in session
  7. Displays booking details in `best_match_booking.html`

#### New `BookAppointmentView`
- **Purpose**: Handle final appointment booking and send confirmation email
- **Process**:
  1. Retrieves booking data from session
  2. Prepares final JSON with all booking details
  3. Calls `email_send()` function from `scheduler.py`
  4. Returns JSON response indicating success/failure

### 3. Updated URLs (`core/urls.py`)
Added three new URL patterns:
- `availability-preference/` → `AvailabilityPreferenceView`
- `availability/` → `AvailabilityView` (existing)
- `book-appointment/` → `BookAppointmentView`

### 4. New Template: `availability_preference.html`
- Clean, minimalist form to collect time preference and urgency
- Shows doctor information for context
- Breadcrumb navigation
- Responsive design matching existing templates

### 5. Updated `doctor_recommendations.html`
- Changed "Check Best Availability" button to link to `availability_preference` instead of directly to `availability`

### 6. Updated `best_match_booking.html`
- Replaced mailto link with AJAX button
- When "Book Appointment" is clicked:
  1. Button shows "Sending..." state
  2. Makes POST request to `/book-appointment/`
  3. `email_send()` function from `scheduler.py` is triggered
  4. Shows success/error message
  5. Button updates to "Appointment Booked!" on success
- Added CSRF token for AJAX request
- Added status message area for feedback

## User Flow

### Complete Booking Process (SIMPLIFIED):
1. **Health Assessment** (`health.html`)
   - User fills out symptoms, email, address
   - System analyzes with `gptapi.py` agent
   - System saves `TriageSubmission` to database
   
2. **Doctor Recommendations** (`doctor_recommendations.html`)
   - User clicks "View Doctor Recommendations"
   - System uses `mental_health_agent.py` to match with specialist (proximity + expertise)
   - System saves result to `mental_health_agent_result.json`
   - Displays matched doctor details
   
3. **Book Appointment** (`availability_preference.html`) **[SIMPLIFIED]**
   - User clicks "Check Best Availability"
   - User selects time preference (morning/afternoon/evening)
   - User indicates if urgent
   - User clicks "Book Appointment & Send Confirmation"
   - **System does everything automatically:**
     - Reads `mental_health_agent_result.json`
     - Builds doctor's schedule from JSON
     - Runs `scheduler.py` agent (automated, no conversation)
     - Finds best available slot based on urgency + time preference
     - Sends confirmation email via `email_send()`
     - Shows success message with booking details on same page
   
4. **Done!**
   - User sees confirmation with date/time
   - Email sent to doctor
   - Can go back to home

## Data Flow

### Session Data Structure:
```python
request.session = {
    'triage_data': {
        'email': 'user@example.com',
        'address': 'Italy, Turin, Via Roma 15',
        'symptoms': 'User symptoms...',
        'additional_context': 'Additional info...',
        'submission_id': 123,
        'analysis': {...}
    },
    'doctor_recommendation': {
        'doctor': {...},
        'specialist': {
            'schedule': 'Mon-Fri 09:00-17:00',
            ...
        },
        'match_reasoning': '...'
    },
    'availability_preference': {
        'time_preference': 'morning',
        'is_urgent': False
    },
    'booking_data': {
        'selected_date': '2025-11-25',
        'selected_time': '10:30 AM',
        'doctor': {...},
        'patient_email': 'user@example.com',
        ...
    }
}
```

## Scheduler Integration Points

### 1. Mental Health Agent Output (Saved to JSON):
```python
# mental_health_agent_result.json
{
  "patient_info": {
    "name": "john",
    "age": "Not provided",
    "address": "Italy, Turin, Via Roma 15",
    "gender": "Not provided"
  },
  "urgency_level": "low",
  "specialist": {
    "name": "Dr. Sarah Johnson",
    "expertise": "Cognitive-Behavioral Therapy",
    "location": "Via Roma 25, Turin",
    "phone_number": "+39 345 112233 4",
    "email": "sarah.johnson@example.com",
    "schedule": "Mon-Fri 09:00-17:00",  # <-- Used by scheduler
    "modality": "Virtual"
  }
}
```

### 2. Input to Scheduler (Built from JSON + User Preference):
```python
initial_appointment_json = {
    "doctor_name": "Dr. Sarah Johnson",  # From JSON
    "doctor_email": "sarah.johnson@example.com",  # From JSON
    "patient_name": "john",  # From session
    "symptoms": "Anxiety in social situations",  # From session
    "doctor_schedule": {...},  # Built from JSON specialist.schedule
    "is_urgent": False,  # From user form
    "time_preference": "morning",  # From user form
}
```

### 3. Scheduler Processing (Automated):
```python
# Step 1: Filter by urgency
if is_urgent:
    use first 3 days
else:
    use days after first 3

# Step 2: Filter by time preference  
filter_by_time_preference("morning")  # 6:00-12:00

# Step 3: Select best slot
select_best_appointment(available_slots)
```

### 4. Output from Scheduler:
```python
final_appointment = {
    "doctor_name": "Dr. Sarah Johnson",
    "doctor_email": "sarah.johnson@example.com",
    "patient_name": "john",
    "symptoms": "Anxiety in social situations",
    "selected_date": "2025-11-25",
    "selected_time": "10:30 AM",
    "patient_notes": "",
    "status": "confirmed",
    "created_at": "2025-11-22T13:42:39.991778",
    "conversation_complete": True
}
```

### 5. Email Sent Immediately:
```python
email_send(final_appointment)
# Sends to doctor's email via AWS Lambda
```

## Email Integration

The `email_send()` function from `scheduler.py` is now triggered **only when the user clicks "Book Appointment"**, not automatically.

### Email Function Input:
```python
final_json = {
    "doctor_name": "Dr. Sarah Johnson",
    "doctor_email": "sarah.johnson@example.com",
    "patient_name": "john",
    "symptoms": "Anxiety in social situations",
    "selected_date": "2025-11-25",
    "selected_time": "10:30 AM",
    "patient_notes": ""
}
```

## TODO: Scheduler Implementation

The current `AvailabilityView` uses mock data for the scheduler output. To fully integrate:

1. **Automated Scheduler**: Modify `scheduler.py` to run without interactive conversation
   - Create a non-interactive version of `run_scheduling_conversation()`
   - Process time preference and urgency automatically
   - Return booking data without user prompts

2. **Integration Point** in `AvailabilityView`:
   ```python
   # Replace this:
   booking_data = {
       "selected_date": "2025-11-25",
       "selected_time": "05:30 PM",
       # ... mock data
   }
   
   # With this:
   from .services.scheduler import run_automated_scheduler
   booking_data = run_automated_scheduler(initial_appointment_json)
   ```

3. **Error Handling**: Add proper exception handling for scheduler failures

## Testing Checklist

- [ ] User can fill out health assessment form
- [ ] User sees doctor recommendation after submission
- [ ] User can click "Check Best Availability"
- [ ] User sees availability preference form
- [ ] User can select time preference and urgency
- [ ] User sees best available appointment
- [ ] User can click "Book Appointment"
- [ ] Confirmation email is sent successfully
- [ ] Success message is displayed to user
- [ ] Error handling works for email failures

## Files Modified

- `core/forms.py` - Added `AvailabilityPreferenceForm`
- `core/views.py` - Added 2 new views, updated `AvailabilityView`
- `core/urls.py` - Added 3 new URL patterns
- `core/templates/core/availability_preference.html` - New template
- `core/templates/core/doctor_recommendations.html` - Updated button link
- `core/templates/core/best_match_booking.html` - Updated to use AJAX for booking

## Files Created

- `SCHEDULER_INTEGRATION.md` - This documentation file

