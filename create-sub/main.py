import requests
from config import Config


def get_user_input():
    """Collect and validate user input for model, domain, post_url, expires, and user."""

    # Ask for the model
    model = input(f"Enter model (default: {Config.DEFAULT_MODEL}): ").strip().lower()
    if not model:
        model = Config.DEFAULT_MODEL
    while model not in Config.VALID_MODELS:
        print(f"Invalid model. Valid options are: {', '.join(Config.VALID_MODELS)}")
        model = (
            input(f"Enter model (default: {Config.DEFAULT_MODEL}): ").strip().lower()
        )
        if not model:
            model = Config.DEFAULT_MODEL

    # Ask for the domain
    domain = input("Enter domain (10-digit number followed by .com): ").strip().lower()
    while not Config.is_valid_domain(domain):
        print("Invalid domain format. Example: 1234567890.com")
        domain = (
            input("Enter domain (10-digit number followed by .com): ").strip().lower()
        )

    # Ask for the post_url
    post_url = input(f"Enter post_url (default: {Config.DEFAULT_POST_URL}): ").strip()
    if not post_url:
        post_url = Config.DEFAULT_POST_URL

    # Ask for the number of days before expiration
    try:
        expires = int(
            input(
                f"Enter number of days before expiration (default: {Config.DEFAULT_EXPIRES}): "
            ).strip()
            or Config.DEFAULT_EXPIRES
        )
    except ValueError:
        print(f"Invalid input. Defaulting to {Config.DEFAULT_EXPIRES} days.")
        expires = Config.DEFAULT_EXPIRES

    # Ask for the user (optional)
    user = input("Enter user (optional, press Enter to skip): ").strip() or None

    return model, domain, post_url, expires, user


def confirm_input(model, domain, post_url, expires, user):
    """Ask the user to confirm the input."""
    print("\nPlease confirm the following information:")
    print(f"Model: {model}")
    print(f"Domain: {domain}")
    print(f"Post URL: {post_url}")
    print(f"Expires in: {expires} day(s)")
    print(f"User: {user if user else 'None'}")

    confirmation = input("Is this information correct? (y/n): ").strip().lower()
    return confirmation == "y"


def post_data(model, domain, post_url, expires, user):
    """Send the collected data via a POST request to the configured host."""
    # Build the data dictionary dynamically
    data = {
        "model": model,
        "domain": domain,
        "post_url": post_url,
        "expires": expires,
    }
    if user:  # Include user only if provided
        data["user"] = user

    try:
        response = requests.post(Config.POST_HOST, json=data)
        response.raise_for_status()  # Raise an error for bad status codes
        print("Subscription created successfully!")
        print(f"Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to create subscription: {e}")


def main():
    """Main entry point for the program."""
    while True:
        # Step 1: Collect input
        model, domain, post_url, expires, user = get_user_input()

        # Step 2: Confirm the input
        if confirm_input(model, domain, post_url, expires, user):
            # Step 3: Send POST request with confirmed input
            post_data(model, domain, post_url, expires, user)
            break
        else:
            print("Let's try again.")


if __name__ == "__main__":
    main()
