import React, { Component } from 'react';

export class GlobalErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, info: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error("GlobalErrorBoundary Caught:", error, info);
    this.setState({ info });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '2rem', background: '#333', color: '#f87171', minHeight: '100vh', fontFamily: 'monospace' }}>
          <h2 style={{ color: '#ef4444' }}>Runtime Error Encountered!</h2>
          <p>{this.state.error && this.state.error.toString()}</p>
          <pre style={{ background: '#000', padding: '1rem', overflow: 'auto' }}>
            {this.state.info && this.state.info.componentStack}
          </pre>
        </div>
      );
    }
    return this.props.children;
  }
}
