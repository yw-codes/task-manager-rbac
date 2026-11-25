def test_index_loading(client):
    """
    Standard smoke test:
    Verifies that the root URL loads successfully and contains the main title.
    """
    response = client.get("/")

    # Assert HTTP status is 200 (OK)
    assert response.status_code == 200

    # Verify core branding text exists in the HTML
    assert b"Task Tracker" in response.data
    assert b"Welcome" in response.data


def test_index_unauthenticated_state(client):
    """
    Verifies the index page state when no user is logged in.
    """
    response = client.get("/")
    # Check for the presence of the Login button or modal trigger
    assert b"Login" in response.data
    # Ensure user-specific content (like 'Logout') is NOT visible
    # assert b'href="/logout"' not in response.data
