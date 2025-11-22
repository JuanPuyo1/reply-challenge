# Phase 2: Doctor Recommendations

## Overview

Phase 2 implements the doctor recommendation system that processes information from an external agent and displays personalized specialist matches with booking capabilities.

---

## Architecture

```
Phase 1 (Triage) → Phase 2 (Doctor Matching)
       ↓
User Submission → AI Analysis → [External Agent] → Doctor Recommendation → Booking
```

---

## Implementation

### 1. **DoctorRecommendationsView** (`core/views.py`)

**Purpose:** Process and display doctor recommendation data from external agent

**Key Features:**
- Receives doctor data in JSON format from external agent
- Formats data as full text for logging/processing
- Passes structured data to template for display

**Mock Data Structure:**
```json
{
    "status": "success",
    "matched": true,
    "doctor": {
        "name": "Dr. Elena Martinez",
        "title": "Clinical Psychologist, PhD",
        "specialization": "Cognitive Behavioral Therapy (CBT)...",
        "license": "PSY-12345-CA",
        "experience_years": 12,
        "photo_url": "...",
        "bio": "...",
        "languages": ["English", "Spanish"],
        "ratings": {
            "average": 4.9,
            "total_reviews": 127
        },
        "education": [...],
        "certifications": [...]
    },
    "availability": {
        "next_available": "Tuesday, November 26, 2025",
        "available_slots": [
            {
                "date": "2025-11-26",
                "day": "Tuesday",
                "time": "10:00 AM",
                "duration_minutes": 50,
                "session_type": "Initial Consultation",
                "price": "$120"
            }
        ]
    },
    "match_reasoning": "Based on your symptoms...",
    "why_this_doctor": [
        "Specializes in academic stress...",
        "Expert in CBT techniques...",
        "..."
    ]
}
```

---

## Integration with External Agent

### Current Implementation (Mock Data)
```python
# In DoctorRecommendationsView.get()
doctor_recommendation = {
    # Mock JSON data
}
```

### Future Implementation (Real Agent)
```python
# Connect to external agent API
def get(self, request):
    submission_id = request.session.get('triage_data', {}).get('submission_id')
    
    # Call external agent
    response = requests.post(
        'https://external-agent-api.com/match-doctor',
        json={'submission_id': submission_id}
    )
    doctor_recommendation = response.json()
    
    # Process and display
    return render(request, 'core/doctor_recommendations.html', {
        'doctor_recommendation': doctor_recommendation,
        ...
    })
```

---

## Template Features (`doctor_recommendations.html`)

### Visual Components:

1. **Doctor Profile Card**
   - Beautiful gradient header
   - Profile photo
   - Name, title, ratings
   - Experience badge

2. **Specialization Section**
   - Clear display of expertise area

3. **About Section**
   - Comprehensive bio

4. **Match Reasoning**
   - Why this doctor is perfect for the user
   - Bullet points of key reasons

5. **Education & Certifications**
   - Collapsible section
   - Full credentials display

6. **Availability Grid**
   - Visual time slot cards
   - Date, time, price
   - Session type

7. **Booking Button**
   - Large, prominent call-to-action
   - Opens email with pre-filled booking request
   - Gradient styling with hover effect

8. **Full Text View**
   - Collapsible section
   - Shows complete recommendation as received from agent
   - Useful for debugging/verification

---

## User Flow

```
1. User completes health assessment
        ↓
2. Clicks "View Doctor Recommendations"
        ↓
3. System retrieves submission from session
        ↓
4. [External Agent processes and returns doctor match]
        ↓
5. DoctorRecommendationsView formats the data
        ↓
6. Beautiful template displays doctor profile
        ↓
7. User reviews doctor information
        ↓
8. User clicks "Book Appointment" button
        ↓
9. Email client opens with booking request
```

---

## Data Flow

### Phase 1 → Phase 2 Connection

**Stored in Session:**
```python
request.session['triage_data'] = {
    'submission_id': 123,
    'email': 'user@example.com',
    'symptoms': '...',
    'analysis': {...}
}
```

**Retrieved in Phase 2:**
```python
triage_data = request.session.get('triage_data', {})
submission_id = triage_data.get('submission_id')
```

---

## Full Text Formatting

The system creates a complete text representation for logging/processing:

```
======================================================================
DOCTOR RECOMMENDATION - PHASE 2
======================================================================

Status: SUCCESS
Match Found: Yes

----------------------------------------------------------------------
RECOMMENDED SPECIALIST
----------------------------------------------------------------------
Name: Dr. Elena Martinez
Title: Clinical Psychologist, PhD
Specialization: Cognitive Behavioral Therapy (CBT)...
...

----------------------------------------------------------------------
AVAILABILITY
----------------------------------------------------------------------
Next Available: Tuesday, November 26, 2025

Available Time Slots:
• Tuesday, 2025-11-26 at 10:00 AM - Initial Consultation ($120)
...

----------------------------------------------------------------------
MATCH REASONING
----------------------------------------------------------------------
Based on your symptoms of sleep disturbance related to exam stress...

----------------------------------------------------------------------
WHY THIS DOCTOR
----------------------------------------------------------------------
✓ Specializes in academic stress and performance anxiety
✓ Expert in CBT techniques proven effective for your symptoms
...

======================================================================
END OF RECOMMENDATION
======================================================================
```

---

## Booking System

### Current Implementation (Email-based)
- Button opens user's email client
- Pre-filled with:
  - Recipient: User's email (for now)
  - Subject: Book Appointment with [Doctor Name]
  - Body: Basic booking request

### Future Enhancement
- Direct booking API integration
- Calendar sync
- Payment processing
- Confirmation emails
- SMS reminders

---

## Styling Highlights

- **Gradient Header:** Purple gradient for visual appeal
- **Card-based Layout:** Clean, modern design
- **Responsive Grid:** Works on mobile and desktop
- **Hover Effects:** Booking button has smooth animation
- **Color Coding:** Green for success, purple for actions
- **Collapsible Sections:** Reduces clutter, improves UX

---

## Testing

### Manual Testing Steps:

1. **Complete Assessment:**
   ```
   Navigate to /
   Fill out form
   Submit
   ```

2. **View Recommendations:**
   ```
   Click "View Doctor Recommendations"
   Verify doctor profile displays
   Check all sections render correctly
   ```

3. **Test Booking:**
   ```
   Click "Book Appointment" button
   Verify email client opens
   Check pre-filled content
   ```

4. **View Full Text:**
   ```
   Expand "View Full Recommendation Text"
   Verify formatted text displays
   ```

---

## External Agent Integration (To Be Implemented)

### Expected Agent Behavior:

**Input to Agent:**
- Submission ID
- User's full text content (from Phase 1)
- Symptoms analysis
- Category and urgency

**Output from Agent:**
- JSON with doctor recommendation
- Formatted exactly as shown in mock data structure
- Must include all required fields

### Integration Points:

1. **API Endpoint:** `/api/match-doctor/`
2. **Method:** POST
3. **Headers:** `Content-Type: application/json`
4. **Request Body:**
   ```json
   {
       "submission_id": 123,
       "full_text_content": "...",
       "category": "anxiety",
       "urgency": "medium"
   }
   ```
5. **Response:** Doctor recommendation JSON

---

## Next Steps

### For Production:

1. **Connect Real Agent:**
   - Replace mock data with actual API call
   - Add error handling
   - Implement retry logic

2. **Enhance Booking:**
   - Real calendar integration
   - Payment processing
   - Automated confirmations

3. **Add Features:**
   - Multiple doctor options
   - Comparison view
   - User reviews
   - Video consultation option

4. **Improve UX:**
   - Add loading states
   - Progress indicators
   - Better error messages
   - Mobile optimization

---

## Files Modified

- ✅ `core/views.py` - Added `DoctorRecommendationsView`
- ✅ `core/urls.py` - Added route `/doctor-recommendations/`
- ✅ `core/templates/core/doctor_recommendations.html` - Beautiful template
- ✅ `core/templates/core/health.html` - Added navigation button

---

## Summary

Phase 2 successfully processes doctor recommendation data from an external agent and presents it in a beautiful, user-friendly interface with booking capabilities. The system is ready to integrate with a real doctor-matching agent by simply replacing the mock data with actual API calls.

