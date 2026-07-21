from app.emergency.content import TOPICS


def test_every_emergency_topic_puts_immediate_action_first() -> None:
    assert len(TOPICS) >= 12
    for topic in TOPICS:
        assert topic.immediate_action
        assert len(topic.immediate_action) <= 180
        assert topic.instructions
        assert topic.do_not
        assert all(len(item) <= 120 for item in topic.instructions + topic.do_not)


def test_chest_pain_and_stroke_are_not_vague() -> None:
    chest = next(topic for topic in TOPICS if topic.slug == "chest-pain")
    stroke = next(topic for topic in TOPICS if topic.slug == "stroke-signs")
    assert "Call 112 now" in chest.immediate_action
    assert "Call 112 now" in stroke.immediate_action
    assert "Do not drive yourself." in chest.do_not
