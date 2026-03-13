import { Link } from 'react-router-dom';
import { XCircle } from 'lucide-react';

export default function PaymentCancel() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="text-center max-w-md mx-auto px-6">
        <XCircle className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
        <h1 className="text-2xl font-serif mb-2" data-testid="payment-cancelled">
          Payment Cancelled
        </h1>
        <p className="text-muted-foreground mb-6">
          Your payment was cancelled. No charges were made.
        </p>
        <Link
          to="/"
          className="text-primary hover:underline"
        >
          Return to Reach
        </Link>
      </div>
    </div>
  );
}
