#   Copyright 2018 The Batfish Open Source Project
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
import json
import os

import pytest
import responses

from pybatfish.client.session import Session
from pybatfish.question.question import QuestionBase, QuestionMeta, _install_questions


def create_question(name, session, description, tags):
    """Create question to manually install into Session.q."""
    return (
        name,
        QuestionMeta(
            name,
            (QuestionBase,),
            {
                "docstring": "docstring",
                "description": description,
                "session": session,
                "tags": tags,
                "template": {},
                "variables": [],
            },
        ),
    )


@pytest.fixture(scope="module")
def questions():
    """Basic pseudo-questions for questions tests."""
    q1 = {"name": "qName1", "description": "description1.", "tags": ["tag1"]}
    q2 = {"name": "qName2", "description": "description2.", "tags": ["tags2"]}
    yield [q1, q2]


@pytest.fixture(scope="function")
def session():
    s = Session(load_questions=False)
    yield s


def test_list_tags(session):
    """Test that question tags are listed as expected."""
    # Should have no tags to start with
    assert len(session.q.list_tags()) == 0

    q1_tags = ["tag1", "tag2"]
    q3_tags = ["tag2"]
    all_tags = set()
    all_tags.update(q1_tags)
    all_tags.update(q3_tags)

    q1 = create_question("qName1", session, "description", q1_tags)
    q2 = create_question("qName2", session, "description", [])
    q3 = create_question("qName3", session, "description", q3_tags)
    _install_questions([q1, q2, q3], session.q)

    # Make sure all tags show up when listing tags
    assert all_tags == session.q.list_tags()


def test_list_questions(session, questions):
    """Test that questions are listed as expected."""
    # Should have no questions to start with
    assert len(session.q.list()) == 0

    qs = [
        create_question(q.get("name"), session, q.get("description"), q.get("tags"))
        for q in questions
    ]
    _install_questions(qs, session.q)

    # Make sure all questions show up when listing questions
    listed_questions = session.q.list()
    for q in questions:
        assert q in listed_questions


def test_load_questions_local(session, tmpdir, questions):
    """Test that questions loaded from a directory show up as expected."""
    # Should have no questions to start with
    assert len(session.q.list()) == 0

    # Should still have no questions after loading an empty dir
    dir_path = str(tmpdir.mkdir("questions"))
    session.q.load(dir_path)
    assert len(session.q.list()) == 0

    for q in questions:
        filename = "{}.json".format(q["name"])
        with open(os.path.join(dir_path, filename), "w") as f:
            f.write(
                json.dumps(
                    {
                        "class": "class",
                        "instance": {
                            "description": q["description"],
                            "instanceName": q["name"],
                            "tags": q["tags"],
                        },
                    }
                )
            )
            f.flush()
    session.q.load(dir_path)

    # Make sure all questions from specified directory show up when listing questions
    listed_questions = session.q.list()
    for q in questions:
        assert q in listed_questions


@responses.activate
def test_load_questions_remote(session, questions):
    """Test that questions are successfully loaded from a mock Batfish service."""
    # Should have no questions to start with
    assert len(session.q.list()) == 0

    # Build correctly formatted getquestiontemplates response
    qs = {}
    for q in questions:
        qs[q["name"]] = json.dumps(
            {
                "class": "class",
                "instance": {
                    "description": q["description"],
                    "instanceName": q["name"],
                    "tags": q["tags"],
                },
            }
        )

    # Intercept the GET request destined for the Batfish service, and just return json response
    # (Success + question templates)
    responses.add(
        responses.GET,
        "http://localhost:9996/v2/question_templates?verbose=False",
        json=qs,
        status=200,
    )

    session.q.load()
    listed_questions = session.q.list()
    # Make sure all questions were loaded from the service
    for q in questions:
        assert q in listed_questions
