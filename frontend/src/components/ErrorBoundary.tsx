import React from 'react';

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

class ErrorBoundary extends React.Component<
  React.PropsWithChildren<{}>,
  ErrorBoundaryState
> {
  constructor(props: React.PropsWithChildren<{}>) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('=== React Error Boundary Caught Error ===');
    console.error('Error:', error);
    console.error('Error Info:', errorInfo);
    console.error('Stack trace:', error.stack);
    console.error('Component stack:', errorInfo.componentStack);
    console.error('Current URL:', window.location.href);
    console.error('User Agent:', navigator.userAgent);
    console.error('Time:', new Date().toISOString());

    this.setState({
      error,
      errorInfo
    });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="f1-error" style={{ margin: '2rem', minHeight: '50vh' }}>
          <div className="f1-error-title">💥 Application Error</div>
          <div style={{ marginBottom: '1rem' }}>
            Something went wrong with the React application.
          </div>
          
          {this.state.error && (
            <div style={{ marginBottom: '1rem' }}>
              <strong>Error:</strong> {this.state.error.message}
            </div>
          )}
          
          <div className="f1-error-details">
            URL: {window.location.href}
            <br />
            Time: {new Date().toLocaleString()}
            <br />
            User Agent: {navigator.userAgent.substring(0, 100)}...
            {this.state.error?.stack && (
              <>
                <br />
                <br />
                <strong>Stack Trace:</strong>
                <br />
                {this.state.error.stack.substring(0, 500)}...
              </>
            )}
            {this.state.errorInfo?.componentStack && (
              <>
                <br />
                <br />
                <strong>Component Stack:</strong>
                <br />
                {this.state.errorInfo.componentStack.substring(0, 500)}...
              </>
            )}
          </div>
          
          <div style={{ marginTop: '2rem', display: 'flex', gap: '1rem', justifyContent: 'center' }}>
            <button 
              onClick={() => window.location.reload()} 
              style={{
                padding: '0.75rem 1.5rem',
                background: '#ff6b35',
                border: 'none',
                borderRadius: '4px',
                color: 'white',
                cursor: 'pointer',
                fontWeight: 'bold'
              }}
            >
              🔄 Reload Page
            </button>
            
            <button 
              onClick={() => window.location.href = '/'} 
              style={{
                padding: '0.75rem 1.5rem',
                background: '#666',
                border: 'none',
                borderRadius: '4px',
                color: 'white',
                cursor: 'pointer',
                fontWeight: 'bold'
              }}
            >
              🏠 Go Home
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;