# Phase 3: Availability & Booking System

## Overview
Phase 3 implements the final step of the patient journey - checking availability and booking an appointment with the recommended specialist.

---

## User Journey

```
Phase 1: Health Assessment
       ↓
Phase 2: Doctor Recommendation
       ↓
Phase 3: Availability & Booking ← YOU ARE HERE
```

---

## Implementation

### 1. **Button Added to Doctor Recommendations** (`doctor_recommendations.html`)

**Changed from:**
```html
<p style="color: #999; font-size: 0.9rem; margin-top: 1rem;">
    <em>(Availability checking feature coming soon)</em>
</p>
```

**To:**
```html
<a href="{% url 'core:availability' %}" 
   role="button" 
   style="margin-top: 1rem;">
    Check Best Availability
</a>
```

---

### 2. **AvailabilityView** (`core/views.py`)

**Processes booking data from external agent:**

**Mock Data Structure:**
```python
booking_data = {
    "selected_date": "2025-11-25",
    "selected_time": "05:30 PM",
    "patient_notes": "",
    "status": "confirmed",
    "created_at": "2025-11-22T13:42:39.991778",
    "conversation_complete": True,
    "doctor": {
        "name": "Dr. Luca Bianchi",
        "specialist": "Clinical Psychologist",
        "subspecialty": "Anxiety and Depression",
        "address": "Via Roma 25",
        "city": "Turin",
        "phone": "+39 345 112233 4",
        "email": "luca.bianchi@mail.com"
    },
    "patient_email": "user@example.com"
}
```

**Key Features:**
- Retrieves triage data from session
- Processes booking data (currently mock)
- Formats as full text for logging
- Passes to template for display

---

### 3. **Booking Template** (`best_match_booking.html`)

**Design Philosophy:** Minimal, clean, professional

**Features:**
- ✅ Status banner (confirmed/failed)
- ✅ Appointment details section
  - Date
  - Time
  - Patient notes (if any)
- ✅ Doctor information section
  - Name
  - Specialist & subspecialty
  - Address & city
  - Phone & email (clickable)
- ✅ Confirmation info
  - Email sent notification
  - Booking timestamp
- ✅ "Book Appointment" button
  - Opens email client
  - Pre-filled with appointment details
- ✅ Full text view (collapsible)
- ✅ Navigation links

**Styling:**
- No emojis ✓
- No crazy colors ✓
- Simple gray/white color scheme
- Clean borders and spacing
- Grid layout for data display

---

### 4. **URL Route** (`core/urls.py`)

**Added:**
```python
path('availability/', AvailabilityView.as_view(), name='availability'),
```

**Complete Flow:**
- `/` - Health assessment form
- `/doctor-recommendations/` - Doctor match
- `/availability/` - Booking confirmation

---

## Data Flow

### External Agent Integration Point

**Where to connect your agent:**

```python
# In AvailabilityView.get()

# Current (mock):
booking_data = {
    "selected_date": "2025-11-25",
    "selected_time": "05:30 PM",
    # ...
}

# Future (real agent):
import requests
response = requests.post(
    'YOUR_BOOKING_AGENT_API_URL',
    json={
        'doctor_id': doctor_id,
        'patient_email': patient_email,
        'symptoms': symptoms
    }
)
booking_data = response.json()
```

**Expected Response Format:**
```json
{
  "selected_date": "2025-11-25",
  "selected_time": "05:30 PM",
  "patient_notes": "",
  "status": "confirmed",
  "created_at": "2025-11-22T13:42:39.991778",
  "conversation_complete": true,
  "doctor": {
    "name": "Dr. Luca Bianchi",
    "specialist": "Clinical Psychologist",
    "subspecialty": "Anxiety and Depression",
    "address": "Via Roma 25",
    "city": "Turin",
    "phone": "+39 345 112233 4",
    "email": "luca.bianchi@mail.com"
  },
  "patient_email": "user@example.com"
}
```

---

## Full Text Output

The system generates a complete text representation:

```
======================================================================
APPOINTMENT BOOKING - PHASE 3
======================================================================

Status: CONFIRMED
Conversation Complete: Yes
Created At: 2025-11-22T13:42:39.991778

----------------------------------------------------------------------
APPOINTMENT DETAILS
----------------------------------------------------------------------
Selected Date: 2025-11-25
Selected Time: 05:30 PM
Patient Notes: None

----------------------------------------------------------------------
DOCTOR INFORMATION
----------------------------------------------------------------------
Name: Dr. Luca Bianchi
Specialist: Clinical Psychologist
Subspecialty: Anxiety and Depression
Address: Via Roma 25
City: Turin
Phone: +39 345 112233 4
Email: luca.bianchi@mail.com

----------------------------------------------------------------------
PATIENT CONTACT
----------------------------------------------------------------------
Email: user@example.com

======================================================================
END OF BOOKING
======================================================================
```

---

## Book Appointment Button

**Functionality:**
- Opens user's email client
- Pre-filled with:
  - **To:** Doctor's email
  - **Subject:** Appointment Confirmation - [Date] at [Time]
  - **Body:** Professional booking confirmation message with patient email

**Example Email:**
```
To: luca.bianchi@mail.com
Subject: Appointment Confirmation - 2025-11-25 at 05:30 PM

Dear Dr. Luca Bianchi,

I would like to confirm my appointment on 2025-11-25 at 05:30 PM.

Patient: user@example.com

Thank you.
```

---

## Design Specifications

### Color Palette
- **Background:** White (#fff) and Light Gray (#f5f5f5, #f9f9f9)
- **Text:** Dark Gray (#333) and Medium Gray (#666)
- **Borders:** Light Gray (#ddd)
- **Accent:** Green for confirmed status (#4caf50)
- **Button:** Dark Gray (#333)

### Typography
- **Headings:** 1.3rem, bold
- **Body:** Default size
- **Small text:** 0.85rem to 0.9rem

### Layout
- **Max width:** 700px (narrower than previous pages)
- **Grid:** 150px labels + 1fr content
- **Spacing:** Consistent 1rem to 2rem margins
- **Borders:** 1px solid, 4px accent borders

---

## Files Modified

- ✅ `core/views.py` - Added `AvailabilityView` with booking processing
- ✅ `core/urls.py` - Added `/availability/` route
- ✅ `core/templates/core/doctor_recommendations.html` - Added button
- ✅ `core/templates/core/best_match_booking.html` - Created booking template

---

## Testing Flow

1. **Start assessment:**
   ```
   http://localhost:8000/
   ```

2. **Complete form and submit**

3. **Click "View Doctor Recommendations"**

4. **Click "Check Best Availability"**

5. **View booking details:**
   - Confirm date/time displayed
   - Verify doctor information
   - Test "Book Appointment" button
   - Check email opens correctly

---

## Status Values

The system handles different booking statuses:

- **confirmed** - Appointment successfully booked (green banner)
- **pending** - Awaiting confirmation
- **failed** - Booking unsuccessful (yellow warning)
- **cancelled** - Appointment cancelled

Currently only "confirmed" is implemented in the mock data.

---

## Next Steps for Production

### 1. **Connect Real Booking Agent**
Replace mock data with actual API call to your booking agent

### 2. **Add Calendar Integration**
- iCal file generation
- Google Calendar "Add to Calendar" link
- Outlook calendar link

### 3. **SMS Notifications**
- Send SMS confirmation
- Reminder SMS before appointment

### 4. **Payment Processing** (if needed)
- Stripe/PayPal integration
- Booking deposit
- Cancellation policy

### 5. **Cancellation/Rescheduling**
- Add "Cancel Appointment" button
- Add "Reschedule" functionality
- Cancellation confirmation email

### 6. **Database Storage**
Create an `Appointment` model:
```python
class Appointment(models.Model):
    submission = models.ForeignKey(TriageSubmission)
    doctor_name = models.CharField(max_length=255)
    selected_date = models.DateField()
    selected_time = models.TimeField()
    status = models.CharField(max_length=20)
    patient_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

---

## Complete User Journey

```
1. User fills health assessment
        ↓
2. AI analyzes symptoms and creates report
        ↓
3. System matches with specialist (Dr. Bianchi)
        ↓
4. User views doctor profile
        ↓
5. User clicks "Check Best Availability"
        ↓
6. Booking agent finds best time slot
        ↓
7. User sees confirmation page
        ↓
8. User clicks "Book Appointment"
        ↓
9. Email client opens with booking details
        ↓
10. User sends email to confirm
```

---

## Summary

Phase 3 successfully completes the patient journey with:
- ✅ Availability checking (via external agent)
- ✅ Booking confirmation display
- ✅ Minimal, professional design
- ✅ Email-based appointment booking
- ✅ Full text logging for processing
- ✅ Clean navigation flow

The system is now a complete end-to-end AI-powered triage and booking platform! 🎉

