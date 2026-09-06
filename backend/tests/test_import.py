import uuid


def roster(suffix):
    return {
        "students": [
            {
                "student_key": f"emma-{suffix}",
                "first_name": "Emma",
                "last_name": f"Chen{suffix}",
                "name": f"Emma Chen{suffix}",
            },
            {
                "student_key": f"liam-{suffix}",
                "first_name": "Liam",
                "last_name": f"Patel{suffix}",
            },
        ],
        "guardians": [
            {
                "student_key": f"emma-{suffix}",
                "name": f"Wei Chen{suffix}",
                "relationship": "Dad",
                "phone": "555-0101",
                "email": "wei@example.com",
            },
        ],
    }


def find_student(client, name):
    matches = [s for s in client.get("/api/v1/students", params={"search": name}).json() if s["name"] == name]
    assert len(matches) == 1
    return matches[0]


def test_import_students_creates_and_is_idempotent(client):
    suffix = uuid.uuid4().hex[:8]
    payload = roster(suffix)

    response = client.post("/api/v1/import/students", json=payload)
    assert response.status_code == 200
    assert response.json() == {"imported_students": 2, "imported_guardians": 1}

    emma = find_student(client, f"Emma Chen{suffix}")
    assert emma["initials"] == "EC"
    assert len(emma["guardians"]) == 1
    assert emma["guardians"][0]["name"] == f"Wei Chen{suffix}"
    assert emma["guardians"][0]["relation"] == "Dad"
    emma_id = emma["id"]

    liam = find_student(client, f"Liam Patel{suffix}")
    assert liam["initials"] == "LP"

    response = client.post("/api/v1/import/students", json=payload)
    assert response.status_code == 200
    assert response.json() == {"imported_students": 2, "imported_guardians": 1}

    emma = find_student(client, f"Emma Chen{suffix}")
    assert emma["id"] == emma_id
    assert len(emma["guardians"]) == 1


def test_import_updates_existing_guardian_on_reimport(client):
    suffix = uuid.uuid4().hex[:8]
    payload = roster(suffix)
    client.post("/api/v1/import/students", json=payload)

    updated = {
        "students": payload["students"][:1],
        "guardians": [
            {
                "student_key": f"emma-{suffix}",
                "name": f"Wei Chen{suffix}",
                "relationship": "Father",
                "phone": "555-0202",
            }
        ],
    }
    response = client.post("/api/v1/import/students", json=updated)
    assert response.status_code == 200
    assert response.json() == {"imported_students": 1, "imported_guardians": 1}

    emma = find_student(client, f"Emma Chen{suffix}")
    assert len(emma["guardians"]) == 1
    assert emma["guardians"][0]["phone"] == "555-0202"
    assert emma["guardians"][0]["relation"] == "Father"


def test_import_unknown_student_key_returns_400(client):
    response = client.post(
        "/api/v1/import/students",
        json={
            "students": [],
            "guardians": [
                {
                    "student_key": "no-such-key",
                    "name": "Ghost Guardian",
                    "relationship": "Mom",
                }
            ],
        },
    )
    assert response.status_code == 400
    assert "detail" in response.json()
