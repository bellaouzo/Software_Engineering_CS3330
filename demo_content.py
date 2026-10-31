"""The words used by seed_demo_data.py: demo accounts, ticket ideas, and comments.

Kept apart from the script so the wording can change without touching the
database code. Categories must match TICKET_CATEGORIES and the COMMENTS keys
must match TICKET_STATUSES (both in routes/tickets.py). Wording stays generic:
no product or school names (Front End Notes 1 and 3).
"""

# (username, display name). Usernames start with "demo_" so they are easy to
# spot and remove, and follow USERNAME_PATTERN in routes/auth.py.
REQUESTERS = [
    ("demo_requester", "Alex Rivera"),
    ("demo_requester2", "Priya Shah"),
    ("demo_requester3", "Marcus Bell"),
    ("demo_requester4", "Hannah Cole"),
    ("demo_requester5", "Diego Ramos"),
]
STAFF = [
    ("demo_staff", "Jordan Lee"),
    ("demo_staff2", "Sam Okafor"),
]

LOCATIONS = [
    "Main Building, Room 104", "Main Building, Room 210", "Main Building, 2nd floor restroom",
    "North Wing, Room 12", "North Wing, break room", "South Wing, Room 305",
    "South Wing, stairwell B", "Library, study room 3", "Library, front desk",
    "Gym, locker room", "Parking garage, level 2", "Front lobby",
]

# category -> list of (title, description)
TICKET_IDEAS = {
    "Plumbing": [
        ("Sink won't drain", "Water sits in the sink for several minutes before it drains."),
        ("Leaking pipe under sink", "There is a slow drip and a puddle under the cabinet."),
        ("Toilet keeps running", "The toilet runs constantly after flushing."),
        ("No hot water", "Only cold water comes out of the taps."),
    ],
    "Electrical": [
        ("Lights flickering", "The overhead lights flicker on and off all day."),
        ("Outlet not working", "Nothing plugged into the outlet by the window gets power."),
        ("Breaker keeps tripping", "Power cuts out when more than two computers are on."),
        ("Exit sign is out", "The exit sign above the door is not lit."),
    ],
    "HVAC": [
        ("Room is too hot", "The thermostat is set to 70 but the room is around 85."),
        ("No heat", "The heater blows cold air even when it is turned all the way up."),
        ("Loud noise from vent", "The air vent rattles loudly whenever the air turns on."),
        ("Bad smell from vents", "A musty smell comes out of the vents in the morning."),
    ],
    "Furniture": [
        ("Broken chair", "One chair has a cracked leg and is not safe to sit on."),
        ("Desk drawer stuck", "The top desk drawer is jammed shut."),
        ("Wobbly table", "The table rocks back and forth when anyone leans on it."),
        ("Need more chairs", "The room has 20 seats but 30 people use it."),
    ],
    "Cleaning": [
        ("Spill on carpet", "Coffee was spilled near the door and left a stain."),
        ("Trash not emptied", "The trash cans have not been emptied in a few days."),
        ("Restroom out of soap", "Both soap dispensers are empty."),
        ("Windows are dirty", "The windows are covered in smudges and dust."),
    ],
    "Other": [
        ("Door won't lock", "The door closes but the lock does not latch."),
        ("Projector not turning on", "The projector stays off when the remote is pressed."),
        ("Wi-Fi drops often", "The connection drops every few minutes in this room."),
        ("Pest sighting", "Saw ants along the wall near the kitchen area."),
    ],
}

# Staff comment for moving a ticket to each status, plus requester replies.
COMMENTS = {
    "Acknowledged": [
        "Thanks for reporting this. We have it on our list.",
        "Got it. Someone will take a look soon.",
        "Received. We will schedule a visit.",
    ],
    "In Progress": [
        "A technician is working on this now.",
        "Parts are ordered, work has started.",
        "We are on site looking at it today.",
    ],
    "Resolved": [
        "This should be fixed now. Let us know if it comes back.",
        "Repair is done. Please check and reply if anything is still wrong.",
        "Fixed and tested. Marking this resolved.",
    ],
    "Closed": [
        "Closing this ticket. Open a new one if the problem returns.",
        "No further issues reported, closing.",
    ],
    "Requester": [
        "Thanks for the update!",
        "It is still happening this morning.",
        "Is there an estimate for when this will be done?",
        "Looks good now, thank you.",
        "One more detail: it is worse in the afternoon.",
    ],
}
