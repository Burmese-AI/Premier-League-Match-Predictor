def dynamo_error_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Handle the error and return a message
            error_message = f"Error occurred in {func.__name__}: {str(e)}"
            return {"error": error_message}  # Return an error message as a dictionary
    return wrapper