import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { api } from '../lib/api';
import { CheckCircle, Loader2 } from 'lucide-react';

export default function PaymentSuccess() {
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get('session_id');
  const [status, setStatus] = useState('checking');
  const [paymentData, setPaymentData] = useState(null);

  useEffect(() => {
    if (sessionId) {
      pollStatus();
    }
  }, [sessionId]);

  const pollStatus = async (attempts = 0) => {
    const maxAttempts = 5;
    const interval = 2000;

    if (attempts >= maxAttempts) {
      setStatus('timeout');
      return;
    }

    try {
      const response = await api.get(`/payments/status/${sessionId}`);
      setPaymentData(response.data);
      
      if (response.data.payment_status === 'paid') {
        setStatus('success');
        return;
      } else if (response.data.status === 'expired') {
        setStatus('expired');
        return;
      }

      // Continue polling
      setTimeout(() => pollStatus(attempts + 1), interval);
    } catch (error) {
      console.error('Failed to check status:', error);
      setTimeout(() => pollStatus(attempts + 1), interval);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="text-center max-w-md mx-auto px-6">
        {status === 'checking' && (
          <>
            <Loader2 className="w-12 h-12 animate-spin text-primary mx-auto mb-4" />
            <h1 className="text-2xl font-serif mb-2">Processing Payment</h1>
            <p className="text-muted-foreground">
              Please wait while we confirm your payment...
            </p>
          </>
        )}

        {status === 'success' && (
          <>
            <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
            <h1 className="text-2xl font-serif mb-2" data-testid="payment-success">
              Payment Successful
            </h1>
            <p className="text-muted-foreground mb-6">
              Your reach attempt has been delivered. Thank you!
            </p>
            {paymentData && (
              <p className="text-sm text-muted-foreground mb-6">
                Amount paid: ${paymentData.amount}
              </p>
            )}
            <Link
              to="/"
              className="text-primary hover:underline"
            >
              Return to Reach
            </Link>
          </>
        )}

        {status === 'expired' && (
          <>
            <h1 className="text-2xl font-serif mb-2">Session Expired</h1>
            <p className="text-muted-foreground mb-6">
              Your payment session has expired. Please try again.
            </p>
            <Link to="/" className="text-primary hover:underline">
              Return to Reach
            </Link>
          </>
        )}

        {status === 'timeout' && (
          <>
            <h1 className="text-2xl font-serif mb-2">Status Unknown</h1>
            <p className="text-muted-foreground mb-6">
              We couldn't confirm your payment status. 
              Please check your email for confirmation.
            </p>
            <Link to="/" className="text-primary hover:underline">
              Return to Reach
            </Link>
          </>
        )}
      </div>
    </div>
  );
}
