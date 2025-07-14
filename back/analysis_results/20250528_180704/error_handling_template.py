class ErrorHandling:
    def handle_sepomex_error(self):
        try:
            # Call SEPOMEX service
            pass
        except ServiceUnavailableError:
            return 'Service is currently unavailable. Please try again later.'
        except Exception as e:
            return f'An unexpected error occurred: {str(e)}'