import os
import json
import requests
from openai import OpenAI
from datetime import datetime
from dotenv import load_dotenv
import argparse
from datetime import datetime, timedelta, time
import re


DAY_MAP = {
    "Mon": 0,
    "Tue": 1,
    "Wed": 2,
    "Thu": 3,
    "Fri": 4,
    "Sat": 5,
    "Sun": 6
}

TIME_RANGES = {
    "morning": (6, 12),
    "afternoon": (12, 18),
    "evening": (18, 23)
}

# Load environment variables from .env file
path_env = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=path_env)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Function definitions for the agent
tools = [
    {
        "type": "function",
        "function": {
            "name": "filter_by_time_preference",
            "description": "Filters the schedule based on time of day preference (morning, afternoon, or evening)",
            "parameters": {
                "type": "object",
                "properties": {
                    "time_preference": {
                        "type": "string",
                        "enum": ["morning", "afternoon", "evening"],
                        "description": "Preferred time of day for the appointment"
                    },
                    "filtered_schedule": {
                        "type": "object",
                        "description": "The schedule to filter based on urgency"
                    }
                },
                "required": ["time_preference", "filtered_schedule"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "select_best_appointment",
            "description": "AI selects the best appointment from available slots based on urgency and symptoms",
            "parameters": {
                "type": "object",
                "properties": {
                    "available_slots": {
                        "type": "object",
                        "description": "Available slots numbered and filtered by time preference"
                    },
                    "urgency": {
                        "type": "boolean",
                        "description": "Whether the appointment is urgent"
                    },
                    "symptoms": {
                        "type": "string",
                        "description": "Patient's symptoms"
                    }
                },
                "required": ["available_slots", "urgency", "symptoms"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_appointment_json",
            "description": "Updates the appointment JSON with newly collected information at each step",
            "parameters": {
                "type": "object",
                "properties": {
                    "field": {
                        "type": "string",
                        "description": "The field to update"
                    },
                    "value": {
                        "description": "The value to set for this field"
                    }
                },
                "required": ["field", "value"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "finalize_appointment",
            "description": "Finalizes the appointment and returns the complete JSON with all collected information",
            "parameters": {
                "type": "object",
                "properties": {
                    "confirm": {
                        "type": "boolean",
                        "description": "Confirmation to finalize the appointment"
                    }
                },
                "required": ["confirm"]
            }
        }
    }
]

def generate_time_slots(start_t, end_t, slot_minutes=90):
    slots = []
    current = datetime.combine(datetime.today(), start_t)
    end = datetime.combine(datetime.today(), end_t)

    while current < end:
        slots.append(current.time().strftime("%I:%M %p"))
        current += timedelta(minutes=slot_minutes)

    return slots


def parse_availability_rule(rule):
    """
    Parses rules like:
      "Mon-Wed 14:00-18:00"
      "Sat 09:00-12:00"
    and returns a dictionary: {weekday_index: (start_time, end_time)}
    """
    rule = rule.strip()
    pattern = r"([A-Za-z]{3})(?:-([A-Za-z]{3}))?\s+(\d{2}:\d{2})-(\d{2}:\d{2})"
    match = re.match(pattern, rule)

    if not match:
        raise ValueError(f"Invalid rule format: {rule}")

    day1, day2, start_str, end_str = match.groups()

    start_t = datetime.strptime(start_str, "%H:%M").time()
    end_t = datetime.strptime(end_str, "%H:%M").time()

    if day2:
        d1 = DAY_MAP[day1]
        d2 = DAY_MAP[day2]
        if d2 < d1:
            raise ValueError("Day range backwards (Mon-Sun is invalid).")
        days = range(d1, d2 + 1)
    else:
        days = [DAY_MAP[day1]]

    return {d: (start_t, end_t) for d in days}


def parse_full_schedule(schedule_str):
    """
    Example input:
    "Mon-Wed 14:00-18:00; Sat 09:00-12:00"
    """
    parts = schedule_str.split(";")
    result = {}

    for p in parts:
        rule_dict = parse_availability_rule(p)
        result.update(rule_dict)

    return result


def build_schedule(schedule_str, start_date, weeks=3, slot_minutes=90):
    availability = parse_full_schedule(schedule_str)

    schedule = {}
    current_date = start_date
    end_date = start_date + timedelta(weeks=weeks)

    while current_date <= end_date:
        weekday = current_date.weekday()

        if weekday in availability:
            start_t, end_t = availability[weekday]
            slots = generate_time_slots(start_t, end_t, slot_minutes)

            schedule[current_date.strftime("%Y-%m-%d")] = [
                {"time": t, "available": True} for t in slots
            ]

        current_date += timedelta(days=1)

    return schedule


def collect_urgency(is_urgent, schedule):
    """Stores the urgency status and filters schedule based on urgency"""
    if isinstance(is_urgent, str):
        is_urgent = is_urgent.lower() == "urgent"
    
    all_dates = sorted(schedule.keys(), key=lambda x: datetime.strptime(x, "%Y-%m-%d"))
    
    if is_urgent:
        selected_dates = all_dates[:3]
        message = f"Urgency status: Urgent. Selected the 3 earliest available dates: {', '.join(selected_dates)}"
    else:
        selected_dates = all_dates[3:] if len(all_dates) > 3 else all_dates
        message = f"Urgency status: Not urgent. Selected later available dates: {', '.join(selected_dates)}"
    
    filtered_schedule = {date: schedule[date] for date in selected_dates if date in schedule}
    
    return {
        "status": "collected",
        "is_urgent": is_urgent,
        "filtered_schedule": filtered_schedule,
        "selected_dates": selected_dates,
        "message": message
    }


def parse_time(time_str):
    """Parse time string like '02:00 PM' and return hour in 24-hour format"""
    try:
        dt = datetime.strptime(time_str, "%I:%M %p")
        return dt.hour
    except:
        return None


def filter_by_time_preference(time_preference, filtered_schedule):
    """Filters the schedule based on time of day preference and creates numbered slots"""
    time_range = TIME_RANGES.get(time_preference)
    
    if not time_range:
        return {"error": "Invalid time preference"}
    
    start_hour, end_hour = time_range
    time_filtered_schedule = {}
    available_slots = {}  # Map slot number to (date, time)
    
    for date, slots in filtered_schedule.items():
        filtered_slots = []
        for slot in slots:
            if not slot.get("available"):
                continue
            
            time_str = slot.get("time", "")
            hour = parse_time(time_str)
            
            if hour is not None and start_hour <= hour < end_hour:
                filtered_slots.append(slot)
        
        if filtered_slots:
            time_filtered_schedule[date] = filtered_slots
    
    # Create numbered slots sequentially
    slot_num = 1
    for date, slots in sorted(time_filtered_schedule.items()):
        for slot in slots:
            time_str = slot["time"]
            available_slots[slot_num] = (date, time_str)
            slot_num += 1
    
    return {
        "status": "filtered",
        "time_preference": time_preference,
        "available_slots": available_slots,
        "total_slots": len(available_slots),
        "message": f"Found {len(available_slots)} available {time_preference} slots"
    }


def select_best_appointment(available_slots, is_urgent, symptoms):
    """AI intelligently selects the best appointment from available slots"""
    if not available_slots:
        return {"error": "No available slots"}
    
    # Convert to list and sort by date, then time
    slots_list = [(num, date, time) for num, (date, time) in available_slots.items()]
    slots_list.sort(key=lambda x: (x[1], parse_time(x[2]) or 0))
    
    # Select best appointment
    if is_urgent:
        # For urgent cases, take the earliest available appointment
        selected_num, selected_date, selected_time = slots_list[0]
    else:
        # For non-urgent, take the first available (which is already sorted)
        selected_num, selected_date, selected_time = slots_list[0]
    
    return {
        "status": "selected",
        "selected_slot_number": selected_num,
        "selected_date": selected_date,
        "selected_time": selected_time,
        "message": f"Selected appointment #{selected_num} on {selected_date} at {selected_time}"
    }


def update_appointment_json(appointment_json, field, value):
    """Updates a specific field in the appointment JSON"""
    appointment_json[field] = value
    return {
        "status": "updated",
        "field": field,
        "message": f"Updated {field} in appointment JSON"
    }
def email_send(final_json):
    pass


def finalize_appointment(appointment_json):
    """Finalizes and returns the complete appointment JSON with only essential fields"""
    # Only keep the essential fields
    final_json = {
        "doctor_name": appointment_json.get("doctor_name"),
        "doctor_email": appointment_json.get("doctor_email"),
        "patient_name": appointment_json.get("patient_name"),
        "symptoms": appointment_json.get("symptoms"),
        "selected_date": appointment_json.get("selected_date"),
        "selected_time": appointment_json.get("selected_time"),
        "patient_notes": appointment_json.get("patient_notes", ""),
        "status": "confirmed",
        "created_at": datetime.now().isoformat(),
        "conversation_complete": True
    }
    email_send(final_json)
    with open("final_appointment.json", "w") as f:
        json.dump(final_json, f, indent=2)
    return {
        "final_appointment": final_json,
        "message": "Appointment confirmed and finalized"
    }


def execute_function(function_name, arguments, appointment_json):
    """Execute the requested function with given arguments"""
    if function_name == "filter_by_time_preference":
        filtered_schedule = arguments.get("filtered_schedule", appointment_json.get("filtered_schedule", {}))
        return filter_by_time_preference(
            arguments["time_preference"],
            filtered_schedule
        )
    elif function_name == "select_best_appointment":
        available_slots = arguments.get("available_slots", appointment_json.get("available_slots", {}))
        return select_best_appointment(
            available_slots,
            arguments["urgency"],
            arguments["symptoms"]
        )
    elif function_name == "update_appointment_json":
        return update_appointment_json(
            appointment_json,
            arguments["field"],
            arguments["value"]
        )
    elif function_name == "finalize_appointment":
        return finalize_appointment(appointment_json)
    else:
        return {"error": f"Unknown function: {function_name}"}


def run_automated_scheduling(initial_json):
    """
    Runs automated appointment scheduling WITHOUT conversation.
    Directly processes time preference and urgency to find best appointment.
    
    Args:
        initial_json: Dictionary containing:
            - doctor_schedule: Built schedule
            - is_urgent: Boolean or string
            - time_preference: "morning", "afternoon", or "evening"
            - patient_name, doctor_name, symptoms, etc.
    
    Returns:
        Final appointment JSON with selected date/time
    """
    appointment_json = initial_json.copy()
    doctor_schedule = appointment_json.get("doctor_schedule", {})
    is_urgent = appointment_json.get("is_urgent", False)
    time_preference = appointment_json.get("time_preference")
    symptoms = appointment_json.get("symptoms", "")
    
    print(f"Running automated scheduler...")
    print(f"  Time Preference: {time_preference}")
    print(f"  Urgent: {is_urgent}")
    
    # Step 1: Process urgency to filter dates
    urgency_result = collect_urgency(is_urgent, doctor_schedule)
    appointment_json["filtered_schedule"] = urgency_result.get("filtered_schedule", {})
    appointment_json["is_urgent"] = urgency_result.get("is_urgent", False)
    
    print(f"  Filtered to {len(appointment_json['filtered_schedule'])} dates")
    
    # Step 2: Filter by time preference
    if time_preference:
        time_result = filter_by_time_preference(time_preference, appointment_json["filtered_schedule"])
        appointment_json["time_preference"] = time_preference
        appointment_json["available_slots"] = time_result.get("available_slots", {})
        print(f"  Found {len(appointment_json['available_slots'])} available {time_preference} slots")
    else:
        # If no preference, use all slots
        time_result = filter_by_time_preference("morning", appointment_json["filtered_schedule"])
        appointment_json["available_slots"] = time_result.get("available_slots", {})
        print(f"  No preference, using all available slots")
    
    # Step 3: Select best appointment
    if appointment_json["available_slots"]:
        selection_result = select_best_appointment(
            appointment_json["available_slots"],
            appointment_json["is_urgent"],
            symptoms
        )
        
        appointment_json["selected_date"] = selection_result.get("selected_date")
        appointment_json["selected_time"] = selection_result.get("selected_time")
        appointment_json["selected_slot_number"] = selection_result.get("selected_slot_number")
        
        print(f"  Selected: {appointment_json['selected_date']} at {appointment_json['selected_time']}")
    else:
        print("  ERROR: No available slots found")
        return None
    
    # Step 4: Finalize (without sending email yet)
    final_json = {
        "doctor_name": appointment_json.get("doctor_name"),
        "doctor_email": appointment_json.get("doctor_email"),
        "patient_name": appointment_json.get("patient_name"),
        "symptoms": appointment_json.get("symptoms"),
        "selected_date": appointment_json.get("selected_date"),
        "selected_time": appointment_json.get("selected_time"),
        "patient_notes": appointment_json.get("patient_notes", ""),
        "status": "confirmed",
        "created_at": datetime.now().isoformat(),
        "conversation_complete": True
    }
    
    print("  Booking prepared (email will be sent when user clicks 'Book Appointment')")
    
    return final_json


def run_scheduling_conversation(initial_json):
    """
    Runs the appointment scheduling conversation using Chat Completions API
    """
    
    appointment_json = initial_json.copy()
    doctor_schedule = appointment_json.get("doctor_schedule", {})
    doctor_name = appointment_json.get("doctor_name", "the doctor")
    is_urgent = appointment_json.get("is_urgent", False)
    
    # Process urgency and filter schedule upfront
    urgency_result = collect_urgency(is_urgent, doctor_schedule)
    appointment_json["filtered_schedule"] = urgency_result.get("filtered_schedule", {})
    appointment_json["is_urgent"] = urgency_result.get("is_urgent", False)
    urgency_message = urgency_result.get("message", "")
    
    system_message = {
        "role": "system",
        "content": f"""You are a helpful medical appointment scheduling assistant.

INITIAL APPOINTMENT DATA:
{json.dumps(appointment_json, indent=2)}

URGENCY ALREADY PROCESSED:
{urgency_message}

CONVERSATION FLOW - Follow these steps:
1. Greet the patient warmly, mention you're scheduling with {doctor_name}
2. Acknowledge their symptoms: {json.dumps(appointment_json.get('symptoms', ''))}
3. Ask about their TIME PREFERENCE: "morning", "afternoon", or "evening"
4. When they answer, call filter_by_time_preference with their preference
   - This will create numbered slots filtered by time
   - Then call update_appointment_json to save "time_preference" and "available_slots"
5. Call select_best_appointment with the available_slots, urgency level, and symptoms
   - This will automatically choose the best appointment
   - Then call update_appointment_json to save "selected_slot_number", "selected_date", and "selected_time"
6. Announce the scheduled appointment: "Perfect! I've scheduled you for [DATE] at [TIME] with {doctor_name}"
7. Call finalize_appointment to complete the booking
8. Show the final confirmation details

IMPORTANT: 
- First ask for time preference
- Filter by time preference to get available slots
- Then automatically select the best appointment from those slots
- NO confirmation needed - just announce the chosen date and time
- Immediately finalize after selection
- Always use update_appointment_json to save information"""
    }
    
    messages = [
        system_message,
        {
            "role": "user",
            "content": "Hello, I'd like to book an appointment."
        }
    ]
    
    print("🏥 Medical Appointment Scheduler Started\n")
    print("📋 Initial JSON:")
    print(json.dumps(appointment_json, indent=2))
    print("=" * 60)
    
    conversation_active = True
    
    while conversation_active:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        assistant_message = response.choices[0].message
        messages.append(assistant_message)
        
        if assistant_message.tool_calls:
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                print(f"\n🔧 Calling function: {function_name}")
                print(f"   Arguments: {json.dumps(function_args, indent=2)}")
                
                function_response = execute_function(function_name, function_args, appointment_json)
                
                if function_name == "filter_by_time_preference":
                    if "available_slots" in function_response:
                        appointment_json["time_preference"] = function_response["time_preference"]
                        appointment_json["available_slots"] = function_response["available_slots"]
                elif function_name == "select_best_appointment":
                    if "selected_date" in function_response:
                        appointment_json["selected_slot_number"] = function_response["selected_slot_number"]
                        appointment_json["selected_date"] = function_response["selected_date"]
                        appointment_json["selected_time"] = function_response["selected_time"]
                elif function_name == "finalize_appointment":
                    conversation_active = False
                    if "final_appointment" in function_response:
                        appointment_json = function_response["final_appointment"]
                
                print(f"   Response: {function_response.get('message', 'Done')}")
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": json.dumps(function_response)
                })
            
            if not conversation_active:
                final_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages
                )
                final_text = final_response.choices[0].message.content
                print(f"\n🤖 Assistant: {final_text}\n")
                break
                
        else:
            assistant_text = assistant_message.content
            print(f"\n🤖 Assistant: {assistant_text}\n")
            
            user_input = input("👤 You: ")
            print()
            
            if user_input.lower() in ['quit', 'exit', 'cancel']:
                print("Appointment scheduling cancelled.")
                conversation_active = False
                break
            
            messages.append({
                "role": "user",
                "content": user_input
            })
    
    print("=" * 60)
    print("\n✅ FINAL APPOINTMENT JSON:")
    print(json.dumps(appointment_json, indent=2))
    
    return appointment_json


if __name__ == "__main__":
    
    import json
    with open("mental_health_agent_result.json", "r") as f:
        json_file = json.load(f)
        
    schedule_rules = json_file["specialist"]["schedule"] if json_file else "Mon-Wed 09:00-17:00; Sat 10:00-14:00"
    today = datetime(2025, 11, 22)

    result = build_schedule(schedule_rules, today)
    initial_appointment_json = {
        "doctor_name": json_file["specialist"]["name"] if json_file else "Dr. Sarah Johnson",
        "doctor_email": json_file["specialist"]["email"] if json_file else "sarah.johnson@example.com",
        "patient_name": json_file["patient_info"]["name"] if json_file else "John Doe",
        "symptoms": json_file["analysis"]["symptoms"] if json_file else "Fever, cough, and fatigue",
        "doctor_schedule": result,
        "is_urgent": json_file["urgency_level"] if json_file else "moderate",
        "time_preference": None,
        "filtered_schedule": None,
        "available_slots": None,
        "selected_date": None,
        "selected_time": None,
        "selected_slot_number": None,
        "patient_notes": ""
    }
    
    final_result = run_scheduling_conversation(initial_appointment_json)