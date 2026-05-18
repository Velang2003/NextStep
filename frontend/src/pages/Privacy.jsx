import { Link } from 'react-router-dom';
import { Lock, ArrowLeft } from 'lucide-react';

export default function Privacy() {
  return (
    <div className="min-h-screen bg-main text-main p-8 selection:bg-primary/30 relative">
      <div className="max-w-4xl mx-auto space-y-12 animate-in-slide relative z-10 py-12">
        <Link to="/" className="inline-flex items-center gap-2 text-muted hover:text-primary transition-colors font-bold text-sm uppercase tracking-widest">
          <ArrowLeft className="w-4 h-4" /> Back to Home
        </Link>
        
        <div className="space-y-4">
          <div className="w-16 h-16 bg-secondary/10 rounded-2xl flex items-center justify-center text-secondary mb-6">
            <Lock className="w-8 h-8" />
          </div>
          <h1 className="text-4xl md:text-5xl font-black font-outfit text-main">Privacy Policy</h1>
          <p className="text-muted text-lg font-medium">Last updated: {new Date().toLocaleDateString()}</p>
        </div>

        <div className="surface-card p-8 md:p-12 space-y-8 prose prose-invert max-w-none prose-p:text-muted prose-headings:text-main prose-headings:font-outfit prose-a:text-primary">
          <section className="space-y-4">
            <h2 className="text-2xl font-bold">1. Information We Collect</h2>
            <p>
              We collect information that you provide directly to us when you create an account, complete your profile, or take our AI-driven skill assessments.
            </p>
            <ul className="list-disc pl-6 space-y-2 text-muted">
              <li><strong>Personal Data:</strong> Name, email address, and authentication credentials.</li>
              <li><strong>Professional Data:</strong> Skills, target job roles, sector preferences, and assessment scores.</li>
              <li><strong>Usage Data:</strong> How you interact with the NextStep platform, including page views and feature usage.</li>
            </ul>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-bold">2. How We Use Your Information</h2>
            <p>
              The primary purpose of collecting your information is to provide you with personalized career roadmaps and intelligent job market insights.
            </p>
            <ul className="list-disc pl-6 space-y-2 text-muted">
              <li>To provide, maintain, and improve our services.</li>
              <li>To match your skills and assessment results with live job listings.</li>
              <li>To communicate with you regarding updates, security alerts, and administrative messages.</li>
            </ul>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-bold">3. Data Security</h2>
            <p>
              We implement industry-standard security measures to protect your personal information. Your authentication is securely managed by Firebase, and we do not store raw passwords on our servers. However, no method of transmission over the Internet or electronic storage is 100% secure.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-bold">4. Third-Party Services</h2>
            <p>
              We use third-party APIs (such as Google Gemini) to analyze job trends and extract skills. We only transmit anonymized or minimal necessary data to these services to protect your privacy. 
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-2xl font-bold">5. Your Data Rights</h2>
            <p>
              You have the right to access, update, or delete your personal information at any time. You can do this through your account settings or by contacting our support team.
            </p>
          </section>
        </div>
      </div>
      
      {/* Background blobs */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute top-[-10%] right-[-5%] w-[50%] h-[50%] rounded-full bg-secondary/5 blur-[150px]" />
        <div className="absolute bottom-[-10%] left-[-5%] w-[40%] h-[40%] rounded-full bg-primary/5 blur-[150px]" />
      </div>
    </div>
  );
}
