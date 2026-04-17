from client_auth import register, login, change_password, delete_account
from client_songs import compose, handle_storage_requests
from client_utils import set_tokens

def startup_screen():
    print("""
    
    _____________________________
    |          WELCOME          |
    |                           |
    |           Enter:          |
    |     REGISTER or LOGIN     |
    |___________________________|
    """)


def main():
    while True:
        startup_screen()

        username = None
        while not username:
            choice = input(">>> ").strip().upper()
            if choice == "REGISTER":
                username, access_token, refresh_token = register()
                set_tokens(access_token, refresh_token)

            elif choice == "LOGIN":
                username, access_token, refresh_token = login()
                set_tokens(access_token, refresh_token)

            else:
                print("Please enter REGISTER or LOGIN.")

        # main loop, only reachable after login/register
        while True:
            print("\nCommands: COMPOSE | STORAGE | CHANGE PASSWORD | DELETE ACCOUNT | LOGOUT")
            choice = input(">>> ").strip().upper()

            if choice == "COMPOSE":
                compose()
            elif choice == "STORAGE":
                handle_storage_requests()
            elif choice == "CHANGE PASSWORD":
                change_password()
            elif choice == "DELETE ACCOUNT":
                if delete_account():
                    set_tokens(None, None)
                    break  # account deleted, exit
            elif choice == "LOGOUT":
                set_tokens(None, None)
                break  # session ended, exit to startup screen
            else:
                print("Command does not exist. Please try again.")


if __name__ == "__main__":
    main()
