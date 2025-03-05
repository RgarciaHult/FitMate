"""
test_project.py
Uses pytest to test three simple functions from project.py:
- register_user
- verify_user
- add_favorite

These tests assume you have a valid database setup. In a real-world
scenario, you might use a separate test database or mock your DB calls.
"""

import pytest
import sqlite3
from project import (
    register_user,
    verify_user,
    add_favorite,
    get_db_connection,
    create_tables
)

@pytest.fixture(scope="module")
def setup_db():
    """
    Fixture to ensure tables are created before tests run,
    and optionally clear data if you want fresh tests.
    """
    create_tables()  # Ensure the tables exist
    yield
    # Optionally, you could clear out test data here if needed
    # with get_db_connection() as conn:
    #     conn.execute("DELETE FROM users")
    #     conn.execute("DELETE FROM favorites")
    #     conn.commit()

def test_register_user(setup_db):
    """
    Test the register_user function by registering a new user.
    Checks if the function returns True for a new username,
    and False if the user already exists.
    """
    # First attempt should succeed
    result_first = register_user("testuser", "testpassword")
    assert result_first is True, "Expected register_user to return True for a new user"

    # Second attempt with the same username should fail
    result_second = register_user("testuser", "anotherpassword")
    assert result_second is False, "Expected register_user to return False for a duplicate user"

def test_verify_user(setup_db):
    """
    Test the verify_user function by verifying credentials of
    the user created in test_register_user.
    """
    # This user should exist and the password should match
    user_row = verify_user("testuser", "testpassword")
    assert user_row is not None, "Expected to verify user with correct credentials"

    # Wrong password should fail
    wrong_pass_user = verify_user("testuser", "wrongpass")
    assert wrong_pass_user is None, "Expected verify_user to return None for incorrect password"

def test_add_favorite(setup_db):
    """
    Test the add_favorite function by adding a meal to favorites.
    We'll insert a dummy meal first, then try to favorite it.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert a dummy meal to ensure we have a meal_id to favorite
    cursor.execute('''
        INSERT OR IGNORE INTO meals (type, name, identifier, categories, prep_time)
        VALUES (?, ?, ?, ?, ?)
    ''', ("Breakfast", "Dummy Meal", "DUM", "Lose Weight", 10))
    conn.commit()

    # Get the meal_id for the inserted meal
    cursor.execute("SELECT id FROM meals WHERE identifier = ?", ("DUM",))
    meal_id_row = cursor.fetchone()
    assert meal_id_row is not None, "Expected to find the dummy meal in the DB"
    meal_id = meal_id_row['id']

    # Attempt to favorite the meal for our test user (id=1 if test_register_user ran)
    # If you're not sure user_id=1 is correct, you could query the users table.
    cursor.execute("SELECT id FROM users WHERE username = ?", ("testuser",))
    user_row = cursor.fetchone()
    conn.close()
    assert user_row is not None, "Expected testuser to exist in the DB"
    user_id = user_row['id']

    # Now call add_favorite
    first_fav_result = add_favorite(user_id, meal_id)
    assert first_fav_result is True, "Expected add_favorite to succeed for a new favorite"

    # Attempting to add the same favorite again should fail
    second_fav_result = add_favorite(user_id, meal_id)
    assert second_fav_result is False, "Expected add_favorite to fail for duplicate entry"