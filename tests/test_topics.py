from echoparley.topics import TopicTracker


def test_topic_tracker_matches_whole_normalized_words() -> None:
    tracker = TopicTracker({"booking": frozenset({"ticket", "book"}), "music": frozenset({"song"})})
    assert tracker.predict("BOOK a ticket") == ("booking",)
    assert tracker.predict("booklet") == ()
