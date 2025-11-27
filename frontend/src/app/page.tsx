import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Brain, ArrowRight, CheckCircle, Shield, Zap } from "lucide-react";
import { motion } from "framer-motion";

export default function Home() {
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-blue-50 via-white to-blue-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-600/10 to-blue-800/10" />
        <div className="relative container mx-auto px-4 py-24 sm:py-32">
          <div className="text-center max-w-4xl mx-auto">
            <div className="flex justify-center mb-8">
              <div className="p-4 bg-primary/10 rounded-full">
                <Brain className="h-16 w-16 text-primary" />
              </div>
            </div>
            <h1 className="text-4xl sm:text-6xl font-bold font-heading mb-6 bg-gradient-to-r from-slate-900 to-slate-600 dark:from-white dark:to-slate-300 bg-clip-text text-transparent">
              CarthaNeuro
            </h1>
            <p className="text-xl sm:text-2xl text-slate-600 dark:text-slate-300 mb-4 font-medium">
              L'intelligence tunisienne au service du cerveau humain
            </p>
            <p className="text-lg text-slate-500 dark:text-slate-400 mb-8 max-w-2xl mx-auto">
              Advanced AI platform for diagnosing neurodegenerative diseases from brain MRI images.
              Combining Tunisian innovation with cutting-edge explainable AI technology.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/diagnosis">
                <Button size="lg" className="text-lg px-8 py-6">
                  Try Diagnosis
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              <Link href="/about">
                <Button variant="outline" size="lg" className="text-lg px-8 py-6">
                  Learn More
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 bg-white dark:bg-slate-900">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold font-heading mb-4">
              How It Works
            </h2>
            <p className="text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
              Our explainable AI platform provides accurate diagnosis with complete transparency
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            <Card className="text-center p-8">
              <CardContent className="pt-6">
                <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-6">
                  <Shield className="h-8 w-8 text-primary" />
                </div>
                <h3 className="text-xl font-semibold mb-4">Secure Upload</h3>
                <p className="text-slate-600 dark:text-slate-400">
                  Upload your brain MRI images securely. We support PNG, JPG, and DICOM formats.
                </p>
              </CardContent>
            </Card>

            <Card className="text-center p-8">
              <CardContent className="pt-6">
                <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-6">
                  <Zap className="h-8 w-8 text-primary" />
                </div>
                <h3 className="text-xl font-semibold mb-4">AI Analysis</h3>
                <p className="text-slate-600 dark:text-slate-400">
                  Our advanced AI analyzes the images and provides diagnosis with confidence scores.
                </p>
              </CardContent>
            </Card>

            <Card className="text-center p-8">
              <CardContent className="pt-6">
                <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-6">
                  <CheckCircle className="h-8 w-8 text-primary" />
                </div>
                <h3 className="text-xl font-semibold mb-4">Explainable Results</h3>
                <p className="text-slate-600 dark:text-slate-400">
                  Get detailed reports with Grad-CAM visualizations showing what the AI focused on.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-slate-50 dark:bg-slate-800">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl sm:text-4xl font-bold font-heading mb-6">
            Ready to Get Started?
          </h2>
          <p className="text-lg text-slate-600 dark:text-slate-400 mb-8 max-w-2xl mx-auto">
            Join healthcare professionals worldwide using CarthaNeuro for accurate,
            explainable AI-powered neurodegenerative disease diagnosis.
          </p>
          <Link href="/diagnosis">
            <Button size="lg" className="text-lg px-8 py-6">
              Start Diagnosis
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </Link>
        </div>
      </section>
    </div>
  );
}
