# Calling the RuijieBypass class from the .so file
from yourgod import RuijieBypass

if __name__ == "__main__":
    # Initialize the class (License check is performed automatically)
    app = RuijieBypass()

    # Directly execute the process instead of using app.run_menu()
    try:
        # If using the updated code, start_process() handles both Banner and Login
        app.start_process()
    except AttributeError:
        # If the .so file is an older version (not yet updated),
        # manually call the original functions to execute
        app.print_banner()
        app.do_login()
