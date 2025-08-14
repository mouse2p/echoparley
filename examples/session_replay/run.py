from echoparley.session import SessionRecorder, decode_session, encode_session

recorder = SessionRecorder()
recorder.append(0, "start", {"seed": 4})
recorder.append(20, "unit", {"id": 2})
encoded = encode_session(recorder.close())
assert encode_session(decode_session(encoded)) == encoded
print("byte-identical replay verified for synthetic session")
