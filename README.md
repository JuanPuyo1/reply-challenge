# AI Triage Specialist - Mental Health Appointment System

## Project Overview

The AI Triage Specialist is an intelligent mental health appointment booking system that uses a multi-agent architecture to match patients with the most appropriate mental health specialists based on their symptoms, location, and preferences. The system combines natural language processing, intelligent matching algorithms, and automated scheduling to streamline the mental health care access process.

## System Architecture

The application follows a three-phase agentic workflow:

### Phase 1: Intelligent Intake Interview
A dynamic form that adapts to user input in real-time, collecting essential patient information including symptoms, clinical history, and contextual details. The form uses AI to generate personalized prompts based on initial symptoms, creating a conversational experience while maintaining a structured data collection approach.

### Phase 2: Specialist Matching
An AI agent analyzes the patient's comprehensive profile and matches them with the most suitable mental health specialist from a database. The matching algorithm considers:
- Symptom analysis and categorization
- Geographic proximity between patient and specialist
- Specialist expertise and subspecialties
- Urgency assessment
- Treatment approach compatibility

### Phase 3: Automated Scheduling
An intelligent scheduling agent that processes the matched specialist's availability and the patient's preferences to find the optimal appointment slot. The system considers urgency levels and time preferences to automatically select and confirm appointments.

## Key Features

### Dynamic Form Generation
- AI-powered placeholder generation that adapts based on user symptoms
- Real-time AJAX interactions for seamless user experience
- Clinical history file upload support
- Address-based location matching

### Safety Guardrails
- Automatic detection of crisis situations (self-harm, suicide ideation)
- Immediate display of crisis hotlines and emergency resources
- Urgency level assessment for appropriate care prioritization

### Intelligent Matching
- Dual-scoring system combining expertise match and location proximity
- GPT-powered location analysis for accurate distance estimation
- Comprehensive patient profile analysis
- Personalized recommendations for each matched specialist

### Automated Appointment Booking
- One-click booking process
- Automatic schedule generation from specialist availability rules
- Time preference filtering (morning, afternoon, evening)
- Urgency-based date prioritization
- Email confirmation system via AWS Lambda

## Technical Stack

### Backend
- Django 5.0.1
- Python 3.x
- OpenAI GPT-4o-mini for AI agents
- LangChain for AI orchestration
- Pandas for data management

### Frontend
- Django Templates
- Vanilla JavaScript (AJAX)
- Minimalist CSS with inline styles
- Responsive design principles

### AI Services
- OpenAI API for natural language processing
- Custom multi-agent architecture
- GPT-powered location proximity analysis

### External Services
- AWS Lambda for email notifications
- Excel/CSV database for specialist information

## Installation

### Prerequisites
```
Python 3.8+
pip package manager
OpenAI API key
```

### Setup Instructions

1. Clone the repository:
```bash
git clone <repository-url>
cd replyhealth
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
Create a `.env` file in the project root:
```
OPENAI_API_KEY=your_openai_api_key_here
```

5. Run database migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

6. Prepare specialist database:
Place your `Specialist_EN.xlsx` file in the `static/` directory with the following columns:
- Name
- Specialist
- Subspecialty
- Address
- Phone
- Email
- Available Hours
- Modality

7. Start the development server:
```bash
python manage.py runserver
```

8. Access the application at `http://localhost:8000`

## Project Structure

```
replyhealth/
├── core/
│   ├── forms.py                    # HealthForm and AvailabilityPreferenceForm
│   ├── models.py                   # TriageSubmission model
│   ├── views.py                    # Main view logic for all phases
│   ├── urls.py                     # URL routing
│   ├── admin.py                    # Django admin configuration
│   ├── services/
│   │   ├── gptapi.py              # Phase 1: TriageAgent for intake
│   │   ├── mental_health_agent.py # Phase 2: Specialist matching agent
│   │   └── scheduler.py           # Phase 3: Appointment scheduling agent
│   └── templates/core/
│       ├── health.html            # Phase 1: Intake form
│       ├── doctor_recommendations.html  # Phase 2: Matched specialist
│       └── availability_preference.html # Phase 3: Booking confirmation
├── replyhealth/
│   ├── settings.py                # Django configuration
│   ├── urls.py                    # Root URL configuration
│   └── wsgi.py                    # WSGI configuration
├── static/
│   └── Specialist_EN.xlsx         # Specialist database
├── mental_health_agent_result.json # Generated match results
├── requirements.txt               # Python dependencies
├── manage.py                      # Django management script
└── README.md                      # Project documentation
```

## User Workflow

### Step 1: Health Assessment
1. User visits the application homepage
2. Fills out comprehensive health form:
   - Email address
   - Physical address (country, city, street)
   - Primary symptoms
   - Optional clinical history file upload
   - Additional context (dynamically prompted based on symptoms)
3. System performs initial triage analysis
4. Safety guardrails check for crisis situations

### Step 2: View Recommendations
1. System processes submission with AI analysis
2. Mental Health Agent matches patient with optimal specialist
3. Match considers expertise alignment and geographic proximity
4. User views matched specialist profile:
   - Name and credentials
   - Specialization and subspecialty
   - Contact information and address
   - Match reasoning explanation
   - Personalized preparation recommendations

### Step 3: Book Appointment
1. User selects time preference (morning, afternoon, evening)
2. Indicates urgency level
3. Clicks "Book Appointment & Send Confirmation"
4. Scheduler automatically:
   - Reads specialist's availability schedule
   - Filters by urgency (first 3 days vs. later dates)
   - Filters by time preference
   - Selects optimal appointment slot
   - Sends confirmation email to doctor
5. User receives immediate confirmation with appointment details

## Multi-Agent System Details

### Agent 1: Triage Agent (gptapi.py)
**Purpose:** Initial symptom analysis and data collection enhancement

**Functions:**
- `generate_dynamic_placeholder()`: Creates contextual prompts
- `analyze_symptoms()`: Performs quick triage for urgency and safety
- `process_full_submission()`: Deep clinical analysis and documentation

**Output:** Unified text document with patient data and AI analysis

### Agent 2: Mental Health Agent (mental_health_agent.py)
**Purpose:** Specialist matching based on comprehensive patient profile

**Functions:**
- `_analyze_user_concerns()`: Extracts keywords and categorizes concerns
- `_calculate_location_proximity()`: GPT-powered distance assessment
- `_match_specialist()`: Dual-scoring algorithm for optimal match
- `_generate_recommendations()`: Personalized pre-appointment guidance

**Output:** JSON file with matched specialist and recommendations

### Agent 3: Scheduler Agent (scheduler.py)
**Purpose:** Automated appointment scheduling

**Functions:**
- `build_schedule()`: Parses availability rules into calendar
- `collect_urgency()`: Filters dates by urgency level
- `filter_by_time_preference()`: Applies morning/afternoon/evening filters
- `select_best_appointment()`: Chooses optimal slot
- `run_automated_scheduling()`: Orchestrates entire scheduling process

**Output:** Final appointment JSON with confirmed date and time

## Data Models

### TriageSubmission
Stores complete patient intake data in unified text format:
- `email`: Patient contact email
- `full_text_content`: Combined user input and AI analysis
- `processed`: Processing status flag
- `created_at`: Submission timestamp
- `updated_at`: Last modification timestamp

## API Integration

### OpenAI GPT-4o-mini
Used across all three agents for:
- Natural language understanding
- Contextual placeholder generation
- Clinical analysis and categorization
- Location proximity assessment
- Intelligent matching decisions

### AWS Lambda Email Service
Endpoint: `https://w5ptej3v39.execute-api.us-east-1.amazonaws.com/Contact`

Sends appointment confirmation emails with:
- Doctor name and email
- Patient name
- Appointment date and time
- Patient symptoms summary
- Additional notes

## Configuration

### Environment Variables
```
OPENAI_API_KEY=<your-openai-api-key>
```

### Specialist Database Format
Excel file with columns:
- Name: Full name of specialist
- Specialist: Primary specialization
- Subspecialty: Specific expertise area
- Address: Physical address
- Phone: Contact phone number
- Email: Contact email
- Available Hours: Format "Mon-Fri 09:00-17:00; Sat 10:00-14:00"
- Modality: In-Person, Virtual, or Hybrid

### Schedule Format Rules
```
Day ranges: Mon-Wed, Thu-Fri
Single days: Sat, Sun
Time ranges: 09:00-17:00 (24-hour format)
Multiple rules: Separated by semicolons

Example: "Mon-Wed 14:00-18:00; Sat 09:00-12:00"
```

## Security Considerations

### API Key Management
- Store OpenAI API key in environment variables
- Never commit API keys to version control
- Use `.env` files for local development
- Configure secure key storage for production

### Data Privacy
- Patient health information stored in database
- Session-based data management for active bookings
- No client-side storage of sensitive health data

### Crisis Response Protocol
Hard-coded crisis detection for:
- Self-harm mentions
- Suicide ideation
- Intent to harm others
- Immediate display of emergency resources

## Development Notes

### Adding New Specialists
1. Update `Specialist_EN.xlsx` in `static/` directory
2. Ensure all required columns are populated
3. Use standard schedule format
4. Restart application to reload database

### Modifying AI Prompts
Agent prompts are located in:
- `core/services/gptapi.py` - Lines 34-46, 78-86, 139-151
- `core/services/mental_health_agent.py` - Lines 209-228, 261-279
- `core/services/scheduler.py` - Lines 488-518

### Customizing Email Templates
Email content is generated in `scheduler.py`:
- Function: `email_send()` (Lines 313-339)
- Customize message format as needed

## Testing

### Manual Testing Checklist
1. Submit health form with various symptom types
2. Verify dynamic placeholder generation
3. Test crisis detection keywords
4. Confirm specialist matching with different locations
5. Verify scheduling with urgent and non-urgent cases
6. Test email delivery
7. Check all three time preference options

### Test Scenarios
- **Scenario 1**: Urgent case, morning preference
- **Scenario 2**: Non-urgent case, afternoon preference
- **Scenario 3**: Crisis keywords trigger safety response
- **Scenario 4**: Different geographic locations for proximity matching

## Troubleshooting

### Common Issues

**Issue**: No specialists found
**Solution**: Verify `Specialist_EN.xlsx` exists in `static/` directory and has correct format

**Issue**: Email not sending
**Solution**: Check AWS Lambda endpoint availability and network connection

**Issue**: OpenAI API errors
**Solution**: Verify API key in `.env` file and check API quota/rate limits

**Issue**: No available appointment slots
**Solution**: Check specialist's schedule format and ensure dates are in future

## Production Deployment

### Recommendations
1. Use environment-based configuration
2. Implement proper database (PostgreSQL recommended)
3. Set up secure session management
4. Configure HTTPS for all endpoints
5. Implement rate limiting for API calls
6. Set up logging and monitoring
7. Create backup strategy for patient data
8. Implement HIPAA-compliant data handling

## Future Enhancements

Potential improvements for the system:
- Multi-language support
- Patient portal for appointment management
- Real-time specialist availability updates
- Integration with electronic health records
- Video consultation scheduling
- SMS notifications
- Patient feedback and rating system
- Analytics dashboard for specialists

## License

This project is developed for educational and research purposes.

## Contact

For questions or support regarding this system, please contact the development team.
