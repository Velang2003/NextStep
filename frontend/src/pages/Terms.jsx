import { Link } from 'react-router-dom';
import { Shield, ArrowLeft } from 'lucide-react';

export default function Terms() {
  return (
    <div className="min-h-screen bg-main text-main p-8 selection:bg-primary/30 relative">
      <div className="max-w-4xl mx-auto space-y-12 animate-in-slide relative z-10 py-12">
        <Link to="/" className="inline-flex items-center gap-2 text-muted hover:text-primary transition-colors font-bold text-sm uppercase tracking-widest">
          <ArrowLeft className="w-4 h-4" /> Back to Home
        </Link>
        
        <div className="space-y-4">
          <div className="w-16 h-16 bg-primary/10 rounded-2xl flex items-center justify-center text-primary mb-6">
            <Shield className="w-8 h-8" />
          </div>
          <h1 className="text-4xl md:text-5xl font-black font-outfit text-main">Terms of Service</h1>
          <p className="text-muted text-lg font-medium">Last updated: {new Date().toLocaleDateString()}</p>
        </div>

        <div className="surface-card p-8 md:p-12 space-y-8 prose prose-invert max-w-none prose-p:text-muted prose-headings:text-main prose-headings:font-outfit prose-a:text-primary">
          <section className="space-y-4">
            <h2 className="text-2xl font-bold">1. Agreement to Terms</h2>
            <p>
              By accessing or using NextStep ("Platform"), you agree to be bound by these Terms of Service. If you disagree with any part of the terms, you may not access the service.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-bold">2. Use License</h2>
            <p>
              Permission is granted to temporarily access the materials on NextStep for personal, non-commercial viewing only. This is the grant of a license, not a transfer of title.
            </p>
            <ul className="list-disc pl-6 space-y-2 text-muted">
              <li>You must not modify or copy the materials.</li>
              <li>You must not use the materials for any commercial purpose.</li>
              <li>You must not attempt to decompile or reverse engineer any software contained on the Platform.</li>
            </ul>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-bold">3. Platform Services and Assessments</h2>
            <p>
              NextStep provides career recommendations and skill assessments based on AI algorithms. We do not guarantee employment, job placements, or the complete accuracy of AI-generated insights. The assessments are designed to guide your career path and should be used as an educational and advisory tool.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-bold">4. User Accounts</h2>
            <p>
              When you create an account with us, you must provide accurate, complete, and current information at all times. Failure to do so constitutes a breach of the Terms, which may result in immediate termination of your account on our Service.
            </p>
            <p>
              You are responsible for safeguarding the password that you use to access the Service and for any activities or actions under your password.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-bold">5. Limitations</h2>
            <p>
              In no event shall NextStep or its suppliers be liable for any damages (including, without limitation, damages for loss of data or profit, or due to business interruption) arising out of the use or inability to use the materials on NextStep's website.
            </p>
          </section>
        </div>
      </div>
      
      {/* Background blobs */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute top-[-10%] right-[-5%] w-[50%] h-[50%] rounded-full bg-primary/5 blur-[150px]" />
        <div className="absolute bottom-[-10%] left-[-5%] w-[40%] h-[40%] rounded-full bg-secondary/5 blur-[150px]" />
      </div>
    </div>
  );
}
