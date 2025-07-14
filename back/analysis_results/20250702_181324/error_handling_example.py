def handle_sepomex_error():
    try:
        # Call to SEPOMEX API
        response = call_sepomex_api()
        if response.status_code != 200:
            raise Exception("SEPOMEX API is unavailable")
    except Exception as e:
        print(f"Error: {str(e)}")
        return "Error: Unable to fetch data from SEPOMEX. Please try again later."

handle_sepomex_error()