// Template for error handling in external service calls
function handleExternalServiceError(serviceName, error) {
    console.error(`Error in ${serviceName}:`, error);
    // Add fallback logic here
    return {
        success: false,
        message: `Service ${serviceName} is currently unavailable. Please try again later.`
    };
}
