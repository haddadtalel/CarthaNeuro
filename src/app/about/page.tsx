"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Brain,
  ArrowRight,
  Users,
  Award,
  Shield,
  Zap,
  Target,
  Heart,
  Microscope,
  Globe,
  CheckCircle,
  Star
} from "lucide-react"
import { motion } from "framer-motion"

const teamMembers = [
  {
    name: "Dr. Amira Ben Ali",
    role: "Chief Medical Officer",
    specialty: "Neurology & AI Ethics",
    image: "/api/placeholder/150/150"
  },
  {
    name: "Dr. Karim Mansouri",
    role: "Lead AI Researcher",
    specialty: "Machine Learning & Computer Vision",
    image: "/api/placeholder/150/150"
  },
  {
    name: "Dr. Leila ben salah",
    role: "Clinical Director",
    specialty: "Neurodegenerative Diseases",
    image: "/api/placeholder/150/150"
  }
]

const achievements = [
  {
    icon: Award,
    title: "ISO 13485 Certified",
    description: "Medical device quality management certification"
  },
  {
    icon: Shield,
    title: "HIPAA Compliant",
    description: "Patient data protection and privacy standards"
  },
  {
    icon: Target,
    title: "98.7% Accuracy",
    description: "Validated diagnostic accuracy across clinical trials"
  },
  {
    icon: Users,
    title: "50+ Hospitals",
    description: "Trusted by leading medical institutions worldwide"
  }
]

const features = [
  {
    icon: Brain,
    title: "Explainable AI",
    description: "Every diagnosis comes with detailed explanations of the AI's decision-making process"
  },
  {
    icon: Zap,
    title: "Real-time Analysis",
    description: "Get results in under 30 seconds with our optimized neural networks"
  },
  {
    icon: Shield,
    title: "Medical Grade Security",
    description: "End-to-end encryption and compliance with international medical standards"
  },
  {
    icon: Globe,
    title: "Multi-language Support",
    description: "Available in Arabic, French, and English for global accessibility"
  }
]

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-blue-50 via-white to-blue-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-600/10 to-blue-800/10" />
        <div className="relative container mx-auto px-4 py-24 sm:py-32">
          <div className="text-center max-w-4xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <div className="flex justify-center mb-8">
                <div className="p-4 bg-primary/10 rounded-full">
                  <Brain className="h-16 w-16 text-primary" />
                </div>
              </div>
              <h1 className="text-4xl sm:text-6xl font-bold font-heading mb-6 bg-gradient-to-r from-slate-900 to-slate-600 dark:from-white dark:to-slate-300 bg-clip-text text-transparent">
                About CarthaNeuro
              </h1>
              <p className="text-xl sm:text-2xl text-slate-600 dark:text-slate-300 mb-4">
                Pioneering Tunisian Innovation in Medical AI
              </p>
              <p className="text-lg text-slate-500 dark:text-slate-400 max-w-3xl mx-auto mb-8">
                CarthaNeuro represents the fusion of Tunisian scientific excellence and cutting-edge artificial intelligence,
                dedicated to revolutionizing neurodegenerative disease diagnosis through explainable, accessible, and accurate medical technology.
              </p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Mission Section */}
      <section className="py-24 bg-white dark:bg-slate-900">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-3xl sm:text-4xl font-bold font-heading mb-6">
              Our Mission
            </h2>
            <p className="text-lg text-slate-600 dark:text-slate-400 mb-12">
              To democratize access to advanced medical diagnostics through Tunisian innovation,
              making explainable AI-powered healthcare accessible to medical professionals worldwide.
            </p>

            <div className="grid md:grid-cols-3 gap-8">
              <Card className="text-center p-6">
                <CardContent className="pt-6">
                  <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-6">
                    <Heart className="h-8 w-8 text-primary" />
                  </div>
                  <h3 className="text-xl font-semibold mb-4">Patient-Centric</h3>
                  <p className="text-slate-600 dark:text-slate-400">
                    Every innovation starts with the patient, ensuring compassionate and accurate care.
                  </p>
                </CardContent>
              </Card>

              <Card className="text-center p-6">
                <CardContent className="pt-6">
                  <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-6">
                    <Microscope className="h-8 w-8 text-primary" />
                  </div>
                  <h3 className="text-xl font-semibold mb-4">Scientific Excellence</h3>
                  <p className="text-slate-600 dark:text-slate-400">
                    Grounded in rigorous research and validated through extensive clinical trials.
                  </p>
                </CardContent>
              </Card>

              <Card className="text-center p-6">
                <CardContent className="pt-6">
                  <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-6">
                    <Globe className="h-8 w-8 text-primary" />
                  </div>
                  <h3 className="text-xl font-semibold mb-4">Global Impact</h3>
                  <p className="text-slate-600 dark:text-slate-400">
                    Bringing Tunisian innovation to healthcare systems around the world.
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 bg-slate-50 dark:bg-slate-800">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold font-heading mb-4">
              Why Choose CarthaNeuro?
            </h2>
            <p className="text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
              Advanced technology meets medical expertise in our comprehensive diagnostic platform
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 max-w-6xl mx-auto">
            {features.map((feature, index) => {
              const Icon = feature.icon
              return (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  viewport={{ once: true }}
                >
                  <Card className="h-full p-6">
                    <CardContent className="pt-6">
                      <div className="flex items-start space-x-4">
                        <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                          <Icon className="h-6 w-6 text-primary" />
                        </div>
                        <div>
                          <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                          <p className="text-slate-600 dark:text-slate-400">{feature.description}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              )
            })}
          </div>
        </div>
      </section>

      {/* Achievements Section */}
      <section className="py-24 bg-white dark:bg-slate-900">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold font-heading mb-4">
              Our Achievements
            </h2>
            <p className="text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
              Recognized excellence in medical AI innovation and patient care
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 max-w-6xl mx-auto">
            {achievements.map((achievement, index) => {
              const Icon = achievement.icon
              return (
                <motion.div
                  key={achievement.title}
                  initial={{ opacity: 0, scale: 0.9 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  viewport={{ once: true }}
                >
                  <Card className="text-center p-6 h-full">
                    <CardContent className="pt-6">
                      <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-6">
                        <Icon className="h-8 w-8 text-primary" />
                      </div>
                      <h3 className="text-xl font-semibold mb-2">{achievement.title}</h3>
                      <p className="text-slate-600 dark:text-slate-400 text-sm">{achievement.description}</p>
                    </CardContent>
                  </Card>
                </motion.div>
              )
            })}
          </div>
        </div>
      </section>

      {/* Team Section */}
      <section className="py-24 bg-slate-50 dark:bg-slate-800">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold font-heading mb-4">
              Our Team
            </h2>
            <p className="text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
              World-class experts combining medical knowledge with AI innovation
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {teamMembers.map((member, index) => (
              <motion.div
                key={member.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
              >
                <Card className="text-center p-6 h-full">
                  <CardContent className="pt-6">
                    <div className="w-24 h-24 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-6">
                      <Users className="h-12 w-12 text-primary" />
                    </div>
                    <h3 className="text-xl font-semibold mb-2">{member.name}</h3>
                    <p className="text-primary font-medium mb-2">{member.role}</p>
                    <p className="text-slate-600 dark:text-slate-400 text-sm">{member.specialty}</p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Contact CTA */}
      <section className="py-24 bg-primary text-primary-foreground">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl sm:text-4xl font-bold font-heading mb-6">
            Ready to Transform Healthcare?
          </h2>
          <p className="text-lg opacity-90 mb-8 max-w-2xl mx-auto">
            Join the growing network of medical professionals using CarthaNeuro to provide
            cutting-edge diagnostic capabilities to their patients.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/login">
              <Button size="lg" variant="secondary" className="text-lg px-8 py-6">
                Get Started
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Link href="/diagnosis">
              <Button size="lg" variant="outline" className="text-lg px-8 py-6 border-primary-foreground text-primary-foreground hover:bg-primary-foreground hover:text-primary">
                Try Demo
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}