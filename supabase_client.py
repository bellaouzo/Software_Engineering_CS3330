from flask import current_app, session
from supabase import Client, create_client


def get_supabase_client() -> Client:
    """Returns a new Supabase client built from the app's SUPABASE_URL and SUPABASE_KEY.

    Raises SupabaseException if either value is missing from the environment.
    """
    return create_client(
        current_app.config["SUPABASE_URL"],
        current_app.config["SUPABASE_KEY"],
    )


def get_user_client() -> Client:
    """Returns a Supabase client that acts as the logged-in user, so RLS applies.

    Use this for every table query made on a user's behalf. If the saved access
    token has expired it is refreshed, and the new tokens replace the old ones in
    the Flask session. Call it only after a login check (see auth_helpers.py).

    Raises AuthError if the saved login is no longer valid, and SupabaseException
    if the app is missing its Supabase settings.
    """
    client = get_supabase_client()
    result = client.auth.set_session(session["access_token"], session["refresh_token"])
    session["access_token"] = result.session.access_token
    session["refresh_token"] = result.session.refresh_token
    return client
