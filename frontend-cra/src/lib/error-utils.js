/**
 * Utility functions for handling FastAPI error responses
 */

/**
 * Extract error message from FastAPI error response
 * FastAPI returns errors in different formats:
 * 1. Simple string: { "detail": "Error message" }
 * 2. Validation errors: { "detail": [{ "msg": "Error 1" }, { "msg": "Error 2" }] }
 * 3. Array of strings: { "detail": ["Error 1", "Error 2"] }
 * 
 * @param {Object} error - Axios error object
 * @returns {string} - Formatted error message
 */
export const extractErrorMessage = (error) => {
  // If it's already a string, return it
  if (typeof error === 'string') {
    return error;
  }

  // If it's an Error object with a message
  if (error instanceof Error && error.message) {
    return error.message;
  }

  // Try to extract from axios error response
  const responseData = error.response?.data;
  
  if (!responseData) {
    return 'An unknown error occurred';
  }

  // Handle FastAPI error format
  const detail = responseData.detail;
  
  if (!detail) {
    // No detail field, try to stringify the response
    try {
      return JSON.stringify(responseData);
    } catch {
      return 'An error occurred';
    }
  }

  // Case 1: detail is a string
  if (typeof detail === 'string') {
    return detail;
  }

  // Case 2: detail is an array
  if (Array.isArray(detail)) {
    // Extract messages from each item
    const messages = detail.map(item => {
      if (typeof item === 'string') {
        return item;
      }
      if (item && typeof item === 'object') {
        // Try common message fields
        return item.msg || item.message || item.error || JSON.stringify(item);
      }
      return String(item);
    });
    
    // Join with semicolons
    return messages.filter(msg => msg && msg.trim()).join('; ');
  }

  // Case 3: detail is an object (not array)
  if (detail && typeof detail === 'object') {
    // Try to extract message from object
    return detail.msg || detail.message || detail.error || JSON.stringify(detail);
  }

  // Fallback
  return String(detail);
};

/**
 * Check if error is a validation error (422 status)
 */
export const isValidationError = (error) => {
  return error.response?.status === 422;
};

/**
 * Extract validation errors as an array of messages
 */
export const extractValidationErrors = (error) => {
  if (!isValidationError(error)) {
    return [];
  }

  const detail = error.response?.data?.detail;
  if (!detail || !Array.isArray(detail)) {
    return [];
  }

  return detail.map(item => {
    if (typeof item === 'string') {
      return item;
    }
    if (item && typeof item === 'object') {
      // Format validation error nicely
      const field = item.loc?.join('.') || 'field';
      const msg = item.msg || 'Invalid value';
      return `${field}: ${msg}`;
    }
    return String(item);
  });
};