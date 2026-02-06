'use client';

import Link from 'next/link';
import { Brain, Shield, Activity, Users, FileText, Zap, ArrowRight, CheckCircle } from 'lucide-react';

export default function HomePage() {
  const features = [
    {
      icon: Brain,
      title: 'AI-Powered Analysis',
      description: 'Advanced deep learning models for accurate Alzheimer\'s detection from MRI scans.',
    },
    {
      icon: FileText,
      title: 'Consultation Forms',
      description: 'Comprehensive patient history collection to enhance diagnostic accuracy.',
    },
    {
      icon: Activity,
      title: 'Real-Time Predictions',
      description: 'Instant analysis combining image and clinical data for quick results.',
    },

  ];

  const stats = [
    { value: 'Multi', label: 'Disease Classes' },
 
    { value: '24/7', label: 'Availability' },
  ];

  const steps = [
    {
      step: '1',
      title: 'Patient Consultation',
      description: 'Collect patient medical history and cognitive symptoms.',
    },
    {
      step: '2',
      title: 'MRI Upload',
      description: 'Upload brain MRI images for AI analysis.',
    },
    {
      step: '3',
      title: 'AI Processing',
      description: 'Models analyze both image and clinical data.',
    },
    {
      step: '4',
      title: 'Get Results',
      description: 'Receive comprehensive diagnosis and recommendations.',
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 bg-white/80 backdrop-blur-md z-50 border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <Brain className="w-8 h-8 text-medical" />
              <span className="text-xl font-bold text-gray-900">Cartha Neuro</span>
            </div>
            <div className="hidden md:flex items-center gap-6">
              <Link href="/about" className="text-gray-600 hover:text-medical transition-colors">
                About
              </Link>
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

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-4xl mx-auto">
            <div className="inline-flex items-center gap-2 bg-medical/10 text-medical px-4 py-2 rounded-full mb-6">
              <Activity className="w-4 h-4" />
              <span className="text-sm font-medium">AI-Powered Alzheimer's Detection</span>
            </div>
            <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6 leading-tight">
              Advanced MRI Analysis for{' '}
              <span className="text-medical">Early Detection</span>
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
              Cartha Neuro combines cutting-edge AI with clinical data to provide accurate
              Alzheimer's disease classification from brain MRI images.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/login?register=true" className="btn btn-primary text-lg px-8 py-3">
                Start Free Trial
                <ArrowRight className="w-5 h-5 ml-2" />
              </Link>
              <Link href="/about" className="btn btn-secondary text-lg px-8 py-3">
                Learn More
              </Link>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-16 max-w-4xl mx-auto">
            {stats.map((stat, index) => (
              <div key={index} className="stat-card text-center">
                <div className="text-3xl font-bold text-medical">{stat.value}</div>
                <div className="text-sm text-gray-600">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">How It Works</h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Simple four-step process for accurate Alzheimer's detection
            </p>
          </div>
          <div className="grid md:grid-cols-4 gap-8">
            {steps.map((item, index) => (
              <div key={index} className="relative">
                <div className="text-center">
                  <div className="w-12 h-12 bg-medical text-white rounded-full flex items-center justify-center text-xl font-bold mx-auto mb-4">
                    {item.step}
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">{item.title}</h3>
                  <p className="text-gray-600 text-sm">{item.description}</p>
                </div>
                {index < steps.length - 1 && (
                  <div className="hidden md:block absolute top-6 left-[60%] w-[80%] h-0.5 bg-gray-200">
                    <ArrowRight className="w-4 h-4 text-gray-400 absolute right-0 -top-1.5 transform translate-x-1/2" />
                  </div>
                )}
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
              Comprehensive tools for healthcare professionals and researchers
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

      {/* Benefits */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 mb-6">
                Accurate Diagnosis Through Combined Analysis
              </h2>
              <p className="text-gray-600 mb-6">
                Cartha Neuro doesn't just analyze MRI images in isolation. Our system
                combines cutting-edge image analysis with comprehensive patient consultation
                data for more accurate predictions.
              </p>
              <ul className="space-y-3">
                {[
                  '90% Image Analysis (EfficientNet/ResNet)',
                  '10% Clinical Data Assessment',
                  'Multi Disease Classification Categories',
                  'Real-time Risk Scoring',
                ].map((item, index) => (
                  <li key={index} className="flex items-center gap-2">
                    <CheckCircle className="w-5 h-5 text-green-500" />
                    <span className="text-gray-700">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="bg-gradient-to-br from-medical/10 to-purple-100 rounded-2xl p-8">
              <div className="bg-white rounded-xl shadow-lg p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Brain className="w-8 h-8 text-medical" />
                  <div>
                    <div className="font-semibold text-gray-900">AI Prediction</div>
                    <div className="text-sm text-gray-500">Combined Analysis</div>
                  </div>
                </div>
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600">Image Analysis</span>
                      <span className="font-medium">90%</span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div className="h-full bg-medical rounded-full" style={{ width: '60%' }} />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600">Clinical Data</span>
                      <span className="font-medium">10%</span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div className="h-full bg-purple-500 rounded-full" style={{ width: '40%' }} />
                    </div>
                  </div>
                </div>
                <div className="mt-4 pt-4 border-t">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-medical">90%</div>
                    <div className="text-sm text-gray-500">Overall Confidence</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-gradient-to-r from-medical to-neural text-white">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to Transform Alzheimer's Detection?</h2>
          <p className="text-white/80 mb-8 max-w-2xl mx-auto">
            Join healthcare professionals using Cartha Neuro for accurate, AI-powered
            Alzheimer's disease detection and patient management.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/login?register=true"
              className="btn bg-white text-medical hover:bg-gray-100 text-lg px-8 py-3"
            >
              Get Started Now
            </Link>
            <Link
              href="/about"
              className="btn border-2 border-white text-white hover:bg-white/10 text-lg px-8 py-3"
            >
              Contact Sales
            </Link>
          </div>
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
                AI-powered Alzheimer's detection system for healthcare professionals.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-gray-400 text-sm">
                <li><Link href="/about" className="hover:text-white">Features</Link></li>
                <li><Link href="/login" className="hover:text-white">Pricing</Link></li>
                <li><Link href="/about" className="hover:text-white">About</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Resources</h4>
              <ul className="space-y-2 text-gray-400 text-sm">
                <li><Link href="/about" className="hover:text-white">Documentation</Link></li>
                <li><Link href="/about" className="hover:text-white">API Reference</Link></li>
                <li><Link href="/about" className="hover:text-white">Support</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Legal</h4>
              <ul className="space-y-2 text-gray-400 text-sm">
                <li><Link href="/about" className="hover:text-white">Privacy Policy</Link></li>
                <li><Link href="/about" className="hover:text-white">Terms of Service</Link></li>
                <li><Link href="/about" className="hover:text-white">HIPAA Compliance</Link></li>
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

