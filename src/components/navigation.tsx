"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Brain, Home, Stethoscope, User, Moon, Sun, Settings, Database, Upload, BarChart3 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useTheme } from "next-themes"

const navigation = [
  { name: "Home", href: "/", icon: Home },
  { name: "Diagnosis", href: "/diagnosis", icon: Stethoscope },
  { name: "Training", href: "/admin", icon: Settings },
  { name: "Data Upload", href: "/data-upload", icon: Upload },
  { name: "Models", href: "/models", icon: BarChart3 },
  { name: "About", href: "/about", icon: Brain },
  { name: "Login", href: "/login", icon: User },
]

export function Navigation() {
  const pathname = usePathname()
  const { theme, setTheme } = useTheme()

  return (
    <nav className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between px-4">
        <div className="flex items-center space-x-4">
          <Link href="/" className="flex items-center space-x-2">
            <Brain className="h-8 w-8 text-primary" />
            <span className="text-xl font-bold font-heading">CarthaNeuro</span>
          </Link>
        </div>

        <div className="flex items-center space-x-4">
          {navigation.map((item) => {
            const Icon = item.icon
            return (
              <Link key={item.name} href={item.href}>
                <Button
                  variant={pathname === item.href ? "default" : "ghost"}
                  className="flex items-center space-x-2"
                >
                  <Icon className="h-4 w-4" />
                  <span className="hidden sm:inline">{item.name}</span>
                </Button>
              </Link>
            )
          })}

          <Button
            variant="ghost"
            size="icon"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          >
            <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
            <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
            <span className="sr-only">Toggle theme</span>
          </Button>
        </div>
      </div>
    </nav>
  )
}