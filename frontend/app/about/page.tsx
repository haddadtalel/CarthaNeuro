'use client';

import Link from 'next/link';
import { Brain, Activity, Shield, Users, FileText, Server, Cpu, CheckCircle, ArrowRight } from 'lucide-react';

export default function AboutPage() {
  const features = [
    {
      icon: Brain,
      title: 'Advanced AI Models',
      description: 'Utilizing EfficientNet and ResNet architectures optimized for medical image analysis.',
    },
    {
      icon: Activity,
      title: 'Combined Analysis',
      description: 'Integrates MRI image analysis with patient consultation data for comprehensive diagnosis.',
    },
    {
      icon: Shield,
      title: 'Secure & Private',
      description: 'HIPAA-compliant data handling with role-based access control.',
    },
    {
      icon: Users,
      title: 'Multi-User Support',
      description: 'Separate interfaces for patients, doctors, and administrators.',
    },
    {
      icon: FileText,
      title: 'Detailed Reports',
      description: 'Comprehensive prediction reports with risk factors and recommendations.',
    },
    {
      icon: Server,
      title: 'MongoDB Atlas',
      description: 'Cloud-based database for secure and scalable data storage.',
    },
  ];

  const techStack = [
    { name: 'Next.js 14', category: 'Frontend Framework', icon: '⚛️' },
    { name: 'FastAPI', category: 'Backend Framework', icon: '🐍' },
    { name: 'MongoDB Atlas', category: 'Database', icon: '🍃' },
    { name: 'TensorFlow CPU', category: 'ML Framework', icon: '🧠' },
    { name: 'EfficientNet', category: 'AI Model', icon: '📊' },
    { name: 'ResNet50', category: 'AI Model', icon: '🔗' },
    { name: 'Tailwind CSS', category: 'Styling', icon: '🎨' },
    { name: 'JWT Auth', category: 'Authentication', icon: '🔐' },
  ];

  const diseaseClasses = [
    { class: "No Alzheimer's Disease", color: 'bg-green-100 text-green-800' },
    { class: 'Mild Cognitive Impairment', color: 'bg-yellow-100 text-yellow-800' },
    { class: 'Early Stage Alzheimer\'s', color: 'bg-orange-100 text-orange-800' },
    { class: 'Moderate Stage Alzheimer\'s', color: 'bg-red-100 text-red-800' },
    { class: 'Advanced Stage Alzheimer\'s', color: 'bg-purple-100 text-purple-800' },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link href="/" className="flex items-center gap-2">
              <Brain className="w-8 h-8 text-medical" />
              <span className="text-xl font-bold text-gray-900">Cartha Neuro</span>
            </Link>
            <div className="flex items-center gap-4">
              <Link href="/login" className="btn btn-secondary">
                Sign In
              </Link>
              <Link href="/login?register=true" className="btn btn-primary">
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="bg-gradient-to-r from-medical to-neural text-white py-20">
        <div className="max-w-7xl mx-auto px-4">
          <div className="text-center max-w-3xl mx-auto">
            <h1 className="text-4xl md:text-5xl font-bold mb-6">
              About Cartha Neuro
            </h1>
            <p className="text-xl text-white/80">
              An advanced AI-powered system for Alzheimer's disease detection from MRI images,
              combining deep learning with clinical data analysis.
            </p>
          </div>
        </div>
      </section>

      {/* What is Cartha Neuro */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 mb-6">
                What is Cartha Neuro?
              </h2>
              <p className="text-gray-600 mb-6">
                Cartha Neuro is a sophisticated web application designed to assist healthcare
                professionals in detecting and classifying Alzheimer's disease from brain MRI scans.
              </p>
              <p className="text-gray-600 mb-6">
                Our system combines state-of-the-art deep learning models (EfficientNet and ResNet)
                with comprehensive patient consultation data to provide accurate, reliable predictions.
              </p>
              <div className="flex flex-wrap gap-3">
                {['Early Detection', 'Accurate Classification', 'Clinical Integration', 'Research Ready'].map((tag) => (
                  <span key={tag} className="px-3 py-1 bg-medical/10 text-medical rounded-full text-sm">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
            <div className="bg-gradient-to-br from-medical/10 to-purple-100 rounded-2xl p-8">
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Prediction Model Weights</h3>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600">MRI Image Analysis</span>
                      <span className="font-medium">60%</span>
                    </div>
                    <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-medical to-medical-dark rounded-full" style={{ width: '60%' }} />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600">Clinical Consultation Data</span>
                      <span className="font-medium">40%</span>
                    </div>
                    <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-purple-500 to-purple-600 rounded-full" style={{ width: '40%' }} />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Disease Classification */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Disease Classification</h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Our AI model classifies MRI scans into four categories based on disease severity
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-4xl mx-auto">
            {diseaseClasses.map((item, index) => (
              <div key={index} className={`p-4 rounded-lg ${item.color}`}>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5" />
                  <span className="font-medium">{item.class}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Key Features</h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Comprehensive tools for Alzheimer's detection and patient management
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div key={index} className="card-hover">
                <div className="w-12 h-12 bg-medical/10 rounded-lg flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-medical" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-gray-600">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">How It Works</h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              A four-step process combining AI analysis with clinical expertise
            </p>
          </div>
          <div className="grid md:grid-cols-4 gap-8 max-w-5xl mx-auto">
            {[
              { step: 1, title: 'Patient Data', desc: 'Collect medical history and symptoms' },
              { step: 2, title: 'MRI Upload', desc: 'Upload brain MRI scan image' },
              { step: 3, title: 'AI Analysis', desc: 'Process with deep learning models' },
              { step: 4, title: 'Get Results', desc: 'View prediction and recommendations' },
            ].map((item, index) => (
              <div key={index} className="text-center">
                <div className="w-16 h-16 bg-medical text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                  {item.step}
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">{item.title}</h4>
                <p className="text-gray-600 text-sm">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-gradient-to-r from-medical to-neural text-white">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to Get Started?</h2>
          <p className="text-white/80 mb-8">
            Join healthcare professionals using Cartha Neuro for accurate Alzheimer's detection.
          </p>
          <Link
            href="/login?register=true"
            className="btn bg-white text-medical hover:bg-gray-100 text-lg px-8 py-3 inline-flex items-center gap-2"
          >
            Start Free Trial
            <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <Brain className="w-6 h-6 text-medical" />
                <span className="text-lg font-bold">Cartha Neuro</span>
              </div>
              <p className="text-gray-400 text-sm">
                AI-powered Alzheimer's detection system.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-gray-400 text-sm">
                <li><Link href="/" className="hover:text-white">Home</Link></li>
                <li><Link href="/about" className="hover:text-white">About</Link></li>
                <li><Link href="/login" className="hover:text-white">Login</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Resources</h4>
              <ul className="space-y-2 text-gray-400 text-sm">
                <li><span className="cursor-not-allowed opacity-50">Documentation</span></li>
                <li><span className="cursor-not-allowed opacity-50">API Reference</span></li>
                <li><span className="cursor-not-allowed opacity-50">Support</span></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Legal</h4>
              <ul className="space-y-2 text-gray-400 text-sm">
                <li><span className="cursor-not-allowed opacity-50">Privacy Policy</span></li>
                <li><span className="cursor-not-allowed opacity-50">Terms of Service</span></li>
                <li><span className="cursor-not-allowed opacity-50">HIPAA Compliance</span></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400 text-sm">
            © 2024 Cartha Neuro. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}

