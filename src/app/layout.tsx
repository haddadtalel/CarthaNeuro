import type { Metadata } from "next";
import { Inter, Poppins } from "next/font/google";
import { ThemeProvider } from "next-themes";
import "./globals.css";
import { Navigation } from "@/components/navigation";
import { AuthProvider } from "@/contexts/auth-context";
import { initializeAuthCleanup } from "@/lib/auth-utils";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const poppins = Poppins({
  variable: "--font-poppins",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "CarthaNeuro - Explainable AI for Neurodegenerative Disease Diagnosis",
  description: "L'intelligence tunisienne au service du cerveau humain. Advanced AI platform for diagnosing Alzheimer's and Parkinson's disease from brain MRI images.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${inter.variable} ${poppins.variable} font-sans antialiased bg-slate-50 text-slate-900 dark:bg-slate-900 dark:text-slate-100`}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <AuthProvider>
            <Navigation />
            <main className="min-h-screen">
              {children}
            </main>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
