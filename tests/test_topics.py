from echoparley.topics import TopicTracker


def test_topic_tracker_matches_whole_normalized_words() -> None:
    tracker = TopicTracker({"booking": frozenset({"ticket", "book"}), "music": frozenset({"song"})})
    assert tracker.predict("BOOK a ticket") == ("booking",)
    assert tracker.predict("booklet") == ()


def test_topic_score_known_and_empty_cases() -> None:
    from echoparley.topics import TopicScores, topic_scores

    assert topic_scores(("a", "b"), ("b", "c")) == TopicScores(0.5, 0.5)
    assert topic_scores((), ()) == TopicScores(1.0, 1.0)
    assert topic_scores((), ("a",)) == TopicScores(0.0, 0.0)
