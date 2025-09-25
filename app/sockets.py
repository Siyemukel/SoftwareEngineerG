from flask import session
from flask_socketio import join_room, leave_room, emit
from flask_login import current_user
from .extensions import socketio, db
from .models import Message

def _room_name(student_id, staff_id):
    # canonical room name for conversation
    return f"conv-student-{student_id}-staff-{staff_id}"

@socketio.on("join")
def handle_join(data):
    """
    data = {
      'student_id': <int>,
      'staff_id': <int>
    }
    """
    # validate current_user
    if not current_user.is_authenticated:
        return

    student_id = data.get("student_id")
    staff_id = data.get("staff_id")
    if not student_id or not staff_id:
        return

    room = _room_name(student_id, staff_id)
    join_room(room)
    # optionally notify others in room
    emit("user_joined", {"room": room, "user": getattr(current_user, "id", None)}, room=room)

@socketio.on("leave")
def handle_leave(data):
    if not current_user.is_authenticated:
        return
    student_id = data.get("student_id")
    staff_id = data.get("staff_id")
    room = _room_name(student_id, staff_id)
    leave_room(room)
    emit("user_left", {"room": room, "user": getattr(current_user, "id", None)}, room=room)

@socketio.on("send_message")
def handle_send_message(data):
    """
    data = {
      'student_id': <int>,
      'staff_id': <int>,
      'content': '...'
    }
    """
    if not current_user.is_authenticated:
        return

    student_id = data.get("student_id")
    staff_id = data.get("staff_id")
    content = data.get("content", "").strip()
    if not student_id or not staff_id or not content:
        return

    # Determine sender/receiver type by current_user object
    if hasattr(current_user, "student_email"):  # Student instance
        sender_type = "student"
        sender_id = current_user.id
        receiver_type = "staff"
        receiver_id = staff_id
    else:
        sender_type = "staff"
        sender_id = current_user.id
        receiver_type = "student"
        receiver_id = student_id

    # Persist message
    msg = Message(
        sender_type=sender_type,
        sender_id=sender_id,
        receiver_type=receiver_type,
        receiver_id=receiver_id,
        content=content
    )
    db.session.add(msg)
    db.session.commit()

    payload = {
        "message": msg.to_dict()
    }

    # Emit to room
    room = _room_name(student_id, staff_id)
    socketio.emit("new_message", payload, room=room)
