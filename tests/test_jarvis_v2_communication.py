from pathlib import Path
from jarvis_v2.personal.contacts import ContactStore, CommunicationService
from jarvis_v2.personal.planner import PersonalPlanner


def test_contacts_and_message_preparation(tmp_path: Path):
    contacts = ContactStore(tmp_path / "contacts.json")
    communication = CommunicationService(tmp_path / "messages.json")
    contact = contacts.add("Dad", phone="+911234567890")
    assert contacts.find("dad")[0].id == contact.id

    planner = PersonalPlanner(contacts=contacts, communication=communication)
    result = planner.plan("prepare message Dad | I'll call you tonight")
    assert result.intent == "prepare_message"
    assert result.messages[0].status == "queued"

    sent = communication.confirm_and_mark_sent(result.messages[0].id)
    assert sent.status == "sent"


def test_planner_lists_contacts(tmp_path: Path):
    contacts = ContactStore(tmp_path / "contacts.json")
    contacts.add("Alice")
    result = PersonalPlanner(contacts=contacts).plan("show my contacts")
    assert result.intent == "list_contacts"
    assert result.contacts[0].name == "Alice"
